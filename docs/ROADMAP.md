# Roadmap

## Estado atual

O `SmartOffers_Automation_Driven` esta em MVP7.8.3A.1 concluido na branch evolutiva `qa/mvp4-integration`. A branch tem nome historico ligado ao MVP4, mas representa a linha atual do produto.

PortalQA ficou como referencia historica e nao deve orientar a arquitetura atual.

O produto ja possui geracao deterministica, dry-run mockado, adapters mockados, catalogo seguro de APIs, runtime binding para QA manual, contrato runtime multi-recurso para `qa4_first_smoke_api_acm_custom_ro` e protecao local para runtime secrets. A execucao real permanece bloqueada por padrao.

Runtime secrets locais estao protegidos por template e `.gitignore`; a protecao local foi registrada no commit `de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71`.

## Direcao

O produto evoluiu de gerador/simulador de testes para laboratorio seguro de automacao SmartOffers/ACM, local-first e mock-first.

A preparacao para execucao real deve permanecer gradual e controlada. Qualquer chamada real futura exige opt-in explicito, ambiente permitido, allowlist, timeout obrigatorio, logs sanitizados, bloqueio de producao e testes cobrindo caminhos permitidos e negados.

## Roadmap futuro atual

Os MVPs 7.6.x e 7.7.x sao historico concluido/aprovado. O plano futuro parte do MVP7.8.3A.1:

- MVP7.8.3B - First QA4 Real Smoke manual
- MVP7.8.4 - QA4 Sanity Runner Standard/Variant/Copy
- MVP7.8.5 - Real Campaign Scenario Pack 01
- MVP7.8.6 - Evidence Comparison & Runner Hardening
- MVP7.9.0 - SmartOffers Real Regression Suite v0
- v0.1 estavel interna

## Prioridade de ambientes

QA4 e a prioridade para o primeiro smoke real controlado e para estabilizar o caminho real.

QA1 vem depois somente se houver config local completa para API, DSN, usuario, senha e client Oracle.

QA2/QA3 entram apenas apos QA4 estar estavel, com os mesmos guardrails e sem promover execucao real por padrao.

## Estimativas

- real QA4 executavel: 2 a 3 dias uteis;
- sanity real padrao/variante/copy: 4 a 5 dias uteis;
- primeiros cenarios reais: 7 a 10 dias uteis;
- v0.1 estavel interna: 15 a 20 dias uteis.

## Guardrails permanentes

- `mode=real` e caminhos equivalentes continuam bloqueados por padrao.
- Execucao real exige opt-in explicito, ambiente permitido, allowlist, timeout, logs sanitizados e bloqueio de producao.
- Runtime secrets devem permanecer fora do Git.
- Catalogo seguro deve continuar com `execution_status=blocked` e `safe_for_real_execution=false` ate MVP especifico.
- QA, BD, API, Kafka e Jenkins reais nao devem ser chamados por testes automatizados ou dry-run.

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
