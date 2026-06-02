import json
from functools import lru_cache
from pathlib import Path


CATALOG_PATH = Path(__file__).with_name("catalog.json")


@lru_cache(maxsize=1)
def load_api_catalog():
    if not CATALOG_PATH.exists():
        return []

    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return list(data.get("apis", []))


def list_api_catalog():
    return load_api_catalog()


def get_api_catalog(api_id):
    for entry in load_api_catalog():
        if entry["api_id"] == api_id:
            return entry
    return None
