#!/usr/bin/env python3
"""
@spec tag verification script (multi-language)

Checks that an @spec tag exists above every class and function declaration.
Prints items with a missing or malformed @spec tag, and returns FAIL if there is even one.

Checks:
1. @spec tag existence — missing = FAIL
2. @spec format — one per line, separated from descriptions
   ✅ @spec FR-04-001        (standalone line)
   ❌ description @spec FR-04-001   (mixed with a description)
   ❌ @spec FR-01, FR-02     (comma-separated)
3. Duplicate IDs within one declaration — the same @spec ID twice in the same block = FAIL
   (the 'merge without duplicates' rule for function merges — the same ID on different declarations is normal)

Supported languages: JavaScript, TypeScript, Python, C#, Java, C++, Vue (SFC)
(cpp is partially supported — qualified definitions (Type Class::method) are detected only at top level (indent 0))

Usage:
    python3 scripts/verify_refs.py src/
    python3 scripts/verify_refs.py src/core/handler.js
    python3 scripts/verify_refs.py src/file1.ts src/file2.ts src/file3.ts
    python3 scripts/verify_refs.py src/services/auth.py
"""

import sys
import os
import re
import json


# Per-language extension mapping
LANG_EXTENSIONS = {
    'js':     ('.js', '.mjs', '.cjs', '.jsx'),
    'ts':     ('.ts', '.tsx'),
    'vue':    ('.vue',),
    'python': ('.py',),
    'csharp': ('.cs',),
    'java':   ('.java',),
    'cpp':    ('.cpp', '.cc', '.cxx', '.h', '.hpp'),
}

ALL_EXTENSIONS = tuple(ext for exts in LANG_EXTENSIONS.values() for ext in exts)

