import os


NORMALIZED_RUNTIME_ENV = {
    "api_url_ref": "SMARTOFFERS_API_URL",
    "db_dsn_ref": "SMARTOFFERS_DB_DSN",
    "db_user_ref": "SMARTOFFERS_DB_USER",
    "db_password_ref": "SMARTOFFERS_DB_PASSWORD",
}
ORACLE_CLIENT_LIB_DIR_ENV = "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"
RUNTIME_PREFLIGHT_READY = "READY"
RUNTIME_PREFLIGHT_BLOCKED = "BLOCKED"


def resolve_legacy_runtime_config(environment_contract, base_env=None):
    env = os.environ if base_env is None else base_env
    contract = environment_contract if isinstance(environment_contract, dict) else {}
    missing_refs = []
    normalized_env = {}
    resolved_refs = {}
    checked_refs = []

    for contract_key, normalized_key in NORMALIZED_RUNTIME_ENV.items():
        ref_name = contract.get(contract_key)
        if not ref_name:
            missing_refs.append(contract_key)
            continue

        checked_refs.append(ref_name)
        resolved_refs[normalized_key] = ref_name
        value = env.get(ref_name)
        if value is None or str(value).strip() == "":
            missing_refs.append(ref_name)
            continue

        normalized_env[normalized_key] = str(value)

    checked_refs.append(ORACLE_CLIENT_LIB_DIR_ENV)
    oracle_client_lib_dir = env.get(ORACLE_CLIENT_LIB_DIR_ENV)
    resolved_refs[ORACLE_CLIENT_LIB_DIR_ENV] = ORACLE_CLIENT_LIB_DIR_ENV
    if oracle_client_lib_dir is None or str(oracle_client_lib_dir).strip() == "":
        missing_refs.append(ORACLE_CLIENT_LIB_DIR_ENV)
    else:
        normalized_env[ORACLE_CLIENT_LIB_DIR_ENV] = str(oracle_client_lib_dir)

    missing_refs = sorted(set(missing_refs))
    preflight = {
        "status": RUNTIME_PREFLIGHT_READY if not missing_refs else RUNTIME_PREFLIGHT_BLOCKED,
        "environment": contract.get("id") or "",
        "missing_refs": missing_refs,
        "checked_refs": sorted(set(checked_refs)),
    }
    return {
        "valid": not missing_refs,
        "blocked_reasons": [f"missing_runtime_ref:{ref}" for ref in missing_refs],
        "normalized_env": normalized_env if not missing_refs else {},
        "preflight": preflight,
        "sanitized": {
            "environment": contract.get("id") or "",
            "resolved_refs": resolved_refs,
            "checked_refs": preflight["checked_refs"],
            "missing_refs": missing_refs,
        },
    }


def preflight_legacy_runtime_config(environment_contract, base_env=None):
    runtime_config = resolve_legacy_runtime_config(environment_contract, base_env=base_env)
    return dict(runtime_config["preflight"])


def build_runtime_config_log(runtime_config):
    sanitized = runtime_config.get("sanitized") or {}
    environment = sanitized.get("environment") or "none"
    resolved_refs = sanitized.get("resolved_refs") or {}
    ref_text = ",".join(
        f"{normalized_key}<-{resolved_refs[normalized_key]}"
        for normalized_key in sorted(resolved_refs)
    )
    missing_refs = ",".join(sanitized.get("missing_refs") or [])
    return (
        f"RUNTIME_CONFIG|environment={environment}|"
        f"refs={ref_text or 'none'}|missing={missing_refs or 'none'}"
    )


def build_runtime_preflight_log(runtime_preflight):
    environment = runtime_preflight.get("environment") or "none"
    checked_refs = ",".join(runtime_preflight.get("checked_refs") or [])
    missing_refs = ",".join(runtime_preflight.get("missing_refs") or [])
    status = runtime_preflight.get("status") or RUNTIME_PREFLIGHT_BLOCKED
    return (
        f"RUNTIME_PREFLIGHT|status={status}|environment={environment}|"
        f"checked_refs={checked_refs or 'none'}|missing={missing_refs or 'none'}"
    )
