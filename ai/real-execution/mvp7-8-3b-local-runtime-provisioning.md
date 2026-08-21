# MVP7.8.3B Local Runtime Provisioning

Status: provisioning and validation only. This guide does not authorize a real
connection, query, API call, authentication attempt or executor invocation.

## Objective and scope

This guide describes how an authorized operator prepares the private local
runtime for the sanitized QA4 smoke profiles. Runtime values must exist only
under `local_secrets/`, which must remain ignored and untracked by Git.

Principles:

- obtain operational values through an approved corporate secret channel;
- use only placeholders in versioned files and documentation;
- never print, log or copy runtime values into Git, PRs, issues, chat or docs;
- validate presence and integrity without loading an Oracle driver;
- do not resolve DNS, open sockets, authenticate, connect or execute SQL;
- do not guess credentials, retry or use alternative passwords;
- stop when any required ref is empty or any integrity comparison fails.

## Recommended local structure

The operator maintains one private file:

```text
local_secrets/
  smartoffers_runtime_local.ps1
```

The directory and file are local-only. Do not create `.env`, connection export,
database profile, ZIP or evidence copies containing runtime values.

## Basic profile refs

`smartoffers_basic_smoke` requires:

```text
SMARTOFFERS_QA4_API_URL
SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN
SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER
SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD
SMARTOFFERS_ORACLE_CLIENT_LIB_DIR
```

`SMARTOFFERS_QA4_DB_*` remains a deprecated alias only for ACM_CUSTOM. New
provisioning must use the explicit ACM_CUSTOM refs.

## Full profile refs

`smartoffers_qa4_full_smoke` adds these refs for future local provisioning:

```text
SMARTOFFERS_QA4_ACM_DB_DSN
SMARTOFFERS_QA4_ACM_DB_USER
SMARTOFFERS_QA4_ACM_DB_PASSWORD
SMARTOFFERS_QA4_BDA_DB_DSN
SMARTOFFERS_QA4_BDA_DB_USER
SMARTOFFERS_QA4_BDA_DB_PASSWORD
```

ACM and BDA are independent resources and do not accept ACM_CUSTOM aliases.
Provisioning these refs does not authorize ACM or BDA execution. They require
separate checkpoints, contracts and operational releases.

## Approved ACM_CUSTOM checkpoint refs

The currently approved provisioning contract is limited to
`ORACLE_ACM_CUSTOM_TECHNICAL_READ_ONLY_01` and `acm_custom_db`:

```text
SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL
SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256
SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT
```

The SQL must be approved separately, read-only, single-statement and designed
to return at most one row and one column. The SQL text, hash and fingerprint
must never be copied into this document.

## PowerShell placeholders

The private local file may follow this shape. Replace placeholders only inside
the ignored local file and only from the approved secret channel.

```powershell
$env:SMARTOFFERS_QA4_API_URL = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD = "<LOCAL_SECRET>"
$env:SMARTOFFERS_ORACLE_CLIENT_LIB_DIR = "<LOCAL_PATH>"

$env:SMARTOFFERS_QA4_ACM_DB_DSN = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_ACM_DB_USER = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_ACM_DB_PASSWORD = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_BDA_DB_DSN = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_BDA_DB_USER = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_BDA_DB_PASSWORD = "<LOCAL_SECRET>"

$env:SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL = "<APPROVED_LOCAL_SQL>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256 = "<APPROVED_LOCAL_SHA256>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT = "<APPROVED_LOCAL_FINGERPRINT>"
```

Do not place real values in a versioned example, command history or terminal
output.

## Local SHA-256 calculation

The approved SQL hash is calculated once from the normalized SQL. Normalization
trims surrounding whitespace and removes one optional final semicolon plus its
trailing whitespace. The calculated value must not be printed.

The destination fingerprint is calculated from the ACM_CUSTOM DSN after all
whitespace is removed and the result is converted to lowercase. It must not be
printed.

The following PowerShell performs only in-memory calculation and comparison.
It does not load a database driver or open a connection.

```powershell
function Get-LocalSha256([string]$Value) {
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return -join ($sha256.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })
    }
    finally {
        $sha256.Dispose()
    }
}

$sql = ([string]$env:SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL).Trim()
if ($sql.EndsWith(";")) {
    $sql = $sql.Substring(0, $sql.Length - 1).TrimEnd()
}

$calculatedSqlHash = Get-LocalSha256 $sql
$approvedSqlHash = ([string]$env:SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256).Trim()
$sqlHashMatches = [bool](
    $sql -and
    $approvedSqlHash -and
    ($calculatedSqlHash -ceq $approvedSqlHash)
)
if ($sqlHashMatches) {
    Write-Output "SQL_HASH_MATCH"
}
else {
    Write-Output "SQL_HASH_DENIED"
}

$dsn = -join (([string]$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN) -split "\s+")
$dsn = $dsn.ToLowerInvariant()
$calculatedFingerprint = Get-LocalSha256 $dsn
$approvedFingerprint = ([string]$env:SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT).Trim()
$fingerprintMatches = [bool](
    $dsn -and
    $approvedFingerprint -and
    ($calculatedFingerprint -ceq $approvedFingerprint)
)
if ($fingerprintMatches) {
    Write-Output "FINGERPRINT_MATCH"
}
else {
    Write-Output "FINGERPRINT_DENIED"
}
```

