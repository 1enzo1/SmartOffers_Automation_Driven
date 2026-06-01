from dataclasses import asdict, dataclass, field


EXECUTION_STATUSES = {"blocked", "mock_only", "qa_enabled", "future_review"}


@dataclass(frozen=True)
class ApiCatalogEntry:
    api_id: str
    name: str
    category: str
    method: str
    path: str
    environment_refs: list[str] = field(default_factory=list)
    supported_environments: list[str] = field(default_factory=list)
    execution_status: str = "blocked"
    notes: str = ""
    safe_for_real_execution: bool = False
    source_collection: str = ""
    source_file: str = ""
    headers_expected: list[dict] = field(default_factory=list)
    payload_base: object = field(default_factory=dict)

    def __post_init__(self):
        if self.execution_status not in EXECUTION_STATUSES:
            raise ValueError(f"execution_status invalido: {self.execution_status}")

        if self.safe_for_real_execution:
            raise ValueError("catalogo MVP7.5 nao permite execucao real")

    def to_dict(self):
        return asdict(self)
