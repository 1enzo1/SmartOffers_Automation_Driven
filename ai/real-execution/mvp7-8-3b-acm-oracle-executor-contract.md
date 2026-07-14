# MVP7.8.3B Oracle ACM Executor Contract

Status: implementation only. Execution remains blocked until a future ACM
operational release is issued.

The executor accepts only `ORACLE_ACM_TECHNICAL_READ_ONLY_01` for `qa4`,
`smartoffers_qa4_full_smoke` and `acm_db`. API mode is `omitted`.

Before driver loading it requires all of the following:

- `BASIC_SMOKE_OK`;
- `EXECUTION_APPROVED`;
- `OPERATIONAL_EXECUTION_RELEASED`;
- `ACM_RUNTIME_READY` from the independent ACM local preflight;
- one attempt, zero retry, `5/5/15` timeouts;
- one row and one column limits;
- fallback, credential guessing and alternative password disabled.

Only ACM refs are accepted: the ACM SQL, hash, destination fingerprint, DSN,
user, password and Oracle client ref. ACM_CUSTOM aliases, BDA, API, Kafka,
Jenkins, FTM, adapter-run and legacy runners are outside this contract.

The executor validates allowlist, local SQL hash, destination fingerprint and
read-only SQL before connecting. It creates at most one connection, cursor and
execute call. It rejects zero or multiple columns, zero rows and more than one
row, never commits, rolls back defensively and closes resources in `finally`.

Output is one sanitized JSON object with no runtime values, SQL, result value,
host, DSN, credential, hash or fingerprint.
