# Alpha 1.1 Acceptance

## Product acceptance scope

Alpha 1.1 is a QA-first product baseline. It does not claim a new QA4 write,
Oracle query, or production capability. Local mocks are Diagnostics only.

### Accepted capabilities

- The default UI flow is `Open app -> QA4 -> Select test -> Validate QA readiness -> Execute in QA -> Result -> View evidence`.
- The primary workspace exposes no mock execution controls; Diagnostics is
  collapsed by default.
- Create Customer with Offer is the QA-oriented product path with a recovered
  governed contract and requires a separately authorized controlled run;
  Recharge Basic remains a local diagnostic with no governed real contract.
- Add Offer Basic is unavailable until external contract information exists and
  does not expose a half-working Execute path.
- Controlled evidence is read-only, allowlisted, sanitized, and displayed
  separately from local mock summaries.
- Create Customer with Offer has a product-facing delegation to the existing
  governed controlled stack. It remains blocked until a current authorization
  and all existing runtime gates are present.
- Test tiers define a practical local-first execution policy.

### Truthful limitations

- Create Customer with Offer reuses the historical composite Offers operation
  and is ready for a separately authorized controlled execution. It does not
  have approved post-execution customer/line read-only validation.
- HTTP execution verification and database post-condition verification are
  distinct product outcomes; the latter remains not configured.
- DB post-condition validation remains a separate capability and is not
  configured for the current product flow.
- Recharge Basic has a sanitized catalog mapping but no governed real binding
  or approved read-only validation contract.
- Add Offer Basic's exact external requirements are documented in
  `ADD_OFFER_EXTERNAL_REQUIREMENTS.md`.
- The immutable Run 02 evidence is represented as `FAIL` because a response
  was not durably captured, regardless of historical runtime reporting.
- Run 03A is source-ready for a separately authorized controlled execution, but
  it is not authorized, released, or executed in this baseline.

## Acceptance gates

| Gate | State |
|---|---|
| Front product flow | READY |
| Local catalog | READY |
| Sanitized evidence reader | READY |
| Future evidence capture regression coverage | READY |
| Tiered local testing | READY |
| New real QA4 write | NOT AUTHORIZED |
| Recovered composite execution contract | READY FOR SEPARATE AUTHORIZATION |
| Post-execution customer/line DB validation | NOT READY |

The `v0.0.0-alpha.1` tag remains the historical Alpha baseline. A later tag
may be created only after independent Tester and Critic acceptance of the
current source baseline.
