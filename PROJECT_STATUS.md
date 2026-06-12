# Project Status

Registro de andamento, decisoes e proximos passos do SmartOffers Automation Driven.

## Estado atual

- Branch base atual: `qa/mvp4-integration`
- Observacao sobre a branch: linha evolutiva atual do produto, apesar do nome historico ligado ao MVP4
- Produto atual: `SmartOffers_Automation_Driven`
- MVP atual concluido: MVP7.7.3
- Ultimo MVP aprovado: MVP7.7.3 - Manual QA4 Execution Readiness Package
- PR do MVP7.6: `#12`
- Merge commit do MVP7.6: `5c0566ff3ad32cb18480c714dd703ce78f10b8eb`
- Execucao real: bloqueada
- Catalogo de APIs: sanitizado e versionado em `core/api_catalog/catalog.json`
- Dados brutos de ambiente/API: nao versionados
- PortalQA: referencia historica, nao orienta a arquitetura atual

## MVPs concluidos

| MVP | Status | Resumo |
| --- | --- | --- |
| MVP1 | Concluido | Gerador base de cenarios |
| MVP2 | Concluido | Templates e perguntas condicionais |
| MVP3 | Concluido | Dry-run mockado |
| MVP4 / MVP4.2 | Concluido | UI principal e ajustes visuais |
| MVP5 | Concluido | Exportacao QA/DET em JSON, DOCX e XLSX |
| MVP6 | Concluido | Biblioteca de Templates SmartOffers |
| MVP6.5 | Concluido | Refactor Foundation |
| MVP7 | Concluido | Adapters Foundation |
| MVP7.5 | Concluido | Catalogo seguro de APIs |
| MVP7.6 | Concluido | SmartOffersAdapter config-driven mockado |
| MVP7.6.2 | Concluido/Aprovado | SmartOffers Ontology em Markdown |
| MVP7.6.3 | Concluido/Aprovado | Operational Playbooks em Markdown |
| MVP7.6.4 | Concluido/Aprovado | Evidence Planner Foundation em Markdown |
| MVP7.6.5 | Concluido/Aprovado | AI Supervisors Foundation em Markdown |
| MVP7.6.6 | Concluido/Aprovado | Scenario Intelligence Layer deterministico |
| MVP7.6.6.1 | Concluido/Aprovado | Safety hotfix para sinais de execucao real |
| MVP7.6.7 | Concluido/Aprovado | Adapter Risk Classifier deterministico |
| MVP7.7.0 | Concluido/Aprovado | Real Execution Readiness Gate deterministico |
| MVP7.7.1.0 | Concluido/Aprovado | Runtime Secret Contract com fake client obrigatorio |
| MVP7.7.1.1 | Concluido/Aprovado | First QA4 Real Call Gate manual e controlado |
| MVP7.7.2 | Concluido/Aprovado | Real Execution Hardening & Evidence Pack |
| MVP7.7.3 | Concluido/Aprovado | Manual QA4 Execution Readiness Package |

## MVP7.6

O MVP7.6 adicionou planejamento mockado para o SmartOffersAdapter usando o catalogo seguro do MVP7.5.

Entregas:

- policy separada para APIs `mock_only`;
- 10 APIs SmartOffers liberadas somente para planejamento mockado;
- `request_plan` deterministico a partir do catalogo;
- resolucao por `api_id` explicito;
- fallback por `event_type` para steps `smartoffers.http_plan` gerados pelo sistema;
- bloqueio controlado para API fora da policy;
- bloqueio controlado para `api_id` inexistente;
- agregacao de adapter-run tratando `blocked` como status nao-passing;
- `mode=real` ainda bloqueado;
- `smartoffers.execution` preservado como execucao fake normal;
- `smartoffers.http_plan` restrito a planejamento de API.

Arquivos centrais do MVP7.6:

- `core/api_catalog/policy.py`
- `core/adapters/fake.py`
- `core/execution/service.py`
- `tests/test_adapters.py`

