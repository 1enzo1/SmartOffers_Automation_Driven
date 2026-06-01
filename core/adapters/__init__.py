from .base import BaseAdapter
from .fake import (
    FakeEvidenceAdapter,
    FakeJenkinsAdapter,
    FakeKafkaAdapter,
    FakeOracleAdapter,
    FakeSmartOffersAdapter,
)
from .registry import AdapterRegistry, default_registry, get_default_adapters
from .results import AdapterResult

__all__ = [
    "AdapterRegistry",
    "AdapterResult",
    "BaseAdapter",
    "FakeEvidenceAdapter",
    "FakeJenkinsAdapter",
    "FakeKafkaAdapter",
    "FakeOracleAdapter",
    "FakeSmartOffersAdapter",
    "default_registry",
    "get_default_adapters",
]
