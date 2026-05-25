from datetime import datetime
from pathlib import Path
import os


def get_base_path(default: str) -> str:
    return os.getenv("PASTA_EXECUCAO", default)


def create_run_path(base_path: str, prefix: str = "te") -> str:
    root = Path(base_path)
    root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%d%m%y_%H%M%S")
    candidate = root / f"{prefix}_{stamp}"
    suffix = 1

    while candidate.exists():
        candidate = root / f"{prefix}_{stamp}_{suffix:02d}"
        suffix += 1

    candidate.mkdir(parents=True, exist_ok=False)
    return str(candidate)


def build_path(*parts: str) -> str:
    return str(Path(*parts))
