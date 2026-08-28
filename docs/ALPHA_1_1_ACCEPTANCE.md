# Alpha 1.1 Acceptance

## Product acceptance scope

Alpha 1.1 is a local/mock-first product baseline. It does not claim a new QA4
write, Oracle query, or production capability.

### Accepted capabilities

- The default UI flow is `Open app -> QA4 -> Select test -> Validate -> Execute -> Result -> View evidence`.
- Create Customer Basic and Recharge Basic execute only local deterministic
  simulations with attempts `0/0` and no QA4 request.
- Add Offer Basic is unavailable until external contract information exists and
  does not expose a half-working Execute path.
- Controlled evidence is read-only, allowlisted, sanitized, and displayed
  separately from local mock summaries.
- Test tiers define a practical local-first execution policy.

### Truthful limitations

- Create Customer with Offer reuses the historical composite Offers operation
  and is ready for a separately authorized controlled execution. It does not
  have approved post-execution customer/line read-only validation.
- Recharge Basic has a sanitized catalog mapping but no governed real binding
  or approved read-only validation contract.
- Add Offer Basic's exact external requirements are documented in
  `ADD_OFFER_EXTERNAL_REQUIREMENTS.md`.
- The immutable Run 02 evidence is represented as `FAIL` because a response
  was not durably captured, regardless of historical runtime reporting.
- Run 03 is not ready or authorized.

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
