import json

from .storage import persist_export_bytes


def export_json_artifact(context):
    payload = {
        "metadata": context["metadata"],
    }

    if context.get("scenario"):
        payload["scenario"] = context["scenario"]

    if context.get("dry_run"):
        payload["dry_run"] = context["dry_run"]

    content = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    return persist_export_bytes(
        content,
        context["source_type"],
        context["source_id"],
        context["metadata"]["export_type"],
        "json",
    )
