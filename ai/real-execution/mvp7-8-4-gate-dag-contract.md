# MVP7.8.4 Canonical Gate DAG Contract

Goal: `ALPHA-MVP784-002`
Task: `TASK_CLASS=DEVELOPMENT`
State: `ACCEPTED`

This is the canonical Alpha contract for dependency admission between the
dormant QA4 checkpoint tools. It records mock-only behavior and does not grant
operational authority. Real transport remains blocked, as do production,
mutation, Oracle, HTTP, Kafka, Jenkins, FTM, legacy subprocesses, automatic
retry, fallback, credential alternatives and real parallel execution.

## Exact DAG

Compact form:

```text
ACM_CUSTOM | ACM | BDA -> API -> Manager consolidation
```

The exact dependency edges are:

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

The following delimited block is the machine-checkable canonical edge set. It
contains every dependency edge and no scheduling or reporting-only relation:

<!-- CANONICAL_GATE_EDGE_SET_BEGIN -->
```text
ACM_CUSTOM_OWN_GUARDS -> ACM_CUSTOM_DB_CHECKPOINT_OK
ACM_OWN_GUARDS -> ACM_DB_CHECKPOINT_OK
BDA_OWN_GUARDS -> BDA_DB_CHECKPOINT_OK
ACM_CUSTOM_DB_CHECKPOINT_OK -> SMARTOFFERS_API_QA4_CHECKPOINT_OK
ACM_DB_CHECKPOINT_OK -> SMARTOFFERS_API_QA4_CHECKPOINT_OK
BDA_DB_CHECKPOINT_OK -> SMARTOFFERS_API_QA4_CHECKPOINT_OK
SMARTOFFERS_API_QA4_CHECKPOINT_OK -> MANAGER_CONSOLIDATION
```
<!-- CANONICAL_GATE_EDGE_SET_END -->

Written without diagram alignment, the independent producer edges are
`ACM_CUSTOM own guards -> ACM_CUSTOM_DB_CHECKPOINT_OK`,
`ACM own guards -> ACM_DB_CHECKPOINT_OK` and
`BDA own guards -> BDA_DB_CHECKPOINT_OK`.

`ACM_CUSTOM`, `ACM` and `BDA` are independent branches. There is no dependency
edge between any two DB branches. The API consumes exactly three canonical DB
gates: `ACM_CUSTOM_DB_CHECKPOINT_OK`, `ACM_DB_CHECKPOINT_OK` and
`BDA_DB_CHECKPOINT_OK`. Manager summaries are terminal reporting artifacts;
they have no outgoing admission edge.

### Scheduling is not dependency

A local deterministic coordinator may schedule ACM_CUSTOM, ACM and BDA in that
order. That sequence is not a dependency and does not allow one branch's result
to enable, suppress or stand in for another branch.

## Producer, consumer, meaning and evidence source

| Gate or summary | Producer | Consumer | Meaning | Evidence source |
|---|---|---|---|---|
| `ACM_CUSTOM_DB_CHECKPOINT_OK` | Pure normalizer over the terminal ACM_CUSTOM result | API bundle validator | ACM_CUSTOM's own guarded, single-attempt, read-only checkpoint completed successfully | Sanitized result from `tools/qa4_manual_smoke.py`, exact ACM_CUSTOM checkpoint/resource identity and positive validations |
| `ACM_DB_CHECKPOINT_OK` | Pure normalizer over the terminal ACM result | API bundle validator | ACM's own guarded, single-attempt, read-only checkpoint completed successfully | Sanitized result from `tools/qa4_acm_manual_smoke.py`, exact ACM checkpoint/resource identity and positive validations |
| `BDA_DB_CHECKPOINT_OK` | Pure normalizer over the terminal BDA result | API bundle validator | BDA's own guarded, single-attempt, read-only checkpoint completed successfully | Sanitized result from `tools/qa4_bda_manual_smoke.py`, exact BDA checkpoint/resource identity and positive validations |
| `SMARTOFFERS_API_QA4_CHECKPOINT_OK` | Pure normalizer over the terminal API result after bundle admission | Manager consolidator | The guarded API health checkpoint completed successfully after the exact DB bundle was accepted | Sanitized result from `tools/qa4_api_health_smoke.py`, exact API checkpoint/resource identity, bundle proof and positive response guards |
| `BASIC_SMOKE_*` | Pure Manager consolidation | Reporting only | Terminal summary for ACM_CUSTOM plus API | Current canonical terminal records for those two components |
| `FULL_SMOKE_*` | Pure Manager consolidation | Reporting only | Terminal summary for ACM_CUSTOM, ACM, BDA and API | Current canonical terminal records for all four components |

The pure implementation boundaries are
`core/real_execution/gate_dag.py` and
`core/real_execution/smoke_consolidation.py`. They perform no network, driver,
filesystem, subprocess or clock I/O.

## Evidence and same-context admission

Caller-supplied success strings are not evidence. A canonical record binds the
exact checkpoint/resource pair, source execution reference, source timestamp,
environment, source profile, orchestration reference, operational-window
reference and window bounds. The normalizer validates `attempts=1` and
`retry=0` before emitting a canonical record; those source policy fields are
not copied into the record. The record contains a sanitized error category,
terminal stop reason, the component-specific validation map and
`sensitive_values_logged=false`.

The orchestration reference, operational-window reference and source execution
reference are opaque ASCII identifiers. Each has length 1 through 128 and must
match `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` exactly: the first character is ASCII
alphanumeric and each remaining character is ASCII alphanumeric, `.`, `_` or
`-`. URLs, `password=...`, `dsn=...`, whitespace, control characters,
non-ASCII text and longer values are invalid. Normalization and revalidation
reject them before admission, and a rejection returns only its deterministic
reason without copying the invalid reference.

