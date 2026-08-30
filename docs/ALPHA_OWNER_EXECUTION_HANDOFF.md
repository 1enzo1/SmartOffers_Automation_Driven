# Alpha Owner Execution Handoff

## Baseline and scope

- baseline: current `codex/post-alpha-ux` source (historical Alpha tag remains immutable);
- scenario: `CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4`;
- environment: QA4 only;
- attempts: one; retry: zero; fallback: false;
- evidence: sanitized only.

This handoff does not introduce a second business flow.  The authorized
environment must reuse the existing Standard Runner, real-controlled bridge,
Offers adapter, manual executor, one-shot ledger, and evidence contract.

## Existing entrypoints

| Entrypoint | Reaches | Can execute the Alpha mutation now? |
| --- | --- | --- |
| `POST /api/qa4/standard/real-controlled-run` | Standard Runner and `run_standard_qa4_real_controlled` | No. It intentionally supplies no runtime, client, policy, approval, or owner opt-in, so it stops before transport. |
| `/executar` | Legacy streaming scripts | No. It does not select the Alpha scenario or bridge. |
| `tools/qa4_*_manual_smoke.py` | Read-only Oracle/API checkpoint contracts | No. They do not run the scenario or Offers adapter. |

The Flask application remains usable locally for the available mock boundary:
`QA4 Standard mock` and the real-controlled API's sanitized `BLOCKED` result.

## Product-facing execution path

When an Owner-authorized QA4 mutation is intentionally scheduled, the product
path is already bound to `run_standard_qa4_real_controlled` through the existing
injection seam:

1. resolve the ignored local QA4 runtime in memory;
2. use the existing bounded BDA offer discovery and keep the product code only
   in memory;
3. create the existing `RealHttpClient` and the existing one-shot ledger;
4. pass the operation-scoped QA4/`CREATE_OFFERS_CUSTOMER`/synthetic-scenario
   no-auth allowlist, approval, opt-in, runtime refs and runtime secrets to the
   bridge;
5. require an explicit confirmation at the application boundary;
6. return only the bridge's sanitized `PASS`, `FAIL`, or `BLOCKED` evidence.

Do not add a POST implementation, duplicate the payload builder, create a new
executor, persist the BDA result, or widen the no-auth exception.  Production,
other operations, other environments, and other scenarios must remain denied.

## Owner execution boundary

The product-facing composition is present in the current source: the QA-first
application creates a server-side, operation-scoped context and delegates to
the existing Standard Runner and real-controlled bridge.  A live run still
requires an explicit Owner authorization and live runtime; this document does
not grant either.
## Operation-scoped authorization

The application confirmation is necessary but not sufficient. The persistent
operation-scoped authorization must be exactly
`ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN`, restricted to QA4,
`real-controlled`, `smartoffers_qa4_full_smoke`,
`CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4`, and `CREATE_OFFERS_CUSTOMER`, with one
attempt, zero retries, and no fallback. The scoped derived destination
attestation may report only `source=derived_qa4_api_url`, `environment=QA4`,
the exact operation/scenario/API identity, and allowlist match; its internally
derived URL fingerprint must match the independent approved fingerprint, while
missing or non-matching attestation denies execution without exposing either
value. This exception does not relax the legacy generic API-health
path/hash preflight, which remains fail-closed for its own checkpoint.

## Preauthorization checklist and stop conditions

Before any live action, confirm the QA4 destination attestation, current
operation/scenario allowlist, synthetic data, evidence capture, and a fresh
server-side operational release. The product validation context must be
created and consumed once; attempts remain `0/1` until immediately before a
request, then become `1/1`. Retry and fallback stay disabled and production is
always denied. Stop without sending a request if any gate, runtime, or network
condition is absent; stopping is the rollback action for this one-shot flow.

Expected sanitized outcomes are `PASS`, `FAIL`, or `BLOCKED`, with request and
response state recorded by the evidence writer. Database post-condition
validation is not configured for this product path and must not be presented as
HTTP execution proof. This handoff ends at `READY_FOR_OWNER_AUTHORIZATION`;
it does not provision a release, call Oracle, or send HTTP.
