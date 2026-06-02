from core.api_catalog.catalog import get_api_catalog
from core.api_catalog.policy import is_mock_plannable

from .base import BaseAdapter
from .results import adapter_result_from_step, normalize_adapter_status


class FakeAdapter(BaseAdapter):
    default_message = "Step executado em adapter fake, sem integrações externas."

    def execute(self, step, context):
        controls = step.get("controls") or {}
        status = normalize_adapter_status(controls.get("status") or step.get("status") or "passed")
        message = controls.get("message") or step.get("message") or self.default_message
        metadata = {
            "mode": context.get("mode", "mock"),
            "source": "fake-adapter",
            "external_calls": False,
        }

        if step.get("payload_kind"):
            metadata["payload_kind"] = step["payload_kind"]

        return adapter_result_from_step(
            self,
            step,
            status=status,
            message=message,
            metadata=metadata,
        )

    def validate_config(self, config):
        validation = super().validate_config(config)
        if validation["status"] != "passed":
            return validation

        validation["message"] = "Adapter fake disponível em modo mock."
        validation["details"]["external_calls"] = False
        return validation


class FakeSmartOffersAdapter(FakeAdapter):
    adapter_id = "fake-smartoffers"
    name = "Fake SmartOffers Adapter"
    supported_step_types = ("smartoffers.execution", "smartoffers.http_plan")
    default_message = "SmartOffers simulado localmente, sem chamada de API real."

    def execute(self, step, context):
        api_id = resolve_step_api_id(step)
        if not api_id:
            return super().execute(step, context)

        metadata = smartoffers_metadata(step, context)
        catalog_entry = get_api_catalog(api_id)
        if not catalog_entry:
            metadata["blocked"] = True
            metadata["block_reason"] = "api_id inexistente no catalogo"
            metadata["api_id"] = api_id
            return adapter_result_from_step(
                self,
                step,
                status="skipped",
                message=f"SmartOffers api_id={api_id} nao encontrado no catalogo seguro.",
                metadata=metadata,
            )

        if not is_mock_plannable(api_id):
            metadata["blocked"] = True
            metadata["block_reason"] = "api_id fora da policy mock_only"
            metadata["api_id"] = api_id
            metadata["catalog_status"] = catalog_entry.get("execution_status")
            return adapter_result_from_step(
                self,
                step,
                status="skipped",
                message=f"SmartOffers api_id={api_id} bloqueado para planejamento mock_only.",
                metadata=metadata,
            )

        metadata["api_id"] = api_id
        metadata["request_plan"] = build_request_plan(catalog_entry)

        controls = step.get("controls") or {}
        status = normalize_adapter_status(controls.get("status") or step.get("status") or "passed")
        message = (
            controls.get("message")
            or step.get("message")
            or f"Request plan SmartOffers mock_only gerado para api_id={api_id}."
        )
        return adapter_result_from_step(
            self,
            step,
            status=status,
            message=message,
            metadata=metadata,
        )


def resolve_step_api_id(step):
    if step.get("api_id"):
        return step["api_id"]

    source_step = step.get("source_step") or {}
    if isinstance(source_step, dict):
        return source_step.get("api_id")

    return None


def smartoffers_metadata(step, context):
    metadata = {
        "mode": context.get("mode", "mock"),
        "source": "smartoffers-planner",
        "external_calls": False,
        "network_calls": False,
    }

    if step.get("payload_kind"):
        metadata["payload_kind"] = step["payload_kind"]

    return metadata


def build_request_plan(entry):
    return {
        "api_id": entry.get("api_id") or "",
        "name": entry.get("name") or "",
        "category": entry.get("category") or "",
        "method": entry.get("method") or "",
        "path": entry.get("path") or "",
        "environment": resolve_environment(entry),
        "environment_variables": list(entry.get("environment_variables") or []),
        "host_placeholder": entry.get("host_placeholder") or "",
        "host_placeholders": list(entry.get("host_placeholders") or []),
        "payload_base": entry.get("payload_base") or {},
        "headers_expected": list(entry.get("headers_expected") or []),
        "execution_status": entry.get("execution_status") or "",
        "safe_for_real_execution": bool(entry.get("safe_for_real_execution")),
        "source": "api-catalog",
        "planning_mode": "mock_only",
    }


def resolve_environment(entry):
    supported_environments = entry.get("supported_environments") or []
    if supported_environments:
        return supported_environments[0]

    refs = entry.get("environment_refs") or []
    for environment in ("QA4", "QA3", "QA2", "QA1"):
        if environment in refs:
            return environment

    return ""


class FakeOracleAdapter(FakeAdapter):
    adapter_id = "fake-oracle"
    name = "Fake Oracle Adapter"
    supported_step_types = ("oracle.query",)
    default_message = "Consulta Oracle simulada localmente, sem conexão com banco real."


class FakeKafkaAdapter(FakeAdapter):
    adapter_id = "fake-kafka"
    name = "Fake Kafka Adapter"
    supported_step_types = ("kafka.lookup",)
    default_message = "Lookup Kafka simulado localmente, sem broker real."


class FakeJenkinsAdapter(FakeAdapter):
    adapter_id = "fake-jenkins"
    name = "Fake Jenkins Adapter"
    supported_step_types = ("jenkins.job", "jenkins.pipeline")
    default_message = "Jenkins simulado localmente, sem job ou subprocesso real."


class FakeEvidenceAdapter(FakeAdapter):
    adapter_id = "fake-evidence"
    name = "Fake Evidence Adapter"
    supported_step_types = (
        "evidence.validation",
        "evidence.checkpoint",
        "evidence.file",
        "evidence.manifest",
    )
    default_message = "Evidência validada em modo fake, sem leitura de sistemas externos."
