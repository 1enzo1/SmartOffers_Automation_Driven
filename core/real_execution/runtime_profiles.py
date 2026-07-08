from copy import deepcopy


SMARTOFFERS_BASIC_SMOKE = "smartoffers_basic_smoke"

RUNTIME_PROFILE_CONTRACTS = {
    SMARTOFFERS_BASIC_SMOKE: {
        "id": SMARTOFFERS_BASIC_SMOKE,
        "label": "SmartOffers basic smoke QA4",
        "environment": "qa4",
        "flow": "smartoffers_basic_smoke",
        "access_profile": "acm_custom_read_only",
        "resources": [
            {
                "id": "smartoffers_api",
                "kind": "api",
                "access": "manual_smoke",
                "required": True,
                "refs": {
                    "url": "SMARTOFFERS_QA4_API_URL",
                },
                "normalized_env": {
                    "url": "SMARTOFFERS_API_URL",
                },
            },
            {
                "id": "acm_custom_db",
                "kind": "oracle_database",
                "schema": "ACM_CUSTOM",
                "access": "read_only",
                "required": True,
                "refs": {
                    "dsn": "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
                    "user": "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
                    "password": "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
                },
                "legacy_refs": {
                    "dsn": ["SMARTOFFERS_QA4_DB_DSN"],
                    "user": ["SMARTOFFERS_QA4_DB_USER"],
                    "password": ["SMARTOFFERS_QA4_DB_PASSWORD"],
                },
                "normalized_env": {
                    "dsn": "SMARTOFFERS_DB_DSN",
                    "user": "SMARTOFFERS_DB_USER",
                    "password": "SMARTOFFERS_DB_PASSWORD",
                },
            },
            {
                "id": "oracle_client",
                "kind": "oracle_client",
                "access": "local_client_library",
                "required": True,
                "refs": {
                    "lib_dir": "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
                },
                "normalized_env": {
                    "lib_dir": "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
                },
            },
        ],
    },
}

DEFAULT_RUNTIME_PROFILE_BY_ENVIRONMENT = {
    "qa4": SMARTOFFERS_BASIC_SMOKE,
}


def list_sanitized_runtime_profiles(environment=None):
    normalized_environment = _normalize_environment(environment)
    profiles = []

    for profile_id in sorted(RUNTIME_PROFILE_CONTRACTS):
        profile = RUNTIME_PROFILE_CONTRACTS[profile_id]
        if normalized_environment and profile.get("environment") != normalized_environment:
            continue
        profiles.append(deepcopy(profile))

    return profiles


def get_sanitized_runtime_profile(profile):
    normalized = normalize_runtime_profile(profile)
    entry = RUNTIME_PROFILE_CONTRACTS.get(normalized)
    return deepcopy(entry) if entry else None


def get_default_runtime_profile_for_environment(environment):
    profile_id = DEFAULT_RUNTIME_PROFILE_BY_ENVIRONMENT.get(_normalize_environment(environment))
    return get_sanitized_runtime_profile(profile_id) if profile_id else None


def normalize_runtime_profile(profile):
    if profile is None:
        return ""
    return str(profile).strip().lower()


def _normalize_environment(environment):
    if environment is None:
        return ""
    return str(environment).strip().lower()
