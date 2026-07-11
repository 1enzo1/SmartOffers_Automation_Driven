# MVP7.8.3B Controlled Manual Smoke Checklist

Status: planning only. Do not connect or call any external system.

## Before Architect Review

- [ ] Profile is `smartoffers_basic_smoke`.
- [ ] Environment is `qa4`.
- [ ] Operator and execution window are referenced through sanitized placeholders.
- [ ] Resource list matches the selected runtime profile.
- [ ] Allowlist contains no production or redirect destination.
- [ ] Every timeout is finite and positive.
- [ ] Attempts equal one and retry equals zero.
- [ ] Automatic fallback and credential guessing are disabled.
- [ ] Oracle category is read-only and the technical query category is approved.
- [ ] API operation identifier is approved or the API checkpoint is explicitly omitted.
- [ ] Evidence fields and stop reasons are sanitized.
- [ ] adapter-run real mode, automated execution, Kafka, Jenkins and FTM Engine remain blocked.

## Stop Immediately

- Destination is outside the allowlist.
- Environment differs from `qa4`.
- Redirect, authentication error, timeout or unclassified Oracle error occurs.
- A write, unapproved query, sensitive output, unexpected subprocess or second retry is requested.
- Sanitization fails.

## Architect Decision

- [ ] `EXECUTION_APPROVED` received for one manual attempt.
- [ ] Otherwise keep `EXECUTION_BLOCKED` and do not run any checkpoint.
