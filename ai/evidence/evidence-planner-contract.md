# Evidence Planner Contract

Este contrato define a forma conceitual do futuro `evidence_plan`.

No MVP7.6.4, o contrato e documental. Ele nao cria schema executavel, validacao automatica, endpoint, fixture, automacao ou codigo Python.

## Objetivo

O `evidence_plan` deve transformar sintomas, campanhas, cenarios e playbooks em uma lista segura de evidencias esperadas.

O plano deve indicar o que pode ser analisado em modo mock/read-only, o que deve permanecer bloqueado e o que depende de controle futuro.

## Forma conceitual

Cada item futuro de `evidence_plan` deve representar uma camada de evidencia.

Campos conceituais:

| Campo | Uso esperado |
| --- | --- |
| `layer` | Nome da camada de evidencia, usando vocabulario definido em `evidence-layers.md`. |
| `goal` | Objetivo operacional da evidencia para o sintoma ou cenario. |
| `source_entities` | Entidades da ontologia relacionadas, como cliente, campanha, evento, metrica, caracteristica, auditoria, processamento, integracao e evidencia. |
| `related_playbooks` | Playbooks que usam ou sugerem a camada. |
| `safe_evidence` | Artefatos seguros esperados, sempre conceituais, mockados ou read-only. |
| `status` | Classificacao segura definida em `evidence-statuses.md`. |
| `blocked_reason` | Motivo para bloquear evidencia quando houver risco de execucao real, dado sensivel ou dependencia nao controlada. |
| `future_adapter` | Adaptador futuro possivel, sem habilitar execucao. |
| `expected_artifact` | Artefato documental ou relatorio esperado em uma fase futura. |

## Regras de preenchimento

- Usar somente camadas listadas em `evidence-layers.md`.
- Usar somente status listados em `evidence-statuses.md`.
- Referenciar playbooks por nome de arquivo.
- Descrever evidencias de forma sanitizada e sem payload real.
- Preferir status `mock` ou `read-only` quando a evidencia puder ser planejada sem risco.
- Usar status `blocked` quando a evidencia exigir Oracle real, API real, Kafka real, Jenkins real, credencial, dado sensivel ou execucao externa.
- Usar status `future-controlled` para dependencias planejadas para MVP futuro com allowlist e guardrails.

## Limites

Este contrato nao muda comportamento de geracao, dry-run, adapter-run, catalogo seguro, exports, rotas ou UI.

Nenhum item deste contrato autoriza `mode=real`, chamadas externas, acesso a ambiente, uso de secrets ou coleta de dados brutos.
