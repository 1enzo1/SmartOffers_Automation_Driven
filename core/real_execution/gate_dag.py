"""Pure normalization and validation for Alpha checkpoint gate evidence."""

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType


GATE_SCHEMA_VERSION = "alpha-mvp784-002.v1"
CANONICAL_EVIDENCE_VALID = "CANONICAL_EVIDENCE_VALID"
CANONICAL_EVIDENCE_BLOCKED = "CANONICAL_EVIDENCE_BLOCKED"
DB_CHECKPOINT_GATES_READY = "DB_CHECKPOINT_GATES_READY"
DB_CHECKPOINT_GATES_BLOCKED = "DB_CHECKPOINT_GATES_BLOCKED"
CANONICAL_DB_GATE_NAMES = (
    "ACM_CUSTOM_DB_CHECKPOINT_OK",
    "ACM_DB_CHECKPOINT_OK",
    "BDA_DB_CHECKPOINT_OK",
)

_RECORD_TYPE = "canonical_checkpoint_evidence"
_VALID = "VALID"
_REJECTED = "REJECTED"
_CONTEXT_FIELDS = (
    "orchestration_id",
    "operational_window_ref",
    "window_started_at",
    "window_expires_at",
    "environment",
    "workflow_profile",
)
_CANONICAL_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_type",
        "evidence_status",
        "component",
        "outcome",
        "gate_name",
        "orchestration_id",
        "operational_window_ref",
        "window_started_at",
        "window_expires_at",
        "workflow_profile",
        "source_execution_id",
        "source_timestamp",
        "source_environment",
        "source_profile",
        "source_checkpoint",
        "source_resource_id",
        "source_status",
        "sanitized_error_category",
        "stop_reason",
        "validations",
    }
)


@dataclass(frozen=True)
class _ComponentSpec:
    component: str
    gate_name: str
    profile: str
    success_status: str
    failed_statuses: frozenset
    blocked_statuses: frozenset
    positive_validations: tuple
    terminal_error_categories: frozenset


_COMMON_DB_VALIDATIONS = (
    ("environment_allowlist", "MATCH"),
    ("resource_allowlist", "MATCH"),
    ("destination_allowlist", "MATCH"),
    ("query_hash_validation", "MATCH"),
    ("read_only_validation", "PASS"),
    ("result_shape_validation", "MATCH"),
)
_PREFLIGHT_DB_VALIDATIONS = _COMMON_DB_VALIDATIONS + (
    ("preflight_validation", "MATCH"),
    ("fingerprint_validation", "MATCH"),
)
_MATCH_VALIDATION_VALUES = frozenset({"MATCH", "DENIED", "BLOCKED"})
_PASS_VALIDATION_VALUES = frozenset({"PASS", "DENIED", "BLOCKED"})
_SANITIZED_VALIDATION_VALUES = MappingProxyType(
    {
        "environment_allowlist": _MATCH_VALIDATION_VALUES,
        "resource_allowlist": _MATCH_VALIDATION_VALUES,
        "destination_allowlist": _MATCH_VALIDATION_VALUES,
        "query_hash_validation": _MATCH_VALIDATION_VALUES,
        "read_only_validation": _PASS_VALIDATION_VALUES,
        "result_shape_validation": _MATCH_VALIDATION_VALUES,
        "preflight_validation": _MATCH_VALIDATION_VALUES,
        "fingerprint_validation": _MATCH_VALIDATION_VALUES,
        "allowlist_validation": _MATCH_VALIDATION_VALUES,
        "path_validation": _MATCH_VALIDATION_VALUES,
        "path_hash_validation": _MATCH_VALIDATION_VALUES,
        "db_gate_bundle_validation": _MATCH_VALIDATION_VALUES,
        "response_body_logged": bool,
        "response_headers_logged": bool,
        "sensitive_values_logged": bool,
    }
)
_COMMON_ORACLE_TERMINAL_CATEGORIES = frozenset(
    {
        "ALLOWLIST_MISMATCH",
        "APPROVAL_MISSING",
        "AUTHENTICATION_ERROR",
        "CONFIG_MISSING",
        "CONNECT_TIMEOUT",
        "ORACLE_CLIENT_ERROR",
        "QUERY_HASH_MISMATCH",
        "READ_ONLY_POLICY_VIOLATION",
        "TOTAL_TIMEOUT",
        "UNCLASSIFIED_ORACLE_ERROR",
    }
)
_PREFLIGHT_ORACLE_TERMINAL_CATEGORIES = (
    _COMMON_ORACLE_TERMINAL_CATEGORIES | {"FINGERPRINT_DENIED"}
)
_API_TERMINAL_CATEGORIES = frozenset(
    {
        "ALLOWLIST_DENIED",
        "APPROVAL_MISSING",
        "AUTHENTICATION_ERROR",
        "AUTHENTICATION_UNCONFIRMED",
        "CONFIG_MISSING",
        "CONNECT_TIMEOUT",
        "DB_CHECKPOINT_GATE_MISSING",
        "FINGERPRINT_DENIED",
        "HTTP_STATUS_DENIED",
        "HTTP_TRANSPORT_ERROR",
        "OPERATIONAL_WINDOW_INACTIVE",
        "PATH_HASH_DENIED",
        "PREFLIGHT_DENIED",
        "READ_ONLY_POLICY_VIOLATION",
        "READ_TIMEOUT",
        "REDIRECT_DENIED",
        "RESPONSE_LIMIT_EXCEEDED",
        "TOTAL_TIMEOUT",
    }
)

