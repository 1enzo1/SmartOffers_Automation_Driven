from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROADMAP_ITEMS = [
    "MVP7.6.1 - Guardrails e documentacao de arquitetura",
    "MVP7.6.2 - Ontologia SmartOffers",
    "MVP7.6.3 - Playbooks operacionais",
    "MVP7.6.4 - Evidence Planner",
    "MVP7.6.5 - AI Supervisors Foundation",
    "MVP7.6.6 - Scenario Intelligence Layer",
    "MVP7.6.7 - Adapter Risk Classifier",
    "MVP7.7 - Primeira chamada real opt-in em QA4",
    "MVP8 - Runner controlado com fila/status",
    "MVP9 - IA auxiliar local-first",
    "MVP10 - Frontend moderno",
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