## APIs mock_only do MVP7.6

Estas APIs continuam com `execution_status=blocked` e `safe_for_real_execution=false` no catalogo. A policy permite apenas montar plano mockado.

```txt
post-ativacao-de-campanha-por-api-2e656ee31c
post-consulta-de-saldo-f3317b27b3
post-evento-de-recarga-6954ef3458
post-evento-vivo-turbo-e124494049
post-o-vivo-next-troca-de-oferta-fedbfb981e
post-retorno-la-xml-e73a7721f4
post-sincronismo-e8537bd912
post-transicao-de-estado-de-servico-aceite-3751798e76
post-vivo-next-habilitacao-de-cliente-ade0841563
post-vivo-next-habilitacao-de-linha-a79ab2e31c
```

## Decisoes de seguranca

- O catalogo versionado deve permanecer sanitizado.
- `catalog.json` nao deve ser alterado para liberar execucao real sem MVP especifico.
- `execution_status` permanece `blocked` para as APIs catalogadas.
- `safe_for_real_execution` permanece `false` para as APIs catalogadas.
- `request_plan` usa placeholders de host, nao hosts reais.
- `mode=real` permanece bloqueado no endpoint de adapter-run.
- Fluxos mockados nao devem chamar rede, Oracle, Kafka, Jenkins nem subprocessos reais.
- MVP7.7 depende da sequencia 7.6.x antes de qualquer chamada real opt-in.

## Fluxo recomendado de desenvolvimento

1. Criar branch a partir de `qa/mvp4-integration`.
2. Implementar apenas o escopo do MVP atual.
3. Rodar `python -m pytest tests -q`.
4. Quando necessario, fazer smoke Flask em background com cleanup.
5. Confirmar porta livre ao final do smoke.
6. Confirmar `git status` limpo ou explicar arquivos gerados.
7. Abrir PR draft.
8. Resolver reviews sem expandir escopo.
9. Marcar Ready for review apenas sem threads abertas.
10. Mergear na branch base correta.

## Proximos MVPs

### MVP7.6.1 - Guardrails e alinhamento da linha evolutiva

Objetivo: corrigir o mapa de produto e registrar guardrails para que o projeto evolua como laboratorio seguro SmartOffers/ACM.

Entregas:

- atualizar `README.md`;
- atualizar `PROJECT_STATUS.md`;
- atualizar `AGENTS.md`;
- atualizar `.agents/skills/smartoffers-automation-architect/SKILL.md`;
- registrar `qa/mvp4-integration` como branch evolutiva atual;
- registrar PortalQA como referencia historica, nao arquitetura atual;
- criar `docs/ARCHITECTURE.md`;
- criar `docs/ROADMAP.md`;
- criar `docs/SECURITY_MODEL.md`;
- criar `docs/SUPERVISORS.md`;
- criar estrutura inicial `ai/` em Markdown.

Nao escopo:

- codigo funcional;
- novos endpoints;
- novos campos de JSON;
- execucao real;
- MCP/App SDK;
- `chatgpt-app-submission.json`.

Fechamento:

- testes existentes devem passar;
- nenhuma chamada externa deve ser adicionada;
- autoavaliacao deve ser entregue no relato final da implementacao.

### MVP7.6.2 - SmartOffers Ontology

Status: concluido/aprovado.

Objetivo: criar vocabulario interno do produto para clientes, campanhas, eventos, metricas, caracteristicas, auditoria, processamento, integracoes e evidencias.

Entregas:

- expandir `ai/knowledge/README.md` como indice da ontologia;
- criar `ai/knowledge/ontology.md`;
- criar `ai/knowledge/customer.md`;
- criar `ai/knowledge/campaign.md`;
- criar `ai/knowledge/event.md`;
- criar `ai/knowledge/metric.md`;
- criar `ai/knowledge/characteristic.md`;
- criar `ai/knowledge/audit.md`;
- criar `ai/knowledge/processing.md`;
- criar `ai/knowledge/integration.md`;
- criar `ai/knowledge/evidence.md`;
- preparar base conceitual para MVP7.6.3 Operational Playbooks e MVP7.6.4 Evidence Planner.

