# Test Suite Rationalization Backlog (light)

This is an initial routing note for the post-Alpha test suite. It does not
remove tests or change the default test command. The full inventory currently
contains 42 Python test files under `tests/`.

## Proposed tiers

### Fast/local tier

Run on normal local changes. These tests use fakes, mock runners, pure
validation, or local Flask clients and should not require network or private
runtime state:

- `test_generation.py`, `test_scenario_intelligence.py`, `test_simulation.py`,
  `test_template_library.py`
- `test_adapters.py`, `test_adapter_risk_classifier.py`, `test_execution_mode_selector.py`,
  `test_legacy_execution_result_semantics.py`
- `test_app_generation_api.py`, `test_api_catalog.py`, `test_export_artifacts_api.py`,
  `test_adapter_ui.py`, `test_product_test_catalog_api.py`
- `test_evidence_payload_builders.py`, `test_evidence_payload_contract.py`,
  `test_sanitized_evidence.py`
- `test_qa4_standard_mock_api.py`, `test_qa4_standard_mock_facade.py`,
  `test_qa4_standard_mock_runner.py`, `test_qa4_standard_mock_ui.py`
- `test_qa4_bda_mock_executor.py`, `test_smoke_consolidation.py`,
  `test_gate_dag.py`

### Controlled-path tier

Run when changing real-controlled contracts or their guards. These tests are
local and should use injected fakes; they must not be treated as permission to
call an external system:

- `test_acm_local_runtime_preflight.py`
- `test_bda_local_runtime_preflight.py`
- `test_qa4_bda_offer_discovery.py`
- `test_qa4_offers_customer_adapter.py`
- `test_qa4_real_controlled_bridge.py`
- `test_qa4_scoped_destination_attestation.py`
- `test_first_qa4_call_executor.py`
- `test_real_execution_hardening.py`, `test_real_execution_readiness.py`,
  `test_real_execution_runtime_contract.py`
- `test_qa4_api_health_checkpoint.py`

### Governance/docs tier

Run when policy, safety, documentation, or source-layout contracts change:

- `test_documentation_guardrails.py`
- `test_runtime_local_template.py`
- `test_manual_qa4_readiness_package.py`
- `test_manual_smoke_plan.py`
- `test_legacy_real_script_safety.py`

### Manual/external-risk tier

Never run casually or as part of an ordinary local loop. These files describe
or gate manual/external smoke activity and require an explicit, separately
scoped authorization and environment review:

- `test_qa4_acm_manual_smoke.py`
- `test_qa4_bda_manual_smoke.py`
- `test_qa4_manual_smoke.py`
- `test_first_qa4_real_call_manual_gate.py`

The tier classification is a routing rule, not an execution authorization.

## Obvious overlap and candidates

- The three `test_qa4_standard_mock_*` files cover adjacent mock API, facade,
  runner, and UI seams. Keep them separate for now, but consider a shared
  fixture/helper to reduce repeated context builders.
- `test_acm_local_runtime_preflight.py` and
  `test_bda_local_runtime_preflight.py` exercise parallel local-runtime guard
  contracts. Compare common assertions and extract only genuinely shared test
  helpers.
- `test_qa4_*_manual_smoke.py`, `test_manual_smoke_plan.py`, and
  `test_manual_qa4_readiness_package.py` overlap in manual-run policy. Keep the
  safety checks, then consolidate duplicated contract fixtures in a later
  pass.
- `test_first_qa4_call_executor.py`,
  `test_first_qa4_real_call_manual_gate.py`, and
  `test_real_execution_hardening.py` are adjacent first-call/real-execution
  coverage. Review for duplicated deny-path assertions before adding tests.
- `test_qa4_api_health_checkpoint.py` and
  `test_qa4_scoped_destination_attestation.py` both cover destination/runtime
  attestation boundaries; keep distinct behavior but share terminology and
  fixture conventions.

## Next steps

1. Add explicit pytest markers for `fast`, `controlled`, `governance`, and
   `manual_external` without changing test behavior.
2. Add a CI/local command that selects the fast tier and a separate command for
   the controlled tier with network disabled or fake drivers injected.
3. Consolidate duplicated fixtures only after measuring runtime and reviewing
   ownership; do not delete historical manual safety coverage.
4. Revisit the manual/external tier only when a separately authorized run is
   planned. Build a future tier report for the larger suite audit rather than
   expanding this light backlog now.
