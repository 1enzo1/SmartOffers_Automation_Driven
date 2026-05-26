import hashlib
import json
import re


class ScenarioValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Dados insuficientes para gerar o cenario")


CUSTOMER_LABELS = {
    "pos": "Pos-pago",
    "pre": "Pre-pago",
    "controle": "Controle",
}

DOCUMENT_LABELS = {
    "PF": "PF",
    "PJ": "PJ",
}

EVENT_LABELS = {
    "habilitacao": "Habilitacao",
    "alteracao_perfil": "Alteracao de perfil",
    "mailing": "Mailing",
    "rehab": "Reabilitacao",
    "upsell": "Upsell",
    "downgrade": "Downgrade",
}

EVENT_ALIASES = {
    "upgrade": "upsell",
    "upsell": "upsell",
    "downgrade": "downgrade",
    "rehab": "rehab",
    "reabilitacao": "rehab",
    "reabilitação": "rehab",
    "mailing": "mailing",
    "habilitacao": "habilitacao",
    "habilitação": "habilitacao",
    "alteracao_perfil": "alteracao_perfil",
    "alteração de perfil": "alteracao_perfil",
    "alteracao de perfil": "alteracao_perfil",
}

VALIDATION_LABELS = {
    "database": "Banco de dados",
    "api": "API",
    "kafka": "Kafka",
    "sms": "SMS",
    "audit": "Auditoria",
    "campaign_attributes": "Campaign Attributes",
    "received_events": "Eventos recebidos",
}

VALIDATION_ORDER = list(VALIDATION_LABELS.keys())

DEADLINE_LABELS = {
    "d0": "D+0",
    "d1": "D+1",
    "d3": "D+3",
    "future": "Agendamento futuro",
}

EVENT_RULES = {
    "habilitacao": {
        "operation": "processEvent",
        "action": "Criar cliente elegivel e processar entrada de campanha",
        "offer_strategy": "baseline",
        "expected_state": "Cliente criado e campanha vinculada",
    },
    "alteracao_perfil": {
        "operation": "processEvent",
        "action": "Alterar perfil do cliente e reprocessar elegibilidade",
        "offer_strategy": "profile_change",
        "expected_state": "Perfil atualizado sem perda de atributos da campanha",
    },
    "mailing": {
        "operation": "processMailing",
        "action": "Processar cliente de mailing para campanha",
        "offer_strategy": "mailing",
        "expected_state": "Cliente importado e elegivel pelo mailing",
    },
    "rehab": {
        "operation": "processEvent",
        "action": "Reabilitar cliente mantendo a oferta original",
        "offer_strategy": "same_rank",
        "expected_state": "Cliente reabilitado sem troca indevida de oferta",
    },
    "upsell": {
        "operation": "processEvent",
        "action": "Alterar oferta para plano de maior rank",
        "offer_strategy": "rank_up",
        "expected_state": "Cliente bonificado apenas quando houver upgrade",
    },
    "downgrade": {
        "operation": "processEvent",
        "action": "Alterar oferta para plano de menor rank",
        "offer_strategy": "rank_down",
        "expected_state": "Cliente sem bonificacao indevida em downgrade",
    },
}

OFFER_STRATEGIES = {
    "baseline": {"initial_offer": "122429157", "target_offer": "122429157"},
    "profile_change": {"initial_offer": "122429157", "target_offer": "122429137"},
    "mailing": {"initial_offer": "MAILING_LIST", "target_offer": "MAILING_LIST"},
    "same_rank": {"initial_offer": "122429157", "target_offer": "122429157"},
    "rank_up": {"initial_offer": "122429157", "target_offer": "104376082"},
    "rank_down": {"initial_offer": "104376082", "target_offer": "122429157"},
}


def generate_scenario(raw_answers):
    answers = normalize_answers(raw_answers)
    errors = validate_answers(answers)

    if errors:
        raise ScenarioValidationError(errors)

    event_rule = EVENT_RULES[answers["event_type"]]
    offer_data = OFFER_STRATEGIES[event_rule["offer_strategy"]]
    scenario_id = build_scenario_id(answers)

    payload = build_payload(answers, event_rule, offer_data)
    execution_steps = build_execution_steps(answers, event_rule, offer_data)
    validation_steps = build_validation_steps(answers)
    queries = build_queries(answers)
    checkpoints = build_checkpoints(answers, event_rule)
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


