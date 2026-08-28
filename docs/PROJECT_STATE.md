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
| Create Customer Basic | LOCAL ONLY | Deterministic synthetic customer/line simulation and local verification | Governed create binding and approved read-only lookup are missing; any real run needs separate Owner authorization. |
| Recharge Basic | LOCAL ONLY | Existing deterministic recharge template through the fake adapter and local plan verification | Governed real binding and approved read-only result validation are missing. |
| Add Offer Basic | UNAVAILABLE | Safely blocked before discovery, planning, or transport | Operation-scoped contract, governed offer input/discovery, and approved read-only validation are missing. |

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

`READY_FOR_RUN_03=false`. No Run 03 scenario, authorization, or source
contract exists yet. A future Create Customer Basic run requires a scoped
real-controlled scenario binding, synthetic-data contract, approved read-only
customer/line validation lookup, evidence capture, one-shot ledger mapping,
and a separate explicit Owner authorization.
