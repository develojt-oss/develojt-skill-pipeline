# Screen-comparison session — ledger walk-through procedure (loaded only on session entry)

> Read this file only when entering the screen-comparison session — never load it during the development phase (bundle implementation and registration): context frugality.
> The session's judge is the human eye (essential 5). This procedure only presents items, records status, and connects repairs — it never judges by itself.
> The sole exception is the 'browser delegation mode' below (conditional on the human's explicit delegation).

## Entry (two paths — same condition: `spec/screen-review.md` has `Unchecked`/`Reinforcing` rows)

1. **Continuous run**: the last bundle reaches pdca quiescence (= no bundle left unchecked) → workflow 7 requests the session start right there.
2. **Resumption**: on builder re-invocation, when the state assessment reads "no unchecked bundles + ledger backlog N" → print the scope report as
   "screen-comparison session (N remaining)" and start after approval. It continues from where it stopped — progress lives only in the ledger's
   Status cells, not in session memory (a state-based rule — the same idea as the findings archive).

If the human instructs "start the screen comparison" (or similar) after any bundle, run the same procedure early with the backlog at that point
(an early session — for projects that boot early; the remaining bundle implementation continues after the session).

## Progress (one item at a time — one screen per turn)

From the first `Unchecked` row (including `Reinforcing` rows awaiting re-comparison) — locate rows by grep, and read only the row being presented (no full reads):

1. **Present one row** (Human-decision sentence rule applies — the one decision is "does this screen match the design baseline?"):
   "Screen to check: {screen}. How to reach the running screen: {how to reach it}. Design baseline to compare against: {design baseline}
   ({reproduced anchors}). {If Notes carry markers — [Dynamic]: this screen has a motion element; it cannot be judged by still comparison —
   please check the motion itself. / Data source: this element is design seed (or real data — grounding FR).} Please compare the running screen
   against the design baseline by eye — answer 'confirmed' if they match, or point out what differs."
2. **Handle the answer — update the ledger before presenting the next row** (wherever the session breaks, the ledger is the truth):
   - "Confirmed" → set that row's Status to `Confirmed` → present the next row.
   - A mismatch or functional defect is flagged (including anything found while reviewing, verifying, or debugging during comparison) → set that
     row's Status to `Reinforcing` and **hand the fix to develojt-code-changer** — after full implementation completion, every fix goes through the
     operations path (not builder's reinforcement mode — that covers only early comparisons during bundle progress). The human invoking changer
     directly amounts to the same. When changer's repair and its checks finish, re-present that row (re-comparison), and on confirmation set it to `Confirmed`.
3. **Interruption** (the human stops, or the session breaks): announce "Screen comparisons remaining: N — re-invoke /develojt-code-builder to
   continue." (the ledger holds the progress; nothing else is needed).

## Browser delegation mode (optional — only with explicit delegation + browser tools connected)

Enter this mode only when the human explicitly delegates it ("check them yourself", or similar) — never switch to it on your own (the default judge is the human eye):

- Per row: navigate the browser per the how-to-reach → capture a screenshot → compare against the design baseline (design/screenshots/{file} ·
  screen-source element · README section) → place the judgment evidence (the gist of the running-screenshot-vs-baseline comparison) side by side in the
  report → on a match, set Status to `Confirmed (auto)`.
- On a mismatch verdict, same as the human-eye path: `Reinforcing` + hand to develojt-code-changer.
- `[Dynamic]` rows must not be judged `Confirmed (auto)` from still screenshots alone — if motion cannot be observed, leave just that row for human confirmation.
- At the session's end, give a summary report covering all `Confirmed (auto)` rows — this mode carries the tension of an agent grading its own implementation
  (essential 5); anchoring the judgment to originals (screenshots, sources) and preserving evidence so the human can recheck at any time is the
  condition of its validity.

## Termination — declaring development-draft completion

When the ledger's `Unchecked` and `Reinforcing` counts reach 0 (verify by count grep):
"Screen comparison complete (all rows confirmed) — the **development draft is complete**. From here, requirement/code changes are taken in by develojt-code-changer."
While a backlog remains, never make this declaration — not even under an "all" / "through EP-NN" instruction.
