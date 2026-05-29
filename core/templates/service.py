from copy import deepcopy

from core.common.normalization import (
    clean_text,
    normalize_customer_type,
    normalize_deadline,
    normalize_event_type,
)

from .catalog import CATEGORY_LABELS, CATEGORY_ORDER, TEMPLATE_LIBRARY


_TEMPLATES_BY_ID = {template["id"]: template for template in TEMPLATE_LIBRARY}

CANONICAL_FIELD_ALIASES = {
    "campanha": "campaign_name",
    "campaign_number": "campaign_id",
    "sistema": "system",
    "objetivo": "objective",
    "tipo_cliente": "customer_type",
    "documento": "document_type",
    "tipo_evento": "event_type",
    "oferta_atual": "current_offer",
    "oferta_alvo": "target_offer",
    "validacoes": "validations",
    "prazo": "deadline_rule",
}


class TemplateNotFoundError(ValueError):
    def __init__(self, template_id):
        self.template_id = template_id
        super().__init__(f"Template nao encontrado: {template_id}")


def list_templates(category=None, event_type=None, customer_type=None):
    category = clean_text(category)
    event_type = normalize_event_type(event_type)
    customer_type = normalize_customer_type(customer_type)

    templates = []
    for template in TEMPLATE_LIBRARY:
        if category and template["categoria"] != category:
            continue
        if event_type and event_type not in template["eventos_suportados"]:
            continue
        if customer_type and customer_type not in template["tipos_cliente_suportados"]:
            continue
        templates.append(public_template(template, include_defaults=False))

    return templates


def list_template_categories():
    counts = {category: 0 for category in CATEGORY_ORDER}
    for template in TEMPLATE_LIBRARY:
        counts[template["categoria"]] = counts.get(template["categoria"], 0) + 1

    return [
        {
            "id": category,
            "nome": CATEGORY_LABELS.get(category, category),
            "template_count": counts[category],
        }
        for category in CATEGORY_ORDER
        if counts.get(category)
    ]


def get_template(template_id):
    template = _TEMPLATES_BY_ID.get(clean_text(template_id))
    if not template:
        return None
    return public_template(template, include_defaults=True)


def apply_template_defaults(raw_answers):
    raw_answers = raw_answers or {}
    template_value = raw_answers.get("template_id") or raw_answers.get("template")
    if isinstance(template_value, dict):
        template_value = template_value.get("id")
    template_id = clean_text(template_value)

    if not template_id:
        return deepcopy(raw_answers), None

    raw_answers = canonicalize_alias_overrides(raw_answers)
    template = _TEMPLATES_BY_ID.get(template_id)
    if not template:
        raise TemplateNotFoundError(template_id)

    merged = deepcopy(template.get("default_answers", {}))
    for key, value in raw_answers.items():
        if key in {"template", "template_id"}:
            continue
        if has_value(value):
            if key == "event_type" and not template_supports_event(template, value):
                continue
            if key == "customer_type" and not template_supports_customer_type(template, value):
                continue
            merged[key] = value

    merged["template_id"] = template_id
    return merged, public_template(template, include_defaults=False)


def canonicalize_alias_overrides(raw_answers):
    normalized = deepcopy(raw_answers)

    campaign = normalized.get("campaign")
    if isinstance(campaign, dict):
        if not has_value(normalized.get("campaign_name")) and has_value(campaign.get("name")):
            normalized["campaign_name"] = campaign["name"]
        if not has_value(normalized.get("campaign_id")) and has_value(campaign.get("id")):
            normalized["campaign_id"] = campaign["id"]

    for alias, canonical in CANONICAL_FIELD_ALIASES.items():
        if has_value(normalized.get(alias)) and not has_value(normalized.get(canonical)):
            normalized[canonical] = normalized[alias]

    if has_value(normalized.get("event_type")):
        normalized["event_type"] = normalize_event_type(normalized["event_type"])
    if has_value(normalized.get("customer_type")):
        normalized["customer_type"] = normalize_customer_type(normalized["customer_type"])
    if has_value(normalized.get("deadline_rule")):
        normalized["deadline_rule"] = normalize_deadline(normalized["deadline_rule"])

    return normalized


def template_supports_event(template, event_type):
    return normalize_event_type(event_type) in set(template.get("eventos_suportados") or [])


def template_supports_customer_type(template, customer_type):
    return normalize_customer_type(customer_type) in set(template.get("tipos_cliente_suportados") or [])


def template_reference(template):
    if not template:
        return None

    return {
        "id": template["id"],
        "nome": template["nome"],
        "descricao": template["descricao"],
        "categoria": template["categoria"],
        "eventos_suportados": list(template["eventos_suportados"]),
        "tipos_cliente_suportados": list(template["tipos_cliente_suportados"]),
        "validacoes_recomendadas": list(template["validacoes_recomendadas"]),
        "steps_gerados": list(template["steps_gerados"]),
        "warnings": list(template["warnings"]),
        "restricoes": list(template["restricoes"]),
    }


def public_template(template, include_defaults):
    data = template_reference(template)
    if include_defaults:
        data["default_answers"] = deepcopy(template.get("default_answers", {}))
    return data


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True
