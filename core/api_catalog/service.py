from .catalog import get_api_catalog, list_api_catalog


def list_api_catalog_entries():
    entries = list_api_catalog()
    return {"apis": entries, "total": len(entries)}


def get_api_catalog_entry(api_id):
    return get_api_catalog(api_id)