def normalize_answers(raw_answers):
    raw_answers = raw_answers or {}
    campaign = raw_answers.get("campaign") or {}

    customer_type = slug(raw_answers.get("customer_type") or raw_answers.get("tipo_cliente"))
    event_type = slug(raw_answers.get("event_type") or raw_answers.get("tipo_evento"))
    event_type = EVENT_ALIASES.get(event_type, event_type)
    deadline_rule = slug(raw_answers.get("deadline_rule") or raw_answers.get("prazo"))
    document_type = (raw_answers.get("document_type") or raw_answers.get("documento") or "").upper()

    return {
        "campaign_name": clean_text(
            raw_answers.get("campaign_name")
            or raw_answers.get("campanha")
            or campaign.get("name")
        ),
        "campaign_id": clean_text(
            raw_answers.get("campaign_id")
            or raw_answers.get("campaign_number")
            or campaign.get("id")
        ),
        "system": clean_text(raw_answers.get("system") or raw_answers.get("sistema") or "SmartOffers"),
        "objective": clean_text(raw_answers.get("objective") or raw_answers.get("objetivo")),
        "customer_type": customer_type,
        "document_type": document_type,
        "event_type": event_type,
        "validations": normalize_validations(raw_answers.get("validations") or raw_answers.get("validacoes")),
        "deadline_rule": deadline_rule,
    }


def validate_answers(answers):
    errors = {}

    required_fields = {
        "campaign_name": "Informe o nome da campanha.",
        "campaign_id": "Informe o numero/ID da campanha.",
        "objective": "Informe o objetivo da campanha.",
        "customer_type": "Selecione o tipo do cliente.",
        "document_type": "Selecione PF ou PJ.",
        "event_type": "Selecione o tipo de evento.",
        "deadline_rule": "Selecione a regra de prazo.",
    }

    for field, message in required_fields.items():
        if not answers.get(field):
            errors[field] = message

    if answers.get("customer_type") and answers["customer_type"] not in CUSTOMER_LABELS:
        errors["customer_type"] = "Tipo de cliente invalido."

    if answers.get("document_type") and answers["document_type"] not in DOCUMENT_LABELS:
        errors["document_type"] = "Documento invalido."

    if answers.get("event_type") and answers["event_type"] not in EVENT_LABELS:
        errors["event_type"] = "Tipo de evento invalido."

    if answers.get("deadline_rule") and answers["deadline_rule"] not in DEADLINE_LABELS:
        errors["deadline_rule"] = "Regra de prazo invalida."

    if not answers.get("validations"):
        errors["validations"] = "Selecione ao menos uma validacao."

    invalid_validations = [item for item in answers.get("validations", []) if item not in VALIDATION_LABELS]
    if invalid_validations:
        errors["validations"] = f"Validacoes invalidas: {', '.join(invalid_validations)}."

    return errors


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
    ext_event_id = 866231225 if is_pre else 986557550
    document_code = "2" if answers["document_type"] == "PJ" else "1"

    attributes = {
        "campaignId": answers["campaign_id"],
        "campaignName": answers["campaign_name"],
        "customerSegment": customer_type.upper(),
        "documentType": document_code,
        "clientType": client_type,
        "msisdn": "{{msisdn}}",
        "account": "{{account}}",
        "externalId": f"{account_prefix}_{{{{account}}}}",
        "initialOffer": offer_data["initial_offer"],
        "targetOffer": offer_data["target_offer"],
        "deadlineRule": answers["deadline_rule"],
        "objective": answers["objective"],
    }

    if answers["event_type"] == "mailing":
        attributes["mailingSource"] = "manual-upload"
        attributes["mailingKey"] = f"MAIL_{answers['campaign_id']}_{{{{msisdn}}}}"

    return {
        "operation": event_rule["operation"],
        "extEventId": ext_event_id,
        "eventTime": "{{event_time}}",
        "eventType": answers["event_type"],
        "system": answers["system"],
        "attributes": attributes,
    }


def build_execution_steps(answers, event_rule, offer_data):
    event_label = EVENT_LABELS[answers["event_type"]]
    deadline = DEADLINE_LABELS[answers["deadline_rule"]]

    steps = [
        {
            "step": 1,
            "action": "Preparar massa de cliente",
            "details": (
                f"Gerar MSISDN, account e externalId para cliente "
                f"{CUSTOMER_LABELS[answers['customer_type']]}/{answers['document_type']}."
            ),
            "expected_result": "Dados obrigatorios disponiveis para montar o payload.",
        },
        {
            "step": 2,
            "action": "Montar payload SmartOffers",
            "details": f"Usar operation {event_rule['operation']} e evento {event_label}.",
            "expected_result": "Payload JSON preenchido com campanha, cliente, oferta e prazo.",
        },
        {
            "step": 3,
            "action": event_rule["action"],
            "details": (
                f"Oferta inicial {offer_data['initial_offer']} e oferta alvo "
                f"{offer_data['target_offer']}."
            ),
            "expected_result": event_rule["expected_state"],
        },
        {
            "step": 4,
            "action": "Registrar evidencias",
            "details": f"Salvar request, response e dados de validacao respeitando prazo {deadline}.",
            "expected_result": "Pacote de evidencias pronto para analise.",
        },
    ]

    if answers["event_type"] == "mailing":
        steps.insert(
            2,
            {
                "step": 3,
                "action": "Preparar arquivo/lista de mailing",
                "details": "Usar a chave de mailing gerada no payload como identificador de importacao.",
                "expected_result": "Cliente disponivel para processamento por mailing.",
            },
        )
        resequence(steps)

    return steps


