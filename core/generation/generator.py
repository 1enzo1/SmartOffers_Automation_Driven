from .normalization import normalize_answers
from .scenario_builder import build_scenario
from .validators import ScenarioValidationError, validate_answers
from core.templates import TemplateNotFoundError, apply_template_defaults, template_reference


def generate_scenario(raw_answers):
    try:
        raw_answers, selected_template = apply_template_defaults(raw_answers)
    except TemplateNotFoundError:
        raise ScenarioValidationError({"template_id": "Template nao encontrado."})

    answers = normalize_answers(raw_answers)
    if selected_template:
        answers["template_id"] = selected_template["id"]

    errors = validate_answers(answers)

    if errors:
        raise ScenarioValidationError(errors)

    scenario = build_scenario(answers)
    if selected_template:
        scenario["template"] = template_reference(selected_template)

    return scenario


__all__ = ["ScenarioValidationError", "generate_scenario"]
