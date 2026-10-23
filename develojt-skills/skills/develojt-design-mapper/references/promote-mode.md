# Promotion Mode (promote) — applying SPEC increments to the STORYBOARD (adoption promotion · new-FR enrollment)

The path taken **after** a deriver increment has **recorded new FRs** in `spec/SPEC.md`. The delegation input comes in two forms:

- **Adoption promotion** — the human adopted candidates from `design/spec-candidates.md`. The mapper links those
  **finalized FRs** with the queue's **finalized anchors** and records them in `design/STORYBOARD.md`.
- **New-FR enrollment** — pure new FRs unrelated to the candidate queue (the operations 'addition' path). The design
  has no such element, so there is no anchor to map — record **a classification only, in the Orphan List's `[No UI]`
  table** (keeping the coverage contract: every live FR appears — common-rules §5. Appearance is the builder's autonomy).

No full regeneration, no negotiation — the mapper counterpart of the deriver's `incremental-mode` (**every** new FR the increment creates in the SPEC is in scope).

> Stage 2 of develojt-code-changer's (operations change intake) delegation: ① deriver incremental (SPEC recording) → ② this mode (STORYBOARD application) —
> shared by classification 'candidate adoption' (adoption promotion) and base 'addition' (new-FR enrollment — delegate-mode step 3-b).
> **The order is forced** — the mapper reads the SPEC as a file, so it sees the FRs only after the deriver has recorded them finalized (verification PASS).

## Entry conditions

- **The target FRs already exist** in `spec/SPEC.md` (deriver incremental/change completed first — the order gate). If absent, do not enter — return to the delegating lead as "deriver incomplete".
- **For adoption promotion**, `design/spec-candidates.md` contains **candidate rows matching** those FRs. **For new-FR enrollment, no matching candidate may exist** — if one does, it is a classification error (a candidate-adoption-path target): do not enter; return to the delegating lead (so enrollment never becomes a door that bypasses the human's adoption decision).
- **develojt-code-changer (operations change intake) delegates in** — the delegating lead **explicitly passes** the `candidate UI ID ↔ new FR ID` pairs **for adoption promotion**, or the `new FR ID (no candidate)` list **for new-FR enrollment** (which candidate was adopted as which FR — and which FR is a pure new one — is known to the lead who received the intake; the mapper never guess-matches).
- **STORYBOARD existence never blocks entry** — absent: [create]; present: [promote/enroll]. (A human running `/develojt-design-mapper` directly is not this mode — that's SKILL.md's mapping/candidate modes.)

## Core principles

- **The SPEC is read-only — never modified.** The mapper only greps the FRs the deriver already recorded (the SPEC's change owner is the deriver — common-rules §0, design-philosophy Axis 4).
- **No negotiation.** The anchors were already finalized by both sides' negotiation in the candidate queue, and the FRs by the deriver — the mapper only **links** the two (the 2-agent 5-round flow is unnecessary — isomorphic to deriver incremental mode).
- **Anchor reuse — re-identification 0.** Move the queue's anchors into the body as-is (queue columns = body columns). Never mint new anchors ("filling the empty FR cell"). **New-FR enrollment creates no anchor and no mapping at all** — inventing an anchor for an element that doesn't exist in the design is the very core of this prohibition (a `[No UI]` classification row only).
- **Create and promote are the same action.** STORYBOARD existence only decides whether to create the file or append — linking candidates to FRs is identical (enrollment too — absent, create the template structure and record into the Orphan List).
- **Never look at the joblist.** The operations phase touches only `spec/SPEC.md` and `design/` (the spliter's territory is inviolable — same as develojt-code-changer delegate-mode).
- **File relay.** Read the SPEC and spec-candidates as files; write the STORYBOARD and spec-candidates as files. The delegating lead's session context is not received — every needed fact is in the files.

## Procedure

1. **Confirm target FRs and candidates (delegation input validation)** — for each item passed by the delegating lead:
   - `grep "{FR ID}" spec/SPEC.md` to confirm the target FR actually exists in the SPEC. If absent, it is an **order violation** (deriver incomplete) — stop entry and return to the delegating lead.
   - **Adoption promotion**: find that UI ID's candidate row (with anchors) in `design/spec-candidates.md`.
   - **New-FR enrollment**: read `design/spec-candidates.md` (if it exists) and confirm **no candidate implies the same behavior** as that FR — if one does, it is a classification error: stop entry and return to the delegating lead as "a candidate-adoption-path target" (the queue is a small file, so whole reading is fine — the whole-Read ban is a rule for large screen sources).
   - [Weaker-model support / required] Never Read the SPEC or screen sources whole — confirm **by grep only**.

2. **Re-verify anchors (adoption promotion only)** — grep the candidate's source anchor in the screen source and confirm at least 1 hit (common-rules §2 self-verification). If it doesn't hit, correct to a more unique identifier (the last validity check before promotion). If nothing can be found: `[No source: reason]`. (New-FR enrollment has no anchor — this step doesn't exist for it.)

3. **Record into the STORYBOARD — create or update (the only branch)**:
   - **No STORYBOARD → create**: build `design/STORYBOARD.md` in the `templates/STORYBOARD-template.md` structure. Record the adopted candidates in the `SB-NN` section tables **per the screen their visual anchor points at**, writing the target FR ID (full form) in the Mapped FR cell (pure decoration: `[Decorative]`). Keep the Document Info, anchor rules, and Orphan List headers per the template — but **never leave the Document Info shared-technical-assets row as a placeholder**: fill it factually, confirmed via `ls` and the screen source's load/reference declarations (`<script src>`, `<link href>`, etc.); if none: "none (ls-confirmed)" (common-rules §1 — the persistent record of the builder's double net. Candidate mode creates no STORYBOARD, so this creation is that row's only recording moment).
   - **STORYBOARD exists → promote**: **move the candidate row as-is** into the `SB-NN` body table of the screen its visual anchor points at, filling the Mapped FR cell `(not adopted)` → target FR ID (full form). Queue columns = body columns, so the move needs no re-identification.
   - **New-FR enrollment → the Orphan List**: not the body table — **add a row to the Orphan List's `[No UI]` table** (template format `FR ID | Requirement gist | Guess` — the gist summarized by grepping that FR in the SPEC). The Guess cell is one line per common-rules §4: a non-UI requirement → "backend/policy (normal)"; a requirement that needs UI → "design omission (appearance is the builder's autonomy — a target for a future design-incorporation verdict)". Never put it in the body table (no mapping, no anchor). If no STORYBOARD exists, create it in the template structure like the create branch above and record into the Orphan List (the shared-technical-assets row rule applies identically).
   - **FR IDs in full form** (abbreviation forbidden — common-rules §3).

4. **Clean the candidate queue (adoption promotion only)** — **remove the promoted rows** from `design/spec-candidates.md` (consumed — prevents duplicates/ghosts). If the queue empties, leave only the header. Unadopted candidates stay untouched. (New-FR enrollment consumes nothing from the queue — queue unchanged.)

5. **Update Document Info and coverage** — re-tally the STORYBOARD Document Info (screen count, UI element count, FR coverage). Check that every live FR is mapped or classified `[No UI]` (common-rules §5 — 0 FRs missed).

6. **Verify (gate)** — **run both scripts yourself** and confirm PASS (self-reporting forbidden):
   ```bash
   bash <skill path>/scripts/verify-anchors.sh design/STORYBOARD.md design/        # body anchors grep (including promoted rows)
   bash <skill path>/scripts/verify-anchors.sh design/spec-candidates.md design/   # queue anchors too, if the queue remains
   bash <skill path>/scripts/verify-coverage.sh design/STORYBOARD.md spec/SPEC.md  # are the target FRs covered in the body?
   ```
   On FAIL, fix and re-run. **Never report completion before PASS** (deliverable guarantee — same as develojt-code-changer delegate-mode).

7. **Completion report (file relay)** — report briefly, only the result facts the delegating lead will read: promoted `UI ID ↔ FR` pairs, enrolled `FR ID ([No UI] · guess)`, whether the STORYBOARD was created or updated, remaining queue count, verification PASS. (The lead reads `design/STORYBOARD.md` directly and proceeds to the next stage — code implementation.)

## Forbidden

- **Never modify the SPEC** — the deriver's territory (R&R). The mapper only reads by grep.
- **Never touch the joblist** — the spliter's territory. The operations phase doesn't even look at it.
- **Never negotiate** — anchors and FRs are both finalized. Never spawn the 2 agents (Theorist/Practitioner).
- **Never promote candidates the delegating lead didn't specify** — adoption is the human's decision (this mode never decides).
- **Never create an anchor or a mapping in new-FR enrollment** — never disguise an element absent from the design as a mapping (a `[No UI]` classification row only — inventing an appearance baseline would make the builder follow a design that doesn't exist).
- **Never mint new anchors or switch to coordinates/volatile indexes** — reuse the queue's anchors as-is (common-rules §2).
- **Never report completion without verification PASS** — the deliverable guarantee comes first (so code never starts on an unverified STORYBOARD).
