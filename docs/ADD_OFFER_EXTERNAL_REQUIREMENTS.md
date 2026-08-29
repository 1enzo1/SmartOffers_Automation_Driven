# Add Offer Basic - External Requirements

Add Offer Basic remains unavailable. Repository archaeology found a distinct
catalogued `Troca de Oferta` item (`post-o-vivo-next-troca-de-oferta-fedbfb981e`)
with a generic `processEvent` template, but no complete authoritative contract.
It is not equivalent to the historical `Create Customer with Offer` flow.
This document records the minimum information required before any planning or
execution capability is added. It intentionally contains no invented values,
SQL, amount, offer, host, credential, or schema.

## Required authoritative artifacts

- Operation-scoped contract: authoritative operation ID, API mapping, method,
  path, and allowed environment.
- Request schema: authoritative required fields, types, constraints, and
  ownership for the Add Offer request.
- Offer input or discovery: governed source, selector/identity, freshness and
  authorization rules for obtaining the offer input.
- Read-only validation: approved lookup identity, query or content hash,
  destination/resource scope, and expected result shape proving the outcome.

## Recovered but insufficient metadata

The tracked catalog identifies a POST `processEvent` template with attributes
including account, MSISDN, offer and billing fields. Its execution policy is
blocked and its values remain placeholders; it does not establish the
operation-specific request/response semantics, adapter, bridge or validator.

Until all artifacts are approved and bound to a future explicit MVP, the UI
must remain `UNAVAILABLE`, Execute must remain disabled, and no discovery,
planning, or transport may run.
