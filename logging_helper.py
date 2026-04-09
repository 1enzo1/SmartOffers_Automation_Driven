from datetime import datetime


def _build_context(msisdn=None, offer=None, external_id=None, extra=None):
    context_parts = []

    if msisdn is not None:
        context_parts.append(f"msisdn={msisdn}")
    if offer is not None:
        context_parts.append(f"offer={offer}")
    if external_id is not None:
        context_parts.append(f"external_id={external_id}")
    if extra:
        for key, value in extra.items():
            context_parts.append(f"{key}={value}")

    return " ".join(context_parts) if context_parts else "-"


def log_success(scenario, step, message, msisdn=None, offer=None, external_id=None, extra=None):
    context = _build_context(
        msisdn=msisdn,
        offer=offer,
        external_id=external_id,
        extra=extra,
    )
    print(
        f"[SCENARIO] {scenario} | [STEP] {step} | [SUCCESS] {message} | context: {context} | ts={datetime.utcnow().isoformat()}Z"
    )


def log_error(scenario, step, message, msisdn=None, offer=None, external_id=None, extra=None):
    context = _build_context(
        msisdn=msisdn,
        offer=offer,
        external_id=external_id,
        extra=extra,
    )
    print(
        f"[SCENARIO] {scenario} | [STEP] {step} | [ERROR] {message} | context: {context} | ts={datetime.utcnow().isoformat()}Z"
    )
