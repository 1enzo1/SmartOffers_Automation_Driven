# Evidence Planner Foundation

Esta pasta registra contratos conceituais para o futuro Evidence Planner do SmartOffers_Automation_Driven.

No MVP7.6.4, `ai/evidence/` e somente Markdown:

- sem Python funcional;
- sem schemas executaveis;
- sem fixtures;
- sem endpoints;
- sem automacoes;
- sem JSONs de cenario;
- sem chamadas reais;
- sem execucao real.

## Contratos

- [evidence-planner-contract.md](evidence-planner-contract.md): contrato conceitual do futuro `evidence_plan`.
- [evidence-layers.md](evidence-layers.md): camadas de evidencia usadas pelo planner.
- [playbook-mapping.md](playbook-mapping.md): relacao entre playbooks operacionais e camadas de evidencia.
- [evidence-statuses.md](evidence-statuses.md): classificacao segura de status de evidencia.

## Fontes de dominio

O Evidence Planner deve usar como base:

- `ai/knowledge/`: ontologia SmartOffers do MVP7.6.2;
- `ai/playbooks/`: playbooks operacionais do MVP7.6.3.

## Regra central

Esta area orienta planejamento deterministico e seguro de evidencias. Ela nao executa consultas, APIs, Kafka, Jenkins, subprocessos, adapters reais ou qualquer chamada externa.

Execucao real permanece bloqueada por padrao e so pode ser discutida em MVP futuro especifico, com opt-in, allowlist, guardrails e testes dedicados.