Nao escopo:

- codigo funcional;
- alteracao de `app.py`, `core/`, `templates/` ou `tests/`;
- novos endpoints;
- schemas executaveis;
- fixtures;
- JSONs de cenario;
- execucao real;
- alteracao de dry-run, adapter-run, `request_plan` ou catalogo seguro;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright ou Flask.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional deve permanecer vazio.

### MVP7.6.3 - Operational Playbooks

Status: concluido/aprovado.

Objetivo: transformar troubleshooting operacional em roteiros seguros e reutilizaveis.

Escopo planejado:

- expandir `ai/playbooks/README.md` como indice dos playbooks;
- criar playbooks Markdown para cliente fora da campanha, SMS nao enviado, evento nao processado, callback nao refletido, beneficio/oferta nao atualizado, campanha travada, backlog/atraso de processamento, publicacao/configuracao e divergencia de evidencia;
- usar a ontologia do MVP7.6.2 como fonte principal;
- preparar base conceitual para MVP7.6.4 Evidence Planner.

Arquivos entregues:

- `ai/playbooks/README.md`;
- `ai/playbooks/customer-not-in-campaign.md`;
- `ai/playbooks/sms-not-sent.md`;
- `ai/playbooks/event-not-processed.md`;
- `ai/playbooks/callback-not-reflected.md`;
- `ai/playbooks/benefit-or-offer-not-updated.md`;
- `ai/playbooks/campaign-stuck-in-state.md`;
- `ai/playbooks/processing-backlog-or-delay.md`;
- `ai/playbooks/catalog-publication-config-issue.md`;
- `ai/playbooks/evidence-mismatch.md`.

Nao escopo:

- codigo funcional;
- alteracao de `app.py`, `core/`, `templates/` ou `tests/`;
- novos endpoints;
- schemas executaveis;
- fixtures;
- JSONs de cenario;
- automacoes;
- execucao real;
- alteracao de dry-run, adapter-run, `request_plan` ou catalogo seguro;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright ou Flask.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional deve permanecer vazio;
- validacoes de secoes, ASCII e seguranca devem passar.

### MVP7.6.4 - Evidence Planner Foundation

Status: concluido/aprovado.

Objetivo: preparar o produto para gerar plano de evidencias, ainda de forma deterministica e sem Oracle real.

Entregas:

- criar `ai/evidence/README.md`;
- criar `ai/evidence/evidence-planner-contract.md`;
- criar `ai/evidence/evidence-layers.md`;
- criar `ai/evidence/playbook-mapping.md`;
- criar `ai/evidence/evidence-statuses.md`;
- registrar camadas conceituais de evidencia;
- mapear playbooks operacionais do MVP7.6.3 para camadas de evidencia;
- definir status seguros `mock`, `read-only`, `blocked` e `future-controlled`;
- atualizar `ai/README.md` com a nova area documental.

Nao escopo:

- codigo funcional;
- `core/evidence/`;
- alteracao de `app.py`, `core/`, `templates/` ou `tests/`;
- novos endpoints;
- schemas executaveis;
- fixtures;
- automacoes;
- JSONs de cenario;
- execucao real;
- alteracao de dry-run, adapter-run, `request_plan` ou catalogo seguro;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright ou Flask.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional deve permanecer vazio;
- validacoes de camadas, playbooks, statuses, ASCII e seguranca devem passar.

### MVP7.6.5 - AI Supervisors Foundation

Status: concluido/aprovado.

Objetivo: criar estrutura inicial de supervisores e skills do produto, ainda sem LLM externo e sem integracoes reais.

Entregas:

