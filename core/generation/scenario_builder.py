import hashlib
import json
import re

from .constants import (
    CUSTOMER_EVENT_IDS,
    CUSTOMER_LABELS,
    DEADLINE_LABELS,
    EVENT_EVENT_IDS,
    EVENT_LABELS,
    EVENT_RULES,
    OFFER_STRATEGIES,
    SCHEDULED_DEADLINES,
    VALIDATION_LABELS,
    VALIDATION_ORDER,
)
from .normalization import escape_sql
from .templates import (
    BASE_EXECUTION_BLOCK,
    EVENT_EXECUTION_BLOCKS,
    FINAL_EXECUTION_BLOCK,
    PREPAID_RECHARGE_CONTEXT_BLOCK,
    SCHEDULE_EXECUTION_BLOCK,
    VALIDATION_BLOCKS,
)


def build_scenario(answers):
    event_rule = EVENT_RULES[answers["event_type"]]
    offer_data = resolve_offer_data(answers, event_rule)
    scenario_id = build_scenario_id(answers)

    payload = build_payload(answers, event_rule, offer_data)
    execution_steps = build_execution_steps(answers, event_rule, offer_data)
    validation_steps = build_validation_steps(answers, offer_data)
    queries = build_queries(answers)
    checkpoints = build_checkpoints(answers, event_rule, offer_data)
    evidence_files = build_evidence_files(answers)
    warnings = build_warnings(answers)

    event_label = EVENT_LABELS[answers["event_type"]]
    customer_label = CUSTOMER_LABELS[answers["customer_type"]]

    return {
        "id": scenario_id,
        "titulo": f"{answers['campaign_name']} - {customer_label} {event_label}",
        "resumo": (
            f"Cenario gerado para campanha {answers['campaign_id']} "
            f"({answers['campaign_name']}) com evento {event_label}, "
            f"cliente {customer_label}/{answers['document_type']} e prazo "
            f"{DEADLINE_LABELS[answers['deadline_rule']]}."
        ),
        "execution_steps": execution_steps,
        "validation_steps": validation_steps,
        "payload": payload,
        "queries": queries,
        "checkpoints": checkpoints,
        "evidence_files": evidence_files,
        "warnings": warnings,
        "source_answers": answers,
    }


def resolve_offer_data(answers, event_rule):
    strategy = OFFER_STRATEGIES[event_rule["offer_strategy"]]
    return {
        "initial_offer": answers.get("current_offer") or strategy["initial_offer"],
        "target_offer": answers.get("target_offer") or strategy["target_offer"],
    }


