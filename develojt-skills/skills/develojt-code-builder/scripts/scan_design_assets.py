#!/usr/bin/env python3
"""develojt-code-builder design/ asset collection script (collection & print only — no judgments).

Prints the deterministic collection of builder workflow step 1 (Assess state) in one go:
  1. Asset listing — fact buckets by extension/name (display classification, not role verdicts)
  2. Companion assets — existence/absence of files pointed at by the screen sources'
     load/reference declarations (<script src>, <link href>, media src, @import, url(), fetch)
     (double net ①)
  3. The STORYBOARD 'Shared technical assets' row (double net ②)
  4. Executable-code candidates in text-based assets (SVG) — same pattern as essential 3's surface check
  5. Presence of the files never followed (candidate queue, conflicts file, mapper intermediates)
     and role-undetermined files

Role, consumption-mode (use as-is / translated reproduction), and data-source judgments are NOT
made here — those belong to SKILL essential 3; this script only supplies the judgments' input facts.
It writes no files (print only).

Usage:
    python3 scan_design_assets.py [design_dir]   (default: ./design)

Exit codes: 0 — collection done (including design/ absent) / 1 — argument error
"""

import fnmatch
import re
import sys
from pathlib import Path

SOURCE_EXTS = {".html", ".htm"}
STYLE_EXTS = {".css"}
SCRIPT_EXTS = {".js", ".mjs"}
FONT_EXTS = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg"}
DATA_EXTS = {".json", ".csv", ".yaml", ".yml"}
SKIP_NAMES = {".DS_Store"}
SKIP_DIRS = {"__pycache__"}

# The files never followed — mapper deliverables, queues, intermediates (same list as builder essential 3)
NONCOMPLIANT_PATTERNS = (
    "spec-candidates.md", "spec-conflicts.md", "inventory.md",
    "map-*.md", "review-*.md", "storyboard-*.md",
    "spec-candidates-*.md", "spec-conflicts-*.md",
)
STORYBOARD_NAME = "STORYBOARD.md"
SHARED_ASSET_KEYWORD = "Shared technical assets"

# The screen sources' load/reference declarations (same family as builder essential 3's enumeration)
REF_RES = (
    re.compile(r"<script[^>]+?src=[\"']([^\"']+)[\"']", re.IGNORECASE),
    re.compile(r"<link[^>]+?href=[\"']([^\"']+)[\"']", re.IGNORECASE),
    re.compile(r"<(?:img|source|audio|video|embed|iframe)[^>]+?src=[\"']([^\"']+)[\"']", re.IGNORECASE),
    re.compile(r"@import\s+(?:url\(\s*)?[\"']?([^\"')\s;]+)"),
    re.compile(r"url\(\s*[\"']?([^\"')\s]+?)[\"']?\s*\)"),
    re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']"),
)
EXTERNAL_PREFIXES = ("http://", "https://", "//", "data:", "mailto:", "tel:", "javascript:", "#")
# Same pattern as essential 3's surface-check grep
SVG_RISK_RE = re.compile(r"<script|javascript:|on(?:load|error|click)=", re.IGNORECASE)

BUCKET_ORDER = (
    "Normative doc (README)", "Screen sources", "Stylesheets", "Scripts", "Images/assets",
    "Fonts", "Data", "Tracing bridge (STORYBOARD)", "Other docs", "Files never followed", "Role undetermined",
)


def collect_files(design: Path) -> list[Path]:
    """Collects every file under design/ in relative-path order (exclusion lists applied)."""
    files = []
    for path in sorted(design.rglob("*")):
        if not path.is_file() or path.name in SKIP_NAMES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(design).parts):
            continue
        files.append(path)
    return files


def bucket_of(path: Path, design: Path) -> str:
    """A file's fact bucket (name first, then extension) — not a role verdict."""
    if any(fnmatch.fnmatch(path.name, pat) for pat in NONCOMPLIANT_PATTERNS):
        return "Files never followed"
    if path.name == STORYBOARD_NAME:
        return "Tracing bridge (STORYBOARD)"
    if path.relative_to(design) == Path("README.md"):
        return "Normative doc (README)"
    ext = path.suffix.lower()
    if ext in SOURCE_EXTS:
        return "Screen sources"
    if ext in STYLE_EXTS:
        return "Stylesheets"
    if ext in SCRIPT_EXTS:
        return "Scripts"
    if ext in FONT_EXTS:
        return "Fonts"
    if ext in IMAGE_EXTS:
        return "Images/assets"
    if ext in DATA_EXTS:
        return "Data"
    if ext == ".md":
        return "Other docs"
    return "Role undetermined"


def extract_refs(source: Path) -> list[str]:
    """Extracts one screen source's load/reference declarations, order-preserving and deduplicated."""
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    refs: list[str] = []
    for regex in REF_RES:
        for ref in regex.findall(text):
            if ref not in refs:
                refs.append(ref)
    return refs