- expandir `ai/supervisors/README.md` como indice operacional;
- criar contratos Markdown para `smartoffers-architect-supervisor`, `campaign-supervisor`, `evidence-supervisor`, `troubleshooting-supervisor`, `catalog-config-supervisor`, `adapter-supervisor` e `safety-supervisor`;
- criar `ai/supervisors/supervisor-routing.md`;
- registrar relacao conceitual entre supervisores e skills futuras em `ai/skills/README.md`;
- usar `ai/knowledge/`, `ai/playbooks/` e `ai/evidence/` como fontes documentais;
- preparar base conceitual para MVP7.6.6 Scenario Intelligence Layer.

Nao escopo:

- codigo funcional;
- LLM externo;
- agentes autonomos;
- ferramentas;
- MCP/App SDK;
- endpoints;
- schemas executaveis;
- fixtures;
- automacoes;
- JSONs operacionais ou de cenario;
- execucao real;
- alteracao de `app.py`, `core/`, `templates/`, `tests/`, catalogo seguro, dry-run, adapter-run ou `request_plan`.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional deve permanecer vazio;
- validacoes de contratos, secoes, roteamento, ASCII e seguranca devem passar.

### MVP7.6.6 - Scenario Intelligence Layer

Status: concluido/aprovado.

Objetivo: adicionar analise deterministica do cenario, incluindo dominio, fluxo principal, camadas de evidencia esperadas e supervisores sugeridos.

Entregas:

- criar documentacao em `ai/scenario-intelligence/`;
- criar pacote interno `core/intelligence/`;
- criar funcao pura `analyze_scenario(scenario: dict) -> dict`;
- derivar dominio, fluxo principal, entidades, playbooks, camadas de evidencia, supervisores, riscos e status geral;
- manter a analise deterministica, read-only, sem I/O, sem rede, sem LLM, sem ambiente real, sem data/hora/random e sem mutar o dict recebido;
- criar testes dedicados em `tests/test_scenario_intelligence.py`.

Nao escopo:

- alteracao de `app.py`, `templates/`, rotas ou UI;
- alteracao de geracao de cenarios ou JSON salvo;
- alteracao de dry-run, adapter-run, catalogo seguro ou `request_plan`;
- endpoint;
- schema executavel;
- automacao externa;
- chamada Oracle, API real, Kafka, Jenkins, rede, subprocesso ou LLM;
- MCP/App SDK;
- Playwright;
- `mode=real`;
- MVP7.6.7.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional proibido deve permanecer vazio;
- validacoes de escopo, ASCII, seguranca, imports proibidos, nao mutacao e determinismo devem passar.

### MVP7.6.6.1 - Scenario Intelligence Safety Hotfix

Status: concluido/aprovado.

Objetivo: bloquear explicitamente sinais de execucao real segura indevida na camada de inteligencia de cenario.

Entregas:

- detectar `safe_for_real_execution=true`;
- detectar `real_execution=true`;
- manter `blocked` com precedencia sobre `future-controlled` e `read-only`;
- adicionar testes dedicados para sinais booleanos e textuais;
- preservar funcao pura, deterministica, sem I/O e sem mutacao do dict recebido.

Nao escopo:

- MVP7.6.7;
- alteracao de rotas, UI, geracao de cenarios, JSON salvo, dry-run, adapter-run, catalogo seguro ou `request_plan`;
- chamada externa, Flask, Playwright, LLM, MCP/App SDK ou execucao real.

Fechamento:

- testes existentes devem passar;
- mudancas devem ficar restritas a `core/intelligence/scenario_analysis.py`, `tests/test_scenario_intelligence.py` e `PROJECT_STATUS.md`;
- `safe_for_real_execution=true` e `real_execution=true` devem resultar em `overall_status=blocked`.

### MVP7.6.7 - Adapter Risk Classifier

Status: concluido/aprovado.

Objetivo: classificar risco antes de qualquer adapter-run real futuro, mantendo `mode=real` bloqueado ate MVP especifico.

Entregas:

