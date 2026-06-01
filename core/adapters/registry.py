from .fake import (
    FakeEvidenceAdapter,
    FakeJenkinsAdapter,
    FakeKafkaAdapter,
    FakeOracleAdapter,
    FakeSmartOffersAdapter,
)


class AdapterRegistry:
    def __init__(self, adapters=None):
        self._adapters = list(adapters or get_default_adapters())

    def all(self):
        return list(self._adapters)

    def list_adapters(self):
        return [
            {
                "adapter_id": adapter.adapter_id,
                "name": adapter.name,
                "supported_step_types": list(adapter.supported_step_types),
            }
            for adapter in self._adapters
        ]

    def healthcheck(self):
        return [adapter.healthcheck(config={}) for adapter in self._adapters]

    def get_for_step_type(self, step_type):
        for adapter in self._adapters:
            if adapter.supports(step_type):
                return adapter
        return None


def get_default_adapters():
    return [
        FakeSmartOffersAdapter(),
        FakeOracleAdapter(),
        FakeKafkaAdapter(),
        FakeJenkinsAdapter(),
        FakeEvidenceAdapter(),
    ]


default_registry = AdapterRegistry()
