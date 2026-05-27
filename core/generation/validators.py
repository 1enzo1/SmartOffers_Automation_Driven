from .constants import (
    CUSTOMER_LABELS,
    DEADLINE_LABELS,
    DOCUMENT_LABELS,
    EVENT_LABELS,
    VALIDATION_LABELS,
)


class ScenarioValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Dados insuficientes para gerar o cenario")


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

    if answers.get("event_type") == "recarga" and answers.get("customer_type") != "pre":
        errors["event_type"] = "Recarga deve ser gerada apenas para cliente Pre-pago."

    if not answers.get("validations"):
        errors["validations"] = "Selecione ao menos uma validacao."

    invalid_validations = [item for item in answers.get("validations", []) if item not in VALIDATION_LABELS]
    if invalid_validations:
        errors["validations"] = f"Validacoes invalidas: {', '.join(invalid_validations)}."

    return errors
