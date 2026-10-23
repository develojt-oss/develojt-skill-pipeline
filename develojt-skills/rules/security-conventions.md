# Universal Secure Coding Principles (Security Conventions)

This file defines universal secure-coding principles independent of language and framework.
Where `code-conventions.md` in the same folder governs "is the code being written good code",
this file governs "is the code being written safe code".

Individual attack techniques number in the tens of thousands, but the vulnerability classes
at their root converge to a few dozen. This file is not an attack list — it defines
**writing principles that block vulnerability classes at the source**, with
OWASP Top 10 · OWASP API Security Top 10 · CWE Top 25 as its backbone.

> **Precedence**: when a security principle in this file conflicts with any other rule
> (code-conventions, `{language}.md`), **the security principle wins**. Security is a floor —
> no other rule may relax it.
>
> **Scope of application**: if the project lacks a given surface, skip that section.
> (e.g., §2 XSS does not apply to a CLI tool with no web UI. However, §5 Secrets and
> §10 Error Handling always apply regardless of surface.)

---

## 0. Security Mindset

- **Secure by Default**: allowlists are the baseline; denylists are auxiliary. Access is denied by default and only what is needed is explicitly allowed. A denylist always ends up missing entries.
- **Assume every external input is hostile**: user input, HTTP headers/cookies/URLs, file contents, external API responses, and values read from the DB (they can be tainted through another path) — all of it. "Values our frontend sends" are external input too — attackers do not go through your frontend.
- **Never trust the client**: client-side validation is for UX. Security decisions (validation, authorization, calculations) must be repeated on the server. Hidden fields, disabled attributes, and front-end routing guards are not security measures.
- **Defense in Depth**: never rely on a single layer. Use parameter binding even when input validation exists; narrow DB account privileges even when authorization checks exist.
- **Never hand-roll security logic**: use vetted standard libraries for encryption, hashing, session management, and token issuance. Self-implemented security logic is an unvetted single line of defense.

---

## 1. Input Validation and Injection Prevention

> §2 "Boundary validation and external dependencies" of `code-conventions.md` defines *where* to validate (at the boundary).
> This section defines the security requirements of that validation.

- **Structural separation is the principle**: never mix data into code/queries/commands as strings. Escaping (character substitution) is auxiliary; APIs that structurally separate data from commands are the principle.

| Surface | Forbidden | Principle |
|------|------|------|
| SQL | Assembling queries via string concatenation/formatting | Parameter binding (prepared statements) or an ORM |
| OS commands | Assembling commands as shell strings, shell=true | Argument-array execution. Prefer libraries over command execution altogether |
| Paths | Joining user input directly into paths | Fix a base directory, canonicalize, and reject anything outside it (§9) |
| NoSQL / LDAP / templates | Inserting input directly into queries/expressions | Use each technology's parameterization API; never evaluate user input as code in templates |
| XML | Parsers with external entities enabled by default | Prevent XXE — explicitly disable external entities and DTD processing |

- **Validate against allowlists**: define type, length, range, and format (regex) as "only these values are allowed". "Reject these values" gets bypassed.
- **No `eval`-style facilities**: never execute strings as code (`eval`, `exec`, the `Function` constructor, dynamic imports fed user input). Language specifics follow `{language}.md`.
- **Size limits**: cap request bodies, uploads, array lengths, and page sizes. Unbounded input is a resource-exhaustion (DoS) surface.

---

## 2. Output Handling and XSS Prevention

