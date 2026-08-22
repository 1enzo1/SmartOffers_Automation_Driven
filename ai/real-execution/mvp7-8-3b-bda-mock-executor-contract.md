# MVP7.8.3B BDA Mock Executor Contract

Classification: `SAFE_LOCAL` / `MOCK_ONLY`.

`tools/qa4_bda_mock_executor.py` simulates the BDA technical checkpoint with
internal `FakeDriver`, `FakeConnection` and `FakeCursor` classes only. It has
no runtime-file loading, network path, external driver loading or real SQL
path.

## Fixed contract

- checkpoint: `ORACLE_BDA_TECHNICAL_READ_ONLY_01`
- environment: `qa4`
- profile: `smartoffers_qa4_full_smoke`
- resource_id: `bda_db`
- API mode: `omitted`
- attempts/retry: `1` / `0`
- timeouts: `5` / `5` / `15`
- result limits: one row and one column
- fallback, credential guessing and alternative password: disabled

## Mock-only gates

The BDA mock branch is independent and consumes only its own runtime, safety
and operational guards. The simulation requires `BDA_RUNTIME_READY`,
`EXECUTION_APPROVED`, `OPERATIONAL_WINDOW_ACTIVE=true` and
`OPERATIONAL_EXECUTION_RELEASED` as test inputs only. These tokens do not
authorize a BDA connection.

The retained `--basic-db-checkpoint-status` option is deprecated parser
compatibility. It is optional and ignored: absent, matching or divergent
values neither authorize nor suppress the fake simulation.
`BASIC_DB_CHECKPOINT_OK` is not a canonical gate.

The BDA preflight remains the source of local hash, fingerprint and allowlist
validation. Its `connection_allowed=false` and `sql_execution_allowed=false`
remain unchanged because the executor simulates rather than performs both
actions.

## Isolation and output

Only BDA refs are accepted. ACM and ACM_CUSTOM refs, aliases and integrity
material are not accepted or imported.

Success emits one sanitized JSON object with `MOCK_EXECUTION_OK` and the
simulation flags. Any invalid gate, integrity result, SQL policy violation,
timeout or result-limit violation emits a sanitized blocked object. No runtime
value, query text, hash, fingerprint, host, credential or result is emitted.
