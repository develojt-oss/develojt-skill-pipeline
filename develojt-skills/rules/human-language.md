# Human-Facing Sentence Protocol (Human-Facing Language)

This file sets how a session writes **every sentence it shows a human** (progress and completion reports, explanations, questions, approval requests, escalations, screen-comparison requests,
the relaying of questions written in ledgers and handover notes). The contract vocabulary and format of deliverable files (SPEC, joblist, findings, STORYBOARD, handoff, etc.)
are not its target — they are invariant (the verification scripts read those very characters). The language choice (English) follows each skill's language clause as-is.

**In one sentence: the reader knows neither the ledgers nor the skills — write so that, reading only this sentence, that person knows "what happened and how, and what
I need to do".**

## 1. The standard for sentences (every output shown to a human)

- **Pick subjects and objects from the human's world** — the product's things (screens, features, behaviors, files) and the human's actions. Ledger and procedure vocabulary (status names, step names,
  cycles, row numbers, IDs) is not the subject of the sentence but a tag attached afterward in parentheses.
- **Point at a target by its content** — never by a row number, ID, or file location alone. Not `row N` but `{what that row is} (row N)`.
- **Write so it can be answered with the material shown now** — never presuppose the human's memory or what was said in a past session. For a human act not in the records,
  do not ask "did you do it back then"; take that decision again now (`judgment-conduct.md` §6).
- **Spell out, on first appearance, words used only inside the documents** — keep pipeline notations and technical terms as-is, but gloss them briefly in parentheses.

## 2. Sentences that ask for a decision (the human-decision sentence rule)

- ① State what must be decided first, in one sentence ② for each option, one line on "what changes if you pick this" ③ one decision
  per sentence (§1 applies as-is).
- The same goes when relaying a one-line question written in a ledger (a `Needs review` row, a handover note) to a human — a skill's "carry verbatim / re-post" means preserving the content,
  not copying the sentence: the content stays as-is, and the sentence is rewritten by this protocol.

## 3. The pre-send check and the failure direction

- **Ask once right before output**: "Would a person who knows none of this project's documents, reading only this sentence, know what happened and how, and what they need
  to do?" If not, do not send it — rewrite it.
- **Failure direction**: when ambiguous, spell it out. Where removing the ledger vocabulary would lose the meaning, do not remove it — add it in parentheses; words the human must type back
  verbatim (notations to be typed as a response) are never changed.
