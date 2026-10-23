---
paths:
  - "src/**"
---

# Enforced Rules

This file is the table of code-writing rules where **recording is enforcement**.
Where `code-conventions.md` is prose norms ("why is this good code"), this file's table is read by machines:

- **Check (defense)**: develojt-code-pdca's detector script (`verify_enforced_rules.py`) reads this
  table, finds violation **candidates**, and the checker's C3 procedure judges them (candidate ≠ defect —
  judgment and rejection cite evidence).
- **Sight (prevention)**: develojt-code-builder prints the existing symbol list (`--inventory`)
  before implementing, so it starts by seeing what already exists (when the list is large, a per-folder tally — look names up with `--inventory=<keyword>`).
- **Adding a rule = adding a row to the table below** — nothing else (no skill changes). **But the row is
  added by a human, in the global originals (the pipeline repository)** — this file in a project is a
  deployed copy, read-only, and no session adds rows here (re-initialization overwrites it with the
  originals and the addition is lost — a promotion need goes to the human via pdca's "Process Improvement
  Proposals": the declaration at the top of `code-conventions.md`). It reaches
  every project in use through re-initialization (`/develojt-init`).
- A project without this file has no C3 check at all (legacy projects behave unchanged).

> **Only machine-checkable rules go into the table** (the check-method vocabulary below is a closed list).
> Rules that machines cannot express belong in `code-conventions.md` prose, not here —
> the table is the promise "written here means checked", and an unchecked row breaks that promise
> silently (a check method the engine doesn't know is flagged with ⚠️ by the script — no silent burial).

---

## Enforced Rules Table

| ID | Rule | Check method |
|---|---|---|
| R-01 | Never define top-level functions/classes/constants with the same name in multiple files — define one and reuse it | scan: same-name |
| R-02 | Never define named constants meaning the same literal value separately in multiple files — define it in one place and reuse it | scan: same-value |
| R-03 | Never define functions with identical bodies in multiple places — merge into one (where and how to merge is autonomous) | scan: same-body |

---

## Check-method vocabulary (closed list — any other value is not machine-checked)

| Value | What it catches | Detection precision rules (deterministic — the failure direction is misses: a candidate detector claims no completeness) |
|---|---|---|
| `scan: same-name` | Declarations with the same name defined in 2+ different files | js/ts/vue/python: top level (indent 0) functions/classes/constants only. java/csharp: class/interface/enum names and `static final`/`const` UPPER-case constants only (method names are out of scope — same-named methods across classes are normal idiom). cpp: `#define`/`const`/`constexpr`/classes only; include guards (`*_H` and the like) and header/implementation pairs sharing a stem are excluded |
| `scan: same-value` | Named constants with the same literal value defined in 2+ different files | Numbers: 3+ characters as written and trivial values (0·1·-1·2·10·100·1000) excluded; strings: 4+ characters. Only literals written identically count as the same value (different spellings are not detected). Groups already reported as same-name are not double-reported |
| `scan: same-body` | Functions whose bodies are identical after normalization (whitespace/comments stripped) in 2+ places | js/ts/vue/python only. Bodies of 3+ normalized lines only (one-line getters excluded) |
| `pattern: <regex>` | Every line the regex matches | Line-by-line check across all supported extensions. A pipe character needed inside the regex is escaped as `\|` within the table cell (the engine restores it before compiling) |

- Supported languages (the same set as the other gates): js·ts·vue·python·csharp·java·cpp — cpp/java/csharp partially, per the table above.
- `tests/`/`__tests__/` and similar test folders are not checked (duplication checks target product code — avoiding false positives on intentional fixture/setup repetition).
- Exceptions: a legitimate same-name/same-value (framework conventions and the like) is absorbed not by deleting the rule but by
  the candidate-rejection ledger (`spec/findings-rejected.md` — the Lead records the checker's rejection verdicts with cited evidence,
  and the detector reads it so it never prints the same candidate again) and `Needs review` (SPEC-specified usage — a human decision).