The source timestamp, evaluation timestamp and window bounds must be
timezone-aware. Source and evaluation times must fall inside the same active
window, source time cannot be in the future, and every API predecessor must
match the same sanitized orchestration context. Stale, mixed-orchestration,
wrong-environment, wrong-profile, wrong-resource, wrong-checkpoint, duplicate,
extra, rejected, non-OK, raw-result and bare-string evidence is rejected.

The API node runs under `smartoffers_qa4_full_smoke`, because its admission
depends on all three DB branches. ACM_CUSTOM retains its source profile
`smartoffers_basic_smoke`; ACM and BDA retain
`smartoffers_qa4_full_smoke`. Runtime profile resource membership is unchanged.

## API admission

`validate_api_db_gate_bundle` is the only DB dependency admission mechanism for
the API checkpoint. It requires exactly three canonical DB gates, one for each
independent branch, all `VALID`, `OK`, current and bound to the same context.
Only after that bundle and all existing API guards pass may the injected fake
client be loaded in automated tests.

Legacy `*_checkpoint_status` CLI options remain parseable only for deprecated
compatibility. They are ignored by active admission and can neither enable nor
block a branch or the API. The CLI does not accept a JSON or file-based evidence
injection surface, and a CLI call containing only legacy status strings remains
blocked before client loading.

`BASIC_DB_CHECKPOINT_OK` is not a canonical node, producer, aggregate,
predecessor or admission condition. The historical name may occur only in
deprecated parser compatibility, historical decision records and negative
regression tests. No compatibility output projection is introduced because no
supported current output consumer was found.

## Manager precedence

Manager consolidation validates current canonical terminal records and
preserves each component outcome and reason. It always returns
`operational_readiness=false`; no summary authorizes execution.

Both summaries use the same leading precedence: `GLOBAL_SAFETY_STOP` first,
then `INVALID_INPUT_EVIDENCE`, then component outcomes. Any input rejected by
canonical validation, including an extra raw or rejected record, sets
`INVALID_INPUT_EVIDENCE` and blocks both summaries. A second otherwise-valid
record for one component is instead materialized as
`DUPLICATE_COMPONENT_EVIDENCE` and follows component outcome precedence.

The following block is the machine-checkable order. Each row is
`summary | priority | condition | status | reason`:

<!-- MANAGER_PRECEDENCE_BEGIN -->
```text
BASIC | 1 | GLOBAL_SAFETY_STOP | BASIC_SMOKE_BLOCKED | GLOBAL_SAFETY_STOP
BASIC | 2 | INVALID_INPUT_EVIDENCE | BASIC_SMOKE_BLOCKED | INVALID_INPUT_EVIDENCE
BASIC | 3 | ALL_COMPONENTS_OK | BASIC_SMOKE_OK | ALL_COMPONENTS_OK
BASIC | 4 | ANY_COMPONENT_FAILED | BASIC_SMOKE_FAILED | COMPONENT_FAILURE
BASIC | 5 | OTHERWISE | BASIC_SMOKE_BLOCKED | COMPONENTS_BLOCKED
FULL | 1 | GLOBAL_SAFETY_STOP | FULL_SMOKE_BLOCKED | GLOBAL_SAFETY_STOP
FULL | 2 | INVALID_INPUT_EVIDENCE | FULL_SMOKE_BLOCKED | INVALID_INPUT_EVIDENCE
FULL | 3 | ALL_COMPONENTS_OK | FULL_SMOKE_OK | ALL_COMPONENTS_OK
FULL | 4 | ANY_COMPONENT_OK | FULL_SMOKE_PARTIAL | COMPONENTS_NOT_ALL_OK
FULL | 5 | ANY_COMPONENT_FAILED | FULL_SMOKE_FAILED | COMPONENT_FAILURE
FULL | 6 | OTHERWISE | FULL_SMOKE_BLOCKED | COMPONENTS_BLOCKED
```
<!-- MANAGER_PRECEDENCE_END -->

Basic components are ACM_CUSTOM and API. Precedence is:

1. global safety stop -> `BASIC_SMOKE_BLOCKED`;
2. invalid input evidence -> `BASIC_SMOKE_BLOCKED`;
3. both components OK -> `BASIC_SMOKE_OK`;
4. any attempted failure -> `BASIC_SMOKE_FAILED`;
5. otherwise -> `BASIC_SMOKE_BLOCKED`.

Full components are ACM_CUSTOM, ACM, BDA and API. Precedence is:

1. global safety stop -> `FULL_SMOKE_BLOCKED`;
2. invalid input evidence -> `FULL_SMOKE_BLOCKED`;
3. all components OK -> `FULL_SMOKE_OK`;
4. at least one OK and at least one non-OK -> `FULL_SMOKE_PARTIAL`;
5. no OK and at least one attempted failure -> `FULL_SMOKE_FAILED`;
6. otherwise -> `FULL_SMOKE_BLOCKED`.

The full planning profile therefore does not consume a pre-existing
`BASIC_SMOKE_OK`; both summaries are produced only after component evaluation.

## Compatibility and blocked operations

Scenario JSON, Flask routes, generation, dry-run, adapter-run, API catalog, UI,
runtime profile resources, `safe_for_real_execution`, `execution_status` and
`mode=real` remain unchanged. Automated evidence is mock-only and uses injected
fake drivers/clients. It must not contact DNS, network, Oracle, HTTP, Kafka,
Jenkins or a subprocess.

Independent acceptance was recorded for implementation head `983bace` after
`676 passed`, adversarial reference probes and clean diff checks. The Alpha
Manager may therefore close `CONTRACT_CONFLICT-001`. Acceptance and conflict
closure are governance evidence only; they are not operational release.
