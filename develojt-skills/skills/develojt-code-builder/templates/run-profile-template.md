# Run Profile (Run Profile) — {project name}

> **The machine input of the releasable invariant (the boot gate `verify_boot.py`).** develojt-code-builder puts a draft into the scaffolding-completion
> report and it is **finalized by human approval** (before finalization this file does not exist, so the gate is a 'not applicable' PASS — legacy
> projects behave unchanged); afterwards, every scope's (bundle/EP) self-check confirms "it builds and it boots" with this file.
> Changing a command or value goes only through re-finalization (human approval) — arbitrary edits to make the gate pass are forbidden (verification is a mirror).
>
> **Machine-readable grammar**: the 6 item names in the table below are fixed (no additions or renames — a profile that cannot be read is reported by the gate
> with exit 2). One value per value cell — write commands as **one-line shell commands** run as-is from the project root, and
> if something does not apply, write `None` (never leave it blank).

| Item | Value |
|---|---|
| Type | {resident or one-shot or library} |
| Build command | {one-line command or None} |
| Boot command | {one-line command — None allowed only for the library type} |
| Observation check | {resident: an http(s) URL — otherwise None} |
| Time limit (s) | {integer — the maximum wait for each step} |
| Stop command | {resident: a cleanup command after confirmation, or None (the gate cleans up by terminating the process)} |

**Success criteria per type (fixed — deterministic):**

- **resident** (systems that stay up, like servers and apps): the build command succeeds → after starting it with the boot command, **the observation-check URL responds with HTTP 2xx** within the time limit. After confirming, the gate cleans up with the stop command (if none, by terminating the process).
- **one-shot** (systems that end after running, like CLIs): the build command succeeds → **the boot command exits with code 0 within the time limit**.
- **library** (artifacts with no standalone boot): **the build command exits with code 0 within the time limit** (boot command and observation check are `None`).

> Match the observation check to the observation result set by the SPEC's runtime-base NFRs (what responds at startup).
> This gate confirms only up to "it comes up" (releasable) — it is not a judgment of whether features run as required (E2E, demos).