_COMPONENTS = MappingProxyType(
    {
        (
            "ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01",
            "acm_custom_db",
        ): _ComponentSpec(
            component="ACM_CUSTOM_DB",
            gate_name="ACM_CUSTOM_DB_CHECKPOINT_OK",
            profile="smartoffers_basic_smoke",
            success_status="CONNECT_AND_READ_OK",
            failed_statuses=frozenset({"FAILED", "CONNECT_AND_READ_FAILED"}),
            blocked_statuses=frozenset({"BLOCKED", "CONNECT_AND_READ_BLOCKED"}),
            positive_validations=_COMMON_DB_VALIDATIONS
            + (("fingerprint_validation", "MATCH"),),
            terminal_error_categories=_COMMON_ORACLE_TERMINAL_CATEGORIES,
        ),
        (
            "ORACLE_ACM_TECHNICAL_READ_ONLY_01",
            "acm_db",
        ): _ComponentSpec(
            component="ACM_DB",
            gate_name="ACM_DB_CHECKPOINT_OK",
            profile="smartoffers_qa4_full_smoke",
            success_status="CONNECT_AND_READ_OK",
            failed_statuses=frozenset({"FAILED", "CONNECT_AND_READ_FAILED"}),
            blocked_statuses=frozenset({"BLOCKED", "CONNECT_AND_READ_BLOCKED"}),
            positive_validations=_PREFLIGHT_DB_VALIDATIONS,
            terminal_error_categories=_PREFLIGHT_ORACLE_TERMINAL_CATEGORIES,
        ),
        (
            "ORACLE_BDA_TECHNICAL_READ_ONLY_01",
            "bda_db",
        ): _ComponentSpec(
            component="BDA_DB",
            gate_name="BDA_DB_CHECKPOINT_OK",
            profile="smartoffers_qa4_full_smoke",
            success_status="BDA_DB_CHECKPOINT_OK",
            failed_statuses=frozenset({"BDA_DB_CHECKPOINT_FAILED"}),
            blocked_statuses=frozenset({"BDA_DB_CHECKPOINT_BLOCKED"}),
            positive_validations=_PREFLIGHT_DB_VALIDATIONS,
            terminal_error_categories=(
                _PREFLIGHT_ORACLE_TERMINAL_CATEGORIES | {"READ_TIMEOUT"}
            ),
        ),
        (
            "SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01",
            "smartoffers_api",
        ): _ComponentSpec(
            component="SMARTOFFERS_API",
            gate_name="SMARTOFFERS_API_QA4_CHECKPOINT_OK",
            profile="smartoffers_qa4_full_smoke",
            success_status="SMARTOFFERS_API_QA4_CHECKPOINT_OK",
            failed_statuses=frozenset({"SMARTOFFERS_API_QA4_CHECKPOINT_FAILED"}),
            blocked_statuses=frozenset({"SMARTOFFERS_API_QA4_CHECKPOINT_BLOCKED"}),
            positive_validations=(
                ("allowlist_validation", "MATCH"),
                ("preflight_validation", "MATCH"),
                ("path_validation", "MATCH"),
                ("path_hash_validation", "MATCH"),
                ("fingerprint_validation", "MATCH"),
                ("db_gate_bundle_validation", "MATCH"),
                ("response_body_logged", False),
                ("response_headers_logged", False),
            ),
            terminal_error_categories=_API_TERMINAL_CATEGORIES,
        ),
    }
)


