#!/usr/bin/env python3
r"""Enforced-rule violation candidate detector (develojt-code-pdca C3 only) + existing-symbol sight print (--inventory).

Reads the 'Enforced Rules Table' in rules/enforced-rules.md and sweeps only the
machine-checkable rules (scan/pattern) — a floor-level detector. Rules are data: add a row
to the table and it is checked with no changes to this script.
Its output is not defects but **candidates** — the judgment (executing declaration? accidental
same name? SPEC-specified usage?) is made by the checker via the C3 procedure in checker-rules.md.
Therefore PASS (0 candidates) does not mean "rules complied with" — only that the
machine-checkable rules produced no candidates.

Check-method vocabulary (closed list — the table's 'Check method' cell):
  scan: same-name    declarations with the same name defined in 2+ different files
                     (js/ts/vue/python: top level only / java/csharp: classes and
                      static final|const constants only / cpp: #define/const/constexpr/
                      classes only, include guards and stem-sharing header/implementation
                      pairs excluded — partial support)
  scan: same-value   named constants with the same literal value defined in 2+ different files
                     (numbers 3+ chars as written, trivial values excluded; strings 4+ chars —
                      only identically written literals count as the same value. Groups already
                      reported as same-name are skipped)
  scan: same-body    functions whose normalized (whitespace/comments stripped) bodies are
                     identical in 2+ places (js/ts/vue/python only · 3+ normalized lines)
  pattern: <regex>   every line the regex matches (a | inside the cell is escaped as \|)
  anything else      not machine-checked — flagged with ⚠️ (no silent burial of a rule)

Rules-file resolution: an .md path argument wins; otherwise .claude/rules/enforced-rules.md
at the run location. If neither exists, PASS (exit 0) as "C3 not applicable" —
projects without the rules file behave unchanged.

Supported languages: JavaScript, TypeScript, Vue, Python, C#, Java, C++ (cpp/java/csharp partial)
tests/ and __tests__/ are not checked (duplication checks target product code —
avoiding false positives on fixture repetition).

Usage:
    python3 scripts/verify_enforced_rules.py src/                    # candidate detection (C3)
    python3 scripts/verify_enforced_rules.py src/ path/to/rules.md   # explicit rules file
    python3 scripts/verify_enforced_rules.py src/ --inventory        # symbol sight print (builder prevention — no judgment, no gate)
    python3 scripts/verify_enforced_rules.py src/ --inventory=keyword # print only names with a partial match (case-insensitive) — the lookup means in summary mode
    python3 scripts/verify_enforced_rules.py src/ --all              # ignore the candidate-rejection ledger — full recheck (on human instruction / checker calibration)

Candidate-rejection ledger: reads spec/findings-rejected.md at the run location (if present); candidates whose key matches
are not printed and are noted in the summary as `N excluded as matching the candidate-rejection ledger` — these are rejection
verdicts (location, basis) the checker made and the Lead recorded, so they are inherited.
Key = for scan candidates (same-name, same-value, same-body), up to the printed line's first ` — `, like
`[R-NN] same-name definition 'main' (function) in 3 places` (anchor path and line excluded — when the place count changes, the
key no longer matches and it is re-judged); for pattern candidates, the printed line minus `:line-number`.

Print cap: when the full inventory list exceeds 16KB, it switches to a summary mode that prints only per-folder tallies (look up
with --inventory=keyword). Candidate detail lines are also printed only up to 16KB, and beyond that a `… N more … not printed`
notice is printed — preventing the tail from silently disappearing when the harness replaces tool output of roughly 30KB or
more with a preview. If the notice appears, it is not exhaustive (narrow the target argument down to subfolders/files and
re-run). The 'also:' lists of same-name, same-value, and same-body candidates also enumerate only up to 20 places and note
`(+N more places)`. Exit codes and count summaries are based on the full set.

Exit codes: 0 — no candidates / not applicable / inventory (PASS); 1 — candidates found (checker on-site confirmation needed); 2 — usage/target error

"""

import hashlib
import os
import re
import sys

# Per-language extension map (the same set as verify_security.py and verify_refs.py)
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

