# SmartOffers - Current Product Usage

This guide describes what a normal user or operator can do with the current
`codex/post-alpha-ux` product. It describes repository and rendered-product
reality, not planned capabilities. The UI was inspected locally on 31 August
2026 without provisioning an operational release, sending a QA request, or
running a database query.

## 1. What SmartOffers is today

SmartOffers is a Flask-based QA test workspace. Its main purpose is to select a
QA4 capability, validate whether it can run safely, execute it only when every
governed prerequisite is present, and show the result and sanitized evidence.

The primary product is **QA-first**. Scenario generation, dry-run, adapter mocks,
and the legacy runner remain available under **Diagnostics** for local
development and investigation. A successful diagnostic is not proof of a QA
execution.

The current product catalog contains:

| Capability | Visible status | What it means today |
| --- | --- | --- |
| Create Customer with Offer | `QA READY` | The governed composite execution contract exists, but a fresh application process cannot execute it until an exact server-side authorization/release and live runtime are supplied. Database post-condition validation is not configured. |
| Recharge Basic | `LOCAL DIAGNOSTIC` | Local deterministic generation and fake-adapter request-plan checks exist. QA execution is not available. |
| Add Offer Basic | `UNAVAILABLE` | The standalone operation contract, governed offer input, and read-only validation contract are missing. |