def build_validation_steps(answers):
    steps = []
    validations = answers["validations"]

    templates = {
        "api": (
            "Validar resposta da API",
            "Conferir status HTTP, body.result e identificadores retornados.",
            "API aceita o evento sem erro funcional.",
        ),
        "database": (
            "Validar persistencia em banco",
            "Consultar CUST_DISCOVERY e CUST_CAMPAIGNS pelo externalId/customerId.",
            "Cliente encontrado e vinculado a campanha esperada.",
        ),
        "campaign_attributes": (
            "Validar Campaign Attributes",
            "Conferir atributos gravados para o contrato da campanha.",
            "Atributos refletem campanha, oferta, prazo e tipo de cliente.",
        ),
        "audit": (
            "Validar auditoria",
            "Consultar ACM_AUDIT_RECORDS por customerId/contractId.",
            "Evento auditado com estado esperado.",
        ),
        "kafka": (
            "Validar Kafka",
            "Pesquisar chave do evento nos topicos de entrada e saida.",
            "Mensagem publicada sem duplicidade ou erro de schema.",
        ),
        "sms": (
            "Validar SMS",
            "Conferir fila/log de envio para MSISDN da massa.",
            "Mensagem enviada apenas quando a regra da campanha exigir.",
        ),
        "received_events": (
            "Validar eventos recebidos",
            "Conferir historico de eventos por externalId.",
            "Evento recebido e correlacionado com a campanha.",
        ),
    }

    for validation in validations:
        title, details, expected = templates[validation]
        steps.append(
            {
                "step": len(steps) + 1,
                "validation": title,
                "details": details,
                "expected_result": expected,
            }
        )

    return steps


def build_queries(answers):
    campaign_id = escape_sql(answers["campaign_id"])
    queries = []

    if "database" in answers["validations"]:
        queries.append(
            {
                "name": "customer_discovery",
                "kind": "sql",
                "purpose": "Localizar cliente processado pelo externalId.",
                "sql": (
                    "SELECT * FROM CUST_DISCOVERY "
                    "WHERE EXTERNAL_ID = :external_id"
                ),
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
                "sql": (
                    "SELECT * FROM ACM_RECEIVED_EVENTS "
                    "WHERE EXTERNAL_ID = :external_id"
                ),
            }
        )

    if "sms" in answers["validations"]:
        queries.append(
            {
                "name": "sms_dispatch",
                "kind": "sql",
                "purpose": "Conferir tentativa de envio de SMS.",
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

    return queries


def build_checkpoints(answers, event_rule):
    checkpoints = [
        f"Campanha {answers['campaign_id']} corresponde ao nome {answers['campaign_name']}.",
        f"Evento usado: {EVENT_LABELS[answers['event_type']]}.",
        f"Prazo esperado: {DEADLINE_LABELS[answers['deadline_rule']]}.",
        event_rule["expected_state"],
    ]

    for validation in answers["validations"]:
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
    }

    for validation in answers["validations"]:
        files.append(validation_files[validation])

    files.append("resumo_analise.json")
    return list(dict.fromkeys(files))


def build_warnings(answers):
    warnings = []

    if answers["customer_type"] == "controle":
        warnings.append("Cliente Controle usa payload base POS no MVP.")

    if answers["deadline_rule"] == "future":
        warnings.append("Agendamento futuro exige conferir data/hora real antes da execucao.")

    if answers["event_type"] == "mailing" and "database" not in answers["validations"]:
        warnings.append("Mailing sem validacao de banco pode dificultar prova de elegibilidade.")

    if "api" not in answers["validations"]:
        warnings.append("Cenario gerado sem validacao explicita de resposta da API.")

    return warnings


def normalize_validations(value):
    if value is None:
        return []

    if isinstance(value, str):
        raw_values = [item.strip() for item in value.split(",")]
    else:
        raw_values = list(value)

    normalized = {slug(item) for item in raw_values if str(item).strip()}
    return [item for item in VALIDATION_ORDER if item in normalized] + sorted(
        item for item in normalized if item not in VALIDATION_ORDER
    )


def resequence(steps):
    for index, step in enumerate(steps, start=1):
        step["step"] = index


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def slug(value):
    value = clean_text(value).lower()
    value = value.replace("-", "_").replace(" ", "_")
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def escape_sql(value):
    return clean_text(value).replace("'", "''")
