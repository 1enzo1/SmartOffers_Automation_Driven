import inspect
import re
from pathlib import Path

import pytest

from tools import qa4_acm_manual_smoke
from tools import qa4_api_health_smoke
from tools import qa4_bda_manual_smoke
from tools import qa4_bda_mock_executor


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_TASK_CLASSES = {"MECHANICAL", "DEVELOPMENT", "DEBUG", "RESEARCH", "REVIEW"}

ROADMAP_ITEMS = [
    "MVP7.8.4 - QA4 Sanity Runner Standard/Variant/Copy",
    "MVP7.8.5 - Real Campaign Scenario Pack 01",
    "MVP7.8.6 - Evidence Comparison & Runner Hardening",
    "MVP7.9.0 - SmartOffers Real Regression Suite v0",
    "v0.1 estavel interna",
]

SUPERVISORS = [
    "smartoffers-architect-supervisor",
    "campaign-supervisor",
    "evidence-supervisor",
    "troubleshooting-supervisor",
    "catalog-config-supervisor",
    "adapter-supervisor",
    "safety-supervisor",
]

SKILLS = [
    "campaign-analysis",
    "evidence-planning",
    "troubleshooting",
    "sql-evidence",
    "api-contract-analysis",
    "request-plan-analysis",
    "adapter-execution-planning",
    "catalog-config-analysis",
    "kafka-nrt-analysis",
    "bko-analysis",
    "risk-classification",
]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _extract_task_class_assignments(document):
    return set(re.findall(r"TASK_CLASS=([^\s`|]*)", document))


def _assert_only_allowed_task_classes(document):
    assigned_task_classes = _extract_task_class_assignments(document)
    assert assigned_task_classes
    assert assigned_task_classes <= ALLOWED_TASK_CLASSES


def _extract_alpha_board_rows(document):
    board = document.split("## Board Alpha", 1)[1].split("\n## ", 1)[0]
    table_lines = [line for line in board.splitlines() if line.startswith("|")]
    assert len(table_lines) >= 3
    assert table_lines[0].startswith("| Prioridade | Goal | TASK_CLASS |")
    assert re.fullmatch(r"\|(?:---\|){6}", table_lines[1])
    return [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in table_lines[2:]
    ]


def _assert_alpha_board_task_classes(document):
    rows = _extract_alpha_board_rows(document)
    allowed_cells = {
        f"`TASK_CLASS={task_class}`"
        for task_class in ALLOWED_TASK_CLASSES
    }
    assert rows
    for row in rows:
        assert len(row) == 6
        assert row[2] in allowed_cells


def test_product_guardrails_are_documented():
    docs = "\n".join(
        [
            _read("README.md"),
            _read("PROJECT_STATUS.md"),
            _read("AGENTS.md"),
            _read(".agents/skills/smartoffers-automation-architect/SKILL.md"),
            _read("docs/ARCHITECTURE.md"),
            _read("docs/ROADMAP.md"),
        ]
    )

    required_fragments = [
        "qa/mvp4-integration",
        "PortalQA ficou como referencia historica",
        "SmartOffers_Automation_Driven",
        "laboratorio seguro",
        "local-first",
        "mock-first",
        "execucao real continua bloqueada por padrao",
        "runtime secrets",
        "opt-in explicito",
        "ambiente permitido",
        "allowlist",
        "timeout",
        "logs sanitizados",
        "bloqueio de producao",
    ]

    for fragment in required_fragments:
        assert fragment in docs


def test_roadmap_supervisors_and_skills_are_documented():
    docs = "\n".join([_read("README.md"), _read("docs/ROADMAP.md"), _read("docs/SUPERVISORS.md")])

    for item in ROADMAP_ITEMS:
        assert item in docs

    for supervisor in SUPERVISORS:
        assert supervisor in docs

    for skill in SKILLS:
        assert skill in docs


