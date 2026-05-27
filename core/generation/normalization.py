import re
import unicodedata

from .constants import (
    DEADLINE_ALIASES,
    EVENT_ALIASES,
    VALIDATION_ALIASES,
    VALIDATION_ORDER,
)


def normalize_answers(raw_answers):
    raw_answers = raw_answers or {}
    campaign = raw_answers.get("campaign") or {}

    customer_type = slug(raw_answers.get("customer_type") or raw_answers.get("tipo_cliente"))
    event_type = slug(raw_answers.get("event_type") or raw_answers.get("tipo_evento"))
    event_type = EVENT_ALIASES.get(event_type, event_type)
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


def normalize_deadline(value):
    normalized = slug(value)
    return DEADLINE_ALIASES.get(normalized, normalized)


def normalize_validations(value):
    if value is None:
        return []

    if isinstance(value, str):
        raw_values = [item.strip() for item in value.split(",")]
    else:
        raw_values = list(value)

    normalized = set()
    for item in raw_values:
        key = slug(item)
        if key:
            normalized.add(VALIDATION_ALIASES.get(key, key))

    return [item for item in VALIDATION_ORDER if item in normalized] + sorted(
        item for item in normalized if item not in VALIDATION_ORDER
    )


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def slug(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.replace("+", "")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def escape_sql(value):
    return clean_text(value).replace("'", "''")
