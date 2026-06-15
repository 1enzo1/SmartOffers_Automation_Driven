from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROADMAP_ITEMS = [
    "MVP7.8.3 - Runtime Preflight & First QA4 Real Smoke",
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


def test_current_real_execution_plan_is_documented():
    docs = "\n".join([_read("README.md"), _read("PROJECT_STATUS.md"), _read("docs/ROADMAP.md")])

    required_fragments = [
        "MVP atual concluido: MVP7.8.2",
        "Ultimo MVP aprovado: MVP7.8.2 - Real QA Runtime Binding & Legacy Config Externalization",
        "de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71",
        "QA4 e prioridade",
        "QA1 vem depois",
        "QA2/QA3",
        "real QA4 executavel: 2 a 3 dias uteis",
        "sanity real padrao/variante/copy: 4 a 5 dias uteis",
        "primeiros cenarios reais: 7 a 10 dias uteis",
        "v0.1 estavel interna: 15 a 20 dias uteis",
    ]

    for fragment in required_fragments:
        assert fragment in docs


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
