# Recharge Basic - External Requirements

Recharge Basic remains a local diagnostic. Repository archaeology found a
catalogued SmartOffers Copy item (`post-evento-de-recarga-6954ef3458`) whose
sanitized metadata identifies a `processEvent` operation and a generic event
template. The catalog entry is blocked for real execution and is not a
complete authoritative contract.

## Recovered facts

- Mutation family: generic `processEvent` event template.
- Request envelope: event identifier, event time, attributes and attribute
  metadata are represented as placeholders in the tracked catalog.
- Domain hints: recharge channel, event dates, external identifier, last
  recharge date/value, mix code, multi-operation and reason code.
- No governed Recharge adapter, real bridge, response contract or result
  normalizer exists in the current product path.
- No approved read-only Recharge validation query or expected result shape was
  found in source, tests, history or query registries.

## Required authoritative artifacts

- The operation identity and operation-scoped QA4 contract for Recharge Basic.
- Complete request schema: required fields, types, constraints, ownership and
  event-time rules. Placeholder attributes are insufficient.
- Success and failure response contract, including the status/response fields
  that define a successful mutation.
- Governed adapter and bridge mapping to the existing controlled execution
  architecture, including destination policy and authorization scope.
- Approved read-only validation lookup identity, query/hash, destination scope
  and expected result shape proving the recharge outcome.

Until these artifacts are supplied and approved, keep the catalog status
`LOCAL DIAGNOSTIC`; do not infer amounts, products, channels, endpoints,
operation identifiers, SQL or success semantics.
