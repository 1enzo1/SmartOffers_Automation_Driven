# Roadmap

## Estado atual

> Current product state is maintained in `PROJECT_STATE.md`; this roadmap keeps
> historical MVP context and records future direction. The active product work
> branch is `codex/post-alpha-ux`. The historical references below are not a
> grant of operational authority.

O `SmartOffers_Automation_Driven` possui baseline pre-alpha imutavel na tag
`v0.0.0-pre-alpha.1`, integrada em `qa/mvp4-integration`. O Owner aceitou o
MVP7.8.3B no recorte DB-only; API e smokes consolidados permanecem incompletos.
MVP7.8.4 esta autorizado para desenvolvimento mock-first. A continuacao de
governanca esta em `codex/alpha`; ver `ALPHA_GOVERNANCE.md`.

PortalQA ficou como referencia historica e nao deve orientar a arquitetura atual.

O produto ja possui geracao deterministica, dry-run mockado, adapters mockados, catalogo seguro de APIs, runtime binding para QA manual, contrato runtime multi-recurso para `smartoffers_basic_smoke` e protecao local para runtime secrets. A execucao real permanece bloqueada por padrao.

Runtime secrets locais estao protegidos por template e `.gitignore`; a protecao local foi registrada no commit `de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71`.

## Direcao

O produto evoluiu de gerador/simulador de testes para laboratorio seguro de automacao SmartOffers/ACM, local-first e mock-first.

A preparacao para execucao real deve permanecer gradual e controlada. Qualquer chamada real futura exige opt-in explicito, ambiente permitido, allowlist, timeout obrigatorio, logs sanitizados, bloqueio de producao e testes cobrindo caminhos permitidos e negados.

## Roadmap futuro atual

### Product milestones

| Milestone | State | Scope |
| --- | --- | --- |
| `v0.0.0-alpha.1` | DONE | Historical controlled Alpha baseline. |
| Alpha 1.1 | QA-FIRST PRODUCT PREAUTH | QA-first workspace with Diagnostics secondary, product delegation to the recovered controlled Offers contract, sanitised evidence UI, and practical test tiers. Real transport remains separately authorized. |
| Real Test Pack | NEXT | Define each new operation-scoped contract, approved read-only validation, and separate Owner authorization before any real execution. |
| Alpha 1.2 preparation | IN PROGRESS | Local contract archaeology and safe product/test hardening are complete for this pass; authoritative Recharge and standalone Add Offer contracts remain external. |
| Beta Candidate | FUTURE | Expand only after independently evidenced real test packs are available. |

The historical Offers execution is represented by the product as **Create
Customer with Offer** and is not a standalone pure customer-creation contract.
Run 03A source readiness comes from the current governed product delegation,
not from historical success alone; authorization and live runtime remain
separate prerequisites.

Os MVPs 7.6.x e 7.7.x sao historico concluido/aprovado. O plano futuro parte do
recorte MVP7.8.3B DB-only:

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
