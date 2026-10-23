# Candidate-Rejection Ledger (findings-rejected)

> The record of verdicts where the pdca checker rejected C2 (security), C3 (enforced rules), and C4 (structure contract) **candidates** as "not a defect".
> The 3 detectors (verify_security, verify_enforced_rules, verify_architecture) read this file at the run location (the project root) and
> do not print candidates whose key matches — recorded verdicts are inherited (for a full re-check, give the detectors `--all`).
> **Key** = the detector's printed line minus `:line-number` (`src/a.py [SEC-A4] os.system(cmd)`). For C3 scan candidates (same-name, same-value, same-body),
> up to the first ` — ` (`[R-01] same-name definition 'main' (function) in 3 places`). Write a `|` inside the key as `\|`.
> For C2 secret candidates, the value is `<masked>` and the key is the printed line as-is, including the end-of-line tag `(…)` — never write the verbatim value in this ledger (a commit target).
> When the code changes and the line text or place count differs, the key no longer matches and the candidate is printed again — that is then a new verdict (an automatic re-check).
> Rows are never deleted (a mismatched key left in place is harmless). The only writer is the Lead (the pdca Check record — carrying the checker's `Note: candidate rejected | key | basis` over as-is).

| Key | Rejection reason (checker note — quoted grounds) | Record (cycle · date) |
|---|---|---|
