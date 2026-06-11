# Scenario Analysis Contract

Este contrato descreve a saida conceitual da funcao pura `analyze_scenario(scenario)`.

O contrato nao altera o JSON salvo de cenario e nao cria endpoint, schema executavel, automacao ou integracao externa.

## Campos

| Campo | Descricao |
| --- | --- |
| `scenario_id` | Identificador do scenario recebido, ou string vazia quando ausente. |
| `domain` | Dominio conceitual da analise. Para este MVP, `smartoffers`. |
| `main_flow` | Fluxo principal derivado do tipo de evento. |
| `event_type` | Evento derivado de `source_answers.event_type`, com fallback para `payload.eventType`. |
| `relevant_entities` | Entidades da ontologia relacionadas ao scenario. |
| `suggested_playbooks` | Playbooks operacionais sugeridos por regras fixas. |
| `expected_evidence_layers` | Camadas de evidencia reconhecidas em `queries`. |
| `suggested_supervisors` | Supervisores conceituais sugeridos. |
| `risks` | Riscos ou bloqueios identificados sem executar nada. |
| `overall_status` | Status geral: `mock`, `read-only`, `blocked` ou `future-controlled`. |

## Garantias

- A funcao e deterministica.
- A funcao nao muta o dict recebido.
- A funcao nao faz I/O.
- A funcao nao le variaveis de ambiente.
- A funcao nao usa data, hora ou aleatoriedade.
- Listas de saida sao ordenadas por regra e deduplicadas.

## Limites

Este contrato nao autoriza execucao real, coleta de evidencia real, chamada externa, criacao de endpoint ou alteracao de comportamento funcional.