- criar documentacao em `ai/risk/`;
- criar pacote interno `core/risk/`;
- criar funcao pura `classify_adapter_risk(work_item: dict) -> dict`;
- classificar risco para adapter, request plan, http plan, item de catalogo, resultado de inteligencia de cenario, evidence layer ou execucao pretendida;
- retornar `risk_level`, `risk_status`, `blocked_reasons`, `allowed_mode`, `required_guardrails`, `related_supervisors` e `safe_next_step`;
- aplicar precedencia `blocked > future_controlled_required > read_only_allowed > mock_allowed`;
- manter execucao real bloqueada e preparar base para MVP7.7 sem inicia-lo;
- criar testes dedicados em `tests/test_adapter_risk_classifier.py`.

Nao escopo:

- alteracao de `app.py`, `templates/`, rotas ou UI;
- alteracao de geracao de cenarios ou JSON salvo;
- alteracao de dry-run, adapter-run, catalogo seguro ou `request_plan`;
- endpoint;
- schema executavel;
- fixture;
- automacao externa;
- chamada Oracle, API real, Kafka, Jenkins, rede, subprocesso ou LLM;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright;
- `mode=real`;
- MVP7.7.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff funcional proibido deve permanecer vazio;
- validacoes de escopo, pureza, determinismo, precedencia, ausencia de mutacao, ASCII e seguranca devem passar.

### MVP7.7.0 - Real Execution Readiness Gate

Status: concluido/aprovado.

Objetivo: criar readiness gate deterministico para avaliar intencao futura de execucao real em QA4 sem executar chamada real.

Entregas:

- criar documentacao em `ai/real-execution/`;
- criar pacote interno `core/real_execution/`;
- criar `build_readiness_policy(...) -> dict`;
- criar `evaluate_real_execution_readiness(request: dict, policy: dict) -> dict`;
- validar opt-in, allowlist, ambiente, kill switch, timeout, retry, policy e risco;
- manter `ready_for_real_call=false` mesmo quando a decisao for `ready_for_manual_review`;
- criar testes dedicados em `tests/test_real_execution_readiness.py`.

Nao escopo:

- MVP7.7.1;
- chamada real;
- client HTTP;
- leitura de `.env` ou variaveis de ambiente;
- host real, IP real, token, secret, credential, payload real, MSISDN, account ou documento real;
- alteracao de `app.py`, `templates/`, rotas ou UI;
- alteracao de geracao de cenarios ou JSON salvo;
- alteracao de dry-run, adapter-run, catalogo seguro ou `request_plan`;
- endpoint;
- schema executavel;
- automacao externa;
- chamada Oracle, API real, Kafka, Jenkins, rede, subprocesso ou LLM;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright;
- liberacao de `mode=real`.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- mudancas devem ficar restritas a `ai/real-execution/`, `core/real_execution/`, `tests/test_real_execution_readiness.py` e `PROJECT_STATUS.md`;
- validacoes de escopo, imports proibidos, logs sanitizados, determinismo, ausencia de mutacao e ausencia de chamada externa devem passar.

### MVP7.7.1.0 - Runtime Secret Contract

Status: concluido/aprovado.

Objetivo: criar contrato de runtime seguro para uma futura primeira chamada QA4, ainda sem chamada real e sem iniciar MVP7.7.1.1.

Entregas:

- criar contrato documental de runtime seguro em `ai/real-execution/runtime-secret-contract.md`;
- criar runbook conceitual em `ai/real-execution/first-call-runbook.md`;
- criar `core/real_execution/runtime.py` para validar referencias runtime injetadas;
- criar `core/real_execution/allowlist.py` com allowlist conceitual separada do catalogo sanitizado;
- criar `core/real_execution/http_client.py` com fake client obrigatorio;
- criar `core/real_execution/executor.py` com `prepare_first_qa4_call(...)`;
- bloquear antes do fake client quando runtime, allowlist, risk classifier, readiness gate ou kill switch falham;
- manter `real_call_executed=false`;
- criar testes dedicados em `tests/test_real_execution_runtime_contract.py` e `tests/test_first_qa4_call_executor.py`.

