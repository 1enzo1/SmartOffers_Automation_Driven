# Test Suite Health Audit — Phase 06

## Inventory

Current collection is **853 tests in 48 test files**:

- Tier 0 (fast safety/import/config): 421
- Tier 1 (feature-targeted): 254
- Tier 2 (offline integration/governance): 53
- Tier 3 (release/manual-risk): 125

The tier markers are explicit in `tests/conftest.py`; no test is silently
assigned to a routine tier. The existing 812-test full verification remains a
historical milestone; the current collection includes subsequent regression
coverage.

The repository does not include the `coverage` package, so this audit uses
collection, marker, source-branch, and targeted failure-path analysis rather
than installing new tooling.

## Risk-oriented findings

### High value (addressed)

The one-shot operational release ledger had limited direct coverage for invalid
scope input, duplicate release keys, malformed plans, and invalid claim
references. Five focused assertions were added to
`tests/test_operational_release_store.py`. They verify fail-closed provisioning,
duplicate prevention, and claim input isolation without exercising any live
runtime.

### Medium value (follow-up)

- Evidence and product API paths have broad malformed/transport coverage, but
  mutation-style testing of every response-normalization branch is not yet
  warranted for the current Alpha scope.
- Legacy manual smoke modules intentionally repeat some environment and
  adapter checks; they remain Tier 3 because they document release-risk
  boundaries. Consider merging only after preserving their distinct operator
  contracts.
- Several tests depend on temporary filesystem paths and environment fixtures;
  they are isolated through `app_client_factory`, but Windows ACL-protected
  pytest cache directories can make ad-hoc collection noisy.

### Low value / recommendations (not deleted)

- Review duplicate catalog assertions and documentation-only guard tests during
  a future suite consolidation.
- Measure slowest Tier 3 groups during a release window rather than on every
  change; no timing-based tier move was made here.
- Avoid adding tests that only restate constants or mock every layer of the
  behavior under test.

## Health assessment

- Governance branches: strong coverage for production blocking, one-shot
  reservation/claim, context replay, and malformed preflight.
- Evidence branches: strong sanitization and persistence-failure coverage;
  current/history isolation is explicitly tested.
- Error states: product API and controlled bridge cover malformed input, 4xx,
  5xx, timeout, blocked, and local exception outcomes.
- Ordering/shared state: no global test ordering plugin is configured; tests use
  isolated fixtures and per-test stores for mutable release state.
- Mock leakage: real transport imports remain isolated to the dedicated client;
  routine tiers use injected/local transports.

No high-risk uncovered branch justified broader implementation in this phase.
