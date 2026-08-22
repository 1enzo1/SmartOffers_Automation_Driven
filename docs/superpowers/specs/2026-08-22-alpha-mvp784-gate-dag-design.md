# Alpha MVP7.8.4 Gate DAG Design

Date: 2026-08-22
Goal: `ALPHA-MVP784-002`
Task class: `DEVELOPMENT`
Decision source: the accepted Architect decision for Option A / `DB_FIRST_API_LAST`

## Objective

Remove the circular and undefined predecessor gates from the dormant QA4
checkpoint flow, replace caller-supplied status strings with current structured
evidence, and add terminal Manager-only smoke consolidation. The change is
local and mock-first: it must not execute Oracle, HTTP, Kafka, Jenkins, FTM,
legacy subprocesses, production, mutation, retry, fallback or real parallelism.

## Canonical topology

The only dependency edges are:

```text
ACM_CUSTOM own guards -> ACM_CUSTOM_DB_CHECKPOINT_OK --+
ACM own guards        -> ACM_DB_CHECKPOINT_OK --------+-> API own guards
BDA own guards        -> BDA_DB_CHECKPOINT_OK --------+     -> SMARTOFFERS_API_QA4_CHECKPOINT_OK
                                                                  |
                                                                  v
                                                        Manager consolidation
                                                          BASIC_SMOKE_*
                                                          FULL_SMOKE_*
```

`ACM_CUSTOM`, `ACM` and `BDA` are independent branches. A deterministic local
schedule may visit them in that order, but no DB branch consumes another DB
status. The API consumes exactly the three canonical DB gates. Manager summaries
are terminal reporting artifacts and never authorize a DB branch or the API.

There is no canonical `BASIC_DB_CHECKPOINT_OK` node. Existing CLI names may stay
temporarily parseable as optional deprecated inputs, but their values are
ignored and cannot enable or block dependency satisfaction. Inventory found no
supported output consumer, so this goal does not add a compatibility projection.

## Structured orchestration context

Every canonical evidence record is bound to a sanitized context:

```python
{
    "orchestration_id": "alpha-run-ref",
    "operational_window_ref": "qa4-window-ref",
    "window_started_at": "2026-08-22T12:00:00+00:00",
    "window_expires_at": "2026-08-22T12:15:00+00:00",
    "environment": "qa4",
    "workflow_profile": "smartoffers_qa4_full_smoke",
}
```

`orchestration_id`, `operational_window_ref` and the executor's source
`execution_id` are opaque sanitized references, not operator names, endpoints
or credentials. Each must have length 1 through 128 and match the closed ASCII
grammar `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` exactly. The first character is
ASCII alphanumeric; every remaining character is ASCII alphanumeric, `.`, `_`
or `-`. URLs, credential or DSN assignments, whitespace, control characters,
non-ASCII characters and longer values are rejected before a canonical record
is created. A rejection contains only a deterministic reason and never copies
the rejected reference.

Each normalizer or consumer also receives an explicit `evaluated_at` timestamp.
Context, source and evaluation timestamps must be timezone-aware; the source
and evaluation must fall inside the same window, and source time must not be
later than evaluation time. This rejects stale, future and cross-window
evidence without relying on wall-clock I/O.

## Canonical evidence record

Create `core/real_execution/gate_dag.py` as a pure module. Its public interface is:

```python
normalize_checkpoint_evidence(result, context, *, evaluated_at) -> dict
validate_canonical_evidence_record(record, context, *, evaluated_at) -> dict
validate_api_db_gate_bundle(records, context, *, evaluated_at) -> dict
```

`normalize_checkpoint_evidence` recognizes only the four exact checkpoint and
resource pairs for ACM_CUSTOM, ACM, BDA and the API. A valid record contains:

```python
{
    "schema_version": "alpha-mvp784-002.v1",
    "record_type": "canonical_checkpoint_evidence",
    "evidence_status": "VALID",
    "component": "ACM_DB",
    "outcome": "OK",
    "gate_name": "ACM_DB_CHECKPOINT_OK",
    "orchestration_id": "alpha-run-ref",
    "operational_window_ref": "qa4-window-ref",
    "window_started_at": "2026-08-22T12:00:00+00:00",
    "window_expires_at": "2026-08-22T12:15:00+00:00",
    "workflow_profile": "smartoffers_qa4_full_smoke",
    "source_execution_id": "sanitized-execution-ref",
    "source_timestamp": "2026-08-22T12:05:00+00:00",
    "source_environment": "qa4",
    "source_profile": "smartoffers_qa4_full_smoke",
    "source_checkpoint": "ORACLE_ACM_TECHNICAL_READ_ONLY_01",
    "source_resource_id": "acm_db",
    "source_status": "CONNECT_AND_READ_OK",
    "sanitized_error_category": "NONE",
    "stop_reason": "CHECKPOINT_COMPLETED",
    "validations": {"fingerprint_validation": "MATCH"},
}
```

The complete validation map contains only allow/deny metadata already safe for
evidence; it never copies runtime refs or values. Rejected input returns a small
record with `evidence_status=REJECTED`, a deterministic `rejection_reason` and
no `gate_name`. It raises no exception and performs no I/O.

`validate_canonical_evidence_record` revalidates schema, record type, evidence
status, exact context and current window before any downstream consumer uses a
normalized record. It returns only a deterministic validation status and reason;
it never promotes a rejected record or a raw result.

