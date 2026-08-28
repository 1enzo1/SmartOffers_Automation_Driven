# Add Offer Basic - External Requirements

Add Offer Basic remains unavailable and local-only. This document records the
authoritative information required before any planning or execution capability
is added. It intentionally contains no invented values, SQL, amount, offer,
host, credential, or schema.

## Required authoritative artifacts

- Operation-scoped contract: authoritative operation ID, API mapping, method,
  path, and allowed environment.
- Request schema: authoritative required fields, types, constraints, and
  ownership for the Add Offer request.
- Offer input or discovery: governed source, selector/identity, freshness and
  authorization rules for obtaining the offer input.
- Read-only validation: approved lookup identity, query or content hash,
  destination/resource scope, and expected result shape proving the outcome.

Until all artifacts are approved and bound to a future explicit MVP, the UI
must remain `UNAVAILABLE`, Execute must remain disabled, and no discovery,
planning, or transport may run.
