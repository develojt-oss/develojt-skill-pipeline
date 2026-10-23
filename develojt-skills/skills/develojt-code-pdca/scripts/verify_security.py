#!/usr/bin/env python3
"""Security rule violation candidate detector (develojt-code-pdca C2 only).

A floor-level detector that sweeps only **the classes detectable by static patterns**
among the principles of rules/security-conventions.md. Its output is not defects but
**candidates** — the judgment (executing code? placeholder? SPEC-specified usage?)
is made by the checker via the C2 procedure in checker-rules.md.
Therefore PASS (0 candidates) does not mean "no security problems" — only that the
machine-detectable classes produced no candidates.

Detection classes (pattern codes):
  SEC-S1  private key block (-----BEGIN ... PRIVATE KEY-----)
  SEC-S2  AWS access key format (AKIA + 16 chars)
  SEC-S3  credential literal assignment (password/secret/api_key etc. = "value")
  SEC-S4  a real value on a credential key in a config-type file (.env, json, yml, toml, ini, properties, config, etc. —
          only values of 6+ chars containing a digit; ${VAR}, %VAR%, <…>-style references excluded — blocking label/placeholder noise)
  SEC-A1  string code execution (eval/exec/new Function)
  SEC-A2  untrusted deserialization (pickle.load / ObjectInputStream / BinaryFormatter)
  SEC-A3  unsafe yaml.load
  SEC-A4  shell string execution (shell=True / os.system·os.popen / subprocess.getoutput·getstatusoutput
          / Runtime.exec / system / child_process.exec·execSync / shell: true)
  SEC-A5  broken hash algorithms (MD5 / SHA-1)
  SEC-A6  TLS verification disabled (verify=False / rejectUnauthorized: false etc.)
  SEC-A7  raw HTML insertion (innerHTML/outerHTML assignment (incl. +=) / dangerouslySetInnerHTML
          / insertAdjacentHTML / v-html / document.write)
  SEC-A8  CORS wildcard (`*` in the Access-Control-Allow-Origin header — language-agnostic)
  SEC-A9  unbounded C functions (gets/strcpy/strcat/sprintf)
  SEC-Q1  SQL string assembly (SQL literal + concatenation/interpolation)

Supported languages: JavaScript, TypeScript, Vue, Python, C#, Java, C++
(SEC-S1~S3 and SEC-A8 are language-agnostic — applied to all supported extensions)
Config-type files (the extensions above, .env*, .npmrc, .pypirc, .netrc) get only SEC-S1, S2, S4, A8 — those inside the
target arguments, and, with `--root-config`, the config-type files directly under the run location (the project root,
non-recursive) as well (the pipeline's code root is src/, but .env, appsettings.json, docker-compose.yml sit at the root —
§5 secrets in config files).

Usage:
    python3 scripts/verify_security.py src/
    python3 scripts/verify_security.py src/ --root-config   # + config-type files directly under the root (.env, etc.)
    python3 scripts/verify_security.py src/ --all           # ignore the candidate-rejection ledger — full recheck (on human instruction / checker calibration)

Candidate-rejection ledger: reads spec/findings-rejected.md at the run location (if present); candidates whose key matches
are not printed and are noted in the summary as `N excluded as matching the candidate-rejection ledger` — these are rejection
verdicts (location, basis) the checker made and the Lead recorded, so they are inherited.
Key = the printed line minus `:line-number` (`src/a.py [SEC-A4] os.system(cmd)`). If the line's text changes, the key no
longer matches and it is printed again.

Secret-value masking: values caught as secrets (the key body on the same line after an S1 marker, S2 keys, S3 and S4 values)
are never carried verbatim in printed lines or keys — the detector's output is a log too (§10), and the rejection ledger is a
commit target (§5). The value's place shows `<masked>`, and a tag at the end of the line carries the value's identity:
  code files, config files git does not ignore → `(value fingerprint xxxxxxxx)` — the first 8 chars of the value's hash. The value
                                                 is already in the repository, or its being there is itself a defect, so no
                                                 new information leaks.
  config files git ignores, git unverifiable    → `(git-ignored file · line N · mtime …)` — a place where a real value legitimately
                                                 stays, so zero information derived from the value. It stops matching when the
                                                 file is rewritten or its git status changes (tracked / un-ignored).
When the value, the file, or the git status changes, the key no longer matches and it is printed again (the inheritance
property is unchanged). Legacy keys (v0.4.0 — lines with the value verbatim) still match too.

Print cap: candidate detail lines are printed up to 16KB, and beyond that a `… N more … not printed` notice is printed (the
harness replaces tool output of roughly 30KB or more with a preview, so the tail would silently disappear). If the notice
appears, it is not exhaustive — narrow the target argument down to subfolders/files and re-run. Exit codes and count summaries
are based on the full set.

Exit codes: 0 — no candidates (PASS) / 1 — candidates found (checker on-site confirmation needed)

"""

