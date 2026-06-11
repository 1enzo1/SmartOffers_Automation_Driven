# Adapter Risk Classifier Contract

Este contrato descreve a saida da funcao pura `classify_adapter_risk(work_item)`.

O contrato nao altera JSON salvo, nao cria schema executavel e nao se integra a adapter-run neste MVP.

## Entrada

`work_item` e um dict conceitual e pode representar:

- adapter;
- request plan;
- http plan;
- item de catalogo;
- resultado de Scenario Intelligence;
- evidence layer;
- execucao pretendida.

## Saida

| Campo | Descricao |
| --- | --- |
| `risk_level` | `low`, `medium`, `high` ou `critical`. |
| `risk_status` | `mock_allowed`, `read_only_allowed`, `future_controlled_required` ou `blocked`. |
| `blocked_reasons` | Lista ordenada e sem duplicidade de motivos de bloqueio ou cautela. |
| `allowed_mode` | `mock`, `read-only` ou `none`. |
| `required_guardrails` | Lista ordenada e sem duplicidade de guardrails requeridos. |
| `related_supervisors` | Supervisores relacionados, sempre incluindo `adapter-supervisor` e `safety-supervisor`. |
| `safe_next_step` | Proximo passo conceitual seguro. |

## Garantias

- A funcao e deterministica.
- A funcao nao muta o dict recebido.
- A funcao nao faz I/O.
- A funcao nao le arquivos ou variaveis de ambiente.
- A funcao nao usa rede, Flask, requests, httpx, subprocess, LLM, data, hora ou random.
- Listas retornadas sao ordenadas por regra e sem duplicidade.

## Precedencia

```txt
blocked > future_controlled_required > read_only_allowed > mock_allowed
```

`future_controlled_required` nao libera execucao real e deve retornar `allowed_mode=none`.
