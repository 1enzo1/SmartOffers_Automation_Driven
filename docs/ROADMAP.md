# Roadmap

## Estado atual

O `SmartOffers_Automation_Driven` esta em MVP7.8.2 concluido na branch evolutiva `qa/mvp4-integration`. A branch tem nome historico ligado ao MVP4, mas representa a linha atual do produto.

PortalQA ficou como referencia historica e nao deve orientar a arquitetura atual.

O produto ja possui geracao deterministica, dry-run mockado, adapters mockados, catalogo seguro de APIs e protecao local para runtime secrets. A execucao real permanece bloqueada por padrao.

## Direcao

O produto evoluiu de gerador/simulador de testes para laboratorio seguro de automacao SmartOffers/ACM, local-first e mock-first.

A preparacao para execucao real deve permanecer gradual e controlada. Qualquer chamada real futura exige opt-in explicito, ambiente permitido, allowlist, timeout obrigatorio, logs sanitizados, bloqueio de producao e testes cobrindo caminhos permitidos e negados.

## Sequencia ajustada

### MVP7.6.1 - Guardrails e documentacao de arquitetura

Registrar direcao de produto, branch evolutiva, limites de seguranca, arquitetura atual e estrutura Markdown inicial para `ai/`.

### MVP7.6.2 - Ontologia SmartOffers

Criar vocabulario interno do produto para cliente, campanha, evento, metricas, caracteristicas, auditoria, processamento, integracoes e evidencias.

### MVP7.6.3 - Playbooks operacionais

Criar roteiros seguros de troubleshooting para sintomas operacionais SmartOffers/ACM.

### MVP7.6.4 - Evidence Planner

Preparar plano deterministico de evidencias por camada, sem consultar Oracle real ou sistemas externos.

### MVP7.6.5 - AI Supervisors Foundation

Criar supervisores do produto como contratos de dominio, sem LLM externo e sem integracoes reais.

### MVP7.6.6 - Scenario Intelligence Layer

Adicionar analise deterministica de cenario com dominio, fluxo principal, camadas de evidencia esperadas, risco e supervisores sugeridos.

### MVP7.6.7 - Adapter Risk Classifier

Classificar risco antes de qualquer adapter-run real futuro, mantendo producao, mutacoes e operacoes destrutivas bloqueadas.

### MVP7.7 - Primeira chamada real opt-in em QA4

Permitir uma primeira chamada real somente em QA4, somente com opt-in e guardrails aprovados.

Condicoes minimas:

- `mode=real`;
- ambiente permitido;
- opt-in explicito;
- allowlist de API/operacao;
- timeout obrigatorio;
- logs sanitizados;
- producao bloqueada;
- testes cobrindo allow e deny.

### MVP8 - Runner controlado com fila/status

Evoluir execucao para modelo controlado, com fila, status, auditoria e cancelamento seguro.

### MVP9 - IA auxiliar local-first

Incorporar IA auxiliar com governanca, apoiada por knowledge base, playbooks, supervisores e politica local-first.

### MVP10 - Frontend moderno

Avaliar uma UI moderna somente quando backend, contratos e guardrails estiverem maduros o suficiente.

## Supervisores previstos

- `smartoffers-architect-supervisor`
- `campaign-supervisor`
- `evidence-supervisor`
- `troubleshooting-supervisor`
- `catalog-config-supervisor`
- `adapter-supervisor`
- `safety-supervisor`

## Skills previstas

- `campaign-analysis`
- `evidence-planning`
- `troubleshooting`
- `sql-evidence`
- `api-contract-analysis`
- `request-plan-analysis`
- `adapter-execution-planning`
- `catalog-config-analysis`
- `kafka-nrt-analysis`
- `bko-analysis`
- `risk-classification`
