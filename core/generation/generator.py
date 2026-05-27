from .normalization import normalize_answers
from .scenario_builder import build_scenario
from .validators import ScenarioValidationError, validate_answers


def generate_scenario(raw_answers):
    answers = normalize_answers(raw_answers)
    errors = validate_answers(answers)

    if errors:
        raise ScenarioValidationError(errors)

    return build_scenario(answers)


__all__ = ["ScenarioValidationError", "generate_scenario"]
