# Alpha 1.1 Product Finalization Implementation Plan

> **For agentic workers:** Execute the approved Owner package in bounded, local/mock-first increments with independent Tester and Critic review.

**Goal:** Finalize the existing post-Alpha product flow, synchronize its canonical documentation, and prepare (but never execute) Run 03.

**Architecture:** Preserve the Flask, HTML/CSS/JavaScript, local/mock-first stack. Product metadata remains the single catalog source; the UI translates it to human language and never enables a real mutation. Evidence stays on the existing sanitised, read-only endpoints.

**Tech Stack:** Python, Flask, vanilla HTML/CSS/JavaScript, pytest.

## Global Constraints

- No real QA4, Oracle, HTTP, Kafka, Jenkins, or production call.
- No React, build step, secret, raw payload, raw response, or persisted synthetic identity.
- Preserve legacy routes and JSON compatibility.
- Run targeted tests first; Tier 3 is only considered after its manual/external-path safety precondition is established.

### Task 1: Reconcile state and documentation

**Files:**
- Create: `docs/PROJECT_STATE.md`, `docs/ALPHA_1_1_ACCEPTANCE.md`, `docs/ARCHITECTURE_DECISIONS.md`
- Modify: `docs/ROADMAP.md`, existing changelog if one is present
- Test: `tests/test_documentation_guardrails.py`

- [ ] Compare the current catalog, endpoints, test tiers, commits and evidence reader with historical documentation.
- [ ] Record only supported current facts, including the immutable Run 02 evidence limitation.
- [ ] Record Run 03 prerequisites as readiness items, not an authorization.
- [ ] Run documentation guardrail tests and `git diff --check`.

### Task 2: Apply minimal product UX fixes from rendered review

**Files:**
- Modify: `templates/index.html`, `core/product_test_catalog.py`, `app.py` only if the review demonstrates a contract mismatch
- Test: `tests/test_product_test_catalog_api.py`, relevant new focused tests

- [ ] Write a failing test for each concrete user-visible defect before changing implementation.
- [ ] Keep environment, test, test data, Validate, Execute, Result and Evidence in that primary order.
- [ ] Translate catalog capability states to the approved user vocabulary and keep unavailable actions disabled.
- [ ] Verify browser flow locally and run Tier 0 plus the feature suite.

### Task 3: Acceptance, freeze, and Run 03 readiness

**Files:**
- Modify: canonical documentation only if acceptance findings require it
- Test: Tier 0 plus the applicable Tier 1/Tier 2 local suites

- [ ] Independent Tester validates journeys A-E and sanitisation.
- [ ] Independent Critic validates product clarity and visual hierarchy.
- [ ] Correct in-scope findings, re-test, commit and push.
- [ ] Tag the source baseline only when every stated Alpha 1.1 gate is proven.
- [ ] Record why any Run 03 requirement remains blocked; do not execute it.
