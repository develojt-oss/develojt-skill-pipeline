# Checker Rules — per-type inspection methods (develojt-code-pdca only)

> The work procedure the develojt-code-pdca-checker agent reads as its first action.
> This is not "look carefully" — **each type is traced, quoted, and judged by its fixed method.**

## Judgment principles (common to all types)

- **Quotable = normal; unquotable = defect.** Quoting the arrival path and implementation site as `file:line`
  is the entirety of judgment. "It probably works" / "it probably doesn't" is not a judgment.
- **Suspicion is not a defect.** If evidence wasn't found, search more (different grep patterns, caller back-tracing).
  Only what remains unfound to the end is a defect — and the evidence then is "the traced path and the broken point".
- **Choices carrying `[Free: reason]` are not inspection targets.** However, if that choice's *result contradicts
  another SPEC requirement*, that is a defect (e.g., a [Free]-chosen retry count is negative, voiding the retry limit).
- **For external-consumer interface requirements, the literal is the requirement.** For the paths, commands, field names, headers, error codes, and formats the SPEC wrote as rows with IDs
  (interfaces that something outside this repository's code builds against — the deriver boundary rule), check whether the code puts out **exactly that value**.
  A similar but different name or shape (differing spelling, notation, or structure) is requirement content unimplemented (M1) or reaching a different target (W2) — neither a `[Free]` nitpick
  nor a style nitpick (style is notation inside the code; this is a value that goes out).
- **Sweeping expressions mean exhaustive coverage.** When a requirement's target/location is sweeping ("on the targets",
  "all", "every", "whenever X occurs"), enumerate every occurrence site of that class in the scope's code and confirm
  the response reaches each site. Satisfying only some sites is a defect, not [Free] — [Free] delegates the value/method,
  never shrinks the application set.
- The starting point is set by the spawn instruction's **inspection lens** (the 'Inspection lenses' section below). Without a lens instruction, it is Lens A.
- **A print-cap notice means "not exhaustive".** If a detection script (C2, C3, C4) prints a `… N more … not printed` notice,
  you have not seen every candidate — split the target argument into subfolders/files and re-run until the notice disappears,
  collect the candidates, and only then judge (the same goes for `(+N more places)` on one candidate line — grep that name to see every place). An 'inspection complete' written with the notice still standing is a false completion.
- **Candidate rejections are recorded and inherited.** A C2, C3, C4 candidate rejection (a 'not a defect' verdict) is returned as one line
  `Note: candidate rejected | key | basis` (the output format section), and the Lead records it in the candidate-rejection ledger (`spec/findings-rejected.md`).
  The 3 detectors do not print candidates that match that ledger's keys — only recorded verdicts are inherited, and unrecorded verdicts
  are still not inherited. When the code changes and the line text or place count differs, the key no longer matches and the candidate
  is printed again — that is then a new verdict (an automatic re-check). For a full re-check, use the detectors' `--all`.

## Inspection lenses (the spawn instruction specifies A/B)

Reading the same scope in the same direction twice makes the second a repetition of the first.
A lens changes the reading's **starting point**, making the two cycles independent trials.
The per-type procedures (M1–S1) and judgment principles are identical across lenses — only the direction of finding implementation sites differs.

### Lens A — implementation tracing (the first-inspection default)

Start from the code: find all implementation sites of the requirement with `grep -rn "@spec {ID}" src/`,
and apply the per-type procedures at those sites.

### Lens B — requirement arrival (quiescence-recheck only)

Start from the SPEC sentences. **Never use @spec tags as the starting point:**

1. For each SPEC ID in scope, extract the **trigger and response vocabulary** (names of events, behaviors, targets) from the EARS sentence.
2. Grep `src/` with that vocabulary (and its candidate English identifiers) to find the implementation sites **from the requirement side**.
3. Confirm the reached site belongs to the declaration carrying that ID's @spec tag (or its call chain) —
   starting from the requirement side exposes, better than Lens A, cases where only the tag exists with the response living
   nowhere, and cases where the tag location and the actual implementation diverge.
4. Then apply the per-type procedures (M1–S1) identically. If vocabulary grep doesn't arrive,
   cross-check via the Lens A method (@spec grep); if the response-producing site still can't be quoted, it is a defect.

