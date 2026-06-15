---
name: smartoffers-automation-architect
description: Use esta skill ao trabalhar no projeto SmartOffers Automation, incluindo geracao deterministica de cenarios, dry-run mockado, exportacao QA/DET, Flask, templates, testes, UI HTML/CSS/JS, rotas de API, guardrails e evolucao incremental do MVP.
---

# SmartOffers Automation Architect

## Papel

Atue como arquiteto tecnico do projeto SmartOffers Automation.

O produto atual e `SmartOffers_Automation_Driven`. PortalQA e uma referencia historica e nao deve orientar a arquitetura atual.

A branch `qa/mvp4-integration` e a linha evolutiva atual, apesar do nome historico. Antes de novo MVP, confirme que a branch contem o merge do MVP7.6 ou posterior.

O projeto e um laboratorio seguro SmartOffers/ACM, local-first e mock-first, implementado como plataforma Flask/Python para:

- gerar cenarios SmartOffers/ACM;
- salvar cenarios em JSON;
- reabrir cenarios;
- simular execucao via dry-run mockado;
- executar adapter-run local/mockado;
- exportar artefatos QA/DET em DOCX, XLSX e JSON;
- evoluir para automacao real controlada no futuro, sempre bloqueada por padrao.

A direcao de produto e evoluir de ferramenta de testes para laboratorio seguro SmartOffers/ACM, com supervisores de dominio, skills reutilizaveis, ontologia SmartOffers, playbooks operacionais, evidence planner, risk classifier e execucao real somente em MVP especifico.

No estado atual, MVP7.8.2 ja externaliza runtime config e o commit `de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71` adicionou protecao local para runtime secrets. Nao implementar execucao real, LLM externo, MCP/App SDK, novos endpoints ou novos campos de JSON fora de MVP explicito.

## Stack atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geracao deterministica por templates
- Dry-run mockado
- Adapter-run mockado
- Exportacao com python-docx e openpyxl
- Sem React no momento
- Sem integracoes reais no momento

## Estrutura principal

- `templates/index.html`: UI principal.
- `core/generation/`: geracao deterministica de cenarios.
- `core/simulation/`: dry-run mockado. Deve ser pacote, nao arquivo `core/simulation.py`.
- `core/exporters/`: exportacao DOCX/XLSX/JSON.
- `core/execution/`: adapter-run local/mockado.
- `core/api_catalog/`: catalogo sanitizado e policy `mock_only`.
- `ai/`: contratos conceituais e operacionais para supervisores, skills, knowledge, playbooks e safety. No MVP7.6.1 nao contem Python funcional.
- `docs/`: arquitetura, roadmap, modelo de seguranca e supervisores.
- `tests/`: suite segura de testes.

## Regras obrigatorias

Nao fazer:

- nao chamar Oracle real;
- nao chamar APIs reais;
- nao chamar Kafka real;
- nao chamar Jenkins real;
- nao executar subprocessos reais para dry-run;
- nao habilitar `mode=real` sem MVP explicito;
- nao habilitar execucao real sem opt-in explicito, ambiente permitido, allowlist, timeout, logs sanitizados e bloqueio de producao;
- nao alterar `safe_for_real_execution` sem MVP especifico;
- nao alterar `execution_status` do catalogo para liberar execucao real sem MVP especifico;
- nao versionar runtime secrets, `.env`, `.dbp`, export DBeaver sensivel ou ZIP bruto de conexao/evidencia;
- nao adicionar React agora;
- nao criar build step frontend;
- nao reestruturar o projeto inteiro sem necessidade;
- nao quebrar rotas antigas;
- nao quebrar compatibilidade com JSONs existentes;
- nao recriar `core/simulation.py`.

## Rotas criticas

Manter funcionando:

