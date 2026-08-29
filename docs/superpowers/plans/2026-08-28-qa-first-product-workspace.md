# QA-First Product Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` task-by-task.

**Goal:** Make QA the product-facing journey while retaining local mock tools only in collapsed Diagnostics, and bind the Create Customer with Offer product action to the existing governed controlled stack without performing real transport.

**Architecture:** Keep Flask, the catalog, and the existing controlled endpoint/bridge/adapter. Add a product-facing orchestration seam that selects the existing controlled path only under an explicit injected transport for tests; it must never introduce a second adapter, bridge, ledger, or transport client. The primary template becomes a QA readiness UI; legacy runner/generator tooling remains accessible only from Diagnostics.

**Tech Stack:** Python, Flask, vanilla HTML/CSS/JavaScript, pytest.

**Spec:** Owner-approved attachments `eadc11ce-7299-4f35-ae2a-0686d73b2a90/pasted-text-1.txt` and `pasted-text-2.txt`.

## Global Constraints

- No QA4, Oracle, HTTP, or production transport during implementation or tests.
- Preserve existing guarded controlled stack; no generic real mode, duplicate adapter, bridge, executor, or ledger.
- QA readiness and DB post-condition validation are separate truths.
- Primary workspace contains zero mock execution controls; Diagnostics is collapsed by default.
- All new behavior is test-first and uses injected mocked transport only.

### Task 1: Product orchestration contract

**Files:**
- Modify: `app.py`, `core/product_test_catalog.py`
- Test: `tests/test_product_test_catalog_api.py`, `tests/test_qa4_real_controlled_bridge.py`

- [ ] Write failing tests proving Create Customer validation returns QA readiness without mutation and product Execute delegates to the existing controlled stack with injected mocked transport.
- [ ] Run focused tests and verify the delegation assertions fail before production changes.
- [ ] Implement the smallest shared product-to-controlled-stack orchestration seam and truth-based readiness projection.
- [ ] Run focused tests; cover 2xx, 4xx, 5xx, timeout, missing authorization, destination mismatch, second attempt, DB-validation unavailable, and evidence persistence failure.

### Task 2: QA-first primary workspace

**Files:**
- Modify: `templates/index.html`
- Test: `tests/test_product_test_catalog_api.py`

- [ ] Write failing source/endpoint behavior tests for QA-first defaults, zero primary mock controls, truth-based statuses, current-run evidence attribution, and Diagnostics collapsed by default.
- [ ] Run focused tests and verify failures.
- [ ] Implement the information architecture over existing endpoints: QA readiness, authorization state, database-validation limitation, QA Execute semantics, and a separate Diagnostics surface.
- [ ] Run focused tests and verify success.

### Task 3: Documentation and independent acceptance

**Files:**
- Modify: `CHANGELOG.md`, `docs/PROJECT_STATE.md`, `docs/ALPHA_1_1_ACCEPTANCE.md`, `docs/ROADMAP.md`
- Test: feature tier plus offline integration tier

- [ ] Update canonical product principles and explicit verification semantics.
- [ ] Run targeted Tier 0/1/2 tests and static checks; inspect diff and secret hygiene.
- [ ] Obtain independent Tester and Critic review, fix in-scope findings, retest, commit, and push.
