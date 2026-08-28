# Changelog

## v0.0.0-alpha.2 - Alpha 1.1 source baseline

- Finalized the catalog-driven testing-product flow for QA4 local/mock work.
- Added Create Customer Basic and Recharge Basic local-only product entries;
  Add Offer Basic remains safely unavailable until its external contract exists.
- Improved Validate, Execute, PASS/FAIL/BLOCKED, and sanitized evidence UX.
- Added canonical Alpha 1.1 state, acceptance, and architecture decision docs.
- Documented practical local test tiers and the immutable Run 02 evidence
  limitation.

No new QA4 write, Oracle query, or production operation is included in this
source baseline.

### Readiness clarification

- Normalized the product UI to show `LOCAL READY` and `UNAVAILABLE` rather
  than internal catalog states.
- Recorded the exact authoritative inputs required before Add Offer can be
  implemented.
- Confirmed that a future standalone pure Create Customer run is a new scoped
  real contract, not an implicit reuse of the existing Offers-controlled path.

### Historical contract canonicalization

- Renamed the product test to **Create Customer with Offer** so it truthfully
  represents the recovered `CREATE_OFFERS_CUSTOMER` composite operation.
- Bound product metadata to the existing Standard Runner, controlled bridge,
  adapter, ledger, attestation, and sanitized evidence contract without
  enabling transport.
- Kept customer/line post-execution DB validation explicitly unavailable and
  documented its exact external requirements.

## v0.0.0-alpha.1

Historical controlled Alpha baseline. See `docs/PROJECT_STATE.md` for the
current source-capability and evidence distinction.