def ref_status(ref: str, source: Path, design: Path) -> tuple[str, str]:
    """One reference as (status, display path) — status: external | exists | missing."""
    if ref.startswith(EXTERNAL_PREFIXES):
        return "external", ref
    clean = ref.split("?")[0].split("#")[0]
    if not clean:
        return "external", ref
    base = design if clean.startswith("/") else source.parent
    target = (base / clean.lstrip("/")).resolve()
    try:
        display = str(target.relative_to(design.resolve()))
    except ValueError:
        display = f"{clean} (outside design/)"
    return ("exists" if target.is_file() else "missing"), display


def svg_risk_hits(files: list[Path], design: Path) -> list[str]:
    """SVG executable-code candidates — relative paths of files hit by the surface-check pattern."""
    hits = []
    for path in files:
        if path.suffix.lower() != ".svg":
            continue
        try:
            if SVG_RISK_RE.search(path.read_text(encoding="utf-8", errors="replace")):
                hits.append(str(path.relative_to(design)))
        except OSError:
            continue
    return hits


def shared_asset_rows(design: Path) -> list[str] | None:
    """The STORYBOARD 'Shared technical assets' rows — None when the STORYBOARD itself is absent."""
    storyboard = design / STORYBOARD_NAME
    if not storyboard.is_file():
        return None
    text = storyboard.read_text(encoding="utf-8", errors="replace")
    return [line.strip() for line in text.splitlines() if SHARED_ASSET_KEYWORD in line]


def print_buckets(files: list[Path], design: Path) -> None:
    """Prints the asset listing in bucket order."""
    buckets: dict[str, list[str]] = {}
    for path in files:
        buckets.setdefault(bucket_of(path, design), []).append(str(path.relative_to(design)))
    print(f"  ℹ️  {len(files)} asset(s) (subfolders included)")
    for name in BUCKET_ORDER:
        if name not in buckets:
            continue
        note = ""
        if name == "Files never followed":
            note = " — not appearance norms (essential 3)"
        elif name == "Role undetermined":
            note = " — state in the report (the human decides the role — essential 3)"
        elif name == "Tracing bridge (STORYBOARD)":
            note = " — read-only (grep by FR ID)"
        print(f"      · {name}({len(buckets[name])}): {', '.join(buckets[name])}{note}")


def print_companions(sources: list[Path], design: Path) -> None:
    """Companion assets (double net ①) — existence/absence of each screen source's load/reference declarations."""
    entries: list[tuple[str, str, str]] = []
    for source in sources:
        src_name = str(source.relative_to(design))
        for ref in extract_refs(source):
            status, display = ref_status(ref, source, design)
            entries.append((status, display, src_name))
    if not entries:
        print("  ℹ️  Companion assets: no load/reference declarations in the screen sources")
        return
    print(f"  ℹ️  Companion assets ({len(entries)} load/reference declaration(s) in the screen sources):")
    marks = {"exists": "✅", "missing": "⚠️ ", "external": "ℹ️ "}
    for status in ("exists", "missing", "external"):
        for st, display, src_name in entries:
            if st == status:
                print(f"      {marks[status]} {status} {display} ← {src_name}")


def main() -> None:
    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [design_dir]", file=sys.stderr)
        sys.exit(1)
    design = Path(sys.argv[1] if len(sys.argv) == 2 else "./design")

    print("=" * 60)
    if not design.is_dir():
        print(f"[SCAN] {design} folder not found — no appearance baseline (implement from the SPEC alone)")
        print("=" * 60)
        sys.exit(0)

    files = collect_files(design)
    print("[SCAN] design/ asset collection — collection only (role/consumption/data-source judgments belong to essential 3)")
    print("=" * 60)
    print_buckets(files, design)

    sources = [p for p in files if bucket_of(p, design) == "Screen sources"]
    print_companions(sources, design)

    rows = shared_asset_rows(design)
    if rows is None:
        print("  ℹ️  No STORYBOARD — double net ② (the shared technical assets row) not applicable")
    elif not rows:
        print("  ⚠️  The STORYBOARD has no 'Shared technical assets' row — double net ② cannot be checked")
    else:
        for row in rows:
            print(f"  ℹ️  STORYBOARD shared technical assets: {row}")

    risks = svg_risk_hits(files, design)
    if risks:
        for rel in risks:
            print(f"  ⚠️  Executable-code candidate (text-based asset): {rel} — never dropped in as-is; state it in the report (the human decides — essential 3)")
    else:
        print("  ✅ 0 executable-code candidates in text-based assets (SVG) (surface check)")
    sys.exit(0)


if __name__ == "__main__":
    main()
