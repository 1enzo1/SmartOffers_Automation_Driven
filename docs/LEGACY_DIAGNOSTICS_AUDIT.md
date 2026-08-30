# Legacy diagnostics ownership audit

This is an evidence-backed ownership map for the compatibility surfaces kept
outside the QA-first product workspace. No code or route is removed by this
audit.

| Surface | UI / entrypoint | Implementation | Coverage | Classification |
| --- | --- | --- | --- | --- |
| Scenario generator | `#diagnosticsNav`, `#diagnosticsSidebar`, generator workspace | Flask generation routes and `core/generation/` | `test_generation.py`, `test_app_generation_api.py`, `test_template_library.py` | KEEP_DIAGNOSTIC |
| Legacy runner | runner workspace and `/executar` compatibility route | `runner/executor.py`, legacy execution helpers | `test_legacy_execution_result_semantics.py`, `test_legacy_real_script_safety.py` | HIDE_PRIMARY |
| Standard mock runner | QA-first diagnostic/controlled mock surfaces | `core/real_execution/` mock facade and runner | `test_qa4_standard_mock_*.py` | KEEP_DIAGNOSTIC |
| Historical controlled evidence | `#controlledEvidence` and Historical runs panel | sanitized evidence reader in `core/real_execution/sanitized_evidence.py` | `test_sanitized_evidence.py`, product catalog API tests | KEEP_COMPATIBILITY |
| Manual QA smoke modules | not a primary UI control; test-only/manual scripts | `tools/qa4_*_manual_smoke.py` | `test_*manual_smoke.py`, `test_first_qa4_real_call_manual_gate.py` | DEPRECATE_CANDIDATE |
| Legacy execution package | no primary product consumer identified | `core/legacy_execution/` | legacy safety/semantics tests | BLOCKED_REQUIRES_OWNER_DECISION |

The generator and runner remain available for existing routes and saved JSON
compatibility, but are intentionally secondary to the QA workspace. Manual
smoke code is retained because it documents historical checkpoints; it must not
be selected by routine local tiers or used as an authorization for live work.

No removal candidate is established: each listed surface either serves a
critical compatibility route or lacks sufficient ownership evidence for safe
deletion. A future cleanup should first prove route consumers and preserve
backward compatibility for existing scenario JSONs.
