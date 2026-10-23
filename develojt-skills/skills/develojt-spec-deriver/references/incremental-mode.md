# Incremental Mode — appending an additional feature to an existing SPEC

The path for adding **one new feature (a single requirement the human has already decided)** to an already agreed-and-finalized `spec/SPEC.md`.
No full regeneration, no negotiation. The requirement is already decided, so it is not subject to Theorist/Pragmatist negotiation.
The deriver does only four things: **format tagging · security surface check · dependency assessment · insertion in the right place.**

## Entry conditions

- `spec/SPEC.md` already exists (finalized).
- The user presented the new feature as a single requirement (e.g., "add CSV to the export formats", "add an email type to the notification channels").
- The same applies when develojt-code-changer (operations change intake) delegates in (the subagent spawned by the intake lead transitions the SPEC with this procedure — operations phase, so only the SPEC is consulted, no joblist).

## Core principles

- **The existing SPEC is frozen.** Never change or delete the text, IDs, or order of existing EPs/FRs.
  (The only exception: updating the '## Summary Statistics' numbers — step 6. What's frozen is the existing EP/FR entries, not the statistics.)
- **No negotiation.** The requirement is already decided. Don't argue whether to include it or at what level.
- **Additions only.** Assign new FR/NFR IDs and insert where needed.
- **However, adding outcome rows to an existing chain is allowed** (step 5 below). That is an addition, not a modification of existing text.

## Procedure

1. **Absorb the existing SPEC** — read `spec/SPEC.md` and grasp the existing EP composition, ID scheme, behavior chains, tech stack, and `[Free]` notation conventions. The new feature must follow those conventions as-is (format consistency).

2. **Assess the owning EP** — which existing EP does the new feature belong to?
   - If it belongs to an existing EP, add the new FR there (ID = that EP's next number).
   - If it fits nowhere, create a new EP (next EP number, after the existing ones in order).

3. **Format tagging** — formalize the new requirement with the same rigor as the existing ones:
   - EARS type classification (Ubiquitous / Event-Driven / State-Driven / Unwanted / Optional — compound patterns notated as combinations like While + When)
   - ID assignment (FR-{EP}-{nnn}; failure cases -E{nn})
   - Source tag (a user-added request, so `[Requested]` or the relevant PRD reference — arbitrary tags like `[Added]` are forbidden; verify-sources rejects them)
   - Mark quantitative/enumerable spots left to AI autonomy with `[Free: reason]`
   - Follow `references/ears-guide.md`.

4. **Security surface check** — compare the new feature against the '[Required] Security requirement derivation
   checklist' table in `references/common-rules.md` (6 surfaces: authentication, authorization, PII, external input,
   files, requests to user-supplied addresses).
   For every surface it has, add that feature's own observable security behavior with the same rigor (step 3's tag
   rules) — source `[Implicit] derived from {grounding FR ID}` (the common-rules checklist's back-tracing notation); policy values without grounding get `[Free: reason]`.
   The checklist's boundary rules apply equally (global principles are never restated in the SPEC).
   If no surface applies, add nothing.
   State the additions separately in the step 8 report as **"N security derivations"** (the human filters any excess).

5. **Dependency assessment (most important)** — how does the new feature weave into existing behavior chains and features?
   - **If it must add an outcome to an existing chain**, *add* an outcome row to that chain table (never modify existing rows — only append outcome entries or add a new trigger row). e.g., if a new notification channel adds one outcome to the "order received" chain, add the outcome to that chain.
   - **If the new feature is in the same series as an existing one** (built the same way), state that fact and the sibling ID to use as the reference in the SPEC. The joblist reads this and carries it as a sibling pointer (prevents double assessment).
   - **If the new feature depends on another feature that doesn't exist yet**, state that dependency in the requirement text or the chain.

6. **Insert** — per the assessments above, write the new IDs and (if needed) chain outcomes into the SPEC at the right places. Existing entries stay invariant.
   After inserting new IDs, re-tally and update '## Summary Statistics' and the distribution by source — the sole exception to the freeze (without the update, verification in step 7 is guaranteed to FAIL).

7. **Verify** — re-run both existing verifications (section order, source tags). Must still PASS after the addition.
   ```bash
   bash .claude/skills/develojt-spec-deriver/scripts/verify-sections.sh spec/SPEC.md
   bash .claude/skills/develojt-spec-deriver/scripts/verify-sources.sh spec/SPEC.md
   ```
   (Global install: `~/.claude/skills/develojt-spec-deriver/scripts/...`)

8. **Notify the user** — briefly report the added ID list, owning EP, dependencies (which chains/series it wove into), and N security derivations (step 4 — omit if none). That is what lets the next stage (spliter incremental) continue.

## Forbidden

- Never modify or delete the text, IDs, or order of existing EPs/FRs.
- Never put the new feature up for negotiation (it is already decided).
- Never touch the joblist directly — joblist updates are the spliter's job. The deriver touches only the SPEC.
- Never leave the dependency/series assessment vague — if it's empty, the next stage can't find the sibling and the approach diverges.
