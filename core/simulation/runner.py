from datetime import datetime, timedelta, timezone
from uuid import uuid4


ALLOWED_STATUSES = {"passed", "failed", "skipped"}


def run_dry_run(scenario):
    """Run a local, integration-free simulation for a saved scenario JSON."""
    adapter = LocalSimulationAdapter()
    return adapter.run(scenario)


class LocalSimulationAdapter:
    """Adapter boundary for future real executors; this implementation is local only."""

    def run(self, scenario):
        scenario_id = str(scenario.get("id") or "scenario")
        started_at = datetime.now(timezone.utc)
        logs = [
            f"DRY_RUN|START|scenario={scenario_id}",
            "DRY_RUN|LOCAL_ONLY|Oracle, APIs, SmartOffers, Kafka, Jenkins e scripts reais desabilitados.",
        ]

        steps = []
        for index, step in enumerate(iter_source_steps(scenario), start=1):
            result = self.execute_step(step, index)
            steps.append(result)
            logs.append(
                "DRY_RUN|STEP|{status}|{type}|{name}|{message}".format(
                    status=result["status"],
                    type=result["type"],
                    name=result["name"],
                    message=result["message"],
                )
            )

        warnings = list(scenario.get("warnings") or [])
        if not steps:
            warnings.append("Cenario sem execution_steps ou validation_steps para simular.")
            logs.append("DRY_RUN|WARN|Nenhum step encontrado no JSON do cenario.")

        summary = build_summary(steps)
        status = resolve_status(summary)
        duration_ms = sum(step["duration_ms"] for step in steps)
        finished_at = started_at + timedelta(milliseconds=duration_ms)

        logs.append(
            "DRY_RUN|END|{status}|total={total}|passed={passed}|failed={failed}|skipped={skipped}".format(
                status=status,
                **summary,
            )
        )

        return {
            "id": build_report_id(scenario_id, started_at),
            "scenario_id": scenario_id,
            "status": status,
            "started_at": format_timestamp(started_at),
            "finished_at": format_timestamp(finished_at),
            "duration_ms": duration_ms,
            "steps": steps,
            "summary": summary,
            "logs": logs,
            "warnings": warnings,
        }

    def execute_step(self, planned_step, index):
        source_step = planned_step["source_step"]
        status, message = resolve_step_outcome(planned_step)

        return {
            "name": planned_step["name"],
            "type": planned_step["type"],
            "status": status,
            "duration_ms": estimate_duration_ms(planned_step, index),
            "message": message,
            "source_step": source_step,
        }


def iter_source_steps(scenario):
    for step in scenario.get("execution_steps") or []:
        yield {
            "name": step.get("action") or f"Execucao {step.get('step', '')}".strip(),
            "type": "execution",
            "source_step": step,
        }

    for step in scenario.get("validation_steps") or []:
        yield {
            "name": step.get("validation") or f"Validacao {step.get('step', '')}".strip(),
            "type": "validation",
            "source_step": step,
        }


def resolve_step_outcome(planned_step):
    source_step = planned_step["source_step"]
    controls = source_step.get("dry_run") or source_step.get("simulation") or {}
    configured_status = (
        controls.get("status")
        or source_step.get("dry_run_status")
        or source_step.get("mock_status")
        or "passed"
    )
    status = normalize_status(configured_status)

    if status == "failed":
        default_message = "Falha simulada definida no JSON do cenario."
    elif status == "skipped":
        default_message = "Step ignorado por controle local de dry-run."
    elif planned_step["type"] == "validation":
        default_message = "Validacao simulada localmente, sem consultar sistemas externos."
    else:
        default_message = "Step simulado localmente, sem executar scripts ou integracoes reais."

    return status, controls.get("message") or source_step.get("dry_run_message") or default_message


def normalize_status(value):
    status = str(value or "passed").strip().lower()
    if status in ALLOWED_STATUSES:
        return status
    return "failed"


def estimate_duration_ms(planned_step, index):
    base = 18 if planned_step["type"] == "execution" else 12
    return base + (index % 5) * 7


def build_summary(steps):
    summary = {"total": len(steps), "passed": 0, "failed": 0, "skipped": 0}

    for step in steps:
        summary[step["status"]] += 1

    return summary


def resolve_status(summary):
    if summary["failed"]:
        return "failed"
    if summary["total"] and summary["passed"] == 0 and summary["skipped"] == summary["total"]:
        return "skipped"
    return "passed"


def build_report_id(scenario_id, started_at):
    timestamp = started_at.strftime("%Y%m%d%H%M%S%f")
    return f"dryrun-{scenario_id}-{timestamp}-{uuid4().hex[:8]}"


def format_timestamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