## 2. Opening the application

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/` in a browser. The Flask development process must
remain running while the UI is in use.

The initial page shows:

- sidebar actions: **Run a test**, **Historical runs**, and collapsed
  **Diagnostics**;
- a fixed environment selector containing `QA4`;
- a grouped Test selector;
- disabled **Validate** and **Execute in QA** buttons until a test is selected;
- collapsed technical details.

The product does not show fields for customer, line, account, MSISDN, offer, or
credentials. Test data for the governed product flow is synthetic and owned by
the server-side contract.

## 3. Main workspace

### Run a test

This is the primary QA workspace. Use it to select a capability, validate its
readiness, see why execution is blocked or allowed, and inspect the current
result/evidence.

The arrow at the top of the sidebar only collapses or expands navigation; it
does not change product state. The header clock is informational.

### Historical runs

This is the separate read-only history view. It lists only persisted,
sanitized controlled-run artifacts. It does not list local diagnostic summaries.

### Diagnostics

This disclosure contains the legacy **Generator** and **Execution** workspaces.
It is secondary to the QA product flow and remains collapsed on initial load.

### Advanced diagnostics

This second disclosure contains legacy runner controls and runtime-oriented
diagnostic information. It is intended for developers or experienced
operators. Do not use its manual-real controls as an alternative to the
governed **Execute in QA** product path.

## 4. Selecting a QA test

The Test selector is grouped into:

- **Available for QA**: Create Customer with Offer;
- **Diagnostic / not available**: Recharge Basic and Add Offer Basic.

Selecting a test shows a short description and its truthful product status.
It also enables **Validate**. Changing the selection clears the previous
readiness, result, validation context, and current evidence reference.

## 5. Validate

**Validate** answers: "Can this selected capability proceed in its current
mode?" It does not send a QA request and does not consume the real one-shot
attempt.

For Create Customer with Offer it checks the current source/runtime contract
surface, including:

- QA4 environment;
- synthetic test data;
- operation and scenario binding;
- destination contract;
- evidence capture;
- one-shot capability;
- authorization/release availability.

The primary readiness summary contains three rows:

- **Infrastructure** - whether the product binding and static execution
  prerequisites are present;
- **Authorization** - whether a suitable server-side release can supply a
  one-use validation context;
- **DB verification** - whether an independent database post-condition check
  exists.

Granular technical readiness messages are available under **Technical
readiness details** and are collapsed by default. The current backend supplies
the infrastructure and authorization checks, while the frontend can append
execution, DB, and authorization summaries; treat this disclosure as supporting
detail rather than a fixed-count checklist.

A normal fresh application process currently shows:

```text
Infrastructure   Ready
Authorization    Required
DB verification  Not configured
```

This means the execution contract exists, but execution is not yet authorized.
It does **not** mean that database verification blocks execution: DB verification
is a separate post-execution limitation.

When an exact operational release was already provisioned inside the server
process, Validate may reserve a short-lived opaque one-use context. The browser
receives only that reference. It never receives the authorization, runtime,
destination, credential, or controlled execution plan.

Validation can be blocked by an unknown test, unavailable capability, missing
contract mapping, missing/expired operational release, or a local application
error. A successful Validate is readiness information; it is not an execution
result and does not itself authorize a QA request.

## 6. Execute in QA

**Execute in QA** is the only normal product action intended to reach the
governed controlled QA stack. It is enabled only when:

1. Create Customer with Offer is selected;
2. Validate returned a valid result;
3. an exact, unexpired server-side operational release supplied a one-use
   context.

An enabled button proves that this server-side context was reserved; it is not
proof that every live gate will still pass. On click, the server rechecks the
controlled contract, destination attestation, live runtime, evidence path, and
one-shot prerequisites. A gate that became unavailable can still produce a
`BLOCKED` result without sending a request.

There is no browser control for creating authorization or runtime state. The
browser submits only `EXECUTE_IN_QA` intent and the opaque context reference.

If authorization is absent, the disabled button is accompanied by:

> Authorization required before QA execution.

If the button is enabled and clicked, the server claims the context once and
delegates to the existing Standard Runner, controlled bridge, adapter, evidence
writer, and result mapping. Production remains blocked. Automatic retry and
fallback are disabled.

**One-shot** means that the real request budget is a single attempt. The budget
is reserved immediately before the external send. A failure before any send may
leave the budget unused; a timeout or ambiguous outcome after the request may
have been sent consumes the attempt. The product must not retry automatically.

The Run 03A source path is statically prepared, but a normal local start does
not create its Owner authorization or operational release. Do not click or
attempt to enable Execute for Run 03A without the separate operator procedure
in `RUN_03A_OPERATOR_RUNBOOK.md`.

## 7. Results

The Result card makes one of these states dominant:

| Result | What it means | What it does not mean | What to do next |
| --- | --- | --- | --- |
| `PASS` | The operation or local diagnostic satisfied the verification available for that path. | It does not automatically prove the database post-condition. A local diagnostic PASS is not a QA execution. | Check the verification type and evidence availability. |
| `FAIL` | A request or diagnostic ran, but its expected contract/result was not achieved. | It is not the same as a safety gate preventing execution. | Review the sanitized reason and evidence; do not retry a governed one-shot run automatically. |
| `BLOCKED` | The operation was not allowed to proceed safely, or the capability is unavailable. | It is not proof that QA itself failed. | Read the visible reason and satisfy the missing prerequisite, or leave the unavailable capability unchanged. |

Supporting fields include the selected test, environment, duration, attempts
when applicable, validation type, DB verification status, and evidence status.

Execution verification and database post-condition verification are separate:
a successful controlled HTTP result may be reported while DB verification
continues to say **Not configured**.

## 8. Evidence

Evidence is the sanitized durable record associated with a controlled run. It
is used to confirm what the governed runtime reported and to support later
review without exposing operational secrets.

Depending on the run, the public record can contain:

- run identifier and timestamp;
- source revision when available;
- environment and product/scenario identity;
- preflight and request/response state;
- HTTP status class;
- attempt transition and retry count;
- `PASS`, `FAIL`, or `BLOCKED` result;
- database validation state.

It deliberately excludes endpoints, hosts, DSNs, credentials, authorization
headers, raw request/response bodies, full customer identifiers, real offer
codes, operational SQL, and internal runtime values.

After a run with persisted evidence, **View evidence** loads the sanitized
record for that active run. Local diagnostic summaries are not persisted as
controlled evidence and therefore do not produce the same evidence action.

## 9. History

**Historical runs** is independent from the current Result card. Each card
represents one persisted controlled artifact and shows:

- status (`PASS`, `FAIL`, or `BLOCKED`);
- the best truthful scenario/test label available in the artifact;
- environment;
- human-readable UTC date and time;
- a collapsed **View details** disclosure.

Expanded details show sanitized technical metadata such as the run ID,
scenario, classification, and **View sanitized evidence**. History does not
substitute one of its records for the active run's evidence.

The current repository includes an immutable historical Run 02 record displayed
as `FAIL` because its response was not durably confirmed. That classification
must not be rewritten as PASS based on historical narrative alone.

## 10. Create Customer with Offer

### Purpose

This product test wraps the recovered composite operation that creates a
synthetic customer/line together with a governed offer. It is not a standalone
customer-only operation and is not the same as standalone Add Offer.

### What the user sees

- Environment: fixed to QA4;
- Test: Create Customer with Offer;
- status: `QA READY`;
- no manually entered customer or offer fields;
- **Validate**;
- readiness summary and collapsed technical checks;
- **Execute in QA**, normally disabled until authorization/release exists;
- Result and View evidence after an eligible run.

### Current behavior

Validate is non-mutating. On a fresh process it confirms infrastructure but
reports **Authorization Required** and **DB verification Not configured**.
Execute requires a separately supplied live runtime, exact Owner authorization,
short-lived operational release, destination attestation, and untouched
one-shot ledger.

If execution eventually returns PASS, that means the existing execution
contract classified the response as successful. It does not mean the new
customer/line state was independently confirmed in Oracle.

### DB verification not configured

There is no approved operation-scoped customer/line lookup, query hash,
database destination binding, and normalized expected result shape. The QA
operation may still execute under its separate authorization, but the product
must report that the database post-condition was not verified.

## 11. Recharge Basic

Recharge Basic is visible and selectable as `LOCAL DIAGNOSTIC`.

Today the repository can deterministically generate the tracked recharge
template and validate a fake-adapter request plan with no external calls. The
primary workspace allows the user to select Recharge and run **Validate**, but
keeps **Execute in QA** disabled. The inline reason correctly says that
execution is unavailable for this test.

The local recharge engine is available through the secondary Diagnostics
generator/adapter workflow and through local automated tests. The primary
Recharge catalog option does not currently expose a separate diagnostic-run
button. Therefore, from the main workspace the user can inspect and validate
the capability status but cannot execute Recharge in QA.

QA execution still needs an authoritative operation contract, complete request
schema, response/success semantics, governed adapter/bridge binding, and an
approved read-only post-condition validator.

## 12. Add Offer Basic

Add Offer Basic is visible and selectable as `UNAVAILABLE`. Validate returns a
clear `BLOCKED` result explaining that integration details need approval and
that no request was sent. Execute remains disabled.

The missing authoritative artifacts are:

- standalone operation identity and QA4 API contract;
- complete request schema;
- governed offer input/discovery contract;
- response success/failure semantics;
- approved read-only validation identity, query/hash, destination, and result
  shape.

Create Customer with Offer cannot fill these gaps: its offer is part of a
composite customer-create operation, while Add Offer is a distinct standalone
product action.

The current generic readiness component can show misleading Authorization/DB
rows after validating unavailable or diagnostic-only capabilities. For
Recharge and Add Offer, use the catalog status, inline Execute reason, and
BLOCKED result as the authoritative user guidance. This is a presentation
limitation, not evidence of QA or DB readiness.

## 13. Diagnostics

Diagnostics exists for local scenario design, simulation, and investigation.
It is secondary and must not be interpreted as the governed QA product path.

### Generator

The Generator workspace provides:

- template library and category filter;
- **Refresh** to reload templates or saved scenarios;
- guided question flow with **Previous** and **Next**;
- **Generate scenario** to create and save deterministic scenario JSON;
- **Clear** to reset the guided form;
- saved-scenario list;
- result tabs for Execution, Validation, Payload, and JSON;
- **Copy JSON**;
- export to DOCX, XLSX, or JSON after a scenario exists;
- **Simulate execution** for a local dry-run;
- **Open saved** and **Go to execution**.

The adapter section provides local mock mode, a visibly blocked real mode,
**Run adapter-run**, **Refresh adapters**, local adapter health, and **Run
Standard mock**. None of these actions is controlled QA execution.

### Execution

The legacy Execution workspace displays terminal output, per-scenario analysis,
and executed-scenario cards. Advanced diagnostics contains scenario selection,
filtering, live analysis, mock/dry-run/manual-real mode selectors, **Run tests**,
**Pause**, **Re-run**, and **Clear**.

Use mock and dry-run modes only for diagnostics. The presence of a
`real_qa_manual` option does not grant authorization and does not replace the
QA-first product route. Guardrails remain responsible for returning BLOCKED.

Some secondary Diagnostics copy remains in Portuguese. This is a known polish
limitation; it does not change the QA-first safety boundary.

## 14. Database capabilities today

The repository contains governed read-only checkpoint implementations for:

- BDA;
- ACM;
- ACM_CUSTOM.

It also contains one bounded BDA offer-discovery path used as an internal
prerequisite for the governed composite Create Customer with Offer operation.

These capabilities are internal automation/code paths. There is no Database
Explorer, no database page, and no Oracle query button in the current UI.
Database connectivity does not establish a campaign validator by itself.

The product currently lacks approved post-condition validation contracts for
Create Customer with Offer, Recharge, and standalone Add Offer. A future
validator requires an authoritative lookup identity, read-only query/hash,
destination/resource scope, and deterministic result shape.

## 15. Current limitations

- A fresh application process has no operational release, so Create Customer
  with Offer Validate stops at Authorization Required and Execute stays disabled.
- The UI cannot create Owner authorization, live runtime, or an operational
  release.
- Create Customer with Offer has no independent DB post-condition validation.
- Recharge has no governed QA mutation or DB validation contract.
- The primary Recharge option has no direct local-diagnostic Execute action;
  related local tooling is under Diagnostics.
- Add Offer is unavailable pending authoritative external contracts.
- Local diagnostics do not create controlled evidence.
- History contains only persisted sanitized controlled artifacts.
- Generic readiness rows for Recharge/Add Offer can be misleading; their
  catalog status and inline execution reason remain authoritative.
- Secondary Diagnostics retains mixed English/Portuguese legacy copy.
- The rendered app currently requests a favicon that is not present, producing
  a harmless local 404 in the browser console.

## 16. Safe actions vs governed actions

### Safe local actions

- open and navigate the UI;
- select any catalog capability;
- use Validate without sending a QA request;
- inspect readiness and collapsed technical details;
- view sanitized History records;
- use Generator templates and guided scenario creation;
- run local dry-runs, fake adapter-runs, and Standard mock diagnostics;
- export locally generated scenario/dry-run artifacts.

### Safe non-mutating actions

- Create Customer with Offer readiness validation;
- catalog and contract inspection;
- sanitized evidence/history reads;
- local adapter health and deterministic mock-plan checks.

Read-only Oracle checkpoints are governed internal tools, not normal UI actions;
they require a separate scoped authorization and runtime procedure.

### Real QA actions requiring authorization

- one controlled Create Customer with Offer execution through **Execute in QA**,
  after the exact live runtime, Owner authorization, operational release,
  destination attestation, evidence path, and one-shot gates are ready.

### Currently unavailable actions

- independent Create Customer database post-condition verification;
- real Recharge execution or post-condition validation;
- standalone Add Offer preparation, execution, or validation;
- production execution;
- automatic retry or fallback for a governed real run.

## 17. Common workflows

### A. I just want to inspect the product

1. Start Flask and open the local URL.
2. Review the three grouped capabilities in **Run a test**.
3. Open **Historical runs** to inspect persisted sanitized records.
4. Expand **Diagnostics** only if you need local tooling.

Expected result: no QA request and no attempt consumption.

### B. I want to validate Create Customer with Offer without executing

1. Select **Create Customer with Offer**.
2. Click **Validate**.
3. Read Infrastructure, Authorization, and DB verification separately.
4. Leave Execute untouched.

Expected result on a fresh process: Infrastructure Ready, Authorization
Required, DB verification Not configured, and Execute disabled.

### C. I want to understand why Execute is disabled

Read the message immediately below the button. For Create Customer with Offer,
**Authorization required before QA execution** means that no exact server-side
release/context is available. DB verification is informational and does not
cause that authorization block.

### D. I want to inspect a previous run

1. Open **Historical runs**.
2. Read the status, scenario, environment, and time.
3. Expand **View details**.
4. Click **View sanitized evidence** if you need the public artifact.

Expected result: a historical record only; it does not become the active Result.

### E. I want to inspect technical diagnostics

1. Expand **Diagnostics**.
2. Open **Generator** for templates, deterministic scenario creation, dry-run,
   exports, and fake adapters.
3. Open **Execution** for the legacy local runner view.
4. Expand **Advanced diagnostics** only when you understand the legacy controls.

Expected result: local/mock work only unless a separate governed product
procedure explicitly authorizes otherwise.

### F. I want to test Recharge

1. Select **Recharge Basic** in the product workspace and click Validate to
   confirm its current local-diagnostic status.
2. For a local simulation, open **Diagnostics -> Generator**, choose a Recharge
   template, complete the guided inputs, generate the scenario, and use the
   local dry-run or mock adapter action.

Expected result: local deterministic output. No Recharge request is sent to QA.

### G. I want to test Add Offer

1. Select **Add Offer Basic**.
2. Click Validate.
3. Read the BLOCKED explanation.

Expected result: no request sent and Execute disabled. The Owner must obtain
the missing authoritative operation, input, response, and validation contracts
before implementation can proceed.

## 18. Capability matrix

| Capability | Usable today | Mode | What works | What does not | Required next |
| --- | --- | --- | --- | --- | --- |
| Create Customer with Offer | Partially | Governed QA, authorization-gated | Selection, non-mutating Validate, controlled product binding, result/evidence path | Fresh-process execution; DB post-condition proof | Exact Owner authorization, live runtime, operational release; separate DB validator contract |
| Create Customer DB validation | No | Not configured | UI reports the limitation separately | No authoritative lookup or PASS/FAIL DB result | Approved lookup identity, query/hash, scope, result shape |
| Recharge Basic | Locally | Local diagnostic | Selection, Validate, deterministic template/fake-plan diagnostics | QA mutation and DB validation; no direct primary diagnostic-run button | Governed mutation/response/adapter contract and validator |
| Add Offer Basic | Inspect only | Unavailable | Selection and truthful BLOCKED result | Planning, execution, validation | Standalone operation, schema, offer input, response, validator |
| Run 03A | Source-prepared | Governed one-shot QA | Static product path and operator runbook | No fresh-process release; no DB validation | Confirm live runtime, exact Owner authorization/release, untouched attempt |
| Evidence | Yes for persisted controlled runs | Read-only sanitized | Active-run lookup when referenced; public projection | Raw payloads/responses and local diagnostic proof | Complete a separately authorized controlled run |
| History | Yes | Read-only sanitized | Status, label, environment, time, details, evidence | Does not show local summaries as controlled history | None for current function |
| Diagnostics | Yes | Local/mock | Generator, dry-run, fake adapters, Standard mock, legacy runner | Does not prove QA execution | Use governed product path for real QA |

## 19. Troubleshooting: why a button is disabled

| Symptom | Current meaning | Next action |
| --- | --- | --- |
| Validate disabled | No test is selected, or the catalog failed to load. | Select a test. If no options load, check the local Flask process. |
| Execute says select and validate | The current selection has not been validated. | Click Validate. |
| Execute says authorization required | Create Customer is statically ready, but no exact server-side release/context exists. | Follow the separate operator authorization/runtime process; do not send authorization through the browser. |
| Execute says unavailable for this test | Recharge or Add Offer has no governed QA execution path. | Use local Diagnostics for Recharge or obtain the missing Add Offer contract. |
| Validation unavailable | The local validation request failed. | Confirm Flask is running and retry only the non-mutating Validate action. |
| Evidence unavailable | No matching allowlisted sanitized artifact exists or local persistence/read failed. | Check the run ID and evidence persistence; do not substitute a History record for the current run. |
| BLOCKED result | A gate or capability prevented safe execution. | Read the user-facing reason; do not treat it as a QA system failure. |

## 20. Current external requirements

Create Customer with Offer execution requires current live runtime and an exact
Owner-authorized operational release. Its DB validator additionally requires
the artifacts in `CREATE_CUSTOMER_EXTERNAL_REQUIREMENTS.md`.

Recharge requires the authoritative mutation, request, response, adapter,
bridge, and validation artifacts in `RECHARGE_EXTERNAL_REQUIREMENTS.md`.

Standalone Add Offer requires the operation, schema, governed offer input,
response semantics, and validation artifacts in
`ADD_OFFER_EXTERNAL_REQUIREMENTS.md`.

These documents identify the missing inputs. They do not authorize execution,
database access, or production use.
