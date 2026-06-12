import os


NORMALIZED_RUNTIME_ENV = {
    "api_url_ref": "SMARTOFFERS_API_URL",
    "db_dsn_ref": "SMARTOFFERS_DB_DSN",
    "db_user_ref": "SMARTOFFERS_DB_USER",
    "db_password_ref": "SMARTOFFERS_DB_PASSWORD",
}
ORACLE_CLIENT_LIB_DIR_ENV = "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"


def resolve_legacy_runtime_config(environment_contract, base_env=None):
    env = os.environ if base_env is None else base_env
    contract = environment_contract if isinstance(environment_contract, dict) else {}
    missing_refs = []
    normalized_env = {}
    resolved_refs = {}

    for contract_key, normalized_key in NORMALIZED_RUNTIME_ENV.items():
        ref_name = contract.get(contract_key)
        if not ref_name:
            missing_refs.append(contract_key)
            continue

        resolved_refs[normalized_key] = ref_name
        value = env.get(ref_name)
        if value is None or str(value).strip() == "":
            missing_refs.append(ref_name)
            continue

        normalized_env[normalized_key] = str(value)

    oracle_client_lib_dir = env.get(ORACLE_CLIENT_LIB_DIR_ENV)
    if oracle_client_lib_dir and str(oracle_client_lib_dir).strip():
        normalized_env[ORACLE_CLIENT_LIB_DIR_ENV] = str(oracle_client_lib_dir)
        resolved_refs[ORACLE_CLIENT_LIB_DIR_ENV] = ORACLE_CLIENT_LIB_DIR_ENV

    missing_refs = sorted(set(missing_refs))
    return {
        "valid": not missing_refs,
        "blocked_reasons": [f"missing_runtime_ref:{ref}" for ref in missing_refs],
        "normalized_env": normalized_env if not missing_refs else {},
        "sanitized": {
            "environment": contract.get("id") or "",
            "resolved_refs": resolved_refs,
            "optional_refs": [ORACLE_CLIENT_LIB_DIR_ENV],
            "missing_refs": missing_refs,
        },
    }


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
