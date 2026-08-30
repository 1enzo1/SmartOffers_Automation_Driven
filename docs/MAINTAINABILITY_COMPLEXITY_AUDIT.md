# Phase 11 — Maintainability and Complexity Audit

Bounded review of Alpha-touched modules. No broad refactor was justified.

## Classification

### REFACTOR_NOW

None. The apparent complexity is concentrated at governed boundaries where
splitting code would risk changing authorization, ledger, evidence, or legacy
compatibility semantics without a stronger contract.

### DOCUMENT_DEBT

- `app.py` product validation/execution routes coordinate catalog lookup,
  context claims, result mapping, and evidence response. They are covered, but
  their responsibility boundaries should be extracted only alongside a future
  API contract change.
- `qa4_offers_customer_adapter.py` contains the complete historical contract
  gate and transport preparation in one module. Its pure helpers are well
  separated; the orchestration function remains a future seam for contract
  versioning.
- Visible status/reason translation exists in both Flask responses and the
  frontend JavaScript. The duplication is intentional at the presentation
  boundary but should be centralized if a typed API schema is introduced.
- Legacy SSE protocol strings and evidence-reference regexes are fragile
  string semantics. They are compatibility contracts and should not be changed
  without migration tests.
- Evidence formatting has separate public, historical, and UI projections;
  this is deliberate isolation, but a future schema module could make the
  mapping more discoverable.

### LEAVE_ALONE

- Pure gate/preflight helpers and the operational release store: small,
  deterministic, and directly tested.
- Sanitization helpers: explicit allowlists and fail-closed validation are safer
  than a broad abstraction at this stage.
- Legacy compatibility routes and mock adapters: retained for route/JSON
  compatibility and clearly de-emphasized from the QA-first product.

## Testability observations

Mutable release/attempt state is injected or instantiated per test. Product
routes use the shared Flask fixture with isolated temporary storage. Tier 3
manual-risk modules are intentionally separated from routine tiers. No
ordering plugin or hidden network dependency was found in the reviewed setup.

Recommended future work is a typed response contract and targeted extraction
of route orchestration after the next product contract milestone; neither is
required for the current Alpha behavior.