For an `OK` outcome, the exact identity, success status, one attempt, zero retry,
`sanitized_error_category=NONE`, `stop_reason=CHECKPOINT_COMPLETED`, positive
resource-specific validations and `sensitive_values_logged=false` are all
mandatory. The API additionally requires its DB bundle validation and its
response/body logging guards. Failed and blocked terminal evidence still needs
valid identity, provenance, one-attempt/zero-retry metadata and the sensitive-log
guard, but does not pretend failed validations were positive.

The source profiles remain explicit: ACM_CUSTOM evidence comes from
`smartoffers_basic_smoke`; ACM, BDA and the Option A API evidence come from
`smartoffers_qa4_full_smoke`. This preserves the basic profile's resource
membership while correctly representing the three-DB API node as full smoke.

## API gate bundle

`validate_api_db_gate_bundle` accepts a list or tuple of normalized records and
requires exactly one current `OK` gate for each name:

```text
ACM_CUSTOM_DB_CHECKPOINT_OK
ACM_DB_CHECKPOINT_OK
BDA_DB_CHECKPOINT_OK
```

It rejects strings, raw executor results, duplicates, extra records, rejected or
non-OK evidence, wrong schema, wrong context, expired windows and mixed
orchestrations. Its return is a sanitized status dictionary:

```python
{
    "status": "DB_CHECKPOINT_GATES_READY",
    "reason": "NONE",
    "gate_names": [
        "ACM_CUSTOM_DB_CHECKPOINT_OK",
        "ACM_DB_CHECKPOINT_OK",
        "BDA_DB_CHECKPOINT_OK",
    ],
}
```

The API function receives `db_checkpoint_gates`, `orchestration_context` and
`gate_evaluated_at`. Legacy `*_checkpoint_status` values stay optional and are
ignored. The CLI does not gain a JSON/file evidence injection surface; a CLI
invocation that supplies only legacy strings remains blocked before client load.
The fake-client tests exercise the structured function surface.

## Executor reconciliation

- ACM removes `BASIC_SMOKE_OK` from admission.
- BDA removes `BASIC_DB_CHECKPOINT_OK` from admission.
- Their legacy CLI parameters become optional and non-authoritative.
- ACM_CUSTOM and ACM results expose explicit positive fingerprint/result-shape
  metadata and `sensitive_values_logged=false` needed by the mapper.
- BDA retains its existing bounded evidence and independence.
- The API preflight and result use `smartoffers_qa4_full_smoke`, retain every
  local allowlist/timeout/read-only/logging guard, expose the sanitized positive
  validations needed by the mapper, and cannot load a client until the three
  structured DB gates validate.
- `safe_for_real_execution`, catalog `execution_status`, `mode=real`, runtime
  profile resource membership and all external execution blocks remain unchanged.

## Terminal consolidation

Create `core/real_execution/smoke_consolidation.py` with the pure interface:

```python
consolidate_smoke_results(
    records,
    context,
    *,
    evaluated_at,
    global_safety_stop=False,
) -> dict
```

It consumes current normalized terminal records, never raw strings. It reports
component outcome/reason data and two non-authoritative summaries:

```text
BASIC components: ACM_CUSTOM_DB, SMARTOFFERS_API
FULL components:  ACM_CUSTOM_DB, ACM_DB, BDA_DB, SMARTOFFERS_API
```

Precedence is deterministic:

- Basic: global stop -> `BLOCKED`; all OK -> `OK`; any attempted failure ->
  `FAILED`; otherwise -> `BLOCKED`.
- Full: global stop -> `BLOCKED`; all OK -> `OK`; at least one OK plus any
  non-OK -> `PARTIAL`; no OK plus any attempted failure -> `FAILED`; otherwise
  -> `BLOCKED`.

The returned statuses are prefixed (`BASIC_SMOKE_*`, `FULL_SMOKE_*`), preserve
all component reasons, set `operational_readiness=false`, and have no outgoing
dependency edge. The manual planning contract consequently stops requiring a
pre-existing `basic_smoke_ok` for the full profile; this changes planning
topology only and still returns `execution_decision=EXECUTION_BLOCKED`.

## Compatibility and safety

Existing JSON scenario formats and Flask routes are untouched. Public runtime
profile resource lists are unchanged. The four dormant checkpoint tools retain
their existing local guards and fake dependency injection. Automated tests must
not import or contact a real driver/client, network, DNS or subprocess.

`BASIC_DB_CHECKPOINT_OK` may remain only in a deprecated parser option,
historical decision prose or negative/static tests. It must not be a mandatory
consumer, producer, aggregate or API/BDA admission condition.

## Acceptance

1. Focused tests prove exact allow/deny normalization for all four components.
2. Bare, stale, future, wrong-resource, wrong-checkpoint and mixed-context
   evidence cannot create or satisfy a gate.
3. ACM_CUSTOM, ACM and BDA run independently with fake drivers; legacy
   predecessor values do not authorize or suppress them.
4. The API fake client is loaded only after the exact three structured DB gates
   and all unchanged API guards pass.
5. Consolidation covers basic/full OK, FAILED, BLOCKED and full PARTIAL while
   preserving reasons and never implying operational readiness.
6. Static tests prevent `BASIC_DB_CHECKPOINT_OK` from becoming authoritative.
7. `python -m pytest tests -q`, `git diff --check` and sanitized Git checks pass.
8. An independent Tester accepts implementation, safety, compatibility,
   evidence and Git state before the Manager closes `CONTRACT_CONFLICT-001`.
