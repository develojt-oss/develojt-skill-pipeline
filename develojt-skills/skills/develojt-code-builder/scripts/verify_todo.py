#!/usr/bin/env python3
"""
TODO/unimplemented function detection script

Finds functions carrying an @spec tag whose body is empty or a TODO.
A script for catching cases where the @spec tag was attached but the actual logic was never implemented.

verify_spec_coverage.py checks only @spec tag existence, so
this script additionally detects "tagged but not implemented" items.

Usage:
    python3 scripts/verify_todo.py src/
    python3 scripts/verify_todo.py src/services/order-service.js
    python3 scripts/verify_todo.py src/file1.ts src/file2.ts src/file3.ts
"""

import sys
import os
import re
import json


SUPPORTED_EXT = (
    '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue',
    '.py', '.cs', '.java', '.cpp', '.cc', '.cxx', '.h', '.hpp',
)

SKIP_DIRS = {'node_modules', 'dist', 'build', 'tests', '__tests__',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

# Body patterns judged as unimplemented
STUB_PATTERNS = [
    re.compile(r'^\s*//\s*TODO', re.IGNORECASE),
    re.compile(r'^\s*//\s*FIXME', re.IGNORECASE),
    re.compile(r'^\s*//\s*to\s+be\s+implemented', re.IGNORECASE),
    re.compile(r'^\s*//\s*unimplemented', re.IGNORECASE),
    re.compile(r'^\s*//\s*placeholder', re.IGNORECASE),
    re.compile(r'^\s*//\s*stub', re.IGNORECASE),
    re.compile(r'^\s*//\s*not\s+implemented', re.IGNORECASE),
    re.compile(r'^\s*#\s*TODO', re.IGNORECASE),
    re.compile(r'^\s*#\s*to\s+be\s+implemented', re.IGNORECASE),
    re.compile(r'^\s*pass\s*$'),                          # Python pass
    re.compile(r'^\s*raise\s+NotImplementedError'),        # Python
    re.compile(r'^\s*throw\s+new\s+Error.*not\s+impl', re.IGNORECASE),  # JS/TS
    re.compile(r'^\s*return\s*;?\s*$'),                    # bare return
    re.compile(r'^\s*return\s+(null|undefined|None)\s*;?\s*$'),  # return null
]


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


DECORATOR_RE = re.compile(r'^\s*@\w')
CS_ATTRIBUTE_RE = re.compile(r'^\s*\[\w')


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


def _own_comment_lines(lines, decl_idx, deco_lines):
    """Returns the line list of the declaration's 'own' comment block directly above it.

    It searches upward while honoring the comment block boundary (a code line, or a blank line
    above the block), so it never mistakes another function's @spec within 20 lines for its own.
    Decorator/annotation and C# attribute ([Attr]) lines are passed through.
    """
    collected = []
    found_comment = False
    for j in range(decl_idx - 1, max(-1, decl_idx - 40), -1):
        if j in deco_lines:
            continue
        s = lines[j].strip()
        if not s:
            if found_comment:
                break
            continue
        if CS_ATTRIBUTE_RE.match(s):
            continue  # pass through C# attribute lines
        is_comment = s.startswith(('*', '/**', '/*', '*/', '//', '#', '"""', "'''"))
        if not is_comment:
            break  # a code line = the comment block boundary (the previous function's body etc.)
        found_comment = True
        collected.append(s)
    return collected


def has_ref_nearby(lines, decl_idx, deco_lines=frozenset()):
    """Checks whether an @spec tag exists in the comment block directly above the declaration (block boundary honored)"""
    return any('@spec' in s for s in _own_comment_lines(lines, decl_idx, deco_lines))


def get_ref_ids(lines, decl_idx, deco_lines=frozenset()):
    """Extracts the @spec ID list from the comment block directly above the declaration (block boundary honored)"""
    refs = []
    ref_pattern = re.compile(r'@spec\s+((?:FR|NFR)-\d+-(?:\d+|E\d+))')
    for s in reversed(_own_comment_lines(lines, decl_idx, deco_lines)):
        for m in ref_pattern.finditer(s):
            refs.append(m.group(1))
    return refs


def is_stub_body(lines, decl_idx, lang):
    """
    Judges whether a function/method body is a stub (unimplemented).

    Criteria:
    1. The body has only TODO/FIXME/to-be-implemented comments
    2. The body is only pass, return null, or throw NotImplementedError
    3. The body is empty (braces only, or 1 line or less)
    """
    if lang in ('python',):
        return _is_stub_python(lines, decl_idx)
    else:
        return _is_stub_braces(lines, decl_idx)


def _find_body_brace(lines, decl_idx):
    """Finds the first 'body' '{' after all parameter parens have closed.

    - Paren depth tracking: object type literal braces inside parameters
      (start: { x: number } etc.) are never mistaken for the body start.
    - A type literal in return-type position (`): { x: number } {`) is treated as a type
      when the previous meaningful char is : | & , and skipped until its pair closes.
    - Braces inside generics <> are not the body either.
    - If the statement ends (;) without a body '{', it's undecidable — expression-body arrows or declaration-only lines.

    Returns: (line index, column index) or (-1, -1)
    """
    paren_depth = 0
    angle_depth = 0
    type_brace_depth = 0
    prev = ''
    for i in range(decl_idx, min(len(lines), decl_idx + 40)):
        s = lines[i].strip()
        # Hitting the next declaration's comment block means no body
        if i > decl_idx and paren_depth == 0 and s.startswith(('//', '/*', '*', '#')):
            return -1, -1
        line = lines[i]
        col = 0
        n = len(line)
        while col < n:
            ch = line[col]
            if ch in (' ', '\t'):
                col += 1
                continue
            # Skip strings/template literals whole — prevents mistaking `${` braces for the body
            if ch in ('"', "'", '`'):
                quote = ch
                col += 1
                while col < n and line[col] != quote:
                    col += 2 if line[col] == '\\' else 1
                col += 1
                prev = quote
                continue
            if type_brace_depth > 0:
                if ch == '{':
                    type_brace_depth += 1
                elif ch == '}':
                    type_brace_depth -= 1
                prev = ch
                col += 1
                continue
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth = max(0, paren_depth - 1)
            elif paren_depth == 0:
                if ch == '<':
                    angle_depth += 1
                elif ch == '>':
                    if prev != '=':  # '=>' (arrow) is not a generic close
                        angle_depth = max(0, angle_depth - 1)
                elif ch == ';':
                    return -1, -1  # statement ended without a body brace
                elif ch == '{':
                    if angle_depth == 0 and prev not in (':', '|', '&', ','):
                        return i, col  # body start
                    type_brace_depth += 1  # a type literal — skip until its pair
            prev = ch
            col += 1
    return -1, -1


def _is_stub_braces(lines, decl_idx):
    """Stub judgment for brace languages (JS/TS/Java/C#/C++)"""
    # Find the body '{' — paren depth tracking (excluding type-literal braces in parameters/return types)
    brace_line, brace_col = _find_body_brace(lines, decl_idx)

    if brace_line < 0:
        return False  # undecidable when the body brace can't be found

    # Collect the body from the body { to its }
    depth = 0
    body_lines = []
    started = False

    for i in range(brace_line, min(len(lines), brace_line + 400)):
        # On the first line, count only from the body '{' (excluding type-literal braces before it)
        seg = lines[i][brace_col:] if i == brace_line else lines[i]
        for ch in seg:
            if ch == '{':
                depth += 1
                started = True
            elif ch == '}':
                depth -= 1

        if started and depth == 0:
            # The closing-brace line — body collection complete
            break

        if i > brace_line:  # body starts after the first line (the one with the body {)
            body_lines.append(lines[i])

    if not body_lines:
        return True  # the body is empty (bare braces)

    # Check whether the body has substantive code
    meaningful_lines = []
    for bl in body_lines:
        stripped = bl.strip()
        if not stripped:
            continue
        if stripped.startswith(('*', '/**', '*/', '//')):
            # A comment — if it's TODO/to-be-implemented, it's a stub
            if any(sp.match(stripped) for sp in STUB_PATTERNS):
                return True
            continue
        meaningful_lines.append(stripped)

    if not meaningful_lines:
        return True  # only comments/blank lines

    # If there's a single meaningful line and it matches a stub pattern
    if len(meaningful_lines) <= 2:
        for ml in meaningful_lines:
            if any(sp.match(ml) for sp in STUB_PATTERNS):
                return True

    return False


def _python_header_end(lines, decl_idx):
    """Returns the line index where the declaration header ends (paren-balance based).

    For a single-line signature it is the declaration line itself (the same path as before).
    For a multi-line signature (def f(\n …\n) -> T:) the header runs to the line where the
    parens close — counting parameter lines as the body lets a genuinely empty implementation
    silently pass as 'implemented'.
    On tracking failure (window exceeded, unbalanced parens) the declaration line is returned,
    falling back to the previous behavior — the failure direction is the old behavior, not
    new false positives.
    """
    depth = lines[decl_idx].count('(') - lines[decl_idx].count(')')
    if depth <= 0:
        return decl_idx
    for k in range(decl_idx + 1, min(len(lines), decl_idx + 31)):
        depth += lines[k].count('(') - lines[k].count(')')
        if depth <= 0:
            return k
    return decl_idx


def _is_stub_python(lines, decl_idx):
    """Python stub judgment (indentation-based)"""
    # The declaration line's indentation level
    decl_indent = len(lines[decl_idx]) - len(lines[decl_idx].lstrip())

    # Parameter lines of a multi-line signature are not the body — walk from after the header's end
    header_end = _python_header_end(lines, decl_idx)

    body_lines = []
    for i in range(header_end + 1, min(len(lines), header_end + 400)):
        line = lines[i]
        if not line.strip():
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= decl_indent and line.strip():
            break  # same/lower indentation = end of body
        body_lines.append(line)

    if not body_lines:
        return True

    # Skip the docstring
    actual_body = []
    in_docstring = False
    for bl in body_lines:
        stripped = bl.strip()
        if stripped.startswith(('"""', "'''")):
            if in_docstring:
                in_docstring = False
                continue
            elif stripped.endswith(('"""', "'''")) and len(stripped) > 3:
                continue  # one-line docstring
            else:
                in_docstring = True
                continue
        if in_docstring:
            continue
        if stripped.startswith('#'):
            if any(sp.match(stripped) for sp in STUB_PATTERNS):
                return True
            continue
        actual_body.append(stripped)

    if not actual_body:
        return True

    if len(actual_body) <= 2:
        for ab in actual_body:
            if any(sp.match(ab) for sp in STUB_PATTERNS):
                return True

    return False


def detect_lang(filepath):
    """Determines the language from the file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ('.py',):
        return 'python'
    return 'braces'  # JS/TS/Java/C#/C++ etc.


# Function/method declaration patterns — separated per language.
# Unified, the JS method pattern (name+parens) mistakes Python call statements (print(...) etc.)
# for declarations, so only the language-appropriate patterns are applied.
PYTHON_DECL_PATTERNS = [
    # Python functions
    re.compile(r'^\s*(async\s+)?def\s+(\w+)'),
    # Python classes
    re.compile(r'^\s*class\s+(\w+)'),
]

BRACE_DECL_PATTERNS = [
    # JS/TS classes
    re.compile(r'^\s*(export\s+)?(default\s+)?class\s+(\w+)'),
    # JS/TS function
    re.compile(r'^\s*(export\s+)?(default\s+)?function\s+(\w+)'),
    # JS/TS arrow
    re.compile(r'^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\('),
    # JS/TS paren-less single-argument arrows (const f = x => …) — same branch as verify_comments
    re.compile(r'^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\w+\s*=>'),
    # C#/Java
    re.compile(r'^\s*(public|private|protected|static|abstract|override|virtual|async|final|synchronized)\s+[\w<>\[\],\s]+\s+(\w+)\s*\('),
    # JS/TS methods — the trailing opening brace '{' is required to distinguish from call statements.
    re.compile(r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{'),
]

IGNORE_LINE = re.compile(
    r'^\s*(if|else|elif|for|foreach|while|switch|return|try|catch|except|throw|'
    r'import|from|using|namespace|package|#include|console|new |this\.|self\.|'
    r'super|//|/\*|\*|#(?!include)|@Override)'
)

SKIP_NAMES = {'constructor', '__init__', 'get', 'set', '__str__', '__repr__',
              'toString', 'hashCode', 'equals'}


def check_file(filepath):
    """
    Finds functions carrying @spec whose body is a stub.

    Returns: (stub list, properly-implemented count)
    """
    lang = detect_lang(filepath)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    # OS-agnostic handling: normalize CRLF/CR to LF (prevents Windows \r line-ending misfires)
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    stubs = []
    ok_count = 0

    # Decorator/annotation line set — passed through in the comment search
    deco_lines = decorator_lines(lines)

    # Apply only the language-appropriate declaration patterns.
    decl_patterns = PYTHON_DECL_PATTERNS if lang == 'python' else BRACE_DECL_PATTERNS

    for i, line in enumerate(lines):
        if IGNORE_LINE.match(line):
            continue
        stripped = line.strip()
        if not stripped or stripped in ('{', '}', '};', ')', ');'):
            continue

        # Declaration match
        matched_name = None
        for p in decl_patterns:
            m = p.match(line)
            if m:
                groups = [g for g in m.groups() if g and g.strip() not in
                          ('async', 'export', 'default', 'const', 'let', 'var',
                           'public', 'private', 'protected', 'static', 'abstract',
                           'override', 'virtual', 'final', 'synchronized',
                           'class', 'def')]
                if groups:
                    matched_name = groups[-1].strip()
                break

        if not matched_name or matched_name in SKIP_NAMES:
            continue

        # Without @spec it's not this script's target (verify_refs.py handles that)
        if not has_ref_nearby(lines, i, deco_lines):
            continue

        ref_ids = get_ref_ids(lines, i, deco_lines)

        if is_stub_body(lines, i, lang):
            stubs.append({
                'line': i + 1,
                'name': matched_name,
                'refs': ref_ids,
                'code': stripped,
            })
        else:
            ok_count += 1

    return stubs, ok_count


def main():
    # Collect positional args, excluding flags like --json
    targets = [a for a in sys.argv[1:] if not a.startswith('--')]

    if not targets:
        print("Usage: python3 scripts/verify_todo.py <path> [path2 ...]")
        print("  e.g.: python3 scripts/verify_todo.py src/")
        print("  e.g.: python3 scripts/verify_todo.py src/file1.ts src/file2.ts")
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

    total_stubs = []
    total_ok = 0

    for fp in files:
        stubs, ok = check_file(fp)
        total_ok += ok
        for item in stubs:
            item['file'] = fp
            total_stubs.append(item)

    total = total_ok + len(total_stubs)

    # --json mode: print the structured result and exit
    if '--json' in sys.argv:
        print(json.dumps({
            'type': 'todo',
            'ok': total_ok,
            'stubs': [{'file': os.path.relpath(s['file']), 'line': s['line'], 'name': s['name'], 'refs': s['refs']} for s in total_stubs]
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  TODO/unimplemented function detection results")
    print(f"{'='*60}")
    print(f"  Files checked:         {len(files)}")
    print(f"  @spec functions:       {total}")
    print(f"  Implemented:           {total_ok}")
    print(f"  Unimplemented (stubs): {len(total_stubs)}")
    print(f"{'='*60}\n")

    if total_stubs:
        print("❌ Functions carrying @spec whose body is unimplemented:\n")
        for item in total_stubs:
            rel = os.path.relpath(item['file'])
            refs_str = ', '.join(item['refs']) if item['refs'] else '(no ID)'
            print(f"  {rel}:{item['line']}  {item['name']}  [{refs_str}]")
            print(f"    {item['code']}\n")
        print(f"\nFAIL — implement the logic of {len(total_stubs)} function(s).")
        print(f"       They carry only @spec tags with TODO/empty bodies.")
        sys.exit(1)
    else:
        print("✅ PASS — every @spec-tagged function has real logic implemented.")
        sys.exit(0)


if __name__ == '__main__':
    main()
