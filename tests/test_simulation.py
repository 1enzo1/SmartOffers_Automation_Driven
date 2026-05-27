from core.generation import generate_scenario
from core.simulation import run_dry_run


def base_answers(**overrides):
    answers = {
        "campaign_name": "Squad162 Upsell",
        "campaign_id": "162",
        "system": "SmartOffers",
        "objective": "Validar bonificacao apenas para upgrade",
        "customer_type": "pos",
        "document_type": "PF",
        "event_type": "upsell",
        "validations": ["api", "database", "audit"],
        "deadline_rule": "d1",
    }
    answers.update(overrides)
    return answers


def test_dry_run_accepts_scenario_json_and_keeps_required_contract():
    scenario = generate_scenario(base_answers())

    report = run_dry_run(scenario)

    assert {
        "id",
        "scenario_id",
        "status",
        "started_at",
        "finished_at",
        "duration_ms",
        "steps",
        "summary",
        "logs",
        "warnings",
    }.issubset(report)
    assert report["scenario_id"] == scenario["id"]
    assert report["summary"]["total"] == len(scenario["execution_steps"]) + len(
        scenario["validation_steps"]
    )
    assert report["steps"][0]["source_step"] == scenario["execution_steps"][0]
    assert any("LOCAL_ONLY" in log for log in report["logs"])


def test_dry_run_with_all_steps_passed():
    scenario = generate_scenario(base_answers())

    report = run_dry_run(scenario)

    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["skipped"] == 0
    assert all(step["status"] == "passed" for step in report["steps"])


def test_dry_run_with_failed_step():
    scenario = generate_scenario(base_answers())
    scenario["execution_steps"][0]["dry_run"] = {
        "status": "failed",
        "message": "Payload invalido no mock.",
    }

    report = run_dry_run(scenario)

    assert report["status"] == "failed"
    assert report["summary"]["failed"] == 1
    assert report["steps"][0]["status"] == "failed"
    assert report["steps"][0]["message"] == "Payload invalido no mock."


def test_dry_run_with_skipped_step():
    scenario = generate_scenario(base_answers())
    scenario["validation_steps"][0]["dry_run_status"] = "skipped"

    report = run_dry_run(scenario)

    assert report["status"] == "passed"
    assert report["summary"]["skipped"] == 1
    assert any(step["status"] == "skipped" for step in report["steps"])