def test_current_alpha_governance_is_documented():
    docs = "\n".join(
        [
            _read("README.md"),
            _read("PROJECT_STATUS.md"),
            _read("docs/ROADMAP.md"),
            _read("docs/ALPHA_GOVERNANCE.md"),
        ]
    )

    required_fragments = [
        "v0.0.0-pre-alpha.1",
        "e1263595aa736de3855234b6f9a0379b944fe70e",
        "codex/alpha",
        "MVP7.8.3B DB-only",
        "API `NOT_READY`",
        "`BASIC_SMOKE_OK=false`",
        "`FULL_SMOKE_OK=false`",
        "MVP7.8.4 - QA4 Sanity Runner Standard/Variant/Copy",
        "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
        "CONTRACT_CONFLICT-001",
        "nao autoriza",
    ]

    for fragment in required_fragments:
        assert fragment in docs


def test_alpha_operation_scoped_transport_contract_stays_default_deny_and_sanitized():
    docs = "\n".join(
        [
            _read("docs/ALPHA_DELIVERY_POLICY.md"),
            _read("docs/ALPHA_GOVERNANCE.md"),
            _read("docs/ALPHA_OWNER_EXECUTION_HANDOFF.md"),
        ]
    )

    for fragment in [
        "REAL_TRANSPORT_ALLOWED=false",
        "ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN",
        "CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4",
        "CREATE_OFFERS_CUSTOMER",
        "retry zero",
        "fallback false",
        "never a destination value",
        "production is unconditionally denied",
    ]:
        assert fragment in docs


def test_alpha_role_boundaries_are_consistent_per_source():
    agents = _read("AGENTS.md")
    architect = _read(".agents/skills/smartoffers-automation-architect/SKILL.md")
    manager = _read(".agents/skills/smartoffers-execution-manager/SKILL.md")
    developer = _read(".agents/skills/smartoffers-automation-developer/SKILL.md")
    governance = _read("docs/ALPHA_GOVERNANCE.md")

    assert "O Arquiteto nao executa trabalho rotineiro" in agents
    assert "Tester/Reviewer diferente de quem" in agents
    assert "`smartoffers-architect-supervisor` nao e" in agents

    assert "O Architect nao assume implementacao" in architect
    assert "escalonamento ao Architect exige divergencia material de contrato ou risco" in architect
    assert "transporte real permanece operacional e contratualmente bloqueado" in architect
    assert "todo transporte real permanecem universalmente\nbloqueados" not in architect
    assert "mode=real` não deve ser universalmente permitido" not in architect
    assert "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01" in architect
    assert "API_QA4_TECHNICAL_NON_MUTATING_01" not in architect

    assert "Tester/Reviewer" in manager
    assert "No estado Alpha\natual, Oracle, API, Kafka e Jenkins reais permanecem bloqueados" in manager
    assert "o Dev nao aprova a propria entrega como\nindependente" in developer

    assert "CONTRACT_CONFLICT-001" in governance
    assert "nao inferir um bypass a partir de evidencia historica" in " ".join(
        governance.split()
    )


def test_alpha_precision_contract_routes_authority_capability_and_task_classes():
    architect = _read(".agents/skills/smartoffers-automation-architect/SKILL.md")
    governance = _read("docs/ALPHA_GOVERNANCE.md")
    architecture = _read("docs/ARCHITECTURE.md")
    execution_plan = _read("ai/real-execution/mvp7-8-3b-execution-plan.md")

    assert "divergencia material de contrato ou risco" in governance
    assert "capacidade tecnica nao cria autorizacao" in governance
    assert "ALPHA-PR18-FIX-001" in governance
    assert "TASK_CLASS=MECHANICAL|DEVELOPMENT|DEBUG|RESEARCH|REVIEW" in governance

    _assert_only_allowed_task_classes(governance)

    assert "entry points dormentes nao sao autorizacao" in architect
    assert "nao devem ser invocados no Alpha" in architect

    dormant_executors = [
        "tools/qa4_manual_smoke.py",
        "tools/qa4_acm_manual_smoke.py",
        "tools/qa4_bda_manual_smoke.py",
        "tools/qa4_api_health_smoke.py",
    ]
    for executor in dormant_executors:
        assert executor in architecture

    assert "executores manuais dormentes" in architecture
    assert "nao constitui liberacao Alpha nem garantia de kill switch" in architecture

    assert "Architect General issues `EXECUTION_APPROVED`" not in execution_plan
    assert "architectural risk envelope" in execution_plan
    assert "authorized operational role" in execution_plan
    assert "EXECUTION_BLOCKED" in execution_plan


