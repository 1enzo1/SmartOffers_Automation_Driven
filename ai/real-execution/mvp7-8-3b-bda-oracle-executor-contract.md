# MVP7.8.3B BDA Oracle Executor Contract

Status: implementation only. The BDA command remains blocked until a future
review renews all gates and emits an operational release for one attempt.

The executor accepts only `ORACLE_BDA_TECHNICAL_READ_ONLY_01` for `qa4`,
`smartoffers_qa4_full_smoke` and `bda_db`. API mode is `omitted`.

BDA is an independent database branch. It consumes only its own runtime,
safety and operational guards; ACM_CUSTOM, ACM, API and smoke-summary statuses
are not predecessors.

Before dynamic driver loading it requires:

- `BDA_RUNTIME_READY` from the independent BDA preflight;
- `EXECUTION_APPROVED`;
- `OPERATIONAL_WINDOW_ACTIVE=true`;
- `OPERATIONAL_EXECUTION_RELEASED`;
- one attempt, zero retry, `5/5/15` timeouts;
- one row and one column limits;
- fallback, credential guessing and alternative password disabled.

The retained `--basic-db-checkpoint-status` option is deprecated parser
compatibility. It is optional and ignored: absent, matching or divergent
values neither authorize nor suppress BDA. `BASIC_DB_CHECKPOINT_OK` is not a
canonical gate.

Only BDA SQL, hash, destination fingerprint, DSN, user, password and Oracle
client refs are accepted. ACM, ACM_CUSTOM and legacy database aliases are not
accepted.

The executor verifies allowlist, local hash, local fingerprint and read-only
SQL before dynamic driver loading. It creates at most one connection, cursor
and execute call, never commits, rolls back defensively and closes resources in
`finally`. Results are limited to one row and one column and are never emitted.

It outputs one sanitized JSON object with `BDA_DB_CHECKPOINT_OK`,
`BDA_DB_CHECKPOINT_FAILED` or `BDA_DB_CHECKPOINT_BLOCKED`. Runtime values, SQL,
query results, host, credentials, hashes and fingerprints are never emitted.
The existing bounded result-shape, fingerprint and sensitive-logging labels
are preserved. The pure Alpha gate normalizer may map a successful sanitized
result to canonical `BDA_DB_CHECKPOINT_OK`; this evidence mapping does not
release operational execution, which remains blocked.
