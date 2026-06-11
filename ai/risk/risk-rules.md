# Adapter Risk Rules

Este arquivo documenta as regras deterministicas do MVP7.6.7.

## Status e modos

| risk_status | risk_level | allowed_mode |
| --- | --- | --- |
| `blocked` | `critical` | `none` |
| `future_controlled_required` | `high` | `none` |
| `read_only_allowed` | `medium` | `read-only` |
| `mock_allowed` | `low` | `mock` |

## Bloqueios

Classificar como `blocked` quando houver sinal de:

- `mode=real`;
- `safe_for_real_execution=true`;
- `real_execution=true`;
- host real, IP, token, secret, credential, password ou senha;
- payload real;
- chamada externa;
- mutacao de catalogo;
- `execution_status` liberado;
- Oracle real;
- API real;
- Kafka real;
- Jenkins/job real.

## Futuro controlado

Classificar como `future_controlled_required` quando houver:

- `future-controlled`;
- `kafka_trace` conceitual;
- `jenkins.job` conceitual;
- evidencia ou adapter que so pode ser avaliado em MVP futuro com opt-in e guardrails.

Este status nao libera execucao real.

## Read-only

Classificar como `read_only_allowed` para:

- evidence layer read-only;
- query conceitual;
- item de catalogo sanitizado com `execution_status=blocked` e `safe_for_real_execution=false`.

## Mock

Classificar como `mock_allowed` para:

- adapter mockado;
- `planning_mode=mock_only`;
- `mode=mock`;
- `request_plan` sanitizado sem sinais bloqueantes.

## Supervisores

Toda classificacao deve incluir:

- `adapter-supervisor`;
- `safety-supervisor`.

Adicionar `evidence-supervisor` para evidencias e `catalog-config-supervisor` para catalogo ou request plan.