# Test folders excluded — intentional fixture/setup repetition must not read as duplication (same as verify_refs)
SKIP_DIRS = {'node_modules', 'dist', 'build', 'tests', '__tests__',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

DEFAULT_RULES_PATH = os.path.join('.claude', 'rules', 'enforced-rules.md')

# ── Print cap: the harness replaces tool output of roughly 30KB or more with a 2KB preview + file, so the tail silently disappears.
#    Detail lines are printed only up to this cap, and the overflow count is left as a notice (preventing silent truncation — exit codes are based on the full set).
PRINT_MAX_BYTES = 16_000


def print_capped(lines: list[str], unit: str) -> None:
    """Print detail lines up to the cap; on overflow, print the remaining count and a re-run hint."""
    used = 0
    for i, line in enumerate(lines):
        size = len(line.encode('utf-8')) + 1
        if used + size > PRINT_MAX_BYTES:
            print(f'… {len(lines) - i} more{unit} not printed — print cap ({PRINT_MAX_BYTES // 1000}KB). '
                  f'Narrow the target argument down to subfolders/files and re-run to see the rest')
            return
        print(line)
        used += size


# ── Candidate-rejection ledger: spec/findings-rejected.md, where the Lead writes the keys (location/basis records) of candidates the checker rejected as "not a defect".
#    Candidates whose key matches are not printed (inheriting the recorded verdict). Without the file, same as before. Rows with a broken format are ignored (the re-judgment direction).
REJECTED_PATH = os.path.join('spec', 'findings-rejected.md')


def load_rejected(path: str = REJECTED_PATH) -> set[str]:
    """Collect the first cell (the key) of the candidate-rejection ledger's table. `\\|` inside a cell is turned back into `|`."""
    keys: set[str] = set()
    if not os.path.isfile(path):
        return keys
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith('|'):
                continue
            cells = line.replace('\\|', '\x00').strip('|').split('|')
            key = cells[0].replace('\x00', '|').strip().strip('`').strip() if cells else ''
            if not key or key == 'Key' or set(key) <= set('-: '):
                continue
            keys.add(key)
    return keys

INVENTORY_INLINE_MAX = PRINT_MAX_BYTES  # inline print cap for the full inventory list — beyond it, summary mode
LOC_MAX = 20                            # enumeration cap for one candidate line's 'also:' list


def join_locs(items: list[str]) -> str:
    """Enumerate the 'also:' list up to the cap and note the rest as a count (preventing one-line blowup)."""
    extra = len(items) - LOC_MAX
    return ', '.join(items[:LOC_MAX]) + (f' (+{extra} more places)' if extra > 0 else '')
RULES_SECTION = '## Enforced Rules Table'
RULE_ID_RE = re.compile(r'^R-\d+$')
SCAN_KINDS = {'same-name', 'same-value', 'same-body'}

# ── Top-level declaration patterns (shared by the same-name scan and the inventory) ──
JS_NAME = r'[A-Za-z_$][\w$]*'
JS_TOP_PATTERNS = [
    ('class',    re.compile(r'^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(' + JS_NAME + r')')),
    ('function', re.compile(r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(' + JS_NAME + r')')),
    ('type',     re.compile(r'^(?:export\s+)?(?:interface|enum|type)\s+(' + JS_NAME + r')')),
    ('const',    re.compile(r'^(?:export\s+)?(?:const|let|var)\s+(' + JS_NAME + r')\s*=')),
]
JS_FUNC_VALUE_RE = re.compile(r'=\s*(?:async\s*)?(?:\(|function\b|' + JS_NAME + r'\s*=>)')
PY_TOP_PATTERNS = [
    ('class',    re.compile(r'^class\s+(\w+)')),
    ('function', re.compile(r'^(?:async\s+)?def\s+(\w+)')),
    ('const',    re.compile(r'^([A-Z][A-Z0-9_]{2,})\s*=')),
]
JC_TOP_PATTERNS = [
    ('class',    re.compile(
        r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|final\s+'
        r'|abstract\s+|sealed\s+|partial\s+)*(?:class|interface|enum|struct|record)\s+(\w+)')),
    ('const',    re.compile(
        r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+)?'
        r'(?:static\s+final|final\s+static|const|static\s+readonly)\s+[\w<>\[\],.]+\s+(\w+)\s*=')),
]
CPP_TOP_PATTERNS = [
    ('class',    re.compile(r'^(?:class|struct)\s+(\w+)')),
    ('macro',    re.compile(r'^\s*#define\s+(\w+)')),
    ('const',    re.compile(r'^(?:static\s+)?(?:const|constexpr)\s+[\w:<>]+\s+(\w+)\s*=')),
]
# Include-guard conventional names — excluded from macro same-name/same-value
INCLUDE_GUARD_RE = re.compile(r'^[A-Z][A-Z0-9_]*_(H|HPP|H_|HPP_|INCLUDED)$')

TOP_PATTERNS_BY_LANG = {
    'js': JS_TOP_PATTERNS, 'ts': JS_TOP_PATTERNS, 'vue': JS_TOP_PATTERNS,
    'python': PY_TOP_PATTERNS,
    'java': JC_TOP_PATTERNS, 'csharp': JC_TOP_PATTERNS,
    'cpp': CPP_TOP_PATTERNS,
}

# ── Same-value scan: named-constant declarations + literal RHS ──
NUM_LIT = r'(-?\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?)'
STR_LIT = r'(["\'])((?:\\.|(?!\1).)*)\1'
LINE_END = r'\s*[;,]?\s*(?:(?://|#).*)?$'
TRIVIAL_NUMS = {'0', '1', '-1', '2', '10', '100', '1000'}
CONST_DECL_BY_LANG = {
    'js':     re.compile(r'^(?:export\s+)?const\s+(' + JS_NAME + r')\s*='),
    'python': re.compile(r'^([A-Z][A-Z0-9_]{2,})\s*='),
    'java':   JC_TOP_PATTERNS[1][1],
    'cpp':    re.compile(r'^\s*(?:#define\s+(\w+)\s+'
                         r'|(?:static\s+)?(?:const|constexpr)\s+[\w:<>]+\s+(\w+)\s*=)'),
}
CONST_DECL_BY_LANG['ts'] = CONST_DECL_BY_LANG['js']
CONST_DECL_BY_LANG['vue'] = CONST_DECL_BY_LANG['js']
CONST_DECL_BY_LANG['csharp'] = CONST_DECL_BY_LANG['java']

# ── Same-body scan: function head patterns (js/ts/vue/python — methods included) ──
JS_KEYWORD_SKIP = {'if', 'for', 'while', 'switch', 'catch', 'return', 'function', 'new',
                   'typeof', 'else', 'do', 'try', 'constructor', 'await', 'yield', 'throw',
                   'import', 'export', 'delete', 'void', 'in', 'of', 'super', 'this'}
JS_BODY_HEADS = [
    re.compile(r'^(\s*)(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(' + JS_NAME + r')\s*\('),
    re.compile(r'^(\s*)(?:export\s+)?(?:const|let|var)\s+(' + JS_NAME + r')\s*=\s*(?:async\s*)?\('),
    re.compile(r'^(\s*)(?:public\s+|private\s+|protected\s+|static\s+|async\s+)*(' + JS_NAME + r')\s*\([^)]*\)\s*\{\s*$'),
]
PY_BODY_HEAD = re.compile(r'^(\s*)(?:async\s+)?def\s+(\w+)\s*\(')
BODY_MIN_LINES = 3     # below this after normalization = trivial (getters) — no candidate
BODY_MAX_WALK = 500    # body-walk cap (runaway guard)
HEAD_MAX_WALK = 30     # function-head (multi-line signature) walk cap


def lang_of(path: str) -> str | None:
    """Return the language key by extension; None outside the supported set."""
    for lang, exts in LANG_EXTENSIONS.items():
        if path.endswith(exts):
            return lang
    return None


def collect_files(targets: list[str]) -> list[str]:
    """Collect supported-extension files from targets (dirs/files) — same shape as verify_security."""
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(os.path.normpath(target))
        elif os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                files.extend(
                    os.path.normpath(os.path.join(root, n)) for n in sorted(names)
                    if n.endswith(ALL_EXTENSIONS))
        else:
            print(f"[ERROR] target does not exist: {target}", file=sys.stderr)
            sys.exit(2)
    return files


def read_lines(path: str) -> list[str]:
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    except OSError as e:
        print(f"[WARN] read failed: {path} ({e})", file=sys.stderr)
        return []


# ── Rules-file parsing (rules are data — only what the table declares is checked) ──

def split_cells(line: str) -> list[str]:
    """Split a table line into cells. `\\|` escapes count as cell content."""
    protected = line.strip().replace('\\|', '\x00')
    return [c.strip().replace('\x00', '|') for c in protected.strip('|').split('|')]


def parse_rules(text: str) -> tuple[dict[str, str], list[tuple[str, re.Pattern]], list[str]]:
    """Parse the enforced-rules table → (scan kind → rule ID, [(rule ID, pattern)], warnings)."""
    scans: dict[str, str] = {}
    patterns: list[tuple[str, re.Pattern]] = []
    warnings: list[str] = []
    match = re.search(rf'{re.escape(RULES_SECTION)}(.*?)(?=^## |\Z)', text, re.DOTALL | re.MULTILINE)
    if not match:
        warnings.append(f"the rules file has no '{RULES_SECTION}' section — 0 rules to check")
        return scans, patterns, warnings
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = split_cells(line)
        if len(cells) < 3 or cells[0] == 'ID' or all(re.fullmatch(r':?-+:?', c) for c in cells if c):
            continue
        rid, _rule, method = cells[0], cells[1], cells[2]
        if not RULE_ID_RE.match(rid):
            warnings.append(f"rule ID format violation (R-NN required): '{rid}' — this row is not checked")
            continue
        if method.startswith('scan:'):
            kind = method.split(':', 1)[1].strip()
            if kind not in SCAN_KINDS:
                warnings.append(f"{rid}: scan kind '{kind}' — unknown to the engine (not machine-checked). "
                                f"Built-in scans: {' · '.join(sorted(SCAN_KINDS))}")
            elif kind in scans:
                warnings.append(f"{rid}: scan '{kind}' declared twice — only the first declaration {scans[kind]} applies")
            else:
                scans[kind] = rid
        elif method.startswith('pattern:'):
            raw = method.split(':', 1)[1].strip()
            try:
                patterns.append((rid, re.compile(raw)))
            except re.error as e:
                warnings.append(f"{rid}: regex error '{raw}' ({e}) — this rule is not checked")
        else:
            warnings.append(f"{rid}: check method '{method}' — unknown to the engine (not machine-checked). "
                            f"Vocabulary: 'scan: {'|'.join(sorted(SCAN_KINDS))}' or 'pattern: <regex>'")
    return scans, patterns, warnings


# ── Collection: top-level declarations (same-name scan + inventory) ──

def top_level_decls(path: str, lines: list[str]) -> list[tuple[str, int, str, str]]:
    """Return the file's top-level declarations [(name, line, kind, language)]."""
    lang = lang_of(path)
    if lang is None:
        return []
    decls = []
    for no, line in enumerate(lines, 1):
        for kind, rx in TOP_PATTERNS_BY_LANG[lang]:
            m = rx.match(line)
            if not m:
                continue
            name = next(g for g in m.groups() if g)
            if lang == 'cpp' and kind == 'macro' and INCLUDE_GUARD_RE.match(name):
                break
            # a js const whose value is function-shaped reads better as a function (inventory readability)
            if kind == 'const' and lang in ('js', 'ts', 'vue') and JS_FUNC_VALUE_RE.search(line):
                kind = 'function'
            decls.append((name, no, kind, lang))
            break
    return decls


def file_unit(path: str) -> str:
    """The 'different files' unit — cpp collapses to the stem so header/implementation pairs count as one place."""
    if lang_of(path) == 'cpp':
        return os.path.splitext(path)[0]
    return path


# ── Scan 1: same-name ──

def scan_same_name(files_lines: dict[str, list[str]]) -> tuple[list[tuple], set[str]]:
    """Name → definition-site groups. 2+ different file units = a candidate."""
    by_name: dict[str, list[tuple[str, int, str]]] = {}
    for path, lines in files_lines.items():
        for name, no, kind, _lang in top_level_decls(path, lines):
            by_name.setdefault(name, []).append((path, no, kind))
    groups, reported_names = [], set()
    for name, locs in sorted(by_name.items()):
        if len({file_unit(p) for p, _n, _k in locs}) >= 2:
            groups.append((name, sorted(locs)))
            reported_names.add(name)
    return groups, reported_names


# ── Scan 2: same-value ──

def literal_value(rest: str) -> tuple[str, str] | None:
    """Return (kind, value key) when the text ends as exactly one literal; None for expressions/calls."""
    m = re.match(r'^\s*' + NUM_LIT + LINE_END, rest)
    if m:
        key = m.group(1).replace('_', '').lower()
        if key not in TRIVIAL_NUMS and len(key) >= 3:
            return ('num', key)
        return None
    m = re.match(r'^\s*' + STR_LIT + LINE_END, rest)
    if m and len(m.group(2)) >= 4:
        return ('str', m.group(2))
    return None


def scan_same_value(files_lines: dict[str, list[str]],
                    name_reported: set[str]) -> list[tuple]:
    """Literal value → named-constant definition-site groups. 2+ different file units = a candidate."""
    by_value: dict[tuple[str, str], list[tuple[str, int, str]]] = {}
    for path, lines in files_lines.items():
        lang = lang_of(path)
        rx = CONST_DECL_BY_LANG.get(lang)
        if rx is None:
            continue
        for no, line in enumerate(lines, 1):
            m = rx.match(line)
            if not m:
                continue
            name = next(g for g in m.groups() if g)
            if lang == 'cpp' and INCLUDE_GUARD_RE.match(name):
                continue
            if '#define' in line[:m.end()]:
                after = m.end()            # #define NAME <literal> — space-separated, no '='
            else:
                eq = line.find('=', m.start())
                if eq == -1:
                    continue
                after = eq + 1
            lit = literal_value(line[after:])
            if lit:
                by_value.setdefault(lit, []).append((path, no, name))
    groups = []
    for value, locs in sorted(by_value.items()):
        if len({file_unit(p) for p, _n, _nm in locs}) < 2:
            continue
        names = {nm for _p, _n, nm in locs}
        if len(names) == 1 and next(iter(names)) in name_reported:
            continue  # already reported as same-name — no double report
        groups.append((value, sorted(locs)))
    return groups


# ── Scan 3: same-body ──

def _norm_body(body: list[str], comment_heads: tuple[str, ...]) -> list[str]:
    """Normalize a body — drop blank and comment-only lines, strip surrounding whitespace."""
    out = []
    for line in body:
        s = line.strip()
        if not s or s.startswith(comment_heads):
            continue
        out.append(s)
    return out


def _py_bodies(path: str, lines: list[str]) -> list[tuple[str, int, str, list[str]]]:
    """Python functions/methods as (name, line, path, raw body lines)."""
    out = []
    for i, line in enumerate(lines):
        m = PY_BODY_HEAD.match(line)
        if not m:
            continue
        indent, name = len(m.group(1)), m.group(2)
        # multi-line signatures — the head ends at the line where paren balance returns to 0 and ends with ':'
        depth, end = 0, None
        for j in range(i, min(i + HEAD_MAX_WALK, len(lines))):
            depth += lines[j].count('(') - lines[j].count(')')
            if depth <= 0 and lines[j].rstrip().endswith(':'):
                end = j
                break
        if end is None:
            continue
        body = []
        for j in range(end + 1, min(end + 1 + BODY_MAX_WALK, len(lines))):
            cur = lines[j]
            if cur.strip() and (len(cur) - len(cur.lstrip())) <= indent:
                break
            body.append(cur)
        out.append((name, i + 1, path, body))
    return out


def _find_body_open(lines: list[str], start_line: int, start_col: int) -> tuple[int, int] | None:
    """Find the first body '{' at paren depth 0 from the name position.

    A '{' inside parameter defaults (depth > 0) is skipped; a ';' at depth 0 means not a function.
    """
    depth = 0
    for j in range(start_line, min(start_line + HEAD_MAX_WALK, len(lines))):
        seg = lines[j]
        k = start_col if j == start_line else 0
        while k < len(seg):
            ch = seg[k]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == '{' and depth <= 0:
                return j, k
            elif ch == ';' and depth <= 0:
                return None
            k += 1
    return None


def _js_bodies(path: str, lines: list[str]) -> list[tuple[str, int, str, list[str]]]:
    """js/ts/vue functions/methods as (name, line, path, raw body lines) — brace-matched."""
    out = []
    for i, line in enumerate(lines):
        head = None
        for rx in JS_BODY_HEADS:
            mm = rx.match(line)
            if mm:
                head = mm
                break
        if head is None:
            continue
        name = head.group(2)
        if name in JS_KEYWORD_SKIP:
            continue
        openpos = _find_body_open(lines, i, head.start(2))
        if openpos is None:
            continue
        oj, ok = openpos
        depth, closed = 0, False
        close_j, close_k = oj, ok
        for j in range(oj, min(oj + BODY_MAX_WALK, len(lines))):
            seg = lines[j]
            k = ok if j == oj else 0
            while k < len(seg):
                ch = seg[k]
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        close_j, close_k, closed = j, k, True
                        break
                k += 1
            if closed:
                break
        if not closed or close_j == oj:
            continue  # unclosed (tracking failed) or one-line body — no candidate material
        body = [lines[oj][ok + 1:]] + lines[oj + 1:close_j] + [lines[close_j][:close_k]]
        out.append((name, i + 1, path, body))
    return out


def scan_same_body(files_lines: dict[str, list[str]]) -> list[tuple]:
    """Normalized-body hash → function-site groups. 2+ places = a candidate (2 in one file too)."""
    by_hash: dict[str, list[tuple[str, int, str, int]]] = {}
    for path, lines in files_lines.items():
        lang = lang_of(path)
        if lang == 'python':
            bodies = _py_bodies(path, lines)
            comment_heads: tuple[str, ...] = ('#',)
        elif lang in ('js', 'ts', 'vue'):
            bodies = _js_bodies(path, lines)
            comment_heads = ('//', '/*', '*')
        else:
            continue  # other languages are outside the body scan (partial support — see the header)
        for name, no, p, body in bodies:
            norm = _norm_body(body, comment_heads)
            if len(norm) < BODY_MIN_LINES:
                continue
            digest = hashlib.sha256('\n'.join(norm).encode()).hexdigest()
            by_hash.setdefault(digest, []).append((p, no, name, len(norm)))
    groups = []
    for _digest, locs in by_hash.items():
        if len(locs) >= 2:
            groups.append(sorted(locs))
    groups.sort()
    return groups


# ── Output ──

def fmt_value(value: tuple[str, str]) -> str:
    kind, key = value
    return f'"{key[:20]}"' if kind == 'str' else key


def print_inventory(files_lines: dict[str, list[str]], keyword: str = '') -> None:
    kw = keyword.lower()
    print('## Existing symbol sight (collection & print only — no judgment, no gate)' + (f' — lookup {keyword!r} (partial name match)' if kw else ''))
    total = 0
    out: list[str] = []
    per_dir: dict[str, list[int]] = {}
    for path in sorted(files_lines):
        decls = top_level_decls(path, files_lines[path])
        if kw:
            decls = [d for d in decls if kw in d[0].lower()]
        if not decls:
            continue
        total += len(decls)
        d = per_dir.setdefault(os.sep.join(path.split(os.sep)[:2]), [0, 0])
        d[0] += 1
        d[1] += len(decls)
        listing = ' · '.join(f'{name}({kind} L{no})' for name, no, kind, _l in decls)
        out.append(f'{path}: {listing}')
    size = sum(len(l.encode('utf-8')) + 1 for l in out)
    if size <= INVENTORY_INLINE_MAX:
        for l in out:
            print(l)
    else:
        print(f'[Summary mode] the full list is {size // 1000}KB — over the print cap ({INVENTORY_INLINE_MAX // 1000}KB), so only per-folder tallies '
              f'are printed. Look up by name: --inventory=<keyword> (partial name match, case-insensitive)')
        print_capped([f'{k}: {v[0]} files · {v[1]} symbols' for k, v in sorted(per_dir.items())], ' folder(s)')
    print(f'— {len(files_lines)} files · {total} top-level symbols{" (lookup matches)" if kw else ""}. '
          f'Before creating a constant/function with the same purpose, look it up in this list (in summary mode, a --inventory=<name stem> lookup) first.')


def main() -> None:
    args = sys.argv[1:]
    inv_flags = [a for a in args if a == '--inventory' or a.startswith('--inventory=')]
    inventory = bool(inv_flags)
    keyword = inv_flags[0].partition('=')[2] if inventory else ''  # '' = the full list
    show_all = '--all' in args
    args = [a for a in args if a not in inv_flags and a != '--all']
    rules_path = None
    targets = []
    for a in args:
        if a.endswith('.md'):
            rules_path = a
        else:
            targets.append(a)
    if not targets:
        print('usage: python3 verify_enforced_rules.py <src dir or files...> '
              '[rules.md] [--inventory | --inventory=keyword] [--all]', file=sys.stderr)
        sys.exit(2)

    files = collect_files(targets)
    files_lines = {p: read_lines(p) for p in files if lang_of(p)}

    if inventory:
        print_inventory(files_lines, keyword)
        sys.exit(0)

    if rules_path is None:
        rules_path = DEFAULT_RULES_PATH
    if not os.path.isfile(rules_path):
        print(f'ℹ️  no enforced-rules file ({rules_path}) — C3 not applicable (0 checks)')
        sys.exit(0)
    with open(rules_path, encoding='utf-8') as f:
        scans, patterns, warnings = parse_rules(f.read())

    candidates = []  # (rule ID, anchor path, anchor line, message, key) — key = the string matched against the candidate-rejection ledger

    if 'same-name' in scans:
        rid = scans['same-name']
        groups, name_reported = scan_same_name(files_lines)
        for name, locs in groups:
            (p0, l0, kind), rest = locs[0], locs[1:]
            others = join_locs([f'{p}:{l}' for p, l, _k in rest])
            head = f"same-name definition '{name}' ({kind}) in {len(locs)} places"
            candidates.append((rid, p0, l0, f'{head} — also: {others}', f'[{rid}] {head}'))
    else:
        name_reported = set()

    if 'same-value' in scans:
        rid = scans['same-value']
        for value, locs in scan_same_value(files_lines, name_reported):
            (p0, l0, n0), rest = locs[0], locs[1:]
            others = join_locs([f'{p}:{l}({n})' for p, l, n in rest])
            head = f'same-value constant {fmt_value(value)} in {len(locs)} places'
            candidates.append((rid, p0, l0, f'{head} — {n0}; also: {others}', f'[{rid}] {head}'))

    if 'same-body' in scans:
        rid = scans['same-body']
        for locs in scan_same_body(files_lines):
            (p0, l0, n0, nl), rest = locs[0], locs[1:]
            others = join_locs([f"{p}:{l}('{n}')" for p, l, n, _c in rest])
            head = f"same-body function '{n0}' ({nl} normalized lines) in {len(locs)} places"
            candidates.append((rid, p0, l0, f'{head} — also: {others}', f'[{rid}] {head}'))

    for rid, rx in patterns:
        for path, lines in sorted(files_lines.items()):
            for no, line in enumerate(lines, 1):
                if rx.search(line):
                    text = line.strip()[:120]
                    candidates.append((rid, path, no, text, f'{path} [{rid}] {text}'))

    rejected = set() if show_all else load_rejected()
    excluded = sum(1 for c in candidates if c[4] in rejected)
    candidates = [c for c in candidates if c[4] not in rejected]
    rej_note = f' · {excluded} excluded as matching the candidate-rejection ledger (--all for everything)' if excluded else ''
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    print_capped([f'{path}:{no} [{rid}] {msg}' for rid, path, no, msg, _k in candidates], ' candidate(s)')

    for w in warnings:
        print(f'⚠️  {w}')

    machine_rules = len(scans) + len(patterns)
    scanned = len(files_lines)
    if not candidates:
        print(f'✅ PASS — no enforced-rule violation candidates ({scanned} files examined · {machine_rules} machine-checked rules{rej_note})')
        if scanned == 0:
            print('[CAUTION] 0 files examined — no supported-language files, so this PASS may be meaningless.')
        if machine_rules == 0:
            print('[CAUTION] 0 machine-checked rules — every check method in the table is outside the engine, so this PASS may be meaningless.')
        sys.exit(0)

    print(f'\n{len(candidates)} candidates ({scanned} files examined · {machine_rules} machine-checked rules{rej_note}) — '
          f'each candidate is a confirmation target, not a defect.')
    print('The checker confirms each on-site and judges via the C3 procedure in checker-rules.md.')
    sys.exit(1)


if __name__ == '__main__':
    main()
