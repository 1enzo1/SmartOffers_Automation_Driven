import re


DOMAIN = "smartoffers"

KNOWN_EVIDENCE_LAYERS = (
    "customer_discovery",
    "campaign_contract",
    "campaign_attributes",
    "received_events",
    "audit_records",
    "sms_dispatch",
    "kafka_trace",
    "schedule_checkpoint",
    "expected_evidence_manifest",
)

BASE_SUPERVISORS = (
    "smartoffers-architect-supervisor",
    "safety-supervisor",
)

STATUS_PRECEDENCE = {
    "mock": 0,
    "read-only": 1,
    "future-controlled": 2,
    "blocked": 3,
}

BLOCKED_PATTERNS = (
    re.compile(r"\bmode\s*[=:]\s*real\b", re.IGNORECASE),
    re.compile(r"\bmode\b.*\breal\b", re.IGNORECASE),
    re.compile(r"\bsafe_for_real_execution\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE),
    re.compile(r"\breal_execution\b[\"']?\s*(?:[=:]\s*)?\btrue\b", re.IGNORECASE),
    re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    re.compile(r"\bhost\s*[=:]\s*[A-Za-z0-9.-]+\b", re.IGNORECASE),
    re.compile(r"\breal_host\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bcredential\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bsenha\b", re.IGNORECASE),
    re.compile(r"\breal_payload\b", re.IGNORECASE),
    re.compile(r"\bpayload real\b", re.IGNORECASE),
    re.compile(r"\bexternal_call\b", re.IGNORECASE),
)

FUTURE_PATTERNS = (
    re.compile(r"\bfuture-controlled\b", re.IGNORECASE),
    re.compile(r"\bfuture controlled\b", re.IGNORECASE),
    re.compile(r"\bfuturo controlado\b", re.IGNORECASE),
    re.compile(r"\bopt-in futuro\b", re.IGNORECASE),
)


def analyze_scenario(scenario):
    """Return a deterministic, read-only conceptual analysis for a scenario."""
    if not isinstance(scenario, dict):
        scenario = {}

    source_answers = _dict_value(scenario.get("source_answers"))
    payload = _dict_value(scenario.get("payload"))
    payload_attributes = _dict_value(payload.get("attributes"))
    queries = _list_value(scenario.get("queries"))

    event_type = _first_text(source_answers.get("event_type"), payload.get("eventType"))
    evidence_layers = _evidence_layers(queries)
    query_names = _query_names(queries)
    main_flow = _main_flow(event_type)
    playbooks = _suggested_playbooks(event_type, evidence_layers)
    relevant_entities = _relevant_entities(
        event_type=event_type,
        evidence_layers=evidence_layers,
        payload=payload,
        payload_attributes=payload_attributes,
        query_names=query_names,
    )
    supervisors = _suggested_supervisors(
        evidence_layers=evidence_layers,
        playbooks=playbooks,
        query_names=query_names,
        payload=payload,
    )
    risks = _risks(scenario, evidence_layers)
    overall_status = _overall_status(evidence_layers, risks)

    return {
        "scenario_id": _text(scenario.get("id")),
        "domain": DOMAIN,
        "main_flow": main_flow,
        "event_type": event_type,
        "relevant_entities": relevant_entities,
        "suggested_playbooks": playbooks,
        "expected_evidence_layers": evidence_layers,
        "suggested_supervisors": supervisors,
        "risks": risks,
        "overall_status": overall_status,
    }


def _dict_value(value):
    return value if isinstance(value, dict) else {}


def _list_value(value):
    return value if isinstance(value, list) else []


def _text(value):
    if value is None:
        return ""
    return str(value)


def _first_text(*values):
    for value in values:
        text = _text(value).strip()
        if text:
            return text
    return ""


def _dedupe_ordered(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _query_names(queries):
    names = []
    for query in queries:
        if isinstance(query, dict):
            names.append(_text(query.get("name")))
    return _dedupe_ordered(names)


def _evidence_layers(queries):
    query_names = set(_query_names(queries))
    return [layer for layer in KNOWN_EVIDENCE_LAYERS if layer in query_names]


def _main_flow(event_type):
    flows = {
        "habilitacao": "customer_activation",
        "alteracao_perfil": "profile_change",
        "mailing": "mailing_import",
        "recarga": "prepaid_recharge",
        "rehab": "customer_rehabilitation",
        "upsell": "offer_upgrade",
        "downgrade": "offer_downgrade",
    }
    return flows.get(event_type, "unknown")


def _suggested_playbooks(event_type, evidence_layers):
    suggestions = []

    if event_type == "recarga" and "sms_dispatch" in evidence_layers:
        suggestions.append("sms-not-sent.md")
    if event_type == "mailing":
        suggestions.append("customer-not-in-campaign.md")
    if event_type in {"upsell", "downgrade"}:
        suggestions.append("benefit-or-offer-not-updated.md")
    if event_type in {"rehab", "alteracao_perfil"}:
        suggestions.append("campaign-stuck-in-state.md")
    if "kafka_trace" in evidence_layers:
        suggestions.append("callback-not-reflected.md")
    if "schedule_checkpoint" in evidence_layers:
        suggestions.append("processing-backlog-or-delay.md")
    if "expected_evidence_manifest" in evidence_layers:
        suggestions.append("evidence-mismatch.md")

    return _dedupe_ordered(suggestions)


def _relevant_entities(event_type, evidence_layers, payload, payload_attributes, query_names):
    entities = ["cliente", "campanha"]

    if event_type:
        entities.append("evento")
    if payload or payload_attributes:
        entities.extend(["caracteristica", "integracao"])
    if {"campaign_contract", "campaign_attributes"} & set(evidence_layers):
        entities.extend(["campanha", "caracteristica"])
    if {"received_events", "schedule_checkpoint", "kafka_trace"} & set(evidence_layers):
        entities.extend(["evento", "processamento", "integracao"])
    if "audit_records" in evidence_layers:
        entities.append("auditoria")
    if "sms_dispatch" in evidence_layers:
        entities.append("integracao")
    if evidence_layers or "expected_evidence_manifest" in query_names:
        entities.append("evidencia")

    return _dedupe_ordered(entities)


def _suggested_supervisors(evidence_layers, playbooks, query_names, payload):
    supervisors = list(BASE_SUPERVISORS)

    if payload or {"campaign_contract", "campaign_attributes"} & set(evidence_layers):
        supervisors.append("campaign-supervisor")
    if evidence_layers:
        supervisors.append("evidence-supervisor")
    if playbooks:
        supervisors.append("troubleshooting-supervisor")
    if (
        "api_contract" in query_names
        or "request_plan" in query_names
        or "kafka_trace" in evidence_layers
        or _payload_operation(payload)
    ):
        supervisors.append("adapter-supervisor")
    if {"campaign_contract", "campaign_attributes"} & set(evidence_layers):
        supervisors.append("catalog-config-supervisor")

    return _dedupe_ordered(supervisors)


def _payload_operation(payload):
    operation = _text(payload.get("operation"))
    return bool(operation)


def _risks(scenario, evidence_layers=None):
    text = _flatten_text(scenario)
    risks = []

    if any(pattern.search(text) for pattern in BLOCKED_PATTERNS):
        risks.append(
            {
                "code": "blocked_real_execution_signal",
                "status": "blocked",
                "reason": "Scenario contains signal of real execution, sensitive data, or external dependency.",
            }
        )

    if any(pattern.search(text) for pattern in FUTURE_PATTERNS):
        risks.append(
            {
                "code": "future_controlled_signal",
                "status": "future-controlled",
                "reason": "Scenario references future controlled execution without enabling it.",
            }
        )

    if evidence_layers and "kafka_trace" in evidence_layers:
        risks.append(
            {
                "code": "future_controlled_kafka_trace",
                "status": "future-controlled",
                "reason": "Kafka trace is conceptual in this MVP and requires future controlled guardrails.",
            }
        )

    return risks


def _flatten_text(value):
    parts = []

    def visit(item):
        if isinstance(item, dict):
            for key in sorted(item):
                parts.append(_text(key))
                visit(item[key])
        elif isinstance(item, list):
            for entry in item:
                visit(entry)
        else:
            parts.append(_text(item))

    visit(value)
    return " ".join(parts)


def _overall_status(evidence_layers, risks):
    statuses = ["mock"]

    if evidence_layers:
        statuses.append("read-only")

    for risk in risks:
        status = risk.get("status") if isinstance(risk, dict) else None
        if status in STATUS_PRECEDENCE:
            statuses.append(status)

    return max(statuses, key=lambda item: STATUS_PRECEDENCE[item])
