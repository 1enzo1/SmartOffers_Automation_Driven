# BDA QA4 Local Runtime Preflight Contract

Classification: `SAFE_LOCAL` / `MOCK_ONLY`.

This contract validates private local BDA runtime integrity without importing an
Oracle driver, resolving a destination, opening a socket, authenticating,
executing SQL or starting a subprocess.

## Fixed allowlist

- checkpoint: `ORACLE_BDA_TECHNICAL_READ_ONLY_01`
- environment: `qa4`
- profile: `smartoffers_qa4_full_smoke`
- resource_id: `bda_db`
- connection_allowed: `false`
- sql_execution_allowed: `false`

Any different request value returns `BDA_RUNTIME_BLOCKED` and
`allowlist_validation=DENIED`.

## BDA-only local refs

```text
SMARTOFFERS_QA4_BDA_SMOKE_SQL
SMARTOFFERS_QA4_BDA_SMOKE_SQL_SHA256
SMARTOFFERS_QA4_BDA_DESTINATION_FINGERPRINT
SMARTOFFERS_QA4_BDA_DB_DSN
SMARTOFFERS_QA4_BDA_DB_USER
SMARTOFFERS_QA4_BDA_DB_PASSWORD
SMARTOFFERS_ORACLE_CLIENT_LIB_DIR
```

The preflight accepts no ACM or ACM_CUSTOM alias, ref, SQL, hash or
fingerprint. BDA remains an independent resource.

## Local checks

The approved SQL is normalized by trimming surrounding whitespace and removing
one final semicolon. Its local SHA-256 must match the BDA SQL hash ref.

The destination is normalized by removing whitespace and lowercasing it. Its
local SHA-256 must match the BDA destination fingerprint ref.

`refs_validation=READY` means every BDA-only ref is present. Any missing BDA
ref returns `refs_validation=BLOCKED`.

`BDA_RUNTIME_READY` requires a matching allowlist, every BDA-only ref present,
`sql_hash_validation=MATCH` and `fingerprint_validation=MATCH`.

## Non-execution boundary

This is a local integrity contract only. `BDA_RUNTIME_READY` does not authorize
an Oracle connection, SQL execution, an executor, API access or an operational
release. BDA real execution remains outside this contract.
