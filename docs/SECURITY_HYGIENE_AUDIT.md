# Security Hygiene Audit

Phase 05 (Night Wave 2) — local repository review.

## Scope and result

The audit covered tracked files, ignore rules, evidence serialization, product
API error handling, legacy compatibility routes, environment projection,
exception handling, HTML/JavaScript rendering, subprocess boundaries, and
temporary artifact conventions. No QA, Oracle, or external HTTP operation was
performed.

P0 findings: none.

P1 findings: none verified in the reviewed local paths.

P2 findings addressed in this phase:

- The legacy SSE compatibility path previously streamed raw exception text.
  It now emits a fixed sanitized message.
- The legacy test loader accepted path traversal input. It now resolves and
  confines requested folders beneath its evidence base.

## Controls verified

- Tracked-file secret hygiene checks pass; local secrets, environment files,
  database profiles, archives, and runtime artifacts are ignored.
- Runtime environment/secrets wrappers use redacted representations.
- Product execution contexts, authorization, destination attestation,
  production blocking, and one-shot controls remain server-side.
- Evidence uses a fixed sanitized public projection and rejects malformed
  persisted records; raw payloads, responses, credentials, and destinations
  are not exposed by the reviewed evidence path.
- Product execution errors return sanitized classifications rather than raw
  tracebacks.
- Legacy subprocess execution remains compatibility-only and requires its
  explicit guard; no product QA path delegates browser-supplied runtime data.

## Remaining risks / follow-up

- `app.py` retains `app.run(debug=True)` for local direct invocation. This is
  acceptable for the development entrypoint but must not be used as a
  production deployment command; deployment should use the supported
  production server configuration with debug disabled.
- Legacy compatibility routes still expose historical functionality. They are
  guarded and outside the QA-first product path; deprecation/removal can be
  considered in a future compatibility cleanup.
- Oracle/QA validation and live destination behavior require separately
  authorized environments and were intentionally not tested here.

## Verification

Targeted security/legacy/evidence suite: 42 passed.

No real QA writes, Oracle queries, or external HTTP calls occurred.