def build_scenario_id(answers):
    canonical = json.dumps(answers, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
    name = re.sub(r"[^a-z0-9]+", "-", answers["campaign_name"].lower()).strip("-")
    name = name[:32].strip("-") or "smartoffers"
    return f"{name}-{answers['event_type']}-{digest}"


def build_payload(answers, event_rule, offer_data):
    customer_type = answers["customer_type"]
    is_pre = customer_type == "pre"
    account_prefix = "NGIN" if is_pre else "NEXT"
    client_type = "1" if is_pre else "2"
    document_code = "2" if answers["document_type"] == "PJ" else "1"

    attributes = {
        "campaignId": answers["campaign_id"],
        "campaignName": answers["campaign_name"],
        "customerSegment": customer_type.upper(),
        "documentType": document_code,
        "clientType": client_type,
        "customerStatus": answers["customer_status"],
        "msisdn": "{{msisdn}}",
        "account": "{{account}}",
        "externalId": f"{account_prefix}_{{{{account}}}}",
        "initialOffer": offer_data["initial_offer"],
        "targetOffer": offer_data["target_offer"],
        "deadlineRule": answers["deadline_rule"],
        "objective": answers["objective"],
    }

    if answers["event_type"] == "mailing":
        attributes["mailingSource"] = answers["mailing_source"]
        attributes["mailingKey"] = f"MAIL_{answers['campaign_id']}_{{{{msisdn}}}}"
        attributes["batchId"] = f"BATCH_{answers['campaign_id']}_{{{{execution_date}}}}"

    if answers["event_type"] == "recarga" or answers["recharge_scenario"] != "none":
        attributes["rechargeScenario"] = answers["recharge_scenario"]
        attributes["rechargeAmount"] = answers["recharge_amount"]
        attributes["rechargeChannel"] = answers["recharge_channel"]
        attributes["rechargeCorrelationId"] = "REC_{{msisdn}}_{{event_time}}"

    if answers["event_type"] in {"alteracao_perfil", "upsell", "downgrade", "rehab"}:
        attributes["profileBeforeOffer"] = offer_data["initial_offer"]
        attributes["profileAfterOffer"] = offer_data["target_offer"]

    if is_scheduled(answers):
        attributes["scheduleCheckpoint"] = f"{DEADLINE_LABELS[answers['deadline_rule']]} after eventTime"

    return {
        "operation": event_rule["operation"],
        "extEventId": EVENT_EVENT_IDS.get(answers["event_type"], CUSTOMER_EVENT_IDS[customer_type]),
        "eventTime": "{{event_time}}",
        "eventType": answers["event_type"],
        "system": answers["system"],
        "attributes": attributes,
    }


def build_execution_steps(answers, event_rule, offer_data):
    context = build_context(answers, event_rule, offer_data)
    blocks = list(BASE_EXECUTION_BLOCK)

    if answers["customer_type"] == "pre" and answers["recharge_scenario"] != "none":
        blocks.extend(PREPAID_RECHARGE_CONTEXT_BLOCK)

    blocks.extend(EVENT_EXECUTION_BLOCKS[answers["event_type"]])

    if is_scheduled(answers):
        blocks.extend(SCHEDULE_EXECUTION_BLOCK)

    blocks.extend(FINAL_EXECUTION_BLOCK)
    return resequence(render_block(blocks, context, "action"))


def build_validation_steps(answers, offer_data):
    context = build_context(answers, EVENT_RULES[answers["event_type"]], offer_data)
    steps = []

    for validation in effective_validations(answers):
        steps.extend(render_block(VALIDATION_BLOCKS[validation], context, "validation"))

    return resequence(steps)


def build_queries(answers):
    campaign_id = escape_sql(answers["campaign_id"])
    queries = []

    if "api" in answers["validations"]:
        queries.append(
            {
                "name": "api_contract",
                "kind": "http_plan",
                "purpose": "Conferir contrato do request planejado.",
                "request": "POST /smartoffers/{{operation}}",
            }
        )

    if "database" in answers["validations"]:
        queries.append(
            {
                "name": "customer_discovery",
                "kind": "sql",
                "purpose": "Localizar cliente processado pelo externalId.",
                "sql": "SELECT * FROM CUST_DISCOVERY WHERE EXTERNAL_ID = :external_id",
            }
        )
        queries.append(
            {
                "name": "campaign_contract",
                "kind": "sql",
                "purpose": "Confirmar vinculo com a campanha gerada.",
                "sql": (
                    "SELECT * FROM CUST_CAMPAIGNS "
                    "WHERE ID_CUSTOMER = :id_customer "
                    f"AND ID_CAMPAIGN = '{campaign_id}'"
                ),
            }
        )

    if "campaign_attributes" in answers["validations"]:
        queries.append(
            {
                "name": "campaign_attributes",
                "kind": "sql",
                "purpose": "Conferir atributos da campanha no contrato.",
                "sql": (
                    "SELECT * FROM CUST_CAMPAIGN_CHARACTERISTICS "
                    "WHERE ID_CAMPAIGN_CONTRACT = :id_contract"
                ),
            }
        )

    if "audit" in answers["validations"]:
        queries.append(
            {
                "name": "audit_records",
                "kind": "sql",
                "purpose": "Conferir registros de auditoria do fluxo.",
                "sql": (
                    "SELECT * FROM ACM_AUDIT_RECORDS "
                    "WHERE CUSTOMER_ID = :id_customer "
                    "AND CONTRACT_ID = :id_contract"
                ),
            }
        )

    if "received_events" in answers["validations"]:
        queries.append(
            {
                "name": "received_events",
                "kind": "sql",
                "purpose": "Conferir historico de eventos recebidos.",
                "sql": "SELECT * FROM ACM_RECEIVED_EVENTS WHERE EXTERNAL_ID = :external_id",
            }
        )

    if "sms" in answers["validations"]:
        queries.append(
            {
                "name": "sms_dispatch",
                "kind": "sql",
                "purpose": "Conferir tentativa de envio de SMS/mensagem.",
                "sql": "SELECT * FROM ACM_SMS_DISPATCH WHERE MSISDN = :msisdn",
            }
        )

    if "kafka" in answers["validations"]:
        queries.append(
            {
                "name": "kafka_trace",
                "kind": "kafka",
                "purpose": "Pesquisar mensagens publicadas por chave de correlacao.",
                "lookup": "key={{external_id}} topic=smartoffers.*",
            }
        )

    if is_scheduled(answers) or "schedule" in answers["validations"]:
        queries.append(
            {
                "name": "schedule_checkpoint",
                "kind": "sql",
                "purpose": "Conferir agendamento planejado para prazo futuro.",
                "sql": (
                    "SELECT * FROM ACM_SCHEDULED_ACTIONS "
                    "WHERE EXTERNAL_ID = :external_id "
                    "AND ID_CAMPAIGN = :campaign_id"
                ),
            }
        )

    queries.append(
        {
            "name": "expected_evidence_manifest",
            "kind": "manifest",
            "purpose": "Lista de evidencias que devem existir apos a execucao manual.",
            "files": build_evidence_files(answers),
        }
    )

    return queries


def build_checkpoints(answers, event_rule, offer_data):
    checkpoints = [
        f"Campanha {answers['campaign_id']} corresponde ao nome {answers['campaign_name']}.",
        f"Evento usado: {EVENT_LABELS[answers['event_type']]}.",
        f"Prazo esperado: {DEADLINE_LABELS[answers['deadline_rule']]}.",
        (
            f"Transicao de oferta planejada: "
            f"{offer_data['initial_offer']} -> {offer_data['target_offer']}."
        ),
        event_rule["expected_state"],
    ]

    if answers["event_type"] == "recarga" or answers["recharge_scenario"] != "none":
        checkpoints.append(
            f"Recarga planejada: valor {answers['recharge_amount']} no canal {answers['recharge_channel']}."
        )

    if is_scheduled(answers):
        checkpoints.append(
            f"Checkpoint de agendamento obrigatorio para {DEADLINE_LABELS[answers['deadline_rule']]}."
        )

    for validation in effective_validations(answers):
        checkpoints.append(f"Validacao obrigatoria: {VALIDATION_LABELS[validation]}.")

    return checkpoints


def build_evidence_files(answers):
    files = [
        "01_payload_request.json",
        "02_api_response.json",
        "03_execution_summary.json",
    ]

    validation_files = {
        "database": "04_database_validation.json",
        "campaign_attributes": "05_campaign_attributes.json",
        "audit": "06_audit_records.json",
        "kafka": "07_kafka_trace.json",
        "sms": "08_sms_dispatch.json",
        "received_events": "09_received_events.json",
        "api": "10_api_contract_validation.json",
        "schedule": "11_schedule_checkpoint.json",
        "evidence": "12_expected_evidence_manifest.json",
    }

    for validation in effective_validations(answers):
        files.append(validation_files[validation])

    files.append("resumo_analise.json")
    return list(dict.fromkeys(files))


def build_warnings(answers):
    warnings = []

    if answers["customer_type"] == "controle":
        warnings.append("Cliente Controle usa payload base POS no MVP.")

    if is_scheduled(answers):
        warnings.append("Prazo futuro exige conferir o checkpoint antes de concluir o teste.")

    if answers["event_type"] == "mailing" and "database" not in answers["validations"]:
        warnings.append("Mailing sem validacao de banco pode dificultar prova de elegibilidade.")

    if answers["event_type"] == "recarga" and "sms" not in answers["validations"]:
        warnings.append("Recarga sem validacao de SMS/mensagem pode perder prova de comunicacao.")

    if "api" not in answers["validations"]:
        warnings.append("Cenario gerado sem validacao explicita de resposta da API.")

    return warnings


def effective_validations(answers):
    validations = list(answers["validations"])

    if is_scheduled(answers):
        validations.append("schedule")

    validations.append("evidence")

    unique = set(validations)
    return [item for item in VALIDATION_ORDER if item in unique]


def build_context(answers, event_rule, offer_data):
    return {
        **answers,
        **offer_data,
        "customer_label": CUSTOMER_LABELS[answers["customer_type"]],
        "event_label": EVENT_LABELS[answers["event_type"]],
        "deadline_label": DEADLINE_LABELS[answers["deadline_rule"]],
        "operation": event_rule["operation"],
    }


def render_block(block, context, title_key):
    rendered = []

    for item in block:
        rendered.append(
            {
                title_key: render_text(item[title_key], context),
                "details": render_text(item["details"], context),
                "expected_result": render_text(item["expected_result"], context),
            }
        )

    return rendered


def render_text(value, context):
    return value.format_map(SafeFormatDict(context))


def is_scheduled(answers):
    return answers["deadline_rule"] in SCHEDULED_DEADLINES


def resequence(steps):
    for index, step in enumerate(steps, start=1):
        step["step"] = index
    return steps


class SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"
