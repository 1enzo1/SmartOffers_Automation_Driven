# Phase 09 — Authoritative Contract Archaeology

Scope: local repository and Git history only. No QA, Oracle, or external HTTP
operation was performed.

| Operation | Required fact | Evidence found | Source | Confidence | Authoritative | Implementable | Missing input |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Create Customer DB post-condition | Approved read-only lookup, identity/hash, destination scope, result shape | No query registry, validator, or tracked sanitized post-create lookup; historical Alpha path records HTTP execution only | `core/product_test_catalog.py`; `939ec10`; `docs/CREATE_CUSTOMER_EXTERNAL_REQUIREMENTS.md` | High | No | No | Approved operation/scenario-scoped customer/line lookup contract and expected result shape |
| Recharge mutation | Operation identity and complete governed QA4 request contract | Tracked catalog entry describes a generic `processEvent` event template with placeholders and a sanitized mapping; local fake plan exists | `core/api_catalog/catalog.json`; `core/product_test_catalog.py`; `docs/RECHARGE_EXTERNAL_REQUIREMENTS.md`; `2901134` | High | No | No real binding | Authoritative operation contract, required fields/types/constraints, and ownership |
| Recharge response | Success/failure response and normalization semantics | No governed adapter, response normalizer, or authoritative response schema | `core/product_test_catalog.py`; `docs/RECHARGE_EXTERNAL_REQUIREMENTS.md` | High | No | No | Approved response contract and success criteria |
| Recharge DB post-condition | Read-only query and result shape | No approved query, hash/allowlist, validator, or tracked artifact found | `core/db/*` (empty placeholders); `docs/RECHARGE_EXTERNAL_REQUIREMENTS.md` | High | No | No | Read-only lookup identity/hash, destination scope, expected result shape |
| Standalone Add Offer mutation | Distinct operation and offer input contract | Catalog contains a separate offer-change `processEvent` template with placeholders; no operation-specific binding | `core/api_catalog/catalog.json`; `core/product_test_catalog.py`; `docs/ADD_OFFER_EXTERNAL_REQUIREMENTS.md`; `4abe28a` | High | No | No | Operation ID/API contract, request schema, governed offer input/discovery |
| Standalone Add Offer validation | Read-only confirmation of resulting offer state | No approved query, validator, result shape, or allowlist found | `core/db/*`; `docs/ADD_OFFER_EXTERNAL_REQUIREMENTS.md` | High | No | No | Approved lookup identity/hash, destination scope, expected result shape |

## Historical Create Customer distinction

The successful Alpha implementation is an Offers customer-create operation
(`CREATE_OFFERS_CUSTOMER`) with a synthetic scenario and existing controlled
adapter/bridge. It is not evidence that standalone Add Offer or a database
post-condition validator exists. The current product correctly reuses that
execution contract while keeping DB validation separate and unconfigured.

The historical `core/api/*` and `core/db/*` modules in the early dashboard
commits are empty placeholders, so they do not provide recoverable contracts.
Ignored/untracked historical evidence was not treated as authoritative tracked
evidence.

## Owner/vendor checklist

Provide the minimum non-secret artifacts listed in
`RECHARGE_EXTERNAL_REQUIREMENTS.md`, `ADD_OFFER_EXTERNAL_REQUIREMENTS.md`, and
`CREATE_CUSTOMER_EXTERNAL_REQUIREMENTS.md`. Each must be approved for QA4 and
bound to the existing server-side controlled architecture; no new parallel
transport or inferred SQL is acceptable.
