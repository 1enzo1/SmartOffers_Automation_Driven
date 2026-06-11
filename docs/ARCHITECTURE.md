# Architecture

## Produto

SmartOffers_Automation_Driven e um laboratorio seguro de automacao SmartOffers/ACM. A arquitetura atual e local-first e mock-first: gera cenarios, salva JSONs, simula execucao, executa adapter-run mockado, exporta evidencias QA/DET e monta `request_plan` deterministico a partir de catalogo seguro.

O MVP7.6.1 nao muda codigo funcional. Este documento registra a arquitetura atual e a direcao futura.

## Linha base

- Branch evolutiva atual: `qa/mvp4-integration`
- MVP concluido: MVP7.6
- Execucao real: bloqueada
- Catalogo de APIs: sanitizado e versionado
- UI: Flask com HTML/CSS/JavaScript puro
- Testes: Pytest
- Frontend moderno: fora do escopo atual

## Componentes atuais

`app.py` expoe as rotas Flask e conecta generation, simulation, execution, exporters, api_catalog e legacy_execution.

`core/generation/` cria cenarios deterministicos a partir de respostas e templates.

`core/simulation/` executa dry-run local usando o JSON salvo, sem Oracle, APIs, Kafka, Jenkins, rede ou subprocessos reais.

`core/execution/` normaliza steps, queries, checkpoints e evidencias para adapter-run mockado.

`core/adapters/` contem adapters fake para SmartOffers, Oracle, Kafka, Jenkins e evidencia.

`core/api_catalog/` guarda catalogo sanitizado e policy `mock_only` para planejamento de request.

`core/exporters/` gera artefatos JSON, DOCX e XLSX para cenarios e dry-runs.

`templates/index.html` contem a experiencia atual em HTML/CSS/JavaScript puro.

## Camada de dominio futura

`ai/` e reservado para contratos conceituais e operacionais do produto:

- `ai/knowledge/`: ontologia SmartOffers;
- `ai/playbooks/`: troubleshooting e roteiros operacionais;
- `ai/safety/`: regras de risco e bloqueio;
- `ai/skills/`: habilidades reutilizaveis do produto;
- `ai/supervisors/`: responsabilidades de supervisores.

No MVP7.6.1, `ai/` nao contem Python funcional, LLM externo, chamadas reais, MCP/App SDK ou execucao.

## Fronteiras de compatibilidade

O MVP7.6.1 nao altera:

- rotas;
- schema de cenarios;
- `execution_steps`;
- `validation_steps`;
- `queries`;
- `checkpoints`;
- `evidence_files`;
- dry-run;
- adapter-run;
- `request_plan`;
- catalogo seguro;
- UI.

Qualquer campo novo em JSON deve ser opcional e precisa de MVP proprio.

## Direcao de extensao

A sequencia correta antes de execucao real e:

1. registrar guardrails e alinhamento;
2. criar ontologia SmartOffers;
3. criar playbooks operacionais;
4. criar evidence planner;
5. criar supervisores;
6. criar scenario intelligence;
7. criar adapter risk classifier;
8. somente depois avaliar `mode=real` opt-in em QA4.
