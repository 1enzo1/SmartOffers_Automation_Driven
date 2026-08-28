# Project State - Alpha 1.1

## Source of truth

The active product branch is `codex/post-alpha-ux`. The immutable historical
pre-Alpha baseline remains `v0.0.0-pre-alpha.1` at
`e1263595aa736de3855234b6f9a0379b944fe70e`. The formally frozen Alpha source
baseline is `v0.0.0-alpha.1` at `3df093c66ea5790f4a9d3c8b0ea279bccf0a9d86`.

This document describes source capability; it never grants operational access.
The product remains local-first and mock-first. Production and unscoped real
transport are denied by default.

## Product flow

`Open app -> QA4 -> Select test -> Validate -> Execute -> Result -> View evidence`

The primary screen is a product-facing shell over existing Flask endpoints.
Guardrails, contracts, and technical details remain sanitized and collapsed by
default. Validate prepares local prerequisites only; Execute performs only the
mode allowed by the selected catalog entry.

## Current catalog

| Test | Product status | Current permitted behavior | Real readiness |
|---|---|---|---|
| Create Customer with Offer | REAL EXECUTION CONTRACT READY | Existing local mock plus the recovered `CREATE_OFFERS_CUSTOMER` controlled execution contract | Separate post-execution customer/line DB validation is not available. The composite Offers operation requires authorization and must not be called a pure customer creation. |
| Recharge Basic | LOCAL READY | Existing deterministic recharge template through the fake adapter and local plan verification | The sanitized catalog is explicitly blocked for real use. A governed operation/scenario binding and approved read-only result validation are missing. |
| Add Offer Basic | UNAVAILABLE | Safely blocked before discovery, planning, or transport | The exact authoritative requirements are in `ADD_OFFER_EXTERNAL_REQUIREMENTS.md`. |

Synthetic values stay in process memory. Local mock runs have a non-persisted
summary, not an evidence artifact.

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

The current inventory is 43 Python test files. The documented TIER_0 command
is the default local product check.

## Run 03 status

`READY_FOR_RUN_03_EXECUTION_PREAUTH=true` for the recovered composite
`CREATE_OFFERS_CUSTOMER` contract, subject to a new explicit Owner
authorization and all existing runtime gates. `READY_FOR_RUN_03_WITH_DB_VALIDATION=false`:
there is no approved customer/line read-only lookup. See
`CREATE_CUSTOMER_EXTERNAL_REQUIREMENTS.md`.
