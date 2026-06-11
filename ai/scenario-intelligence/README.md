# Scenario Intelligence Layer

Esta pasta define a camada conceitual do MVP7.6.6 para analise deterministica de cenarios SmartOffers.

O objetivo e produzir uma leitura segura de um scenario ja existente, sem alterar JSON salvo, rotas, UI, dry-run, adapter-run, catalogo seguro ou `request_plan`.

## Fontes permitidas

- `ai/knowledge/`: ontologia SmartOffers.
- `ai/playbooks/`: sintomas e playbooks operacionais.
- `ai/evidence/`: Evidence Planner Foundation.
- `ai/supervisors/`: supervisores e roteamento conceitual.

## Contratos

- [scenario-analysis-contract.md](scenario-analysis-contract.md): formato conceitual de saida da analise.
- [routing-rules.md](routing-rules.md): regras deterministicas usadas para sugerir entidades, evidencias, playbooks, supervisores, riscos e status.

## Regra central

A inteligencia de cenario e local, deterministica e read-only. Ela nao chama rede, Oracle, APIs, Kafka, Jenkins, subprocessos, LLM externo ou ambiente real.

## Relacao com MVP7.6.7

O MVP7.6.6 prepara informacoes conceituais para o futuro Adapter Risk Classifier, mas nao implementa classificacao de risco de adapter real nem libera `mode=real`.
