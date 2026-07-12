# MVP7.8.3B Oracle ACM_CUSTOM Executor Contract

Status: implementation review only. Do not execute this checkpoint before OPERATIONAL_EXECUTION_RELEASED.

The executor accepts only `ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01` for `qa4` and `smartoffers_basic_smoke`. API mode is `omitted`; ACM, BDA, Kafka, Jenkins, FTM Engine, legacy subprocesses and adapter-run real mode are outside the contract.

The local runtime provides the ACM_CUSTOM connection references, Oracle client directory, approved technical SELECT, approved query hash and destination fingerprint. These values never enter Git, command arguments or output.

The executor requires both `EXECUTION_APPROVED` and `OPERATIONAL_EXECUTION_RELEASED`, one attempt, zero retry, no fallback, no alternate credential, connect timeout 5, read timeout 5 and total timeout 15. It validates the destination by local fingerprint, validates the exact query hash, rejects non-SELECT or multi-statement text and closes the session with defensive rollback.

Output is one sanitized JSON object. It never includes endpoint values, host, IP, DSN, user, password, SQL text, payload, response body or returned query value.
