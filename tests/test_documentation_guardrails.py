from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

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
    assert "todo transporte real permanecem universalmente\nbloqueados" in architect
    assert "mode=real` não deve ser universalmente permitido" not in architect
    assert "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01" in architect
    assert "API_QA4_TECHNICAL_NON_MUTATING_01" not in architect

    assert "Tester/Reviewer" in manager
    assert "No estado Alpha\natual, Oracle, API, Kafka e Jenkins reais permanecem bloqueados" in manager
    assert "o Dev nao aprova a propria entrega como\nindependente" in developer

    assert "CONTRACT_CONFLICT-001" in governance
    assert "nao\ninferir um bypass a partir de evidencia historica" in governance


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