@pytest.mark.parametrize("malformed_task_class", ["research", "REVIEW_EXTRA", "REVIEW2", ""])
def test_alpha_task_class_validation_rejects_malformed_complete_tokens(malformed_task_class):
    document = f"`TASK_CLASS=REVIEW`\n`TASK_CLASS={malformed_task_class}`"

    with pytest.raises(AssertionError):
        _assert_only_allowed_task_classes(document)


def test_future_roadmap_does_not_relist_completed_mvp76_or_mvp77_as_pending():
    roadmap = _read("docs/ROADMAP.md")
    future_section = roadmap.split("## Roadmap futuro atual", 1)[1]

    obsolete_pending_items = [
        "MVP7.6.1 - Guardrails e documentacao de arquitetura",
        "MVP7.6.2 - Ontologia SmartOffers",
        "MVP7.6.3 - Playbooks operacionais",
        "MVP7.6.4 - Evidence Planner",
        "MVP7.6.5 - AI Supervisors Foundation",
        "MVP7.6.6 - Scenario Intelligence Layer",
        "MVP7.6.7 - Adapter Risk Classifier",
        "MVP7.7 - Primeira chamada real opt-in em QA4",
    ]

    for item in obsolete_pending_items:
        assert item not in future_section


def test_alpha_gate_dag_has_no_legacy_or_summary_predecessor_in_active_admission():
    acm_validation = inspect.getsource(qa4_acm_manual_smoke._validate_arguments)
    bda_validation = inspect.getsource(qa4_bda_manual_smoke._validate_arguments)
    bda_mock_validation = inspect.getsource(qa4_bda_mock_executor._validate_arguments)
    api_validation = inspect.getsource(qa4_api_health_smoke._validate_arguments)

    assert "basic_smoke_status" not in acm_validation
    assert "basic_db_checkpoint_status" not in bda_validation
    assert "basic_db_checkpoint_status" not in bda_mock_validation
    assert "basic_db_checkpoint_status" not in api_validation
    assert "validate_api_db_gate_bundle" in api_validation


def test_alpha_gate_dag_contract_declares_exact_task_class_and_blocks_transport():
    content = _read("ai/real-execution/mvp7-8-4-gate-dag-contract.md")

    required_fragments = [
        "ALPHA-MVP784-002",
        "TASK_CLASS=DEVELOPMENT",
        "ACM_CUSTOM | ACM | BDA -> API -> Manager consolidation",
        "smartoffers_qa4_full_smoke",
        "real transport remains blocked",
        "mock-only",
    ]
    for fragment in required_fragments:
        assert fragment.lower() in content.lower()


def test_alpha_gate_dag_contract_preserves_independence_provenance_and_terminal_precedence():
    content = _read("ai/real-execution/mvp7-8-4-gate-dag-contract.md")

    required_fragments = [
        "Producer, consumer, meaning and evidence source",
        "ACM_CUSTOM own guards -> ACM_CUSTOM_DB_CHECKPOINT_OK",
        "ACM own guards -> ACM_DB_CHECKPOINT_OK",
        "BDA own guards -> BDA_DB_CHECKPOINT_OK",
        "Scheduling is not dependency",
        "exactly three canonical DB gates",
        "BASIC_SMOKE_OK",
        "BASIC_SMOKE_FAILED",
        "BASIC_SMOKE_BLOCKED",
        "FULL_SMOKE_OK",
        "FULL_SMOKE_PARTIAL",
        "FULL_SMOKE_FAILED",
        "FULL_SMOKE_BLOCKED",
        "BASIC_DB_CHECKPOINT_OK",
        "deprecated",
    ]
    for fragment in required_fragments:
        assert fragment in content