def normalize_checkpoint_evidence(result, context, *, evaluated_at):
    """Normalize one sanitized executor result without performing any I/O."""

    result_data = result if isinstance(result, dict) else {}
    context_data = context if isinstance(context, dict) else {}

    context_reason = _validate_context(context_data, evaluated_at)
    if context_reason:
        return _rejected(context_reason)

    spec = _component_spec(
        result_data.get("checkpoint"), result_data.get("resource_id")
    )
    if spec is None:
        return _rejected("UNKNOWN_CHECKPOINT_RESOURCE")

    if (
        result_data.get("environment") != context_data["environment"]
        or result_data.get("profile") != spec.profile
    ):
        return _rejected("SOURCE_IDENTITY_MISMATCH")

    outcome = _outcome_for_status(result_data.get("status"), spec)
    if outcome is None:
        return _rejected("SOURCE_STATUS_MISMATCH")

    provenance_reason = _validate_provenance(
        result_data.get("execution_id"),
        result_data.get("timestamp"),
        context_data,
        evaluated_at,
    )
    if provenance_reason:
        return _rejected(provenance_reason)

    if (
        type(result_data.get("attempts_used")) is not int
        or result_data["attempts_used"] != 1
        or type(result_data.get("retry_count")) is not int
        or result_data["retry_count"] != 0
    ):
        return _rejected("ATTEMPT_POLICY_MISMATCH")

    if result_data.get("sensitive_values_logged") is not False:
        return _rejected("SENSITIVE_LOGGING_DENIED")

    if not _validation_values_are_sanitized(result_data, spec):
        return _rejected("VALIDATION_VALUE_INVALID")

    if outcome == "OK":
        if (
            result_data.get("sanitized_error_category") != "NONE"
            or result_data.get("stop_reason") != "CHECKPOINT_COMPLETED"
        ):
            return _rejected("SUCCESS_METADATA_MISMATCH")
        if not _positive_validations_match(result_data, spec):
            return _rejected("SUCCESS_VALIDATION_MISMATCH")
    else:
        if not _terminal_failure_metadata_is_valid(result_data, spec):
            return _rejected("TERMINAL_METADATA_MISMATCH")
        if not _terminal_validations_match(result_data, spec):
            return _rejected("TERMINAL_VALIDATION_MISMATCH")

    return _valid_record(result_data, context_data, spec, outcome)


