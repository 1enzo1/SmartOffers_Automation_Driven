# Run 03A Operator Runbook (QA4)

This runbook is a deterministic handoff for the single authorized
`Create Customer with Offer` execution. It does not authorize a run by itself.

## Gate sequence

1. **Static READY** — product binding, server context, single-use context,
   Standard Runner mapping, controlled bridge, adapter, destination contract,
   synthetic data, one-shot ledger, evidence capture/view, and result mapping
   all pass the static preflight. `production` must be explicitly `false` and
   attempts must remain `0/1`.
2. **Live runtime READY** — the approved QA4 runtime references and controlled
   contract are present server-side. Never print their values. A missing VPN,
   runtime, or destination attestation is a stop before send.
3. **Owner authorization READY** — the authorization names exactly QA4,
   `Create Customer with Offer`, the approved scenario/run, one attempt, zero
   retries, no fallback, and non-production scope. Do not reuse an older or
   broader authorization.
4. **Operational release READY** — provision the short-lived server-side
   release for this run. The browser receives only an opaque one-use context.
5. **Validate** — confirm readiness without mutation. Keep DB post-condition
   validation visibly separate; it is currently not configured.
6. **Reserve immediately before send** — consume the one-shot ledger only after
   every gate passes and immediately before the external request.
7. **Request sent / response received** — send exactly once through the product
   path (UI → Standard Runner → controlled bridge → adapter). Record only
   sanitized evidence.

## Stop conditions

| Condition | Required action |
| --- | --- |
| VPN/network unavailable before send | Stop as `BLOCKED_EXTERNAL`; do not consume the attempt. |
| Destination attestation mismatch | Stop as `BLOCKED`; do not send. |
| Missing, expired, or mismatched authorization/release | Stop as `BLOCKED`; do not send. |
| Attempt already consumed | Stop as `BLOCKED`; never retry. |
| Timeout or ambiguous response after send | Keep attempt consumed; classify according to transport contract; do not retry. |
| Definite 4xx/5xx or contract failure | `FAIL`; no retry. |
| Evidence persistence mismatch/failure | Treat evidence as failed/incomplete; do not resend. Preserve runtime truth separately. |
| DB post-condition unavailable | Do not convert to execution failure; report `DB_VALIDATION_STATUS=NOT_CONFIGURED`. |

## Evidence fields

Persist only the sanitized run ID, timestamp, source revision when available,
environment, product test/scenario identity, preflight result, request/response
booleans, HTTP status class, attempt transition, retry count, result, and DB
validation status. Never persist endpoints, credentials, full customer data,
offer codes, raw payloads, or raw responses.

## Completion vocabulary

- `STATIC_READY`: local contract checks pass.
- `LIVE_RUNTIME_READY`: server-side runtime is present and attested.
- `OWNER_AUTHORIZATION_READY`: exact owner authorization is active.
- `REQUEST_SENT`: the one external mutation was attempted.
- `RESPONSE_RECEIVED`: a response was received; this does not imply DB proof.
- `DB_POSTCONDITION_NOT_CONFIGURED`: execution may be reported separately from
  database verification.

If any gate is unclear, stop and request the missing authoritative input rather
than guessing or creating a second path.