def test_alpha_gate_dag_contract_has_exact_canonical_edge_set():
    content = _read("ai/real-execution/mvp7-8-4-gate-dag-contract.md")
    match = re.search(
        r"<!-- CANONICAL_GATE_EDGE_SET_BEGIN -->\s*```text\s*(.*?)\s*```\s*"
        r"<!-- CANONICAL_GATE_EDGE_SET_END -->",
        content,
        re.DOTALL,
    )
    assert match is not None

    edge_lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    actual_edges = {
        tuple(part.strip() for part in line.split("->", maxsplit=1))
        for line in edge_lines
    }
    expected_edges = {
        ("ACM_CUSTOM_OWN_GUARDS", "ACM_CUSTOM_DB_CHECKPOINT_OK"),
        ("ACM_OWN_GUARDS", "ACM_DB_CHECKPOINT_OK"),
        ("BDA_OWN_GUARDS", "BDA_DB_CHECKPOINT_OK"),
        ("ACM_CUSTOM_DB_CHECKPOINT_OK", "SMARTOFFERS_API_QA4_CHECKPOINT_OK"),
        ("ACM_DB_CHECKPOINT_OK", "SMARTOFFERS_API_QA4_CHECKPOINT_OK"),
        ("BDA_DB_CHECKPOINT_OK", "SMARTOFFERS_API_QA4_CHECKPOINT_OK"),
        ("SMARTOFFERS_API_QA4_CHECKPOINT_OK", "MANAGER_CONSOLIDATION"),
    }

    assert len(edge_lines) == len(expected_edges)
    assert actual_edges == expected_edges


def test_alpha_gate_dag_contract_has_exact_manager_precedence_and_reasons():
    content = _read("ai/real-execution/mvp7-8-4-gate-dag-contract.md")
    match = re.search(
        r"<!-- MANAGER_PRECEDENCE_BEGIN -->\s*```text\s*(.*?)\s*```\s*"
        r"<!-- MANAGER_PRECEDENCE_END -->",
        content,
        re.DOTALL,
    )
    assert match is not None

    actual_precedence = tuple(
        tuple(part.strip() for part in line.split("|"))
        for line in match.group(1).splitlines()
        if line.strip()
    )
    expected_precedence = (
        ("BASIC", "1", "GLOBAL_SAFETY_STOP", "BASIC_SMOKE_BLOCKED", "GLOBAL_SAFETY_STOP"),
        ("BASIC", "2", "INVALID_INPUT_EVIDENCE", "BASIC_SMOKE_BLOCKED", "INVALID_INPUT_EVIDENCE"),
        ("BASIC", "3", "ALL_COMPONENTS_OK", "BASIC_SMOKE_OK", "ALL_COMPONENTS_OK"),
        ("BASIC", "4", "ANY_COMPONENT_FAILED", "BASIC_SMOKE_FAILED", "COMPONENT_FAILURE"),
        ("BASIC", "5", "OTHERWISE", "BASIC_SMOKE_BLOCKED", "COMPONENTS_BLOCKED"),
        ("FULL", "1", "GLOBAL_SAFETY_STOP", "FULL_SMOKE_BLOCKED", "GLOBAL_SAFETY_STOP"),
        ("FULL", "2", "INVALID_INPUT_EVIDENCE", "FULL_SMOKE_BLOCKED", "INVALID_INPUT_EVIDENCE"),
        ("FULL", "3", "ALL_COMPONENTS_OK", "FULL_SMOKE_OK", "ALL_COMPONENTS_OK"),
        ("FULL", "4", "ANY_COMPONENT_OK", "FULL_SMOKE_PARTIAL", "COMPONENTS_NOT_ALL_OK"),
        ("FULL", "5", "ANY_COMPONENT_FAILED", "FULL_SMOKE_FAILED", "COMPONENT_FAILURE"),
        ("FULL", "6", "OTHERWISE", "FULL_SMOKE_BLOCKED", "COMPONENTS_BLOCKED"),
    )

    assert actual_precedence == expected_precedence


def test_alpha_gate_dag_is_linked():
    contract_path = "ai/real-execution/mvp7-8-4-gate-dag-contract.md"
    real_execution_readme = _read("ai/real-execution/README.md")
    architecture = _read("docs/ARCHITECTURE.md")

    assert "mvp7-8-4-gate-dag-contract.md" in real_execution_readme
    assert contract_path in architecture


