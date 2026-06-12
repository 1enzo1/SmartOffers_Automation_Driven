# MVP7.7.4 - Evidence Regression Analysis

Status: concluded for documentation and deterministic diagnosis. This document is a sanitized analysis only. It does not authorize production fixes, QA4 calls, DB calls, adapter-run changes or dry-run changes.

## Scope

Inputs inspected locally:

- Standard evidence that worked for API/DB baseline: `te_120626_091902.zip`
- Variant evidence that failed: `te_120626_024118.zip`
- Copy evidence that failed: `te_120626_092954.zip`

The raw ZIPs remain ignored and are not versioned. This analysis records only structural differences: file counts, root keys, metadata presence, event time shape and aggregate outcomes. It does not store host, IP, token, secret, real payload, MSISDN, account, document or response body.

## Reference Materials

Available tracked reference:

- `core/api_catalog/catalog.json` contains sanitized `payload_base` entries with `attributeDetails` placeholders for SmartOffers request planning.

No tracked Postman collection or environment JSON suitable for direct use was found in the workspace scan beyond the sanitized catalog. Historical root-level scripts were inspected only to identify builder differences and are not executed by this MVP.

## Evidence Summary

| Evidence | Observed role | Request files | API result shape | DB evidence shape |
| --- | --- | ---: | --- | --- |
| `te_120626_091902.zip` | Standard baseline | 30 | `result=true`, `status=Success` at response root | DB validation artifacts present; campaign entry signal present in existing summary |
| `te_120626_024118.zip` | Variant failure | 4 | `result=false`, `status=Error` at response root | No discovery artifact in ZIP |
| `te_120626_092954.zip` | Copy failure | 12 | `result=false`, `status=Error` at response root | Discovery artifacts present with zero rows |

The legacy `resumo_analise.json` is useful but not authoritative for this regression because the analyzer expects some responses under `body.result`, while these ZIPs store `result` at the response root.

## Payload Differences

Standard baseline:

- Root payload keys: `operation`, `extEventId`, `eventTime`, `attributes`, `attributeDetails`.
- Every inspected request contains `attributeDetails`.
- Each request has 14 sent attributes and 14 metadata entries.
- No sent attribute lacks metadata.

Variant failure:

- Root payload keys: `operation`, `extEventId`, `eventTime`, `attributes`.
- No inspected request contains `attributeDetails`.
- POS request shape has 14 attributes and zero metadata entries.
- PRE request shape has 20 attributes and zero metadata entries.
- Every sent attribute is missing matching metadata.

Copy failure:

- Root payload keys: `operation`, `extEventId`, `eventTime`, `attributes`.
- No inspected request contains `attributeDetails`.
- POS request shape has 14 attributes and zero metadata entries.
- PRE request shape has 6 attributes and zero metadata entries.
- Every sent attribute is missing matching metadata.

## AttributeDetails Regression

The standard payload sends metadata for each attribute through `attributeDetails`. The variant and copy payloads remove that metadata completely.

Probable impact:

- The API receives opaque attributes without the expected type/name metadata.
- The API rejects the event before downstream persistence or campaign evaluation.
- DB validation either cannot run with a discovered customer or finds zero discovery rows.

This is the strongest observed regression and matches the current hypothesis.

## EventTime Difference

All three evidence sets contain `eventTime` as a string with the same shape: `dd-mm-yyyy HH:MM:SS`.

Observed difference:

- Standard baseline uses the same event time shape as variant/copy.
- Variant/copy are not failing because `eventTime` is absent.
- `eventTime` remains a secondary review item because builder behavior differs between historical scripts, but it is not the primary structural gap in these ZIPs.

## PRE Attribute Difference

The PRE flow differs between variant and copy:

- Variant PRE sends a broader shape with 20 attributes.
- Copy PRE sends a reduced shape with 6 attributes.
- Both omit `attributeDetails`, so both are incomplete even before business-rule evaluation.

The reduced copy PRE payload increases risk because it drops several non-secret operational characteristic categories, such as date, provisioning, profile and ownership signals, while also omitting metadata.

## API And DB Impact

Standard baseline:

- API accepts the request shape.
- DB/campaign validation has enough evidence to indicate the customer entered the campaign path.
- Existing summary may still report downstream delay because audit/metrics evidence is absent.

Variant/copy:

- API returns error shape for every inspected request.
- Variant does not produce discovery evidence in the ZIP.
- Copy produces discovery evidence with zero rows.
- The failure appears to happen before useful downstream DB/campaign evidence is created.

## Deterministic Diagnosis Added

MVP7.7.4 adds `core/utils/evidence_payload_contract.py`, a pure analyzer for in-memory payload dictionaries. It classifies payloads as complete only when:

- `attributes` is present and non-empty;
- `attributeDetails` is present;
- every sent attribute has corresponding metadata;
- `eventTime` is present in the expected string shape.

Tests use synthetic sanitized fixtures. They do not open raw ZIPs, call QA4, call APIs, call Oracle, use real payloads or require response bodies.

## Probable Cause

The likely cause is not an environment outage or DB-only problem. The standard path sends a full SmartOffers payload with `attributeDetails`; variant and copy build reduced payloads without `attributeDetails`.

Recommended next MVP, not part of this fix:

- update variant/copy payload builders to include metadata for every sent attribute;
- keep exact metadata sourced from sanitized catalog or approved contract;
- add a separate fix for the legacy analyzer response-root limitation if needed;
- rerun only through an approved manual QA4 process.
