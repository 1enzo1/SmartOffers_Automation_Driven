from dataclasses import dataclass, field


ALLOWED_ADAPTER_STATUSES = {"passed", "failed", "skipped"}


def normalize_adapter_status(value):
    status = str(value or "passed").strip().lower()
    if status in ALLOWED_ADAPTER_STATUSES:
        return status
    return "failed"


@dataclass(frozen=True)
class AdapterResult:
    adapter_id: str
    adapter_name: str
    step_id: str
    step_name: str
    step_type: str
    status: str
    message: str
    duration_ms: int = 0
    source_section: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_type": self.step_type,
            "status": normalize_adapter_status(self.status),
            "message": self.message,
            "duration_ms": int(self.duration_ms or 0),
            "source_section": self.source_section,
            "metadata": dict(self.metadata or {}),
        }


def adapter_result_from_step(adapter, step, status="passed", message="", metadata=None):
    return AdapterResult(
        adapter_id=adapter.adapter_id,
        adapter_name=adapter.name,
        step_id=step.get("id") or "",
        step_name=step.get("name") or "",
        step_type=step.get("type") or "",
        status=normalize_adapter_status(status),
        message=message,
        duration_ms=step.get("duration_ms") or 0,
        source_section=step.get("source_section") or "",
        metadata=metadata or {},
    ).to_dict()