## Defect type codes

| Code | Name | One-line definition |
|---|---|---|
| M1 | coverage gap | A SPEC ID has no @spec tag, or has only the tag with the requirement's content unimplemented |
| W1 | missing wiring | A behavior chain's trigger fails to reach some of its required outcomes |
| W2 | incorrect wiring | A trigger reaches a different target than the SPEC's, or a different trigger causes the outcome |
| W3 | uncalled provider | No call/registration path reaches an @spec declaration (an unreachable implementation) |
| F1 | missing failure behavior | An If/Unwanted requirement's failure handling/guard is absent from the implementation |
| C1 | constraint violation | Violation of the tech stack, forbidden libraries, or deterministic constraints (SPEC Document Info) |
| C2 | security rule violation | Machine-detectable violation of the global security rules (`.claude/rules/security-conventions.md`) — hardcoded secrets (including credential values in config-type files), dangerous APIs, query string assembly |
| C3 | enforced-rule violation | Machine-checkable violation of the enforced-rules table (`.claude/rules/enforced-rules.md`) — duplicate definitions (same name/value/body), forbidden patterns |
| C4 | structure-contract violation | Machine-checkable violation of the structure contract (`spec/ARCHITECTURE.md`) — cross-layer references in directions not allowed, folders absent from the layer map |
| S1 | series deviation | An item the joblist grouped into a series is built differently from the reference implementation |

## Per-type verification procedures

### M1 — coverage gap

