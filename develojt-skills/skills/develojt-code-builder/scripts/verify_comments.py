#!/usr/bin/env python3
"""
Comment language verification script

Checks that the comment block on every class/function declaration follows the configured
language. The language comes from the convention (.claude/rules/code-conventions.md),
item comment-language.
- english (default for this package): presence of a substantive English description —
  if the SPEC is English, comments must be English too, so they match the design terminology and design↔code cross-checking is fast.
  A block holding only @tags (@spec etc.), symbols, or non-English text does not count.
- korean: presence of Korean text in the comment block.

Language resolution priority: --lang= flag > convention comment-language > english fallback.

Usage:
    python3 scripts/verify_comments.py src/
    python3 scripts/verify_comments.py src/ --lang=korean
    python3 scripts/verify_comments.py src/core/handler.js
    python3 scripts/verify_comments.py src/file1.ts src/file2.ts src/file3.ts
"""

import sys
import os
import re
import json


# A "substantive description" = at least one comment line that is not an @tag line
# and contains an alphabetic word of 2+ letters.
WORD_RE = re.compile(r'[A-Za-z]{2,}')

# korean mode: presence of Korean (Hangul) text in the comment block
KOREAN_RE = re.compile(r'[\uAC00-\uD7AF\u3131-\u3163]')

# Convention file location (assumes execution from the project root — same CWD as the builder gate)
CONVENTIONS_PATH = os.path.join('.claude', 'rules', 'code-conventions.md')
VALID_LANGS = ('english', 'korean')

SUPPORTED_EXT = (
    '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue',
    '.py', '.cs', '.java', '.cpp', '.cc', '.cxx', '.h', '.hpp',
)

