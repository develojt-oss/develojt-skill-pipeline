# EARS Grammar Guide (Easy Approach to Requirements Syntax)

EARS is a grammar that formalizes natural-language requirements into structured sentences.
Its purpose is to remove ambiguity and produce testable/verifiable requirements.

---

## The 5 types

### 1. Ubiquitous — always-true requirements

Requirements the system must satisfy at all times, unconditionally.

```
Pattern: The system shall [requirement]

Examples:
  The system shall store user passwords encrypted
  The system shall support Korean and English
  The system shall include an HTTP status code in every API response
```

---

### 2. Event-Driven — when a specific event occurs

Requirements where the system must react when a specific trigger (event) occurs.

```
Pattern: When [trigger], the system shall [response]

Examples:
  When the user presses the login button, the system shall validate the credentials
  When an order is received, the system shall decrement the stock quantity
  When a payment completes, the system shall send a confirmation email
  When a file upload completes, the system shall run a virus scan
```

---

### 3. Unwanted — when an undesirable situation occurs

Handling for errors, exceptions, boundary conditions, and other undesirable situations.

```
Pattern: If [abnormal situation], the system shall [response]

Examples:
  If login fails 5 times in a row, the system shall lock the account for 30 minutes
  If the network connection drops, the system shall switch to offline mode
  If an uploaded file exceeds 10MB, the system shall reject the upload and display a notice
  If an already-processed request is submitted again, the system shall ignore that request
```

---

### 4. State-Driven — while a specific state holds

Requirements the system must satisfy continuously while it is in a specific state.

```
Pattern: While [state], the system shall [behavior]

Examples:
  While a batch job is running, the system shall refresh and display the processed count every second
  While the user is logged in, the system shall track the session timeout
  While data synchronization is in progress, the system shall display the progress rate
  While the battery is at 20% or below, the system shall stay in power-saving mode
```

---

### 5. Optional Feature — when a specific feature is included

Requirements that apply only when the system includes a specific feature.

```
Pattern: Where [feature/condition], the system shall [requirement]

Examples:
  Where multilingual support is included, the system shall support RTL language layouts
  Where offline mode is supported, the system shall manage a local cache
  Where administrator privileges are granted, the system shall display the user management menu
```

---

## Compound patterns (combinations)

Types can be combined.

```
While + When:
  While a job is in the running state, When the user presses pause,
  the system shall transition to the waiting state

Where + If:
  Where a payment feature is included, If a payment fails,
  the system shall roll back the transaction and notify the user
```

---

## Good requirements vs bad requirements

```
❌ Bad requirements (vague, unmeasurable, or dictating the implementation)
  "The system shall be fast"
  "The system shall authenticate with JWT"
  "The system shall be easy to use"
  "The system shall cache with Redis"

✅ Good requirements (clear, measurable, What only)
  "The system shall keep API response time within 200ms"
  "The system shall provide user authentication and session management"
  "The system shall make core features reachable within 3 taps"
  "The system shall cache repeatedly-read data to reduce DB load"
```

**Core principles:**
- State only the **What** — the **How** belongs to the design/implementation stage
- Must be measurable or verifiable
- One requirement per sentence

---

## ID scheme

```
FR-epic#-seq   : Functional Requirement
NFR-epic#-seq  : Non-Functional Requirement
FR-epic#-Eseq  : Edge Case

Examples:
  FR-01-001   EP-01's first functional requirement
  NFR-00-001  a cross-cutting non-functional requirement
  FR-03-E01   EP-03's first edge case
```

---

## `[Implicit]` tag usage criteria

Requirements derived without being stated in the PRD are marked `[Implicit]`.

```
Derivation grounds:
  - Judged essential through scenario tracing
  - Essential for the feature's completeness
  - Implicit behavior the user naturally expects
  - Essential handling for system safety/security

Example:
  | FR-02-010 | [Implicit] | Event-Driven | When the browser tab is deactivated,
  |           |            |              | the system shall automatically save the input being written as a temporary draft |
```

---

## `[Needs review]` tag usage criteria

Marked on items the two agents could not agree on or lack confidence in.

```
Pattern: [Needs review: reason]

Example:
  | FR-03-006 | PRD EP-03 | Event-Driven |
  | When accessed from mobile, the system shall support touch input
  | [Needs review: mobile support scope unclear in the PRD] |
```

---

## `[Requested]` tag usage criteria

Marked on requirements added/changed by user request after the PRD was first written.
It differs from [Implicit] because the user explicitly added it through conversation, even though it wasn't in the PRD.

```
Usage conditions:
  - A feature the user personally requested after the PRD
  - A requirement changed/extended to reflect implementation feedback
  - An item absent from the PRD but included after user confirmation

Example:
  | FR-09-001 | [Requested] | Ubiquitous | The system shall provide 5 report formats |
```

---

## `[Removed]` tag usage criteria

Marked on requirements removed during negotiation or implementation.
For history tracing, they are never fully deleted from the document — they remain with strikethrough (~~).

```
Usage conditions:
  - Items agreed unnecessary as a negotiation outcome
  - Items removed after being replaced by another requirement
  - Items removed during implementation after user confirmation

Example:
  | FR-06-005 | [Removed] | — | ~~In-house notification sending removed. External notification service integration only~~ |
```

---

## The complete source tag scheme (summary)

Only the 6 tags below are used in a requirement's source column.
Never invent tags outside this list.
Consistent tags are what make cross-document tracing and search possible.

| Tag | Meaning | Example |
|---|---|---|
| `PRD EP-XX` | Requirement directly derived from a PRD epic | `PRD EP-01` |
| `PRD Considerations` | Directly derived from the PRD "Additional Considerations" section | Cross-cutting concerns: performance, security, schedule, constraints, etc. |
| `[Implicit]` | Not in the PRD but required for scenario/completeness | Error handling, boundary conditions |
| `[Requested]` | Added/changed by user request after the PRD | Reflecting user feedback |
| `[Removed]` | Removed after agreement (history preserved, strikethrough) | Judged replaced/unnecessary |
| `[Needs review: reason]` | Agreement not reached or confidence insufficient | Needs the user's judgment |