- `/`
- `/executar`
- `/listar_testes`
- `/ver_teste`
- `/abrir_pasta`
- `/api/questions`
- `/api/scenarios`
- `/api/scenarios/generate`
- `/api/scenarios/<id>`
- `/api/scenarios/<id>/dry-run`
- `/api/scenarios/<id>/adapter-run`
- `/api/scenarios/<id>/export/docx`
- `/api/scenarios/<id>/export/xlsx`
- `/api/scenarios/<id>/export/json`
- `/api/dry-runs/<id>`
- `/api/dry-runs/<id>/export/docx`
- `/api/dry-runs/<id>/export/xlsx`
- `/api/dry-runs/<id>/export/json`
- `/api/adapters`
- `/api/adapters/health`
- `/api/api-catalog`
- `/api/api-catalog/<api_id>`

## Padrao de evolucao

Sempre preferir:

- mudancas pequenas;
- modulos separados;
- compatibilidade com JSON existente;
- testes cobrindo nova funcionalidade;
- frontend simples;
- arquitetura preparada para adapters reais no futuro.

Mudancas de documentacao e guardrails nao devem alterar comportamento de geracao, dry-run, adapter-run, exports, catalogo ou UI.

Antes de novo MVP:

- confirmar branch base correta;
- buscar remoto com `git fetch --all --prune`;
- confirmar que a branch contem o ultimo MVP mergeado;
- evitar aplicar MVP novo sobre base antiga.

## Supervisores e skills do produto

A arquitetura futura pode ter supervisores e skills como camada de dominio do produto, mas isso nao habilita IA externa nem execucao real por si so.

Supervisores previstos:

- smartoffers-architect-supervisor;
- campaign-supervisor;
- evidence-supervisor;
- troubleshooting-supervisor;
- catalog-config-supervisor;
- adapter-supervisor;
- safety-supervisor.

Skills previstas:

- campaign-analysis;
- evidence-planning;
- troubleshooting;
- sql-evidence;
- api-contract-analysis;
- request-plan-analysis;
- adapter-execution-planning;
- catalog-config-analysis;
- kafka-nrt-analysis;
- bko-analysis;
- risk-classification.

## Geracao de cenarios

O gerador deve ser deterministico.

Uma resposta do usuario pode gerar multiplos steps.

Exemplo:

- usuario escolhe `recarga`;
- sistema gera step de execucao da recarga, step de validacao, queries/checkpoints e evidencias esperadas.

Known limitation:

- `event_type == "recarga"` ainda pode permitir `recharge_scenario == "none"` no modo mockado.
- Nao corrigir incidentalmente fora de um MVP especifico.
- Tratar como futuro hardening para fase de execucao real/adapters.

## Dry-run

Dry-run deve:

- usar cenario JSON salvo;
- simular execucao;
- gerar relatorio JSON;
- gerar logs mockados;
- marcar steps como passed/failed/skipped;
- respeitar overrides como `dry_run.status` e `dry_run_status`;
- nunca tocar em sistemas externos.

## Adapter-run

Adapter-run deve permanecer local e mockado ate MVP especifico de execucao real. `mode=real` deve continuar bloqueado.

## Exportacao QA/DET

Exports devem:

- usar cenario salvo e/ou relatorio dry-run salvo;
- gerar DOCX, XLSX e JSON enriquecido;
- preservar dados de steps, payload, queries, checkpoints, evidencias, warnings, logs e status.

Ao exportar queries/evidencias:

- nao considerar apenas `sql` e `lookup`;
- tambem preservar `request`, `endpoint`, `method`, `files`;
- se nenhuma chave conhecida existir, serializar o item completo como JSON compacto/legivel.

## UI

Preservar:

- Gerador de Cenarios;
- Cenarios Salvos;
- Dry-run;
- Exportacoes;
- Execucao Legada;
- sidebar recolhivel;
- Suite de Testes na sidebar;
- botoes Executar/Pausar/Continuar/Re-run/Limpar;
- toggle-pill;
- filtros Todos/Passed/Failed/Skipped;
- terminal com horario por linha.

Nao regredir visual do MVP4.2 ao alterar `templates/index.html`.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa.

Se precisar validar:

- subir Flask em background;
- usar porta livre;
- testar endpoints;
- encerrar apenas o processo iniciado pela tarefa;
- confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```
