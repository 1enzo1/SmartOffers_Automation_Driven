# Architecture Decisions

## ADR-001 - Product UI is a thin catalog-driven layer

**Decision:** Keep Flask and the existing product-test catalog as the source of
truth. The primary UI translates safe catalog metadata into user language; it
does not create a parallel backend, execution path, or policy engine.

**Consequences:** Existing routes and JSON remain compatible. Internal gate
names, hashes, destinations, and raw transport material remain outside the
normal user view.

## ADR-002 - Local mock and controlled evidence remain distinct

**Decision:** A local simulation returns a non-persisted summary. Only the
allowlisted sanitized evidence reader can show persisted controlled records.

**Consequences:** The UI never implies that a local mock produced a QA4 proof.
The historical Run 02 artifact is preserved and normalized to `FAIL` because
its response was not durably captured.

## ADR-003 - Unavailable capabilities fail closed in the catalog

**Decision:** Add Offer stays unavailable until its operation-scoped contract,
governed offer source, and read-only validation are known. Create Customer and
Recharge remain local-only until their real bindings and validations are
approved.

**Consequences:** No hardcoded offer, arbitrary SQL, or accidental external
mutation is introduced to improve the interface.

## ADR-004 - Real execution remains a separately authorized boundary

**Decision:** UI validation and catalog visibility never authorize real
execution. Every future controlled QA4 run requires its own contract,
preflight, one-shot ledger, sanitised evidence, and explicit Owner decision.

**Consequences:** Run 03 preparation is documentation and source readiness
only. It cannot be inferred from Run 01/02 or Alpha 1.1 local tests.