def validate_canonical_evidence_record(record, context, *, evaluated_at):
    """Revalidate one normalized record for a current orchestration context."""

    if not isinstance(record, dict) or set(record) != _CANONICAL_RECORD_FIELDS or (
        record.get("schema_version") != GATE_SCHEMA_VERSION
        or record.get("record_type") != _RECORD_TYPE
        or record.get("evidence_status") != _VALID
    ):
        return _evidence_validation("CANONICAL_RECORD_INVALID")

    context_data = context if isinstance(context, dict) else {}
    context_reason = _validate_context(context_data, evaluated_at)
    if context_reason:
        return _evidence_validation(context_reason)

    if not _record_context_matches(record, context_data):
        return _evidence_validation("CONTEXT_MISMATCH")

    spec = _component_spec(
        record.get("source_checkpoint"), record.get("source_resource_id")
    )
    if spec is None or (
        record.get("component") != spec.component
        or record.get("gate_name") != spec.gate_name
        or record.get("source_environment") != context_data["environment"]
        or record.get("source_profile") != spec.profile
        or record.get("workflow_profile") != context_data["workflow_profile"]
    ):
        return _evidence_validation("CANONICAL_RECORD_IDENTITY_MISMATCH")

    outcome = _outcome_for_status(record.get("source_status"), spec)
    if outcome is None or record.get("outcome") != outcome:
        return _evidence_validation("CANONICAL_RECORD_OUTCOME_MISMATCH")

    provenance_reason = _validate_provenance(
        record.get("source_execution_id"),
        record.get("source_timestamp"),
        context_data,
        evaluated_at,
    )
    if provenance_reason:
        return _evidence_validation(provenance_reason)

    validations = record.get("validations")
    allowed_validation_names = {
        name for name, _ in spec.positive_validations
    } | {"sensitive_values_logged"}
    if (
        not isinstance(validations, dict)
        or not set(validations) <= allowed_validation_names
        or validations.get("sensitive_values_logged") is not False
        or not _validation_values_are_sanitized(validations, spec)
    ):
        return _evidence_validation("CANONICAL_RECORD_VALIDATION_MISMATCH")

    if outcome == "OK" and (
        record.get("sanitized_error_category") != "NONE"
        or record.get("stop_reason") != "CHECKPOINT_COMPLETED"
        or not all(
            validations.get(name) == expected
            for name, expected in spec.positive_validations
        )
    ):
        return _evidence_validation("CANONICAL_RECORD_VALIDATION_MISMATCH")

    if outcome != "OK" and (
        not _terminal_failure_metadata_is_valid(record, spec)
        or not _terminal_validations_match(validations, spec)
    ):
        return _evidence_validation("CANONICAL_RECORD_VALIDATION_MISMATCH")

    return {"status": CANONICAL_EVIDENCE_VALID, "reason": "NONE"}


def validate_api_db_gate_bundle(records, context, *, evaluated_at):
    """Validate exactly the three current structured DB gates required by API."""

    context_data = context if isinstance(context, dict) else {}
    context_reason = _validate_context(context_data, evaluated_at)
    if context_reason:
        return _bundle_blocked(context_reason)

    if not isinstance(records, (list, tuple)) or len(records) != len(
        CANONICAL_DB_GATE_NAMES
    ):
        return _bundle_blocked("DB_GATE_CARDINALITY_MISMATCH")

    gate_names = []
    for record in records:
        validation = validate_canonical_evidence_record(
            record, context_data, evaluated_at=evaluated_at
        )
        if validation["status"] != CANONICAL_EVIDENCE_VALID:
            return _bundle_blocked(validation["reason"])
        if record.get("outcome") != "OK":
            return _bundle_blocked("DB_GATE_NOT_OK")
        gate_names.append(record.get("gate_name"))

    if len(set(gate_names)) != len(gate_names):
        return _bundle_blocked("DB_GATE_DUPLICATE")
    if set(gate_names) != set(CANONICAL_DB_GATE_NAMES):
        return _bundle_blocked("DB_GATE_SET_MISMATCH")

    return {
        "status": DB_CHECKPOINT_GATES_READY,
        "reason": "NONE",
        "gate_names": list(CANONICAL_DB_GATE_NAMES),
    }


