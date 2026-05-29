from core.common.normalization import (
    clean_text,
    escape_sql,
    normalize_customer_type,
    normalize_deadline,
    normalize_event_type,
    normalize_validations,
    slug,
)


def normalize_answers(raw_answers):
    raw_answers = raw_answers or {}
    campaign = raw_answers.get("campaign") or {}

    customer_type = normalize_customer_type(
        raw_answers.get("customer_type") or raw_answers.get("tipo_cliente")
    )
    event_type = normalize_event_type(raw_answers.get("event_type") or raw_answers.get("tipo_evento"))
    deadline_rule = normalize_deadline(raw_answers.get("deadline_rule") or raw_answers.get("prazo"))
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
        "customer_status": clean_text(raw_answers.get("customer_status") or "ativo"),
        "event_type": event_type,
        "current_offer": clean_text(raw_answers.get("current_offer") or raw_answers.get("oferta_atual")),
        "target_offer": clean_text(raw_answers.get("target_offer") or raw_answers.get("oferta_alvo")),
        "mailing_source": clean_text(raw_answers.get("mailing_source") or "upload_manual"),
        "recharge_scenario": slug(raw_answers.get("recharge_scenario") or "none"),
        "recharge_amount": clean_text(raw_answers.get("recharge_amount") or "20.00"),
        "recharge_channel": clean_text(raw_answers.get("recharge_channel") or "POS"),
        "validations": normalize_validations(raw_answers.get("validations") or raw_answers.get("validacoes")),
        "deadline_rule": deadline_rule,
    }