SKIP_DIRS = {'node_modules', 'dist', 'build', 'tests', '__tests__',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

# Class/function declarations (cast wide — every public declaration must carry a doc comment)
DECL_PATTERNS = [
    # JS/TS
    re.compile(r'^\s*(export\s+)?(default\s+)?class\s+(\w+)'),
    re.compile(r'^\s*(export\s+)?(default\s+)?function\s+(\w+)'),
    # const/let/var function assignment — only when the RHS is the function keyword or an arrow (=>).
    # Matching a bare `= (` mistakes ordinary paren-first expressions (`const x = (a*b)/c`) for functions (false-positive fix).
    re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function\b|\([^)]*\)(?:\s*:\s*[^=>{]+)?\s*=>|\w+\s*=>)'),
    re.compile(r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{'),
    # Python
    re.compile(r'^\s*(async\s+)?def\s+(\w+)'),
    # C#/Java
    re.compile(r'^\s*(public|private|protected|internal|static|abstract|sealed|partial|final|synchronized)\s+.*\s+(\w+)\s*\('),
    re.compile(r'^\s*(public|private|protected|internal|static|abstract|sealed|partial)\s+.*(class|struct|interface|enum)\s+(\w+)'),
    # C++
    re.compile(r'^\s*(class|struct)\s+(\w+)'),
]

IGNORE_PATTERNS = [
    re.compile(r'^\s*(if|else|elif|for|foreach|while|switch|return|try|catch|except|throw|import|from|using|namespace|package|#include|console|new |this\.|self\.|super\()'),
    re.compile(r'^\s*(//|/\*|\*|#(?!include)|"""|\'\'\'|@Override|@Deprecated)'),
]

SKIP_NAMES = {'constructor', '__init__', '__str__', '__repr__', 'get', 'set',
              'toString', 'hashCode', 'equals', 'main'}

DECORATOR_RE = re.compile(r'^\s*@\w')

# js/ts-only depth-tracking extensions (vue excluded because of template interpolation {{ }})
JS_TS_EXT = ('.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx')


def decorator_lines(lines):
    """Builds the index set of decorator/annotation (@name) lines and their multi-line argument lines.

    The comment search above a declaration passes through (continues over) these lines,
    so universal patterns like @app.route(...) and @Override never break the comment block.
    """
    marked = set()
    i = 0
    while i < len(lines):
        if DECORATOR_RE.match(lines[i]):
            marked.add(i)
            depth = lines[i].count('(') - lines[i].count(')')
            j = i
            # Multi-line arguments: lines continuing until the paren closes are part of the decorator
            while depth > 0 and j + 1 < len(lines) and j - i < 20:
                j += 1
                marked.add(j)
                depth += lines[j].count('(') - lines[j].count(')')
            i = j + 1
        else:
            i += 1
    return marked


def _brace_depths(lines):
    """Computes the brace depth at the start of each line (a js/ts-only heuristic).

    Braces inside strings, template literals, and comments are excluded from the depth.
    Used to exclude local const/let/var declarations inside function bodies from the
    doc-comment requirement. It is not a perfect parser, so the exclusion judgment
    requires 'indentation present' on top of 'depth > 0' — even when tracking skews,
    top-level declarations are never dropped.
    """
    depths = []
    depth = 0
    in_block_comment = False
    in_template = False
    for line in lines:
        depths.append(depth)
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if in_block_comment:
                if ch == '*' and i + 1 < n and line[i + 1] == '/':
                    in_block_comment = False
                    i += 1
                i += 1
                continue
            if in_template:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '`':
                    in_template = False
                i += 1
                continue
            if ch == '/' and i + 1 < n and line[i + 1] == '/':
                break  # line comment
            if ch == '/' and i + 1 < n and line[i + 1] == '*':
                in_block_comment = True
                i += 2
                continue
            if ch in ('"', "'"):
                quote = ch
                i += 1
                while i < n and line[i] != quote:
                    i += 2 if line[i] == '\\' else 1
                i += 1
                continue
            if ch == '`':
                in_template = True
                i += 1
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth = max(0, depth - 1)
            i += 1
    return depths


def find_source_files(path):
    """Returns the source file list under the target path"""
    if os.path.isfile(path):
        return [path] if path.lower().endswith(SUPPORTED_EXT) else []
    result = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.lower().endswith(SUPPORTED_EXT):
                result.append(os.path.join(root, f))
    return sorted(result)


def extract_name(line):
    """Extracts the class/function name from a declaration line"""
    for p in DECL_PATTERNS:
        m = p.match(line)
        if m:
            groups = [g for g in m.groups() if g and g.strip() not in
                      ('async', 'export', 'default', 'const', 'let', 'var',
                       'public', 'private', 'protected', 'internal', 'static',
                       'virtual', 'override', 'abstract', 'sealed', 'partial',
                       'final', 'synchronized', 'inline', '(', 'function',
                       'class', 'struct', 'interface', 'enum', 'def', 'async def')]
            if groups:
                return groups[-1].strip()
    return None


def get_comment_above(lines, idx, deco_lines=frozenset()):
    """Returns the text of the comment block directly above a declaration (up to 25 lines up).

    Decorator/annotation lines (deco_lines) are passed through — they never break the comment block."""
    comment_text = []
    for j in range(idx - 1, max(-1, idx - 26), -1):
        if j in deco_lines:
            continue
        s = lines[j].strip()
        if s.startswith(('*/', '*/;')):
            # Block-comment end → collect upward until its start
            comment_text.insert(0, s)
            for k in range(j - 1, max(-1, j - 30), -1):
                comment_text.insert(0, lines[k].strip())
                if lines[k].strip().startswith(('/**', '/*')):
                    break
            break
        elif s.startswith(('*', '/**', '/*', '//', '#')):
            comment_text.insert(0, s)
        elif s == '':
            if comment_text:
                break
            continue
        else:
            break
    return '\n'.join(comment_text)


def _read_docstring_at(lines, start):
    """Reads the docstring text starting at line `start` ('' if none)"""
    if start >= len(lines):
        return ''
    next_s = lines[start].strip()
    if not next_s.startswith(('"""', "'''", 'r"""', "r'''")):
        return ''
    parts = [next_s]
    if next_s.count('"""') >= 2 or next_s.count("'''") >= 2:
        return next_s
    for k in range(start + 1, min(len(lines), start + 29)):
        parts.append(lines[k].strip())
        if lines[k].strip().endswith(('"""', "'''")):
            break
    return '\n'.join(parts)


def get_docstring_below(lines, idx):
    """Returns the text of a Python docstring (below the declaration header).

    The line right after the declaration is tried first (single-line signatures — the
    previous behavior, unchanged). If that is empty and the declaration line's parens are
    still open, this is a multi-line signature — paren-balance tracking finds the header's
    end (the `) -> T:` line) and reads the next line. The new search fires only where the
    old code returned '', so previously found docstrings keep their result, and a tracking
    failure (window exceeded, unbalanced parens) ends empty-handed just like before.
    """
    found = _read_docstring_at(lines, idx + 1)
    if found:
        return found
    depth = lines[idx].count('(') - lines[idx].count(')')
    if depth <= 0:
        return ''
    for k in range(idx + 1, min(len(lines), idx + 31)):
        depth += lines[k].count('(') - lines[k].count(')')
        if depth <= 0:
            return _read_docstring_at(lines, k + 1)
    return ''


def has_substantive_text(comment):
    """Whether the comment block contains a substantive English description (english mode).

    An @tag line (@spec, @param, @returns, …) is not a description. An English description means
    at least one non-tag line carrying an alphabetic word of 2+ letters (a line holding only non-English text does not count).
    """
    for raw in comment.splitlines():
        line = raw.strip().lstrip('/*#').strip().rstrip('*/').strip()
        if not line:
            continue
        if line.startswith('@'):
            continue
        if WORD_RE.search(line):
            return True
    return False


def resolve_lang(argv):
    """Resolves the verification language. Priority: --lang= flag > convention comment-language > english fallback.

    An invalid value exits immediately with an error (silently letting a configuration typo fall back to english would distort the gate).
    """
    for a in argv:
        if a.startswith('--lang='):
            lang = a.split('=', 1)[1].strip().lower()
            if lang not in VALID_LANGS:
                print(f"❌ Invalid --lang value: {lang} (english|korean)")
                sys.exit(1)
            return lang
    if os.path.isfile(CONVENTIONS_PATH):
        with open(CONVENTIONS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = re.match(r'^comment-language:\s*(\S+)', line.strip())
                if m:
                    lang = m.group(1).lower()
                    if lang not in VALID_LANGS:
                        print(f"❌ Invalid comment-language value in the convention: {lang} (english|korean) — {CONVENTIONS_PATH}")
                        sys.exit(1)
                    return lang
    return 'english'


def check_file(filepath, lang='english'):
    """
    Checks that each class/function comment in the file follows the configured language. english: a substantive description exists (@tags/symbols alone do not count) / korean: the comment block contains Korean text.

    Returns: (list of items without a description, count with one)
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    no_desc = []
    ok_count = 0

    # Decorator/annotation line set — passed through in the comment search
    deco_lines = decorator_lines(lines)
    # js/ts only: brace depth — for excluding local const/let/var inside function bodies
    is_js_ts = filepath.lower().endswith(JS_TS_EXT)
    depths = _brace_depths(lines) if is_js_ts else None

    for i, line in enumerate(lines):
        if any(ip.match(line) for ip in IGNORE_PATTERNS):
            continue
        stripped = line.strip()
        if not stripped or stripped in ('{', '}', '};', ')', ');'):
            continue

        # Local const/let/var declarations inside a function body (arrow helpers etc.) are not doc-comment targets.
        # Depth tracking can skew, so 'indentation present' is required on top of 'depth > 0' (prevents top-level misses).
        if (depths is not None and depths[i] > 0 and line[:1] in (' ', '\t')
                and re.match(r'^(const|let|var)\b', stripped)):
            continue

        name = extract_name(line)
        if not name or name in SKIP_NAMES:
            continue

        # Skip Python private helpers
        if name.startswith('_') and not name.startswith('__'):
            continue

        # Collect comments: the block above + Python docstring (passing through decorator/annotation lines)
        comment = get_comment_above(lines, i, deco_lines)
        comment += '\n' + get_docstring_below(lines, i)

        if not comment.strip():
            # No comment at all — it cannot be satisfied in either language, so it's an omission
            no_desc.append({
                'line': i + 1,
                'name': name,
                'code': stripped,
                'reason': 'no comment'
            })
        elif (has_substantive_text(comment) if lang == 'english'
              else KOREAN_RE.search(comment)):
            ok_count += 1
        else:
            no_desc.append({
                'line': i + 1,
                'name': name,
                'code': stripped,
                'reason': ('no English description (@tags/symbols/non-English only)' if lang == 'english'
                           else 'no Korean text in the comment')
            })

    return no_desc, ok_count


def main():
    # Collect positional args, excluding flags like --json
    targets = [a for a in sys.argv[1:] if not a.startswith('--')]

    if not targets:
        print("Usage: python3 scripts/verify_comments.py <path> [path2 ...]")
        print("  e.g.: python3 scripts/verify_comments.py src/")
        print("  e.g.: python3 scripts/verify_comments.py src/file1.ts src/file2.ts")
        sys.exit(1)

    files = []
    for target in targets:
        if not os.path.exists(target):
            print(f"❌ Path not found: {target}")
            sys.exit(1)
        files.extend(find_source_files(target))

    # De-duplicate (order preserved)
    seen = set()
    unique_files = []
    for f in files:
        af = os.path.abspath(f)
        if af not in seen:
            seen.add(af)
            unique_files.append(f)
    files = unique_files

    if not files:
        print(f"⚠️  No source files found: {' '.join(targets)}")
        sys.exit(0)

    lang = resolve_lang(sys.argv[1:])
    # per-language labels (english: substantive description / korean: Korean text)
    crit = 'description' if lang == 'english' else 'Korean comment'

    total_no_desc = []
    total_ok = 0

    for fp in files:
        missing, ok = check_file(fp, lang)
        total_ok += ok
        for item in missing:
            item['file'] = fp
            total_no_desc.append(item)

    total = total_ok + len(total_no_desc)
    ratio = (total_ok / total * 100) if total > 0 else 0

    # --json mode: print the structured result and exit
    if '--json' in sys.argv:
        print(json.dumps({
            'type': 'comments',
            'lang': lang,
            'ok': total_ok,
            'fail': len(total_no_desc),
            'ratio': round(ratio, 1),
            'missing': [{'file': os.path.relpath(m['file']), 'line': m['line'], 'name': m['name'], 'reason': m['reason']} for m in total_no_desc]
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  Comment language verification results (comment-language: {lang})")
    print(f"{'='*60}")
    print(f"  Files checked:        {len(files)}")
    print(f"  Declarations total:   {total}")
    print(f"  Compliant:            {total_ok}")
    print(f"  Non-compliant:        {len(total_no_desc)}")
    print(f"  Compliance ratio:     {ratio:.1f}%")
    print(f"{'='*60}\n")

    if total_no_desc:
        print(f"❌ Items without a {crit}:\n")
        for item in total_no_desc:
            rel = os.path.relpath(item['file'])
            print(f"  {rel}:{item['line']}  {item['name']}  ({item['reason']})")
            print(f"    {item['code']}\n")
        print(f"\nFAIL — add a {crit} to {len(total_no_desc)} item(s).")
        sys.exit(1)
    else:
        if total == 0:
            print("⚠️  0 checks — possibly unsupported syntax (e.g., cpp free functions/qualified definitions). Confirm comments manually.")
        print(f"✅ PASS — every class/function carries a {crit}.")
        sys.exit(0)


if __name__ == '__main__':
    main()
