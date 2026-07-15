# QA4 API Health Checkpoint Contract

Status: mock-first implementation only. This contract does not authorize a
network request, DNS lookup, authentication attempt, adapter-run real mode or
any use of a private runtime.

## Fixed Contract

| Field | Value |
| --- | --- |
| checkpoint | `SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01` |
| api_operation_id | `smartoffers_api_health_readiness_01` |
| environment | `qa4` |
| profile | `smartoffers_basic_smoke` |
| resource_id | `smartoffers_api` |
| method | `GET` |
| access mode | `read_only` |
| attempts / retry | `1` / `0` |
| redirects / fallback | `false` / `false` |
| timeouts | `5` / `5` / `15` |
| allowed HTTP status | `200` only |

The checkpoint has no payload, query parameters, path parameters, customer
identifiers, response body logging or response header logging. The catalog
entry remains `blocked` and `safe_for_real_execution=false`.

## Private Runtime Refs

Store values only in `local_secrets/smartoffers_runtime_local.ps1`; it must
remain ignored by Git. Only these names are part of the initial contract:

```text
SMARTOFFERS_QA4_API_URL
SMARTOFFERS_QA4_API_HEALTH_PATH
SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256
SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT
```

Use placeholders in the local template only:

```powershell
$env:SMARTOFFERS_QA4_API_URL = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_API_HEALTH_PATH = "<LOCAL_SECRET>"
$env:SMARTOFFERS_QA4_API_HEALTH_PATH_SHA256 = "<APPROVED_LOCAL_SHA256>"
$env:SMARTOFFERS_QA4_API_DESTINATION_FINGERPRINT = "<APPROVED_LOCAL_FINGERPRINT>"
```

Authentication is not assumed. The service owner must explicitly confirm that
this exact technical health path accepts unauthenticated `GET` without headers.
If authentication is required, this checkpoint remains blocked until a new
approved contract introduces a dedicated opaque authentication reference.

## Local Integrity Validation

The operator calculates the SHA-256 values locally without printing either
input or digest. The path is hashed exactly after trimming outer whitespace.
The destination fingerprint is the SHA-256 of the destination after whitespace
is removed and case is normalized. The local preflight compares both computed
values with their approved local references.

Allowed preflight output contains only contract metadata, ref names and these
tokens: `API_RUNTIME_READY`, `API_RUNTIME_BLOCKED`, `MATCH`, `DENIED`, `READY`
and `BLOCKED`. It must never include a URL, path, hash, fingerprint, token,
header, response or other runtime value.

## Gates And Transport

The executor requires `BASIC_SMOKE_OK`, `EXECUTION_APPROVED`,
`OPERATIONAL_EXECUTION_RELEASED` and a freshly computed `API_RUNTIME_READY`
before loading its real HTTP transport. Automated tests use only
`FakeHttpClient` and `FakeResponse`.

The real transport is structurally redirect-deny: it sends one `GET` at most
and does not follow 3xx responses. A 3xx response produces
`REDIRECT_DENIED`; any status other than 200, timeout, authentication failure,
response-limit breach or unexpected transport error stops immediately. Evidence
is one sanitized JSON object and omits body and headers.

## Service Owner Confirmation

Before an operational release, request a response through the approved secure
channel covering only these points:

1. The health path is a technical `GET` with no state change.
2. It accepts no payload, query parameter, variable path segment or customer identifier.
3. The expected success status is 200 and the response is within the approved finite limit.
4. Authentication is not required; otherwise the checkpoint remains blocked.
5. Redirects are not part of the endpoint behavior.

No endpoint, path, header, token or response content belongs in Git, chat, PR,
issues, documentation or logs.