def _parse_utc(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def _validate_context(context, evaluated_at):
    if any(
        not isinstance(context.get(field), str) or not context[field].strip()
        for field in _CONTEXT_FIELDS
    ):
        return "ORCHESTRATION_CONTEXT_INVALID"
    if (
        context["environment"] != "qa4"
        or context["workflow_profile"] != "smartoffers_qa4_full_smoke"
    ):
        return "ORCHESTRATION_CONTEXT_INVALID"

    window_started = _parse_utc(context["window_started_at"])
    window_expires = _parse_utc(context["window_expires_at"])
    if window_started is None or window_expires is None or window_started >= window_expires:
        return "ORCHESTRATION_CONTEXT_INVALID"

    evaluated = _parse_utc(evaluated_at)
    if evaluated is None:
        return "EVALUATED_AT_INVALID"
    if evaluated < window_started:
        return "OPERATIONAL_WINDOW_NOT_STARTED"
    if evaluated > window_expires:
        return "OPERATIONAL_WINDOW_EXPIRED"
    return None


def _validate_provenance(execution_id, source_timestamp, context, evaluated_at):
    if not isinstance(execution_id, str) or not execution_id.strip():
        return "SOURCE_EXECUTION_ID_MISSING"

    source_time = _parse_utc(source_timestamp)
    if source_time is None:
        return "SOURCE_TIMESTAMP_INVALID"
    window_started = _parse_utc(context["window_started_at"])
    window_expires = _parse_utc(context["window_expires_at"])
    evaluated = _parse_utc(evaluated_at)
    if source_time < window_started or source_time > window_expires:
        return "SOURCE_OUTSIDE_OPERATIONAL_WINDOW"
    if source_time > evaluated:
        return "SOURCE_TIMESTAMP_IN_FUTURE"
    return None


def _positive_validations_match(result, spec):
    return all(
        result.get(name) == expected for name, expected in spec.positive_validations
    )


def _component_spec(checkpoint, resource_id):
    if not isinstance(checkpoint, str) or not isinstance(resource_id, str):
        return None
    return _COMPONENTS.get((checkpoint, resource_id))


def _validation_values_are_sanitized(values, spec):
    validation_names = {
        name for name, _ in spec.positive_validations
    } | {"sensitive_values_logged"}
    return all(
        name not in values or _validation_value_is_sanitized(name, values[name])
        for name in validation_names
    )


def _validation_value_is_sanitized(name, value):
    allowed = _SANITIZED_VALIDATION_VALUES[name]
    if allowed is bool:
        return type(value) is bool
    return isinstance(value, str) and value in allowed


def _rejected(reason):
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "record_type": _RECORD_TYPE,
        "evidence_status": _REJECTED,
        "rejection_reason": reason,
    }


def _record_context_matches(record, context):
    return all(
        record.get(field) == context[field]
        for field in (
            "orchestration_id",
            "operational_window_ref",
            "window_started_at",
            "window_expires_at",
            "workflow_profile",
        )
    )


def _outcome_for_status(status, spec):
    if not isinstance(status, str):
        return None
    if status == spec.success_status:
        return "OK"
    if status in spec.failed_statuses:
        return "FAILED"
    if status in spec.blocked_statuses:
        return "BLOCKED"
    return None


def _terminal_failure_metadata_is_valid(result, spec):
    error_category = result.get("sanitized_error_category")
    stop_reason = result.get("stop_reason")
    return (
        isinstance(error_category, str)
        and error_category in spec.terminal_error_categories
        and stop_reason == "IMMEDIATE_STOP"
    )


def _terminal_validations_match(values, spec):
    if spec.component != "SMARTOFFERS_API":
        return True
    return (
        values.get("response_body_logged") is False
        and values.get("response_headers_logged") is False
    )


def _valid_record(result, context, spec, outcome):
    validation_names = tuple(name for name, _ in spec.positive_validations)
    validations = {
        name: result[name] for name in validation_names if name in result
    }
    validations["sensitive_values_logged"] = False
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "record_type": _RECORD_TYPE,
        "evidence_status": _VALID,
        "component": spec.component,
        "outcome": outcome,
        "gate_name": spec.gate_name,
        "orchestration_id": context["orchestration_id"],
        "operational_window_ref": context["operational_window_ref"],
        "window_started_at": context["window_started_at"],
        "window_expires_at": context["window_expires_at"],
        "workflow_profile": context["workflow_profile"],
        "source_execution_id": result["execution_id"],
        "source_timestamp": result["timestamp"],
        "source_environment": result["environment"],
        "source_profile": result["profile"],
        "source_checkpoint": result["checkpoint"],
        "source_resource_id": result["resource_id"],
        "source_status": result["status"],
        "sanitized_error_category": result["sanitized_error_category"],
        "stop_reason": result["stop_reason"],
        "validations": validations,
    }


def _evidence_validation(reason):
    return {"status": CANONICAL_EVIDENCE_BLOCKED, "reason": reason}


def _bundle_blocked(reason):
    return {
        "status": DB_CHECKPOINT_GATES_BLOCKED,
        "reason": reason,
        "gate_names": [],
    }
