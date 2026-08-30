# Product API error-state matrix

This local matrix records the intentionally sanitized behavior of the
product-facing routes. It is a contract for UI mapping, not an authorization
for external execution.

| Surface | Condition | HTTP | Result / reason | External action |
| --- | --- | ---: | --- | --- |
| Catalog | valid request | 200 | curated tests | none |
| Validate | unknown test | 404 | `BLOCKED` / `TEST_NOT_FOUND` | none |
| Validate | unavailable or invalid contract | 200 | `BLOCKED` with safe reason | none |
| Execute | missing/malformed JSON or missing intent | 200 | `BLOCKED` / intent required | none |
| Execute | unknown fields or browser runtime/auth data | 200 | `BLOCKED` / input not allowed | none |
| Execute | missing, expired, used, or wrong context | 200 | `BLOCKED` / context reason | none |
| Execute | unavailable or diagnostic-only test | 200 | `BLOCKED` / capability reason | none |
| Execute | local delegate exception | 500 | `BLOCKED` / `LOCAL_EXECUTION_ERROR` | none unless a separately authorized controlled request had already begun |
| Evidence | unknown run, wrong run, invalid JSON, partial record | 404 | `BLOCKED` / `EVIDENCE_NOT_FOUND` | none |
| Evidence list / History | valid or empty store | 200 | sanitized recognized records only | none |

Persisted evidence is read through a fixed run-ID enum and explicit public
allowlist. Malformed typed fields are rejected before projection; historical
Run02 inconsistencies remain immutable and normalize to `FAIL` when response or
one-shot confirmation is absent. `PASS` is never synthesized from incomplete
or contradictory evidence.