import hashlib
import os
import re
import subprocess
import sys

# Per-language extension mapping (same set as verify_refs.py)
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

# Config-type files — outside the code extensions, but places where secrets ride (§5). Only SEC-S1, S2, S4, A8 apply.
CONFIG_EXTENSIONS = ('.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf',
                     '.properties', '.config', '.env')
CONFIG_DOTFILES = ('.npmrc', '.pypirc', '.netrc')

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

# Note: unlike the other verify scripts, tests/ and __tests__/ are NOT skipped —
# security-conventions §5 forbids hardcoded secrets in test code too.
SKIP_DIRS = {'node_modules', 'dist', 'build',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

# ── Language-agnostic: secrets (flagged even inside comments/strings — leaks care nothing for location) ──
GLOBAL_PATTERNS = [
    ('SEC-S1', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('SEC-S2', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('SEC-S3', re.compile(
        r'(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey'
        r'|access[_-]?token|auth[_-]?token|client[_-]?secret'
        r'|private[_-]?key|connection[_-]?string)\b'
        r'\s*[:=]\s*["\']([^"\']{4,})["\']')),  # value group (2) is for the masking position — the match span is unchanged
    # After the header name, separators (one or more non-word chars such as quotes, colons, equals, commas, brackets, alignment spaces — no upper bound), then `*` — independent of config syntax
    ('SEC-A8', re.compile(r'Access-Control-Allow-Origin\W+\*')),
]
CONFIG_GLOBAL_PATTERNS = [p for p in GLOBAL_PATTERNS if p[0] != 'SEC-S3']  # S3 is for code syntax (quoted values) only

# ── Config-type files: a real value on a credential key (SEC-S4) ──
# key (partial match, case-insensitive) [:=] value — the value's quotes are optional, up to whitespace/quotes/,;#, 6+ chars containing a digit (excluding labels/words).
CONFIG_SECRET_RE = re.compile(
    r'(?i)(password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?token|auth[_-]?token|token'
    r'|client[_-]?secret|private[_-]?key|connection[_-]?string)[\w.-]*["\']?\s*[:=]\s*["\']?'
    r'(?=[^"\'\s,;#]*\d)([^"\'\s,;#]{6,})')
# Reference/substitution forms are not real values: ${VAR} $VAR %VAR% <VAR> {{VAR}} $(cmd)
CONFIG_PLACEHOLDER_RE = re.compile(r'^(?:\$\{|\$[A-Za-z_]|%|<|\{\{|\$\()')

# ── Per-language: dangerous APIs ──
LANG_PATTERNS = {
    'python': [
        # (?<!\.) — excludes same-named method calls like model.eval()/obj.exec() (built-in eval/exec only)
        ('SEC-A1', re.compile(r'(?<!\.)\b(eval|exec)\s*\(')),
        ('SEC-A2', re.compile(r'\bpickle\.loads?\s*\(')),
        ('SEC-A3', re.compile(r'\byaml\.load\s*\(')),
        # os.popen and subprocess.getoutput/getstatusoutput run the argument string through the shell (the same class as os.system)
        ('SEC-A4', re.compile(r'shell\s*=\s*True|os\.(system|popen)\s*\(|subprocess\.get(status)?output\s*\(')),
        ('SEC-A5', re.compile(r'\bhashlib\.(md5|sha1)\s*\(')),
        ('SEC-A6', re.compile(r'\bverify\s*=\s*False\b')),
    ],
    'js': [
        ('SEC-A1', re.compile(r'\beval\s*\(|new\s+Function\s*\(')),
        # Only explicit child_process calls and execSync — a bare exec( is excluded as a same-named idiom such as RegExp.exec (the miss direction)
        ('SEC-A4', re.compile(r'\bchild_process\.(exec|execSync)\s*\(|\bexecSync\s*\(|\bshell\s*:\s*true\b')),
        ('SEC-A6', re.compile(r'rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED')),
        ('SEC-A7', re.compile(
            r'\.(innerHTML|outerHTML)\s*\+?=|dangerouslySetInnerHTML'
            r'|\.insertAdjacentHTML\s*\(|document\.write\s*\(')),
    ],
    'csharp': [
        ('SEC-A2', re.compile(r'\bBinaryFormatter\b')),
        ('SEC-A5', re.compile(r'\b(MD5|SHA1)\.Create\s*\(|new\s+(MD5|SHA1)CryptoServiceProvider')),
        ('SEC-A6', re.compile(r'ServerCertificate(Custom)?ValidationCallback\s*[+]?=')),
    ],
    'java': [
        ('SEC-A2', re.compile(r'new\s+ObjectInputStream\s*\(')),
        ('SEC-A4', re.compile(r'Runtime\.getRuntime\(\)\.exec\s*\(')),
        ('SEC-A5', re.compile(r'MessageDigest\.getInstance\s*\(\s*"(MD5|SHA-?1)"')),
    ],
    'cpp': [
        ('SEC-A4', re.compile(r'\bsystem\s*\(')),
        ('SEC-A9', re.compile(r'\b(gets|strcpy|strcat|sprintf)\s*\(')),
    ],
}
# ts and vue share the js patterns (vue adds v-html)
LANG_PATTERNS['ts'] = LANG_PATTERNS['js']
LANG_PATTERNS['vue'] = LANG_PATTERNS['js'] + [
    ('SEC-A7', re.compile(r'\bv-html\s*=')),
]

# ── SQL string assembly (js·ts·vue·python·csharp·java) ──
# A literal starting with a SQL keyword right after a quote + a concatenation/interpolation trace on the same line → candidate.
SQL_LITERAL_RE = re.compile(
    r'["\'`]\s*(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|DELETE)\b', re.IGNORECASE)
SQL_CONCAT_RE = re.compile(r'["\'`]\s*\+|\+\s*["\'`]|\$\{')
SQL_FSTRING_RE = re.compile(r'\bf["\']')  # python f-string
CS_INTERP_RE = re.compile(r'\$@?"|@\$"')  # C# interpolated strings ($"...", $@"...")
SQL_LANGS = {'js', 'ts', 'vue', 'python', 'csharp', 'java'}


def lang_of(path: str) -> str | None:
    """Return the language key for the extension. None if unsupported."""
    for lang, exts in LANG_EXTENSIONS.items():
        if path.endswith(exts):
            return lang
    return None


def is_config(path: str) -> bool:
    """Is this a config-type file (outside the code extensions — .env*, the listed dotfiles, config extensions)?"""
    base = os.path.basename(path)
    return base.startswith('.env') or base in CONFIG_DOTFILES or base.endswith(CONFIG_EXTENSIONS)


# ── Secret-value masking: the detector's output is a log too (§10) — values caught as secrets are never carried verbatim in printed lines or rejection keys (see the docstring).
#    Masking follows exactly the criteria detection uses to catch secrets (detection targets and verdicts unchanged — only the print representation and keys change).
SECRET_RES = dict(p for p in GLOBAL_PATTERNS if p[0] in ('SEC-S1', 'SEC-S2', 'SEC-S3'))
KEY_MATERIAL_RE = re.compile(r'[A-Za-z0-9+/]{20,}')  # key body on the same line after a private-key marker (one-line JSON, etc.)
SECRET_MASK = '<masked>'


def secret_spans(line: str, cfg: bool) -> list[tuple[int, int]]:
    """Positions of the values caught as secrets on the line — the key body after an S1 marker, S2 keys, S3 (code) / S4 (config) values. Overlaps are merged."""
    spans = [m.span() for m in SECRET_RES['SEC-S2'].finditer(line)]
    m = SECRET_RES['SEC-S1'].search(line)
    if m and KEY_MATERIAL_RE.search(line, m.end()):
        spans.append((m.end(), len(line)))
    if cfg:
        spans += [m.span(2) for m in CONFIG_SECRET_RE.finditer(line) if not CONFIG_PLACEHOLDER_RE.match(m.group(2))]
    else:
        spans += [m.span(2) for m in SECRET_RES['SEC-S3'].finditer(line)]
    merged: list[tuple[int, int]] = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def mask_line(line: str, spans: list[tuple[int, int]], width: int = 120) -> str:
    """Within the print width, replace secret-value positions with <masked> — a value straddling the width is masked in its visible part too."""
    out, pos = [], 0
    for s, e in spans:
        if s >= width:
            break
        out += [line[pos:s], SECRET_MASK]
        pos = min(e, width)
    out.append(line[pos:width])
    return ''.join(out)


def run_git(args: list[str], data: bytes | None = None) -> subprocess.CompletedProcess | None:
    """One read-only git query — None on no git, errors, or timeout."""
    feed = {'input': data} if data is not None else {'stdin': subprocess.DEVNULL}
    try:
        return subprocess.run(['git', *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30, **feed)
    except (OSError, subprocess.SubprocessError):
        return None


def git_ignored_map(paths: list[str]) -> dict[str, bool | None]:
    """For each config file, does git treat it as ignored (untracked) — True/False; None when unverifiable (no git, not a repository).
    Asks once (check-ignore --stdin); on failure (paths outside the repository mixed in, etc.) asks again per file — so one file's
    circumstances never cloud another file's verdict."""
    def ask(ps: list[str]) -> set[str] | None:
        r = run_git(['check-ignore', '-z', '--stdin'], b''.join(os.fsencode(p) + b'\0' for p in ps))
        if r is None or r.returncode not in (0, 1):
            return None
        return {os.fsdecode(b) for b in r.stdout.split(b'\0') if b}

    if not paths:
        return {}
    hit = ask(paths)
    if hit is not None:
        return {p: p in hit for p in paths}
    if len(paths) > 1:
        inside = run_git(['rev-parse', '--is-inside-work-tree'])
        if inside is not None and inside.stdout.strip() == b'true':
            return {p: (None if (h := ask([p])) is None else p in h) for p in paths}
    return dict.fromkeys(paths)


def secret_tag(path: str, no: int, line: str, spans: list[tuple[int, int]], ignored: bool | None) -> str | None:
    """The value's identity tag — a value fingerprint for code files and config files git does not ignore; elsewhere (a place where a real value legitimately stays), the line and the file's mtime."""
    if lang_of(path) or ignored is False:
        values = '\x00'.join(line[s:e] for s, e in spans)
        return f'value fingerprint {hashlib.sha256(values.encode("utf-8")).hexdigest()[:8]}'
    try:
        mtime = os.stat(path).st_mtime_ns
    except OSError:
        return None
    return f'{"git-ignored file" if ignored else "git unverifiable"} · line {no} · mtime {mtime}'


def scan_config_file(path: str, lines: list[str]) -> list[tuple[int, str, str]]:
    """One config-type file's candidate list — S1, S2, A8 + S4 (a real value on a credential key)."""
    hits = []
    for no, line in enumerate(lines, 1):
        for code, rx in CONFIG_GLOBAL_PATTERNS:
            if rx.search(line):
                hits.append((no, code, line.strip()))
        m = CONFIG_SECRET_RE.search(line)
        if m and not CONFIG_PLACEHOLDER_RE.match(m.group(2)):
            hits.append((no, 'SEC-S4', line.strip()))
    return hits


def scan_file(path: str) -> list[tuple[int, str, str]]:
    """Return one file's candidate list [(line number, pattern code, line content)]."""
    lang = lang_of(path)
    cfg = lang is None and is_config(path)
    if lang is None and not cfg:
        return []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
    except OSError as e:
        print(f"[WARN] read failed: {path} ({e})", file=sys.stderr)
        return []
    if cfg:
        return scan_config_file(path, lines)

    patterns = GLOBAL_PATTERNS + LANG_PATTERNS.get(lang, [])
    hits = []
    for no, line in enumerate(lines, 1):
        for code, rx in patterns:
            if rx.search(line):
                hits.append((no, code, line.strip()))
        if lang in SQL_LANGS and SQL_LITERAL_RE.search(line):
            if SQL_CONCAT_RE.search(line) or (
                    lang == 'python' and SQL_FSTRING_RE.search(line) and '{' in line) or (
                    lang == 'csharp' and CS_INTERP_RE.search(line) and '{' in line):
                hits.append((no, 'SEC-Q1', line.strip()))
    return hits


def collect_files(targets: list[str]) -> list[str]:
    """Collect supported-extension files from the targets (directories/files)."""
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(os.path.normpath(target))
        elif os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                files.extend(
                    os.path.normpath(os.path.join(root, n)) for n in sorted(names)
                    if n.endswith(ALL_EXTENSIONS) or is_config(n))
        else:
            print(f"[ERROR] target does not exist: {target}", file=sys.stderr)
            sys.exit(2)
    return files


def root_config_files() -> list[str]:
    """Config-type files directly under the run location (the project root) — non-recursive (never descends into subfolders, .claude, or spec)."""
    return sorted(n for n in os.listdir('.') if os.path.isfile(n) and is_config(n))


def main() -> None:
    args = sys.argv[1:]
    root_config = '--root-config' in args
    show_all = '--all' in args
    args = [a for a in args if a not in ('--root-config', '--all')]
    if not args:
        print("Usage: python3 verify_security.py <src directory or files...> [--root-config] [--all]", file=sys.stderr)
        sys.exit(2)

    files = collect_files(args)
    root_files = root_config_files() if root_config else []
    files += [f for f in root_files if f not in files]
    rejected = set() if show_all else load_rejected()
    total = 0
    excluded = 0
    detail = []
    rows = [(path, no, code, line, secret_spans(line, lang_of(path) is None))
            for path in files for no, code, line in scan_file(path)]
    ignored = git_ignored_map(sorted({r[0] for r in rows if r[4] and lang_of(r[0]) is None}))  # only config files with secret values
    for path, no, code, line, spans in rows:
        shown = line[:120]
        keys = {f"{path} [{code}] {shown}"}  # key = the printed line minus :line-number
        if spans:  # a line with a secret value — the verbatim value leaves the print and the key, and a tag carries its identity (the legacy key above still matches)
            tag = secret_tag(path, no, line, spans, ignored.get(path))
            shown = f"{mask_line(line, spans)} ({tag or 'mtime check failed — not inherited even if recorded'})"
            if tag:
                keys.add(f"{path} [{code}] {shown}")
        if keys & rejected:
            excluded += 1
            continue
        total += 1
        detail.append(f"{path}:{no} [{code}] {shown}")
    print_capped(detail, ' candidate(s)')
    rej_note = f" · {excluded} excluded as matching the candidate-rejection ledger (--all for everything)" if excluded else ""

    scanned = sum(1 for f in files if lang_of(f) or is_config(f))
    root_note = f" · including {len(root_files)} root config file(s)" if root_config else ""
    if total == 0:
        print(f"✅ PASS — no security rule violation candidates ({scanned} files examined{root_note}{rej_note})")
        if scanned == 0:
            print("[CAUTION] 0 files examined — no supported-language files, so this PASS may be meaningless.")
        sys.exit(0)

    print(f"\n{total} candidate(s) ({scanned} files examined{root_note}{rej_note}) — each candidate is a confirmation target, not a defect.")
    print("The checker confirms each on-site and judges via the C2 procedure in checker-rules.md.")
    sys.exit(1)


if __name__ == '__main__':
    main()