Do not write `$calculatedSqlHash` or `$calculatedFingerprint` to standard output,
logs or evidence. Store approved static values in the private runtime; do not
recalculate them automatically every time the runtime loads.

## Presence and integrity validation without connection

This validation checks ref presence and consumes the local integrity results. It
does not load the executor, Oracle client or any network library. Run the local
SHA-256 calculation above first in the same PowerShell session. `RUNTIME_READY`
requires every ref, `SQL_HASH_MATCH` and `FINGERPRINT_MATCH`.

```powershell
$requiredRefs = @(
    "SMARTOFFERS_QA4_API_URL",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD",
    "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL",
    "SMARTOFFERS_QA4_ACM_CUSTOM_SMOKE_SQL_SHA256",
    "SMARTOFFERS_QA4_ACM_CUSTOM_DESTINATION_FINGERPRINT"
)

$runtimeReady = $true
foreach ($ref in $requiredRefs) {
    $value = [Environment]::GetEnvironmentVariable($ref)
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Output ("REF_EMPTY " + $ref)
        $runtimeReady = $false
    }
    else {
        Write-Output ("REF_PRESENT " + $ref)
    }
}

if ($sqlHashMatches -ne $true -or $fingerprintMatches -ne $true) {
    $runtimeReady = $false
}

if ($runtimeReady) {
    Write-Output "RUNTIME_READY"
}
else {
    Write-Output "RUNTIME_BLOCKED"
}
```

Permitted output tokens are:

```text
REF_PRESENT
REF_EMPTY
SQL_HASH_MATCH
SQL_HASH_DENIED
FINGERPRINT_MATCH
FINGERPRINT_DENIED
RUNTIME_READY
RUNTIME_BLOCKED
```

## Output policy

Permitted:

- ref names;
- boolean readiness states;
- approved status tokens listed above;
- sanitized error categories and stop reasons.

Prohibited:

- URL, host, IP, port, SID, service name or DSN value;
- user, password, token, cookie or authorization header;
- SQL text, calculated hash or destination fingerprint;
- payload, response body, MSISDN, account or customer data;
- driver error, connection string or stack trace containing runtime values.

## Approval gates

`EXECUTION_APPROVED` is an architectural approval for the exact checkpoint,
environment, profile, resource and one-attempt contract. It is not sufficient
to start an operation by itself.

`OPERATIONAL_EXECUTION_RELEASED` is a separate release for the controlled
operational window. Both gates must be explicit and scoped. They must be absent
by default. Provisioning and validation do not set either gate.

ACM and BDA remain blocked even if their local refs are present. Their values
must not be reused through the ACM_CUSTOM checkpoint.

## Pre-execution checklist

- [ ] Runtime file is under ignored `local_secrets/` only.
- [ ] Selected profile and checkpoint have explicit approvals.
- [ ] Required refs report `REF_PRESENT` without printing values.
- [ ] Approved SQL reports `SQL_HASH_MATCH`.
- [ ] Destination fingerprint reports `FINGERPRINT_MATCH`.
- [ ] Runtime presence reports `RUNTIME_READY`.
- [ ] SQL is approved as one row, one column and read-only.
- [ ] Attempts, retry and finite timeouts match the approved contract.
- [ ] No fallback, credential guessing or alternative password is allowed.
- [ ] ACM and BDA remain blocked unless separately approved.
- [ ] `EXECUTION_APPROVED` and `OPERATIONAL_EXECUTION_RELEASED` are reviewed as
      separate gates immediately before any future operation.

## Troubleshooting

### CONFIG_MISSING

One or more required refs are empty. Stop. Obtain the missing value through the
approved secret channel, update only the private local runtime and repeat the
presence validation. Do not guess or copy values from another resource.

### HASH_MISMATCH

The normalized SQL does not match the approved static SHA-256. Stop. Do not
recalculate and overwrite the approved hash automatically. Ask the checkpoint
owner to confirm the approved SQL and hash through the secret channel.

### FINGERPRINT_MISSING

The approved destination fingerprint is absent or validation reports
`FINGERPRINT_DENIED`. `RUNTIME_READY` must remain false and `RUNTIME_BLOCKED`
must be emitted. Stop. Do not connect and do not reuse another resource
fingerprint. Ask the environment owner to provision or confirm the approved
static fingerprint in the private local runtime.
