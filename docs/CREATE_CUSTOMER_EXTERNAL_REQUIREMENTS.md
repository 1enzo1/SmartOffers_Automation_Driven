# Create Customer with Offer - External Requirements

## Scope

The recoverable historical real operation is `CREATE_OFFERS_CUSTOMER`, exposed
to the product as **Create Customer with Offer**. It is not a standalone
customer/line creation contract.

## Execution contract gaps

| What is missing | Why it is required | Expected source | How it will be validated | Secret | Blocks Run 03 |
| --- | --- | --- | --- | --- | --- |
| None for the recovered composite Offers operation | The operation, scenario, adapter, bridge, one-shot scope, attestation, BDA offer discovery, and evidence mapping already exist in source | Existing controlled Alpha implementation | Local mapping and mocked contract tests | No | No |
| A standalone customer/line operation definition, if that product is required later | The recovered operation requires an eligible governed offer and must not be relabeled as pure customer creation | Authoritative SmartOffers API/operation owner | Operation/scenario/allowlist/request-contract tests before any transport | No | Yes, only for a future pure-customer Run 03 |

## Read-only validation gaps

| What is missing | Why it is required | Expected source | How it will be validated | Secret | Blocks Run 03 |
| --- | --- | --- | --- | --- | --- |
| Read-only lookup identity and approved resource for the customer/line outcome | It must prove the post-operation entity state, not a generic readiness checkpoint | ACM_CUSTOM/ACM/BDA data owner | Scoped destination and resource contract | No | Yes, when DB validation is required |
| Canonical query text held outside Git and its approved deterministic hash | The executor must allow exactly one safe lookup and reject arbitrary SQL | Database/query owner | Hash allowlist and read-only guard tests | Query text is sensitive operational material | Yes, when DB validation is required |
| Expected normalized result shape for a successful customer/line outcome | The product needs a deterministic PASS/FAIL decision without returning customer data | Data owner and test-contract owner | Fake result-shape and mismatch tests | No | Yes, when DB validation is required |

No Oracle action is authorized by this document. It only makes the missing
validation contract actionable.