- **Output encoding is the default**: when placing dynamic data into HTML, use only the framework's auto-escaping path. React's JSX, Vue's `{{ }}`, etc. are safe by default — the features that bypass that default are the danger points.
- **No raw HTML insertion**: never use APIs that bypass escaping — `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, and the like. Only when a requirement demands rendering user-authored rich text, pass it through a vetted sanitizer library first.
- **Context-appropriate encoding**: HTML body, attributes, URLs, and JavaScript strings each have different encoding rules. In particular, when user input goes into `href`/`src`, block dangerous schemes like `javascript:` with an allowlist (http/https).
- **Exact Content-Type on API responses**: declare JSON responses as `application/json`. Leave the browser no room to interpret the response as HTML.

---

## 3. Authentication

- **Store passwords only with dedicated hashes**: use only deliberately slow, purpose-built algorithms — bcrypt / argon2 / scrypt. General-purpose hashes (MD5, SHA-256 — even salted), reversible encryption, and plaintext storage are forbidden.
- **Compare in constant time**: compare password hashes, tokens, and signatures with the library-provided constant-time comparison. Plain string comparison is a timing-attack surface.
- **Brute-force defense**: put attempt limits (rate limit / lockout / delay) on every authentication attempt point — login, verification-code checks, etc.
- **Uniform authentication failure responses**: never distinguish "no such account" from "wrong password". It leaks account existence (the same applies to sign-up and password-reset responses).
- **Session and token handling**:
  - Generate session IDs and tokens with cryptographic randomness (§7). Predictable values (sequence numbers, timestamps) are forbidden.
  - Reissue the session ID on successful login (prevents session fixation). Invalidate server-side on logout and password change.
  - Every token must expire. For JWT, the server pins the signature algorithm (reject `none` and client-specified algorithms) and never trusts the payload without signature verification.
  - Browser session cookies get `HttpOnly` + `Secure` + `SameSite`. Prefer HttpOnly cookies over storing tokens in localStorage.

---

## 4. Authorization

Authentication (who are you) and authorization (what may you do) are separate. Endpoints that check only authentication are the root of authorization vulnerabilities.

- **Check authorization on the server for every request**: hiding items from a list is not authorization. The same check must trigger for requests that arrive with a directly specified URL/ID.
- **Object ownership checks (IDOR prevention)**: at every point that accesses a resource by ID, like `/orders/123`, check "does this user have rights to this resource". "Is logged in" alone cannot stop an attacker swapping in someone else's resource ID.
- **Enforce authorization in a shared layer**: apply it by default at a common point — middleware, decorators, guards — rather than writing it per handler. Per-handler checks always end up missing an endpoint. Structure public endpoints as explicitly declared exceptions (default deny).
- **Least privilege**: grant user roles, API keys, service accounts, and DB accounts only the minimum they need. Never give the application's DB account DDL or administrative privileges.
- **CSRF defense on state changes**: web requests that change state (POST/PUT/DELETE) under cookie-based authentication need a CSRF token or a `SameSite` cookie strategy. Never change state on GET requests.

---

## 5. Secrets Management

> Makes concrete the "Never put sensitive information in code" clause of §3 "Configuration management" in `code-conventions.md`.

- **Hardcoding is absolutely forbidden**: never write API keys, passwords, tokens, private keys, or DB connection strings into source code, committed config files, comments, test code, or logs. No examples, no defaults, no "temporary" — temporary lasts forever.
- **Injection path is environment variables or a secrets manager**: only "reading code" exists in the codebase. If you use a `.env` file, it must be in `.gitignore`, and only an empty-valued `.env.example` is committed.
- **A secret committed even once is leaked**: deleting it later still leaves it in git history. If committed by mistake, the response is not deletion but **immediate revocation and reissue**.
- **Never send secrets outward**: ensure API responses, frontend bundles, and error messages contain no secrets. Anything that went into a frontend build is public.

---

## 6. Sensitive Data & PII

- **Collect minimally**: collect and store only what the requirements need. Data you never stored can never leak — the surest defense.
- **Protect at rest**: encrypt personally identifiable information protected by law (national IDs, card numbers, contact details, …) when storing (§7). Values that never need to be read back (passwords) are hashed, not encrypted (§3).
- **Cut off exposure points**: never put sensitive data in logs, error messages, or URL query strings. URLs spread via browser history, server logs, and Referer headers. If an identifier is needed, use an internal ID.
- **Masking is the display default**: when showing sensitive data on screens or in responses, partial-exposure masking (e.g., `****-1234`) is the default; showing the full value happens only when explicitly required.
- **API responses use field allowlists**: never serialize and return DB entities as-is. Declare exactly the fields to expose in a response-only DTO. Returning entities directly becomes an automatic leak point the moment a new column is added (including the reverse of Mass Assignment — inputs also declare their allowed binding fields).

---

## 7. Cryptography

- **Standard libraries only — never self-implement**: use the language/platform's vetted cryptography library. Never implement or modify algorithms yourself.
- **Strong algorithms only**: symmetric encryption uses AES-256 (authenticated modes like GCM), hashing uses SHA-256 or stronger, passwords use §3's dedicated hashes. **Broken algorithms (MD5, SHA-1, DES, RC4) and ECB mode are forbidden in new code.**
- **Randomness from a CSPRNG**: security-purpose randomness — tokens, session IDs, verification codes, salts, IVs — comes from a cryptographic RNG (`crypto`-class APIs). General-purpose `random` is predictable.
- **Key management**: encryption keys are secrets — apply §5 as-is. Never keep keys and ciphertext in the same store.

---

## 8. Network & Transport Security

- **All traffic over TLS (HTTPS)**: not just external traffic — service-to-service traffic defaults to HTTPS too. Options that disable certificate verification (verify=false and friends) are never committed, even for dev convenience.
- **CORS by allowlist**: `Access-Control-Allow-Origin: *` and reflecting the request Origin verbatim are forbidden. Enumerate allowed origins explicitly. Wildcards are especially forbidden on APIs carrying credentials.
- **Security headers by default**: web responses set `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, and `X-Frame-Options` (or CSP frame-ancestors). If the framework/middleware has a security-header preset (helmet and friends), use it.
- **Rate limiting**: put call-frequency limits on public endpoints — especially authentication (§3), sending (mail/SMS), and expensive operations like search.

