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
