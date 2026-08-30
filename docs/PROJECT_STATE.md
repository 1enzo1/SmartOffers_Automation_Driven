# Project State - Alpha 1.1

## Source of truth

The active product branch is `codex/post-alpha-ux`. The immutable historical
pre-Alpha baseline remains `v0.0.0-pre-alpha.1` at
`e1263595aa736de3855234b6f9a0379b944fe70e`. The formally frozen Alpha source
baseline is `v0.0.0-alpha.1` at `3df093c66ea5790f4a9d3c8b0ea279bccf0a9d86`.

This document describes source capability; it never grants operational access.
QA is the product purpose. Local diagnostics support development and diagnosis,
but are not the default product mode. Production and unscoped real transport
are denied by default.

## Product flow

`Open app -> QA4 -> Select test -> Validate QA readiness -> Execute in QA -> Result -> View evidence`

The primary screen is a QA-first shell over existing Flask endpoints. Mock,
generator, and legacy runner tooling lives under collapsed Diagnostics.
Guardrails, contracts, and technical details remain sanitized and collapsed by
default. Validate is non-mutating and reports QA execution readiness separately
from database post-condition validation.

For a governed product execution, the runtime owner must provision an exact,
short-lived operational release inside the application process before Validate.
There is no HTTP/browser route for provisioning and no default release. The
browser can receive only a one-use opaque validation reference; authorization,
runtime plan, destination and window data never return to the browser.

## Current catalog

| Test | Product status | Current permitted behavior | Real readiness |
|---|---|---|---|
| Create Customer with Offer | QA READY / REQUIRES AUTHORIZATION | Product delegation to the recovered `CREATE_OFFERS_CUSTOMER` controlled execution contract | Execution verification is available under a separate current authorization. Separate post-execution customer/line DB validation is not configured. |
| Recharge Basic | LOCAL DIAGNOSTIC | Existing deterministic recharge template through the fake adapter and local plan verification | The sanitized catalog is explicitly blocked for real use. A governed operation/scenario binding and approved read-only result validation are missing. |
| Add Offer Basic | UNAVAILABLE | Safely blocked before discovery, planning, or transport | The exact authoritative requirements are in `ADD_OFFER_EXTERNAL_REQUIREMENTS.md`. |

Synthetic values stay in process memory. Local mock runs have a non-persisted
summary, not an evidence artifact.

Execution verification is not database post-condition verification. A successful
controlled HTTP execution must never be presented as customer/line database
validation while the approved read-only lookup is unavailable.

## Evidence truth

The Run 01 technical success was reported but lacks formally recoverable
evidence. The immutable Run 02 source artifact remains unchanged. Its runtime
path showed a sent request, but the old durable capture missed response and
post-ledger fields. The sanitizer intentionally presents that artifact as
`FAIL` with `RESPONSE_NOT_CONFIRMED`; it must not be promoted to a passing
repeatability result.

Future controlled runs use the repaired automatic sanitized capture path. That
repair is tested locally; it does not authorize a new QA4 operation.

## Test workflow

Use `docs/TEST_SUITE_RATIONALIZATION_BACKLOG.md`:

- TIER_0_FAST for import/config/safety smoke and small changes;
- TIER_1_FEATURE for the touched product surface;
- TIER_2_INTEGRATION_OFFLINE for feature milestones;
- TIER_3_FULL only for release milestones after manual/external-path safety is confirmed.

The current inventory is 48 Python test files (851 collected tests). Executable
markers in `tests/conftest.py` route 419 tests to TIER_0, 254 to TIER_1, 53 to
TIER_2, and 125 to the release/manual TIER_3 set. Routine selectors exclude
manual/external-risk modules.

## Run 03 status

`READY_FOR_RUN_03_EXECUTION_PREAUTH=true` for the recovered composite
`CREATE_OFFERS_CUSTOMER` contract, subject to a new explicit Owner
authorization and all existing runtime gates. `READY_FOR_RUN_03_WITH_DB_VALIDATION=false`:
there is no approved customer/line read-only lookup. See
`CREATE_CUSTOMER_EXTERNAL_REQUIREMENTS.md`.

Alpha 1.2 contract recovery confirms that Recharge remains a local diagnostic
because no authoritative governed mutation, response, or validation contract
was recoverable. Standalone Add Offer remains unavailable; its exact external
requirements are recorded separately. These states are distinct from the
proven composite Create Customer with Offer execution path.
