from datetime import datetime, timedelta, timezone
from uuid import uuid4

from core.adapters import default_registry
from core.adapters.results import adapter_result_from_step


class AdapterRunModeError(ValueError):
    pass


def list_adapters(registry=None):
    registry = registry or default_registry
    return registry.list_adapters()


def adapters_healthcheck(registry=None):
    registry = registry or default_registry
    return registry.healthcheck()


def run_adapter_scenario(scenario, mode="mock", registry=None):
    mode = normalize_mode(mode)
    if mode == "real":
        raise AdapterRunModeError("mode real bloqueado: apenas mode='mock' está habilitado.")
    if mode != "mock":
        raise AdapterRunModeError("mode invalido: apenas mode='mock' está habilitado.")

    registry = registry or default_registry
    scenario_id = str(scenario.get("id") or "scenario")
    started_at = datetime.now(timezone.utc)
    logs = [
        f"ADAPTER_RUN|START|scenario={scenario_id}|mode={mode}",
        "ADAPTER_RUN|LOCAL_ONLY|Oracle, APIs, Kafka, Jenkins, rede e subprocessos reais desabilitados.",
    ]
    warnings = list(scenario.get("warnings") or [])
    adapter_results = []

    context = {
        "scenario_id": scenario_id,
        "mode": mode,
        "source": "adapter-run",
        "source_answers": scenario.get("source_answers") or {},
        "payload": scenario.get("payload") or {},
    }

    for step in iter_adapter_steps(scenario):
        adapter = registry.get_for_step_type(step["type"])
        if not adapter:
            result = adapter_result_from_step(
                NullAdapter(),
                step,
                status="skipped",
                message=f"Nenhum adapter registrado para step_type={step['type']}.",
            )
            warnings.append(result["message"])
        else:
            result = adapter.execute(step, context)

        adapter_results.append(result)
        if (result.get("metadata") or {}).get("blocked"):
            warnings.append(result["message"])
        logs.append(
            "ADAPTER_RUN|STEP|{status}|{adapter}|{type}|{name}|{message}".format(
                status=result["status"],
                adapter=result["adapter_id"],
                type=result["step_type"],
                name=result["step_name"],
                message=result["message"],
            )
        )

    if not adapter_results:
        warnings.append("Cenário sem steps, queries, checkpoints ou evidências para adapter-run.")
        logs.append("ADAPTER_RUN|WARN|Nenhuma unidade de execução encontrada no JSON do cenário.")

    summary = build_summary(adapter_results)
    status = resolve_status(summary)
    duration_ms = sum(result["duration_ms"] for result in adapter_results)
    finished_at = started_at + timedelta(milliseconds=duration_ms)
    run_id = build_run_id(scenario_id, started_at)

    logs.append(
        "ADAPTER_RUN|END|{status}|total={total}|passed={passed}|failed={failed}|blocked={blocked}|skipped={skipped}".format(
            status=status,
            **summary,
        )
    )

    return {
        "scenario_id": scenario_id,
        "run_id": run_id,
        "mode": mode,
        "status": status,
        "adapter_results": adapter_results,
        "summary": summary,
        "logs": logs,
        "warnings": warnings,
        "started_at": format_timestamp(started_at),
        "finished_at": format_timestamp(finished_at),
        "duration_ms": duration_ms,
        "source": "adapter-run",
    }


def iter_adapter_steps(scenario):
    index = 0

    for step in scenario.get("execution_steps") or []:
        index += 1
        yield normalize_step(
            index,
            "execution_steps",
            "smartoffers.execution",
            step.get("action") or f"Execução {step.get('step', '')}".strip(),
            step,
            payload_kind="execution",
        )

    for query in scenario.get("queries") or []:
        index += 1
        step_type = resolve_query_step_type(query)
        yield normalize_step(
            index,
            "queries",
            step_type,
            query.get("name") or f"Query {index}",
            query,
            payload_kind=query.get("kind") or "query",
        )

    for step in scenario.get("validation_steps") or []:
        index += 1
        yield normalize_step(
            index,
            "validation_steps",
            "evidence.validation",
            step.get("validation") or f"Validação {step.get('step', '')}".strip(),
            step,
            payload_kind="validation",
        )

    for checkpoint in scenario.get("checkpoints") or []:
        index += 1
        yield normalize_step(
            index,
            "checkpoints",
            "evidence.checkpoint",
            f"Checkpoint {index}",
            {"checkpoint": checkpoint},
            payload_kind="checkpoint",
        )

    for filename in scenario.get("evidence_files") or []:
        index += 1
        yield normalize_step(
            index,
            "evidence_files",
            "evidence.file",
            filename,
            {"filename": filename},
            payload_kind="evidence_file",
        )


def normalize_step(index, source_section, step_type, name, source_step, payload_kind):
    controls = {}
    if isinstance(source_step, dict):
        controls.update(source_step.get("dry_run") or source_step.get("simulation") or {})
        controls.update(source_step.get("adapter_run") or {})

        status_fallback = source_step.get("dry_run_status") or source_step.get("mock_status")
        message_fallback = source_step.get("dry_run_message") or source_step.get("mock_message")
        if status_fallback and not controls.get("status"):
            controls["status"] = status_fallback
        if message_fallback and not controls.get("message"):
            controls["message"] = message_fallback

    normalized = {
        "id": f"{source_section}-{index}",
        "name": name or f"Step {index}",
        "type": step_type,
        "source_section": source_section,
        "source_step": source_step,
        "payload_kind": payload_kind,
        "controls": controls or {},
        "duration_ms": estimate_duration_ms(step_type, index),
    }

    if isinstance(source_step, dict) and source_step.get("api_id"):
        normalized["api_id"] = source_step["api_id"]

    return normalized


def normalize_mode(mode):
    if mode is None:
        return "mock"
    if not isinstance(mode, str):
        raise AdapterRunModeError("mode invalido: deve ser string e usar mode='mock'.")
    return mode.strip().lower()


def resolve_query_step_type(query):
    kind = str(query.get("kind") or "").strip().lower()
    if kind == "sql":
        return "oracle.query"
    if kind == "kafka":
        return "kafka.lookup"
    if kind == "http_plan":
        return "smartoffers.http_plan"
    if kind == "manifest":
        return "evidence.manifest"
    return "evidence.validation"


def build_summary(results):
    summary = {"total": len(results), "passed": 0, "failed": 0, "blocked": 0, "skipped": 0}
    for result in results:
        status = result.get("status")
        if status in summary:
            summary[status] += 1
    return summary


def resolve_status(summary):
    if summary["failed"]:
        return "failed"
    if summary["blocked"]:
        return "blocked"
    if summary["total"] and summary["passed"] == 0 and summary["skipped"] == summary["total"]:
        return "skipped"
    return "passed"


def estimate_duration_ms(step_type, index):
    base_by_type = {
        "smartoffers.execution": 24,
        "smartoffers.http_plan": 14,
        "oracle.query": 18,
        "kafka.lookup": 16,
        "evidence.manifest": 10,
        "evidence.validation": 12,
        "evidence.checkpoint": 8,
        "evidence.file": 6,
    }
    return base_by_type.get(step_type, 10) + (index % 4) * 3


def build_run_id(scenario_id, started_at):
    timestamp = started_at.strftime("%Y%m%d%H%M%S%f")
    return f"adapterrun-{scenario_id}-{timestamp}-{uuid4().hex[:8]}"


def format_timestamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class NullAdapter:
    adapter_id = "unassigned"
    name = "Unassigned Adapter"
