from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    adapter_id = ""
    name = ""
    supported_step_types = ()

    def supports(self, step_type):
        return step_type in self.supported_step_types

    @abstractmethod
    def execute(self, step, context):
        """Execute a normalized adapter step and return a serializable result."""

    def validate_config(self, config):
        if config is None:
            config = {}

        if not isinstance(config, dict):
            return {
                "status": "failed",
                "message": "Configuração deve ser um objeto.",
                "details": {},
            }

        return {
            "status": "passed",
            "message": "Configuração mockada válida.",
            "details": {"config_keys": sorted(config.keys())},
        }

    def healthcheck(self, config=None):
        validation = self.validate_config(config or {})
        return {
            "adapter_id": self.adapter_id,
            "name": self.name,
            "status": validation["status"],
            "message": validation["message"],
            "supported_step_types": list(self.supported_step_types),
            "details": validation.get("details") or {},
        }