---

## 9. Files & External Resources

- **File uploads get 4-fold validation**: ① extension and MIME type by allowlist, ② size cap, ③ the stored filename is server-generated (never use the user's filename in a path), ④ storage lives outside the web root or in a non-executable store. An uploaded file placed where the server executes or interprets it leads straight to remote code execution.
- **Path traversal prevention**: whenever user input touches a file path, fix a base directory, canonicalize the final path, then check it is inside the base. Stripping `../` substrings gets bypassed.
- **Deserialization caution**: never deserialize untrusted data with language-native serialization (pickle, Java serialization, …) — it is a code-execution surface. Exchange external data in data-only formats like JSON, and validate the schema (§1).
- **SSRF prevention**: features where the server fetches a user-supplied URL (webhooks, URL previews, image fetching) are restricted to an allowlist of domains, and requests to internal addresses (localhost, private IPs, metadata IPs) are blocked. Redirect-following must pass the same checks.
- **Open-redirect prevention**: when user input determines a redirect target (post-login navigation, etc.), allow only paths within your own domain.

---

## 10. Error Handling & Logging Security

> Makes concrete the security side of §2 Error handling and §3 Logging in `code-conventions.md`.

- **Separate external responses from internal logs**: stack traces, SQL statements, internal paths, and framework versions are a map for attackers. Record details in server logs; return outward only a generalized message plus an error ID for tracing.
- **Debug mode never ships**: keep framework debug/dev modes (verbose error pages, auto-reload, debug endpoints) out of production via per-environment configuration (§ code-conventions, Configuration management).
- **What never goes into logs**: passwords, tokens, session IDs, API keys (§5), and raw PII (§6). Code that logs entire requests wholesale violates this automatically.
- **Do log security events**: record security events traceably — login success/failure, authorization denials, validation failures (who, when, what) — excluding the forbidden items above.

---

## 11. Dependencies & Supply Chain

> Builds on §4 Package manager of `code-conventions.md` (minimal dependencies, lock files, pinned versions), adding the security requirements.

- **Run a vulnerability audit at install/add time**: run the ecosystem's audit tool (`npm audit`, `pip-audit`, `dotnet list package --vulnerable`, …) when adding dependencies, and never adopt a version with known high-severity vulnerabilities.
- **Verify names exactly**: typosquatting (malicious packages under similar names) is a real attack. Check spelling, publisher, and download counts, and for packages whose existence is uncertain (possible hallucination), confirm they exist in the official registry before adding.
- **Version pinning follows code-conventions §4**: committed lock files + exact version pinning are the first defense against supply-chain tampering.

---

## 12. Database Security

- **Access via parameter binding** (§1) — restated because it is DB security's first principle.
- **Application accounts get least privilege**: grant the runtime account only the DML it needs. Separate DDL, account management, and file-access privileges into a migration-only account. Never connect the application as root/admin.
- **Connection info is a secret**: apply §5 as-is. The DB is never exposed directly to external networks by default.
- **Data-at-rest protection follows §6 and §7**: what to encrypt/hash is §6; how is §7.