1. For each SPEC ID in scope, run `grep -rn "@spec {ID}" src/`.
2. No tag → M1 defect (evidence: the empty grep + the SPEC requirement's original text).
3. Tag present → read that declaration's body and confirm **the EARS sentence's observable response** is actually produced.
   If the response is "display/play/record/remove" etc. and the body doesn't produce that output → M1 (evidence: file:line + the missing response).
   (The builder's verify_spec_coverage already checks tag existence — your added value is step 3.)

### W1 — missing wiring (the heart of this inspection)

For each row of the SPEC's **Observable Behavior Chain** tables:

1. Find the trigger's implementation site (the related IDs' @spec → the trigger-producing code).
2. **For each required simultaneous outcome**, trace the arrival path from the trigger site to the outcome-producing site —
   direct calls / event emit→on / callbacks, any method works. Quote each link of the path as `file:line`.
   (For events, the emit and the subscription must exist **as a pair** — emit without a subscription is a break.)
3. If even one outcome's path can't be quoted → W1 (evidence: the traced path + the broken link).
4. Paths conditionally broken by unsubscription or screen (module) teardown (missing re-subscription after re-initialization etc.) are W1 too.

### W2 — incorrect wiring

Checked alongside the W1 trace:

1. Does the outcome also fire **from another trigger**? If the SPEC has no such trigger → W2
   (e.g., the completion notification also sent at receipt time, not completion).
2. Does the trigger additionally cause an outcome absent from the SPEC that **contradicts another requirement**? W2 only when contradictory
   (a non-contradictory extra behavior is implementation discretion — not a defect).
3. In requirements with target distinctions (admin/regular user, sender/receiver, …), is it applied to the opposite target? → W2.

### W3 — uncalled provider (an unreachable implementation)

M1 looks at declaration bodies; W1 looks at chain table rows — neither sees "a healthy body that nobody calls".
This procedure closes that blind spot. Even with a tag and a response-producing body, if no execution path
reaches the declaration, the requirement is unmet.

1. Grep all of `src/` for each in-scope @spec-tagged declaration's name (function, method, class) —
   collect call/reference sites excluding the definition itself and calls inside its own file.
2. Without direct calls, trace indirect arrival — arrival via framework delegation (config object registration,
   routing tables, lifecycle conventions, event subscription registration, …) is normal. Quote the registration site as `file:line`.
3. If no arrival path can be quoted:
   - If the joblist records an **intentional deferral** of this connection and the row carrying the deferral is unchecked (`[ ]`)
     → not a defect. Report as a note only (the deferral is resolved by that row's work).
   - If there is no deferral, or the row carrying it is checked (`[x]`) yet arrival is still impossible
     → W3 (evidence: the definition's file:line + "call/registration grep empty").
4. **Deferrals written in the scope rows' Notes are this inspection's confirmation targets** — trace the arrival path of the
   connection that deferral points at by the same method, and report W3 if unquotable.
5. If calls exist but all of them pass only the same default arguments, so the differentiation the requirement specifies
   (variation by stage/level/kind) can never be expressed by any call → W3 (evidence: argument quotes from every call site).

### F1 — missing failure behavior

For each If/Unwanted-type requirement in scope:

1. In the body at the @spec site, find the **If condition's check code** (guards, branches, clamps).
2. If the condition check is absent, or the check exists but the SPEC's required response (showing a notice,
   proceeding without interruption, forbidding below-zero, …) is not there → F1 (evidence: file:line + the missing guard).
3. For "must proceed without error"-type requirements, check whether that failure is wrapped by propagation-stopping handling (catch, early return).

### C1 — constraint violation

1. Read the tech stack and runtime environment from the SPEC `Document Info`.
2. Grep the dependency files (package.json etc.) and import statements — any framework beyond the stated ones, or forbidden libraries, creeping in.
3. For no-external-transmission / no-storage NFRs, grep for the relevant API usage
   (e.g., for a web runtime: fetch/XMLHttpRequest/localStorage — pick the concrete API names to fit the SPEC's runtime environment).

### C2 — security rule violation (machine-detectable floor)

The SPEC's security requirements (lockout, masking, expiry, …) are not this type — the general
procedures (M1·W1·F1) inspect those. C2 catches only what is globally forbidden regardless of the SPEC,
and among that, only **the classes detectable by static patterns**.
The scope is all of `src/`, not the bundle (the scan costs nothing, and duplicate reports are blocked by the existing defect ID list).

1. Run the script:
   `python3 .claude/skills/develojt-code-pdca/scripts/verify_security.py src/ --root-config`
   (`--root-config` = also checks, non-recursively, the config-type files (.env, appsettings.json, etc.) directly under the run location (the project root) —
   security-conventions §5's secrets in config files. Config-type files inside src/ are checked even without the option.)
   Every output line is a **candidate** — never copy it into a defect row as-is. Secret values are printed masked as `<masked>`, and the `(…)` tag
   at the end of the line carries the value's identity (the value itself is read at that site during step 2's on-site confirmation — the transcription rule is in step 4 and the output format section).
2. For each candidate, read the site and record C2 **only when the site actually violates the security rule**:
   - **Secrets (SEC-S\*)**: an actual credential value → C2. It is a defect even inside a comment,
     string, config, or test code (leaks care nothing for location). An obvious placeholder (format example,
     meaningless dummy) → reject the candidate — note the site and reason in Notes.
   - **Dangerous APIs (SEC-A\*) / query assembly (SEC-Q1)**: these three are candidate rejections (note the site
     and quoted grounds) — ① a mention inside a comment or string literal, ② **a same-named different
     function** (an object's or framework's same-named method is not the language's built-in dangerous
     API — quote the receiver), ③ **usage whose danger condition is resolved on the spot** (a safe loader
     specified, only constant input reaching it, … — quote the resolving grounds verbatim). Any other
     executing code → C2.

   A candidate rejection is returned in the `Note: candidate rejected | key | basis` format (the output format section) — the Lead records it in the candidate-rejection
   ledger, and from the next cycle on the detector does not print that candidate (the judgment principle 'Candidate rejections are recorded and inherited' — verdicts without records are still not inherited).
3. If the usage is explicitly specified by the SPEC (Document Info, requirements), do not record C2 —
   report it as a note instead. A global rule colliding with an explicit human decision is for the human
   to resolve (the Lead raises it as `Needs review`).
4. Evidence: `file:line` + pattern code + a quote of the line. The Target cell is the related SPEC ID
   if one exists, otherwise `global`.
   For secrets (SEC-S\*), never write the verbatim value anywhere in the symptom, evidence, or notes (§5 — the ledger is a commit target too) — the evidence's
   line quote is the detector's printed line minus the end-of-line `(…)` tag (the value fingerprint is not carried into the defect row either — the tag is used only in candidate-rejection keys).
5. Even a script PASS (0 candidates) does not mean "no security problems" — only that the
   machine-detectable classes had no candidates. On PASS the C2 procedure ends here
   (never extend security judgment beyond the patterns on your own).

### C3 — enforced-rule violation (machine-detectable floor)

The SPEC's quality/structure requirements are not this type — the general procedures (M1, W1, F1) cover those.
C3 catches only the writing rules globally forbidden regardless of the SPEC (the enforced-rules table in
`.claude/rules/enforced-rules.md`), and among them only **the machine-checkable classes (scan/pattern)**.
**C3 is not style nitpicking** — it judges only what starts from script candidates and never extends
quality judgment beyond the table. The scope is all of `src/`, not the bundle (same as C2 — duplication
arises between files, so only a global view sees it, and duplicate reports are blocked by the existing
defect-ID list). **Without the rules file there is nothing to check for C3 — skip it.**

1. Run the script:
   `python3 .claude/skills/develojt-code-pdca/scripts/verify_enforced_rules.py src/`
   Each output line is a **candidate** — never copy it into a defect row as-is. ⚠️ lines (check methods
   outside the engine) are not defects but rules-file maintenance material — report them as notes only.
2. For each candidate, read **every** listed site and judge C3 only when the rule violation is real.
   These three are candidate rejections (quote the site and grounds in a note):
   ① an appearance inside a comment or string literal (not an executing declaration — quote the site),
   ② **different entities that merely share a name or value** (show that the two declarations mean
   different things by quoting both definitions and their usage — a redefinition that means the same
   thing under a different spelling or name is not rejection grounds but a violation),
   ③ **a same-name declaration a language/framework convention requires per file** (quote the
   convention's grounds — a config file or official convention). Any other executing code → C3.
3. If the duplication/definition is explicitly specified by the SPEC (Document Info or a requirement),
   do not record it as C3 — report it as a note (a global rule colliding with an explicit human
   decision, so the judgment belongs to the human; the Lead raises it as `Needs review`).
4. Evidence: `file:line` of **every** listed site + the rule ID (R-NN) + a quote of the line. The Target
   cell is the related SPEC ID if one exists, otherwise `global`.
5. Even a script PASS (0 candidates) does not mean "rules complied with" — only that the
   machine-checkable rules had no candidates. On PASS the C3 procedure ends here
   (never extend rule judgment beyond the table or beyond the machine checks on your own).

### C4 — structure-contract violation (machine-detectable floor)

The SPEC's quality/structure requirements are not this type — the general procedures (M1, W1, F1) cover those.
C4 catches only, regardless of the SPEC, the **structure contract this project finalized through a human** (`spec/ARCHITECTURE.md`),
and among it only **the machine-checkable classes (cross-layer references in directions not allowed, folders
absent from the layer map)**. **C4 is not design nitpicking** — it judges only what starts from script
candidates and never extends structural judgment beyond the machine checks (the contract's §3 placement
prose, interface quality, coupling density, etc. are out of scope). **It never judges whether the contract itself
is right** — when a contract revision seems needed, write that as a note only (revisions belong to the
human — the Lead raises it). The scope is all of `src/`, not the bundle (same as C2/C3 — direction
violations arise between files, so only a global view sees them, and duplicate reports are blocked by the
existing defect-ID list). **Without the contract file there is nothing to check for C4 — skip it.**

1. Run the script:
   `python3 .claude/skills/develojt-code-pdca/scripts/verify_architecture.py src/`
   Each output line is a **candidate** — never copy it into a defect row as-is. ⚠️ lines (contract
   sentences the engine cannot parse) are not defects but contract-grammar maintenance material —
   report them as notes only (contract edits belong to the human). `[CAUTION]` lines (held verdicts —
   a tally of candidates not printed because a table could not be read — and the empty-Allowed-table
   notice) are the same: notes, not candidates (with a held verdict present, 0 candidates never means
   "structure complied with").
2. For each candidate, read the site and judge C4 only when the contract violation is real.
   These three are candidate rejections (quote the site and grounds in a note):
   ① a reference inside a comment or string literal (not an executing import/include — quote the site),
   ② **an exception or coexistence the contract explicitly allows** (a sentence in the contract body or
   revision history allowing that reference/place actually exists — quote that sentence. An unrecorded
   "probably coexistence" is not rejection grounds but a violation — only recorded coexistence is legal),
   ③ **a script resolution error** (the import's real target is a different file/layer than the script
   judged — quote the real target's file:line). Any other executing code → C4.
3. If the reference/placement is explicitly specified by the SPEC (Document Info or a requirement),
   do not record it as C4 — report it as a note (the contract colliding with an explicit human
   decision, so the judgment belongs to the human; the Lead raises it as `Needs review`).
4. Evidence: `file:line` (the folder path for unlisted-folder candidates) + the violation content
   (which layer → which layer / the unlisted place) + a quote of the line. The Target cell is the
   related SPEC ID if one exists, otherwise `global`.
5. Even a script PASS (0 candidates) does not mean "structure complied with" — only that the
   machine-checkable classes had no candidates. On PASS the C4 procedure ends here
   (never extend structural judgment beyond the machine checks on your own).

### S1 — series deviation

(Projects without a joblist have no series definitions — S1 has nothing to inspect; skip it.)

1. From the joblist, identify the scope items' series and the **reference implementation** (the series' first item).
2. Compare the reference implementation's code (found via @spec) with the scope item's code — is it the same *way*
   (same foundation reused / same pattern / same wiring method)?
3. If a different way → S1 (evidence: both sides' file:line + one line on what differs).
   Caution: never judge which way is better — judge only "differs from the reference" (consistency is the criterion).

## Re-verification procedure (rows in `Awaiting recheck`)

1. Re-trace the defect row's original evidence (the broken point) — from the beginning, by the same method.
2. If the path now quotes → **Resolved** (evidence: the new arrival path's file:line).
3. If still unquotable → **unresolved** (evidence: the still-broken point). Note whether the fix changed somewhere else.
4. If the fix **created a new defect**, report it as a separate new row (never mixed into the existing row).

## Output format (ledger rows verbatim)

Return new defects in findings.md's defect ledger row format (IDs as `F-NEW-1`, `F-NEW-2`… —
real numbers are assigned by the Lead):

```
| F-NEW-1 | New | W1 | FR-08-001 | confirmation notification not sent on order confirmation | OrderConfirmed emit confirmed at orderService.ts:274, but the subscribing notifier.ts has no send call (logs only) | |
```

Re-verification verdicts, one line per row:

```
F-003: Resolved — orderService.ts:151 emit → notifier.ts:518 subscription path confirmed
F-007: unresolved — a guard was added (stockView.ts:42) but only the internal value is clamped, not the stock display
```

Notes (non-defect reports — C2/C3/C4's SPEC-specified usage, candidate rejections, and ⚠️ contract grammar, W3's intentional deferrals,
SPEC-addition opinions) are returned one per line with a `Note:` prefix, before the summary line.
In particular, **a C2/C3/C4 SPEC-specified-usage note must never be omitted** — the Lead raises it as a
`Needs review` row (a global rule or the contract colliding with an explicit human decision — the human resolves it).
**A C2/C3/C4 candidate-rejection note is fixed to one line: `Note: candidate rejected | {key} | {quoted basis}`** — the key is the detector's printed line
minus `:line-number` (e.g., `src/a.py [SEC-A4] os.system(cmd)` / C4 `src/data/repo.py [C4] direction violation candidate: …`); for C3 scan
candidates (same-name, same-value, same-body), up to the first ` — ` (e.g., `[R-01] same-name definition 'main' (function) in 3 places`). Write a `|` inside the key as `\|`.
The key of a C2 secret candidate is the printed line as-is, including `<masked>` and the end-of-line tag (e.g., `src/a.py [SEC-S3] password = "<masked>" (value fingerprint 3f9a1c2b)`)
— never turn it back into the verbatim value, and never write the verbatim value in the basis quote either (when the value or the file changes, the tag changes and it is re-judged).
The Lead carries that line as-is into a row of the candidate-rejection ledger — if the format is off, it is not inherited and the next cycle judges it again.

Final summary line: `Inspection complete. New N / recheck resolved N / unresolved N`

## Forbidden (summary — identical to the agent definition)

Fixing code / inventing requirements / nitpicking [Free] / nitpicking style (except series deviation) /
defect rows without evidence / duplicate reports of existing defects / guessing implementation intent and giving the benefit of the doubt.
