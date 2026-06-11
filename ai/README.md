# AI Domain Contracts

Esta pasta registra contratos conceituais e operacionais para a camada de dominio do SmartOffers_Automation_Driven.

No MVP7.6.1, `ai/` e somente Markdown:

- sem Python funcional;
- sem LLM externo;
- sem MCP/App SDK;
- sem chamadas reais;
- sem execucao;
- sem alteracao de JSON, rotas ou adapters.

## Subpastas

- `evidence/`: contratos conceituais do Evidence Planner.
- `knowledge/`: ontologia e conhecimento SmartOffers.
- `playbooks/`: roteiros operacionais e troubleshooting.
- `safety/`: categorias de risco e guardrails.
- `skills/`: habilidades reutilizaveis do produto.
- `supervisors/`: responsabilidades de supervisores de dominio.

## Regra central

Esta camada orienta o produto, mas nao executa sistemas externos. Execucao real so pode existir em MVP especifico e com controles explicitos.
