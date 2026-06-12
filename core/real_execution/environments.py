from copy import deepcopy


QA_ENVIRONMENT_CONTRACT = {
    "qa1": {
        "id": "qa1",
        "label": "QA1",
        "api_url_ref": "SMARTOFFERS_QA1_API_URL",
        "db_dsn_ref": "SMARTOFFERS_QA1_DB_DSN",
        "db_user_ref": "SMARTOFFERS_QA1_DB_USER",
        "db_password_ref": "SMARTOFFERS_QA1_DB_PASSWORD",
    },
    "qa2": {
        "id": "qa2",
        "label": "QA2",
        "api_url_ref": "SMARTOFFERS_QA2_API_URL",
        "db_dsn_ref": "SMARTOFFERS_QA2_DB_DSN",
        "db_user_ref": "SMARTOFFERS_QA2_DB_USER",
        "db_password_ref": "SMARTOFFERS_QA2_DB_PASSWORD",
    },
    "qa3": {
        "id": "qa3",
        "label": "QA3",
        "api_url_ref": "SMARTOFFERS_QA3_API_URL",
        "db_dsn_ref": "SMARTOFFERS_QA3_DB_DSN",
        "db_user_ref": "SMARTOFFERS_QA3_DB_USER",
        "db_password_ref": "SMARTOFFERS_QA3_DB_PASSWORD",
    },
    "qa4": {
        "id": "qa4",
        "label": "QA4",
        "api_url_ref": "SMARTOFFERS_QA4_API_URL",
        "db_dsn_ref": "SMARTOFFERS_QA4_DB_DSN",
        "db_user_ref": "SMARTOFFERS_QA4_DB_USER",
        "db_password_ref": "SMARTOFFERS_QA4_DB_PASSWORD",
    },
}


def list_sanitized_qa_environments():
    return [deepcopy(QA_ENVIRONMENT_CONTRACT[key]) for key in sorted(QA_ENVIRONMENT_CONTRACT)]


def normalize_qa_environment(environment):
    if environment is None:
        return ""
    return str(environment).strip().lower()


def get_sanitized_qa_environment(environment):
    normalized = normalize_qa_environment(environment)
    entry = QA_ENVIRONMENT_CONTRACT.get(normalized)
    return deepcopy(entry) if entry else None
