import re
import unicodedata


EVENT_ALIASES = {
    "upgrade": "upsell",
    "upsell": "upsell",
    "downgrade": "downgrade",
    "rehab": "rehab",
    "reabilitacao": "rehab",
    "mailing": "mailing",
    "recarga": "recarga",
    "recharge": "recarga",
    "habilitacao": "habilitacao",
    "alteracao_perfil": "alteracao_perfil",
    "alteracao_de_perfil": "alteracao_perfil",
}

CUSTOMER_TYPE_ALIASES = {
    "controle": "controle",
    "pos": "pos",
    "pos_pago": "pos",
    "pospago": "pos",
    "pre": "pre",
    "pre_pago": "pre",
    "prepago": "pre",
}

VALIDATION_ALIASES = {
    "db": "database",
    "banco": "database",
    "banco_de_dados": "database",
    "api": "api",
    "campaign_attributes": "campaign_attributes",
    "attributes": "campaign_attributes",
    "auditoria": "audit",
    "audit": "audit",
    "sms": "sms",
    "mensagem": "sms",
    "mensageria": "sms",
    "received_events": "received_events",
    "eventos_recebidos": "received_events",
    "kafka": "kafka",
    "agendamento": "schedule",
    "schedule": "schedule",
    "evidencias": "evidence",
    "evidence": "evidence",
}

VALIDATION_ORDER = [
    "database",
    "api",
    "campaign_attributes",
    "audit",
    "sms",
    "received_events",
    "kafka",
    "schedule",
    "evidence",
]

DEADLINE_ALIASES = {
    "d0": "d0",
    "d_0": "d0",
    "0": "d0",
    "d1": "d1",
    "d_1": "d1",
    "1": "d1",
    "d3": "d3",
    "d_3": "d3",
    "3": "d3",
    "d5": "d5",
    "d_5": "d5",
    "5": "d5",
    "d7": "d7",
    "d_7": "d7",
    "7": "d7",
    "future": "future",
    "futuro": "future",
    "agendamento_futuro": "future",
}


def normalize_event_type(value):
    return normalize_lookup_value(value, EVENT_ALIASES)


def normalize_customer_type(value):
    return normalize_lookup_value(value, CUSTOMER_TYPE_ALIASES)


def normalize_deadline(value):
    return normalize_lookup_value(value, DEADLINE_ALIASES)


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


def normalize_lookup_value(value, aliases):
    normalized = slug(value)
    return aliases.get(normalized, normalized)


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
