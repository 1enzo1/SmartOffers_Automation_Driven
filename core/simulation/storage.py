import json
import os
from pathlib import Path


DEFAULT_DRYRUN_DIR = "dryruns_gerados"


def get_dry_run_dir():
    return Path(os.getenv("DRYRUNS_GERADOS_PATH", DEFAULT_DRYRUN_DIR))


def save_dry_run_report(report):
    dry_run_dir = get_dry_run_dir()
    dry_run_dir.mkdir(parents=True, exist_ok=True)

    path = dry_run_dir / f"{report['id']}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(path)
