# ACM QA4 Local Runtime Preflight Contract

Classification: `SAFE_LOCAL` / `MOCK_ONLY`.

This contract validates private local runtime integrity without importing an
Oracle driver, resolving a destination, opening a socket, authenticating,
executing SQL or starting a subprocess.

## Fixed allowlist

- checkpoint: `ORACLE_ACM_TECHNICAL_READ_ONLY_01`
- environment: `qa4`
- profile: `smartoffers_qa4_full_smoke`
- resource_id: `acm_db`

Any different value returns `ACM_RUNTIME_BLOCKED` and
`allowlist_validation=DENIED`.

## ACM-only local refs

```text
SMARTOFFERS_QA4_ACM_SMOKE_SQL
SMARTOFFERS_QA4_ACM_SMOKE_SQL_SHA256
SMARTOFFERS_QA4_ACM_DESTINATION_FINGERPRINT
SMARTOFFERS_QA4_ACM_DB_DSN
SMARTOFFERS_QA4_ACM_DB_USER
SMARTOFFERS_QA4_ACM_DB_PASSWORD
SMARTOFFERS_ORACLE_CLIENT_LIB_DIR
```

The preflight accepts no ACM_CUSTOM alias, ref, SQL, hash or fingerprint. ACM
and ACM_CUSTOM remain independent resources.

## Local checks

The approved SQL is normalized by trimming surrounding whitespace and removing
one final semicolon. Its local SHA-256 must match the ACM SQL hash ref.

The destination is normalized by removing whitespace and lowercasing it. Its
local SHA-256 must match the ACM destination fingerprint ref.

The only result fields are allowlist metadata, ref names, missing ref names and
the following status tokens:

```text
ACM_RUNTIME_READY
ACM_RUNTIME_BLOCKED
MATCH
DENIED
```

`refs_validation=READY` means every ACM-only ref is present. Any missing ACM
ref returns `refs_validation=BLOCKED`.

`ACM_RUNTIME_READY` requires a matching allowlist, every ACM-only ref present,
`sql_hash_validation=MATCH` and `fingerprint_validation=MATCH`. It does not
authorize an ACM connection. A separate ACM operational release is required
before any future execution.