def test_alpha_mvp784_board_row_has_exact_class_and_completed_state():
    governance = _read("docs/ALPHA_GOVERNANCE.md")
    matching_rows = [row for row in _extract_alpha_board_rows(governance) if row[1].startswith("ALPHA-MVP784-002 ")]

    assert len(matching_rows) == 1
    assert matching_rows[0][2] == "`TASK_CLASS=DEVELOPMENT`"
    assert matching_rows[0][3] == "`STATE=COMPLETED`"


def test_every_alpha_board_row_has_one_exact_allowed_task_class_cell():
    governance = _read("docs/ALPHA_GOVERNANCE.md")

    _assert_alpha_board_task_classes(governance)


@pytest.mark.parametrize(
    "malformed_cell",
    (
        "`TASK_CLASS=REVIEW` extra",
        "TASK_CLASS=REVIEW",
    ),
)
def test_alpha_board_rejects_task_class_cell_contamination(malformed_cell):
    governance = _read("docs/ALPHA_GOVERNANCE.md")
    malformed_board = governance.replace("`TASK_CLASS=REVIEW`", malformed_cell, 1)

    with pytest.raises(AssertionError):
        _assert_alpha_board_task_classes(malformed_board)


def test_alpha_contract_conflict_is_resolved_after_independent_acceptance():
    governance = _read("docs/ALPHA_GOVERNANCE.md")

    conflict_section = governance.split("### `CONTRACT_CONFLICT-001`", 1)[1].split("### `STATE_DIVERGENCE-001`", 1)[0]
    normalized_conflict = " ".join(conflict_section.split())
    assert "RESOLVIDO" in normalized_conflict
    assert "Tester independente aceitou os 12 criterios" in normalized_conflict
    assert "983bace" in normalized_conflict
    assert "676 passed" in normalized_conflict
    assert "nao libera transporte real" in normalized_conflict
    assert "permanece aberta" not in normalized_conflict


def test_alpha_contract_conflict_describes_previous_cycle_in_the_past():
    governance = _read("docs/ALPHA_GOVERNANCE.md")
    conflict_section = governance.split("### `CONTRACT_CONFLICT-001`", 1)[1].split("### `STATE_DIVERGENCE-001`", 1)[0]
    normalized_conflict = " ".join(conflict_section.split())

    assert "O contrato/executor ACM anterior exigia `BASIC_SMOKE_OK`" in normalized_conflict
    assert "removeu o predecessor da admissao ACM" in normalized_conflict
    assert "O contrato/executor ACM exige `BASIC_SMOKE_OK`" not in normalized_conflict


def test_alpha_gate_record_validates_attempt_policy_without_claiming_to_store_it():
    content = _read("ai/real-execution/mvp7-8-4-gate-dag-contract.md")
    normalized_content = " ".join(content.split())

    assert "normalizer validates `attempts=1` and `retry=0` before emitting" in normalized_content
    assert "It also records one attempt, zero retry" not in normalized_content


def test_current_product_docs_agree_on_run03a_preauthorization_state():
    project_state = _read("docs/PROJECT_STATE.md")
    roadmap = _read("docs/ROADMAP.md")
    acceptance = _read("docs/ALPHA_1_1_ACCEPTANCE.md")
    decisions = _read("docs/ARCHITECTURE_DECISIONS.md")
    handoff = _read("docs/ALPHA_OWNER_EXECUTION_HANDOFF.md")
    docs = "\n".join([project_state, roadmap, acceptance, decisions, handoff])

    assert "Create Customer with Offer" in docs
    assert "READY_FOR_RUN_03_EXECUTION_PREAUTH=true" in project_state
    assert "Run 03 is not ready or authorized." not in acceptance
    assert "It is not equivalent to the historical `Create Customer with Offer`" not in roadmap
    assert "The exact composition link above is not present" not in handoff
    assert "READY_FOR_RUN_03_WITH_DB_VALIDATION=false" in project_state
    assert "DB post-condition validation" in acceptance
    assert "## ADR-004" in decisions and "## ADR-005" in decisions