SKIP_DIRS = {'node_modules', 'dist', 'build', 'tests', '__tests__',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

# @spec format check patterns
# The correct form: the line has only @spec and an ID (comment markers * // # allowed)
GOOD_REF_RE = re.compile(
    r'^\s*(?:\*|//|#)?\s*@spec\s+(?:FR|NFR)-\d+-(?:\d+|E\d+)\s*$'
)
# Any line containing @spec (format-agnostic)
ANY_REF_RE = re.compile(r'@spec\s+(?:FR|NFR)-\d+')
# Multiple IDs joined by commas
COMMA_REF_RE = re.compile(r'@spec\s+.*,')
# Captures only the ID from an @spec line (for duplicate-ID-within-one-declaration detection)
ID_CAPTURE_RE = re.compile(r'@spec\s+((?:FR|NFR)-\d+-(?:\d+|E\d+))')


def detect_lang(filepath):
    """Determines the language from the file extension"""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    for lang, exts in LANG_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None


def find_source_files(path):
    """Returns the supported source file list under the target path"""
    if os.path.isfile(path):
        return [path] if path.lower().endswith(ALL_EXTENSIONS) else []

    source_files = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.lower().endswith(ALL_EXTENSIONS):
                source_files.append(os.path.join(root, f))
    return sorted(source_files)


# ─── Common helpers ─────────────────────────────────────────────

DECORATOR_RE = re.compile(r'^\s*@\w')


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
    @spec requirement. It is not a perfect parser, so the exclusion judgment requires
    'indentation present' on top of 'depth > 0' — even when tracking skews,
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


# ─── Per-language declaration patterns ──────────────────────────

def _js_ts_patterns():
    return [
        re.compile(r'^\s*export\s+(default\s+)?class\s+(\w+)'),
        re.compile(r'^\s*class\s+(\w+)'),
        re.compile(r'^\s*(export\s+)?(default\s+)?function\s+(\w+)'),
        re.compile(r'^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\('),
        re.compile(r'^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function'),
        # Paren-less single-argument arrows (const f = x => …) — same branch as verify_comments
        re.compile(r'^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\w+\s*=>'),
        re.compile(r'^\s*(async\s+)?(\w+)\s*\('),
    ]

def _js_multiline_call(lines, decl_idx):
    """Determines whether this is a multi-line function 'call' (a JS/TS/Vue-only helper).

    From a `name(` line, search a bounded window (30 lines) to where the paren closes;
    if a block start follows ('{' or a TS return type '+ {'), it's a declaration — otherwise a call.
    When determination is uncertain (parens inside strings etc.), return False to keep the
    existing conservative behavior (catch it first; the LLM judges genuineness).
    """
    depth = 0
    started = False
    for k in range(decl_idx, min(len(lines), decl_idx + 30)):
        for ch_idx, ch in enumerate(lines[k]):
            if ch == '(':
                depth += 1
                started = True
            elif ch == ')' and started:
                depth -= 1
                if depth == 0:
                    rest = lines[k][ch_idx + 1:].strip()
                    if not rest:
                        for k2 in range(k + 1, min(len(lines), k + 3)):
                            nxt = lines[k2].strip()
                            if nxt:
                                rest = nxt
                                break
                    # A declaration is followed by '{' / '=>' / ': return-type { or =>' after the closing paren
                    if (rest.startswith('{') or rest.startswith('=>')
                            or re.match(r'^:\s*[\w<>\[\]., |&]+\s*(\{|=>)', rest)):
                        return False
                    return True
    return False


def _js_ts_ignores():
    return [
        re.compile(r'^\s*(if|else|for|while|switch|return|try|catch|throw|import|from|console|new|typeof|delete|void|await)'),
        re.compile(r'^\s*this\.'),
        re.compile(r'^\s*super\('),
        re.compile(r'^\s*(//|/\*|\*)'),
    ]

def _python_patterns():
    return [
        re.compile(r'^\s*class\s+(\w+)'),
        re.compile(r'^\s*(async\s+)?def\s+(\w+)'),
    ]

def _python_ignores():
    return [
        re.compile(r'^\s*(if|else|elif|for|while|return|try|except|raise|import|from|with|assert|pass|yield)'),
        re.compile(r'^\s*self\.'),
        re.compile(r'^\s*(#|"""|\'\'\'|\')'),
    ]

def _csharp_patterns():
    return [
        re.compile(r'^\s*(public|private|protected|internal|static|abstract|sealed|partial)\s+.*(class|struct|interface|enum)\s+(\w+)'),
        re.compile(r'^\s*(public|private|protected|internal|static|virtual|override|abstract|async)\s+[\w<>\[\],\s]+\s+(\w+)\s*\('),
    ]

def _csharp_ignores():
    return [
        re.compile(r'^\s*(if|else|for|foreach|while|switch|return|try|catch|throw|using|namespace|var|new)'),
        re.compile(r'^\s*(//|/\*|\*)'),
    ]

def _java_patterns():
    return [
        re.compile(r'^\s*(public|private|protected|static|abstract|final)?\s*(class|interface|enum)\s+(\w+)'),
        re.compile(r'^\s*(public|private|protected|static|final|abstract|synchronized)?\s+[\w<>\[\]]+\s+(\w+)\s*\('),
    ]

def _java_ignores():
    return [
        re.compile(r'^\s*(if|else|for|while|switch|return|try|catch|throw|import|package|new|super)'),
        re.compile(r'^\s*(//|/\*|\*|@Override|@Deprecated)'),
    ]

def _cpp_patterns():
    return [
        re.compile(r'^\s*(class|struct)\s+(\w+)'),
        # Qualified definitions (Type Class::method / Class::Class / Class::~Class) —
        # detected only at top level (indent 0). Prevents false positives on indented qualified calls (Logger::log(...)).
        re.compile(r'^(?:(?:virtual|static|inline)\s+)*(?:[\w:<>]+[\s*&]+)?[\w:]+::(~?\w+)\s*\('),
        re.compile(r'^\s*(virtual\s+|static\s+|inline\s+)*([\w:]+[\s*&]+)+(\w+)\s*\('),
    ]

def _cpp_ignores():
    return [
        re.compile(r'^\s*(if|else|for|while|switch|return|try|catch|throw|#include|#define|#pragma|using|namespace|template)'),
        re.compile(r'^\s*(//|/\*|\*)'),
    ]

LANG_CONFIG = {
    'js':     {'patterns': _js_ts_patterns,  'ignores': _js_ts_ignores,   'skip_names': {'constructor', 'get', 'set'}},
    'ts':     {'patterns': _js_ts_patterns,  'ignores': _js_ts_ignores,   'skip_names': {'constructor', 'get', 'set'}},
    'vue':    {'patterns': _js_ts_patterns,  'ignores': _js_ts_ignores,   'skip_names': {'constructor', 'get', 'set'}},
    'python': {'patterns': _python_patterns, 'ignores': _python_ignores,  'skip_names': {'__init__', '__str__', '__repr__'}},
    'csharp': {'patterns': _csharp_patterns, 'ignores': _csharp_ignores,  'skip_names': set()},
    'java':   {'patterns': _java_patterns,   'ignores': _java_ignores,    'skip_names': set()},
    'cpp':    {'patterns': _cpp_patterns,    'ignores': _cpp_ignores,     'skip_names': set()},
}


def check_ref_format(lines, decl_idx, deco_lines=frozenset()):
    """
    Checks the @spec format in the comment block directly above the declaration.
    Detects the comment block's boundary precisely, never mis-referencing another function's comment.
    Decorator/annotation lines (deco_lines) are passed through — they never break the comment block.

    Returns: (has_ref, format_issues)
      has_ref: True if at least one @spec tag exists
      format_issues: list of malformed lines [{line, text, reason}]
    """
    # Stage 1: determine the extent of the comment block directly above the declaration
    comment_start = -1
    comment_end = decl_idx - 1  # from the line right above the declaration

    # Search upward for the comment block's start.
    # The boundary is decided by a 'blank line' or a 'code line' (logic below). The hard cap is
    # merely a safety stop for abnormally long files, so it is generous (prevents misjudging a
    # missing @spec above a long doc comment).
    for j in range(decl_idx - 1, max(-1, decl_idx - 200), -1):
        # Pass through decorator/annotation lines (the @spec comment may sit above them)
        if j in deco_lines:
            continue

        stripped = lines[j].strip()

        # Blank line: a blank line above the comment block is the boundary
        if not stripped:
            if comment_start >= 0:
                break  # once a comment was found, a blank line is the boundary
            continue

        # Check whether it's a comment line
        is_comment = (
            stripped.startswith(('*', '/**', '/*', '*/', '//', '#'))
            or stripped.startswith(("'''", '"""'))
        )

        if is_comment:
            comment_start = j
        else:
            # Hitting a code line ends the comment block (the previous function's body)
            break

    if comment_start < 0:
        # No comment block
        return False, []

    # Stage 2: check @spec within the comment block
    has_ref = False
    format_issues = []
    seen_ids = {}  # ID → first-occurrence line within this declaration (this block). For duplicate detection

    for j in range(comment_start, decl_idx):
        line = lines[j]
        stripped = line.rstrip()

        if not ANY_REF_RE.search(stripped):
            continue

        has_ref = True

        # Check 0: duplicate IDs within one declaration — never tag the same @spec ID twice in the same block.
        # (The same ID on different declarations is normal — one requirement spanning several functions. Per-block checks never catch that case.)
        id_m = ID_CAPTURE_RE.search(stripped)
        if id_m:
            sid = id_m.group(1)
            if sid in seen_ids:
                format_issues.append({
                    'line': j + 1,
                    'text': stripped.strip(),
                    'reason': f'duplicate ID — never tag {sid} twice on one declaration (merge without duplicates)'
                })
                continue
            seen_ids[sid] = j + 1

        # Check 1: multiple IDs joined by commas
        if COMMA_REF_RE.search(stripped):
            format_issues.append({
                'line': j + 1,
                'text': stripped.strip(),
                'reason': 'comma-separated — @spec is one per line'
            })
            continue

        # Check 2: one-line JSDoc (/** description @spec ... */)
        if '/**' in stripped and '*/' in stripped and '@spec' in stripped:
            format_issues.append({
                'line': j + 1,
                'text': stripped.strip(),
                'reason': 'one-line JSDoc — split into a multi-line block'
            })
            continue

        # Check 3: a description and @spec on the same line
        clean = re.sub(r'^\s*(?:/\*\*|\*/|\*|//|#)\s*', '', stripped).strip()
        if clean and not clean.startswith('@spec') and '@spec' in clean:
            format_issues.append({
                'line': j + 1,
                'text': stripped.strip(),
                'reason': 'mixed with a description — write @spec on its own line'
            })
            continue

        # Check 4: trailing space/tab contamination after the @spec ID
        # `line` is LF-normalized by the caller with newlines removed, so any trailing
        # spaces/tabs here are pure contamination (independent of OS line endings).
        if re.search(r'@spec\s+(?:FR|NFR)-\d+-(?:\d+|E\d+)[ \t]+$', line):
            format_issues.append({
                'line': j + 1,
                'text': stripped.strip(),
                'reason': 'trailing whitespace after the ID — no spaces/tabs at the end of an @spec line'
            })
            continue

        # Check 5: any other 'one per line, ID only' violation (text after the ID, space-separated multiple IDs, …)
        if not GOOD_REF_RE.match(line):
            format_issues.append({
                'line': j + 1,
                'text': stripped.strip(),
                'reason': "ID-only standalone line — the '@spec FR-XX-XXX' form (one per line, no descriptions)"
            })
            continue

    return has_ref, format_issues


def check_refs_in_file(filepath):
    """
    Checks @spec existence and format on the file's class/function declarations.

    Returns: (missing, bad_format, ok_count)
    """
    lang = detect_lang(filepath)
    if not lang:
        return [], [], 0

    config = LANG_CONFIG[lang]
    patterns = config['patterns']()
    ignore_patterns = config['ignores']()
    skip_names = config['skip_names']

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    # OS-agnostic handling: normalize CRLF/CR to LF, then split into lines.
    # This blocks false positives from Windows (CRLF) trailing \r creeping into whitespace/format checks.
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    missing = []
    bad_format = []
    ok_count = 0

    # Decorator/annotation line set — passed through in the comment search
    deco_lines = decorator_lines(lines)
    # js/ts only: brace depth — for excluding local const/let/var inside function bodies (vue excluded because of template interpolation)
    depths = _brace_depths(lines) if lang in ('js', 'ts') else None

    for i, line in enumerate(lines):
        if any(ip.match(line) for ip in ignore_patterns):
            continue

        stripped = line.strip()
        if not stripped or stripped in ('{', '}', '};', ')', ');', '],'):
            continue

        # Local const/let/var declarations inside a function body (arrow helpers etc.) are not @spec targets.
        # Depth tracking can skew, so 'indentation present' is required on top of 'depth > 0' (prevents top-level misses).
        if (depths is not None and depths[i] > 0 and line[:1] in (' ', '\t')
                and re.match(r'^(const|let|var)\b', stripped)):
            continue

        matched_name = None
        for p in patterns:
            m = p.match(line)
            if m:
                groups = [g for g in m.groups() if g and g.strip() not in
                          ('async', 'export', 'default', 'const', 'let', 'var',
                           'public', 'private', 'protected', 'internal', 'static',
                           'virtual', 'override', 'abstract', 'sealed', 'partial',
                           'final', 'synchronized', 'inline',
                           'class', 'struct', 'interface', 'enum',
                           'def', 'async def')]
                if groups:
                    matched_name = groups[-1].strip()
                break

        if not matched_name:
            continue

        if matched_name in skip_names:
            continue

        # Function-call false-positive prevention: handled conservatively.
        # Core principle: regexes alone can't perfectly separate JS's ambiguous syntax
        # (calls with arrow functions as arguments, local const/let inside functions, …).
        # The harder we try to catch every case, the more new false positives appear, and
        # eventually the coder contorts healthy code to dodge verification. So here we skip
        # only what is 'definitely a call'. The remaining ambiguous cases get caught first,
        # and judging their genuineness (omission vs false positive) belongs to the LLM.
        if lang in ('js', 'ts', 'vue'):
            # Only explicit call terminators count as calls: lines ending in ');' without the 'function'/'class' keywords.
            # This alone filters most simple one-line calls.
            if (stripped.endswith(');')
                    and 'function' not in stripped
                    and not re.search(r'\bclass\s+\w', stripped)):
                continue
            # A line whose first argument starts with an arrow/function literal (useEffect(() => …),
            # f(function …), f(async () => …)) can never be a declaration by grammar — a parameter
            # list cannot start with '(' or the function keyword. Anchored to grammar rather than a
            # name list, so it holds regardless of callback body length (_js_multiline_call's 30-line window).
            if re.match(r'^(?:async\s+)?[\w$]+\s*\(\s*(?:\(|function\b|async\s+\()', stripped):
                continue
            # Multi-line calls: if no block start ('{') follows once the parens close, it's a call.
            # Determined only when the declaration line has a '(' (prevents mis-tracking next-line parens on class declarations etc.).
            if '(' in stripped and _js_multiline_call(lines, i):
                continue

        if lang == 'python' and matched_name.startswith('_') and matched_name not in skip_names:
            continue

        # @spec existence + format check (passing through decorator/annotation lines)
        has_ref, format_issues = check_ref_format(lines, i, deco_lines)

        if not has_ref:
            missing.append({
                'line': i + 1,
                'name': matched_name,
                'code': stripped
            })
        elif format_issues:
            for issue in format_issues:
                bad_format.append({
                    'decl_line': i + 1,
                    'decl_name': matched_name,
                    'ref_line': issue['line'],
                    'ref_text': issue['text'],
                    'reason': issue['reason']
                })
        else:
            ok_count += 1

    return missing, bad_format, ok_count


def main():
    # Collect positional args, excluding flags like --json
    targets = [a for a in sys.argv[1:] if not a.startswith('--')]

    if not targets:
        print("Usage: python3 scripts/verify_refs.py <path> [path2 ...]")
        print("  e.g.: python3 scripts/verify_refs.py src/")
        print("  e.g.: python3 scripts/verify_refs.py src/core/handler.js")
        print("  e.g.: python3 scripts/verify_refs.py src/file1.ts src/file2.ts")
        sys.exit(1)

    source_files = []
    for target in targets:
        if not os.path.exists(target):
            print(f"❌ Path not found: {target}")
            sys.exit(1)
        source_files.extend(find_source_files(target))

    # De-duplicate (order preserved)
    seen = set()
    unique_files = []
    for f in source_files:
        af = os.path.abspath(f)
        if af not in seen:
            seen.add(af)
            unique_files.append(f)
    source_files = unique_files

    if not source_files:
        print(f"⚠️  No source files found: {' '.join(targets)}")
        print(f"    Supported extensions: {', '.join(ALL_EXTENSIONS)}")
        sys.exit(0)

    total_missing = []
    total_bad_format = []
    total_ok = 0

    for fp in source_files:
        missing, bad_format, ok = check_refs_in_file(fp)
        total_ok += ok
        for item in missing:
            item['file'] = fp
            total_missing.append(item)
        for item in bad_format:
            item['file'] = fp
            total_bad_format.append(item)

    # Print results
    # --json mode: print the structured result and exit
    if '--json' in sys.argv:
        print(json.dumps({
            'type': 'refs',
            'ok': total_ok,
            'missing': [{'file': os.path.relpath(m['file']), 'line': m['line'], 'name': m['name']} for m in total_missing],
            'bad_format': [{'file': os.path.relpath(b['file']), 'line': b['ref_line'], 'name': b['decl_name'], 'reason': b['reason']} for b in total_bad_format]
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  @spec tag verification results")
    print(f"{'='*60}")
    print(f"  Files checked:  {len(source_files)}")
    print(f"  @spec OK:       {total_ok}")
    print(f"  @spec missing:  {len(total_missing)}")
    print(f"  Format errors:  {len(total_bad_format)}")
    print(f"{'='*60}\n")

    has_error = False

    if total_missing:
        has_error = True
        print("❌ Items missing an @spec tag:\n")
        for item in total_missing:
            rel_path = os.path.relpath(item['file'])
            print(f"  {rel_path}:{item['line']}  {item['name']}")
            print(f"    {item['code']}\n")

    if total_bad_format:
        has_error = True
        print("❌ Items with @spec format errors:\n")
        print("  Correct form:")
        print("    * @spec FR-04-001       (one per line, separated from descriptions)")
        print()
        for item in total_bad_format:
            rel_path = os.path.relpath(item['file'])
            print(f"  {rel_path}:{item['ref_line']}  ({item['decl_name']})")
            print(f"    {item['ref_text']}")
            print(f"    → {item['reason']}\n")

    if has_error:
        total_issues = len(total_missing) + len(total_bad_format)
        print(f"\nFAIL — fix {total_issues} item(s).")
        if total_missing:
            print(f"       @spec missing: {len(total_missing)}")
        if total_bad_format:
            print(f"       format errors: {len(total_bad_format)}")
        sys.exit(1)
    else:
        if total_ok == 0:
            print("⚠️  0 checks — possibly unsupported syntax (e.g., cpp indented qualified definitions). Confirm tags/coverage manually.")
        print("✅ PASS — every class/function carries a correctly-formed @spec tag.")
        sys.exit(0)


if __name__ == '__main__':
    main()
