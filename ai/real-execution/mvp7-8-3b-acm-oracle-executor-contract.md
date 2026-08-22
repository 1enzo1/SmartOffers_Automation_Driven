# MVP7.8.3B Oracle ACM Executor Contract

Status: implementation only. Execution remains blocked until a future ACM
operational release is issued.

The executor accepts only `ORACLE_ACM_TECHNICAL_READ_ONLY_01` for `qa4`,
`smartoffers_qa4_full_smoke` and `acm_db`. API mode is `omitted`.

ACM is an independent database branch. It consumes only its own runtime,
safety and operational guards; ACM_CUSTOM, BDA, API and smoke-summary statuses
are not predecessors.

Before driver loading it requires all of the following:

- `EXECUTION_APPROVED`;
- `OPERATIONAL_EXECUTION_RELEASED`;
- `ACM_RUNTIME_READY` from the independent ACM local preflight;
- one attempt, zero retry, `5/5/15` timeouts;
- one row and one column limits;
- fallback, credential guessing and alternative password disabled.

The retained `--basic-smoke-status` option is deprecated parser compatibility.
It is optional and ignored: absent, matching or divergent values neither
authorize nor suppress ACM.

Only ACM refs are accepted: the ACM SQL, hash, destination fingerprint, DSN,
user, password and Oracle client ref. ACM_CUSTOM aliases, BDA, API, Kafka,
Jenkins, FTM, adapter-run and legacy runners are outside this contract.

The executor validates allowlist, local SQL hash, destination fingerprint and
read-only SQL before connecting. It creates at most one connection, cursor and
execute call. It rejects zero or multiple columns, zero rows and more than one
row, never commits, rolls back defensively and closes resources in `finally`.

Output is one sanitized JSON object with no runtime values, SQL, result value,
host, DSN, credential, hash or fingerprint. It includes bounded validation
labels such as `fingerprint_validation=MATCH|DENIED`,
`result_shape_validation=MATCH|DENIED` and
`sensitive_values_logged=false`; a denied fingerprint returns
`sanitized_error_category=FINGERPRINT_DENIED` without changing the blocked
execution behavior. The pure Alpha gate normalizer may map a successful
sanitized result to `ACM_DB_CHECKPOINT_OK`. That mapping is evidence only and
does not release operational execution, which remains blocked.