Nao escopo:

- MVP7.7.1.1;
- chamada real;
- client HTTP real;
- leitura de `.env`, arquivo externo ou variaveis reais;
- host real, IP real, material de autenticacao, credencial, massa real, linha, conta ou documento real;
- alteracao de `app.py`, `templates/`, rotas ou UI;
- alteracao de geracao de cenarios ou JSON salvo;
- alteracao de dry-run, adapter-run, catalogo seguro ou `request_plan`;
- endpoint;
- schema executavel;
- automacao externa;
- chamada Oracle, API real, Kafka, Jenkins, rede, subprocesso ou LLM;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- Playwright;
- liberacao de `mode=real`.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- mudancas devem ficar restritas a `ai/real-execution/`, `core/real_execution/`, `tests/test_real_execution_runtime_contract.py`, `tests/test_first_qa4_call_executor.py` e `PROJECT_STATUS.md`;
- validacoes de escopo, imports proibidos, logs sanitizados, fake client obrigatorio, determinismo, ausencia de mutacao e ausencia de chamada externa devem passar.

### MVP7.7.1.1 - First QA4 Real Call Gate

Status: concluido/aprovado.

Objetivo: criar gate manual controlado para uma futura primeira chamada real em QA4, sem executar chamada real durante implementacao, testes, CI ou Self Review.

Entregas:

- criar contrato documental em `ai/real-execution/first-real-call-manual-contract.md`;
- criar `core/real_execution/real_http_client.py` como client real isolado e nao exportado;
- preservar `prepare_first_qa4_call(...)` como fluxo fake/readiness;
- criar `execute_first_qa4_call_manual(...)` como fluxo manual controlado;
- separar `runtime_refs` sanitizado de `runtime_secrets` em memoria;
- garantir que `runtime_secrets` nao vai para risk classifier, readiness, logs, evidencia ou retorno;
- exigir approval manual sanitizado;
- bloquear antes do client quando approval, kill switch, readiness, risk classifier, allowlist, timeout, retry ou runtime falham;
- manter `adapter-run mode=real` bloqueado;
- criar testes dedicados em `tests/test_first_qa4_real_call_manual_gate.py`.

Nao escopo:

- execucao real durante implementacao, testes, CI ou Self Review;
- UI;
- rota;
- integracao com adapter-run;
- alteracao de dry-run;
- alteracao do catalogo seguro;
- alteracao de `request_plan`;
- chamada Oracle, Kafka ou Jenkins;
- Playwright;
- MCP/App SDK;
- `chatgpt-app-submission.json`;
- versionamento de endpoint real, endereco de rede real, material de autenticacao, credencial, cabecalho real, massa real, linha, conta, documento ou corpo bruto.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- mudancas devem ficar restritas a `ai/real-execution/`, `core/real_execution/`, `tests/test_first_qa4_real_call_manual_gate.py` e `PROJECT_STATUS.md`;
- import HTTP padrao permitido somente em `core/real_execution/real_http_client.py`;
- validacoes de escopo, imports, evidencia sanitizada, runtime separado, approval, fake/dummy tests, ausencia de mutacao e ausencia de chamada externa automatizada devem passar.

### MVP7.7.2 - Real Execution Hardening & Evidence Pack

Status: concluido/aprovado.

Objetivo: endurecer a camada de execucao real manual criada nos MVPs 7.7.0, 7.7.1.0 e 7.7.1.1, sem executar QA4, sem chamada real e sem dado real.

Entregas:

- criar documento consolidado de hardening/evidencia;
- criar checklist operacional de execucao manual;
- criar matriz de guardrails;
- criar contrato de evidencia sanitizada;
- criar testes negativos adicionais para isolamento do client real e guardrails;
- validar que `RealHttpClient` nao e exportado em `core/real_execution/__init__.py`;
- validar que `execute_first_qa4_call_manual` nao e exportado em `core/real_execution/__init__.py`;
- validar que o import HTTP padrao aparece somente em `core/real_execution/real_http_client.py`;
- validar que falhas de guardrail bloqueiam antes do client;
- validar que `runtime_secrets` nao aparece em evidencia, log ou retorno.

Nao escopo:

- execucao QA4;
- chamada real;
- dado real;
- UI;
- rota;
- integracao com adapter-run;
- alteracao de dry-run;
- alteracao do catalogo seguro;
- alteracao de `request_plan`;
- chamada Oracle, Kafka ou Jenkins;
- Playwright;
- MCP/App SDK;
- `chatgpt-app-submission.json`.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- mudancas devem ficar restritas a `ai/real-execution/`, testes de hardening, utilitarios puros em `core/real_execution/` se necessarios e `PROJECT_STATUS.md`;
- diff deve permanecer vazio nos caminhos proibidos;
- worktree deve ficar limpa apos commit/push.

### MVP7.7.3 - Manual QA4 Execution Readiness Package

Status: concluido/aprovado.

Objetivo: criar o pacote final para orientar uma futura execucao manual QA4, sem executar QA4, sem chamada real, sem dado real e sem automacao.

Entregas:

- criar `ai/real-execution/manual-qa4-readiness-package.md`;
- criar `ai/real-execution/manual-qa4-operator-script-template.md`;
- criar `ai/real-execution/manual-qa4-approval-template.md`;
- criar `ai/real-execution/manual-qa4-evidence-template.md`;
- manter todos os templates somente com placeholders sanitizados;
- validar por teste que os templates existem, permanecem ASCII, usam placeholders e nao contem formatos com aparencia de valor real;
- validar que `RealHttpClient` e `execute_first_qa4_call_manual` continuam fora do `__init__.py`;
- validar que o import HTTP padrao permanece isolado no client real;
- validar que `adapter-run mode=real` continua bloqueado.

Nao escopo:

- execucao QA4;
- chamada real;
- dado real;
- automacao;
- UI;
- rota;
- integracao com adapter-run;
- alteracao de dry-run;
- alteracao do catalogo seguro;
- alteracao de `request_plan`;
- chamada Oracle, Kafka ou Jenkins;
- Playwright;
- MCP/App SDK;
- `chatgpt-app-submission.json`.

Fechamento:

- Self Review final: APROVADO;
- testes existentes devem passar;
- diff deve permanecer vazio nos caminhos proibidos;
- worktree deve ficar limpa apos commit/push.

### MVP7.7 - Primeira chamada real opt-in em QA4

Objetivo: permitir a primeira chamada real controlada em QA4, somente com opt-in e guardrails.

MVP7.7 depende de ontologia SmartOffers, playbooks operacionais, evidence planner, supervisores de dominio, risk classifier, policy explicita de allow/deny e testes cobrindo cenarios permitidos e negados.

Condicoes esperadas:

```txt
mode=real
environment=QA4
REAL_EXECUTION_ENABLED=true
API explicitamente liberada
timeout configurado
logs sanitizados
producao bloqueada
```

### MVP8 - Runner controlado / filas

Objetivo: evoluir execucao para modelo assincrono/controlado, com fila e acompanhamento de status.

### MVP9 - IA auxiliar local-first

Objetivo: incorporar IA auxiliar com uso controlado, apoiada por knowledge base, playbooks e supervisores.

### MVP10 - Frontend moderno

Objetivo: avaliar uma UI mais robusta somente quando o backend estiver maduro o suficiente.

## Documentos

- `docs/ARCHITECTURE.md`: arquitetura atual e direcao futura.
- `docs/ROADMAP.md`: sequencia de MVPs e dependencias.
- `docs/SECURITY_MODEL.md`: regras de execucao real, dados sensiveis, `mode=real`, QA4 e bloqueio de producao.
- `docs/SUPERVISORS.md`: supervisores e skills previstos.
