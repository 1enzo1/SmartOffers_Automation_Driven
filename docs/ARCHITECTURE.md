# Architecture

## Produto

`SmartOffers_Automation_Driven` e o produto principal atual. PortalQA ficou como referencia historica e nao deve orientar a arquitetura.

O produto e um laboratorio seguro de automacao SmartOffers/ACM, local-first e mock-first. Ele gera cenarios deterministicos, salva JSONs, simula execucao por dry-run mockado, executa adapter-run mockado, exporta artefatos QA/DET e monta `request_plan` a partir de catalogo seguro.

## Linha base

- Branch evolutiva atual: `qa/mvp4-integration`, apesar do nome historico.
- Baseline imutavel: `v0.0.0-pre-alpha.1` no merge `e1263595aa736de3855234b6f9a0379b944fe70e`.
- Continuacao de governanca: `codex/alpha`.
- Estado atual: MVP7.8.3B aceito no recorte DB-only; MVP7.8.4 autorizado para desenvolvimento mock-first.
- Runtime secrets locais: protegidos por `.gitignore` e template sanitizado desde o commit `de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71`.
- Execucao real: bloqueada por padrao.
- Catalogo de APIs: sanitizado, versionado e `mock_only`.
- UI: Flask com HTML/CSS/JavaScript puro.
- Testes: Pytest.
- Frontend moderno: roadmap futuro.

## Componentes atuais

`app.py` expoe as rotas Flask e conecta geracao, simulacao, execucao, exporters, catalogo de APIs e runner legado.

`core/generation/` cria cenarios deterministicos a partir de respostas e templates.

`core/simulation/` executa dry-run local usando JSON salvo, sem Oracle, APIs, Kafka, Jenkins, rede ou subprocessos reais.

`core/execution/` normaliza steps, queries, checkpoints e evidencias para adapter-run mockado.

`core/adapters/` contem adapters fake para SmartOffers, Oracle, Kafka, Jenkins e evidencia.

`core/api_catalog/` guarda catalogo sanitizado e policy `mock_only` para planejamento de request.

`core/legacy_execution/` mantem o runner legado protegido por modo, ambiente, perfil runtime, confirmacao explicita, preflight sanitizado e runtime config externo ao Git.

`core/real_execution/runtime_profiles.py` define contratos sanitizados por perfil/fluxo. O perfil oficial inicial e `smartoffers_basic_smoke`, que exige SmartOffers API, ACM_CUSTOM read-only e Oracle client por nomes de refs, sem valores reais. Alias `SMARTOFFERS_QA4_DB_*` sao aceitos apenas como legado temporario para ACM_CUSTOM e nao representam ACMV4 ou BDA.

`tools/qa4_manual_smoke.py`, `tools/qa4_acm_manual_smoke.py`,
`tools/qa4_bda_manual_smoke.py` e `tools/qa4_api_health_smoke.py` sao executores manuais dormentes.
Alguns possuem capacidade tecnica de carregar clientes e acionar transporte,
mas essa capacidade nao constitui liberacao Alpha nem garantia de kill switch.
Eles permanecem operacional e contratualmente
proibidos de invocacao real no Alpha.

`core/exporters/` gera artefatos JSON, DOCX e XLSX para cenarios e dry-runs.

`ai/` contem contratos conceituais e operacionais para ontologia, playbooks, evidencia, risco, real execution, skills e supervisores.

Os contratos em `ai/supervisors/*` pertencem ao dominio interno do produto. Eles
nao sao os papeis multiagente de desenvolvimento descritos em `AGENTS.md`, nao
usam ferramentas e nao possuem autoridade operacional. O snapshot de
governanca e as divergencias vigentes ficam em `docs/ALPHA_GOVERNANCE.md`.

## Guardrails de execucao real

`mode=real` e qualquer caminho equivalente continuam bloqueados por padrao. Uma futura execucao real so pode existir em MVP especifico e deve exigir:

- opt-in explicito;
- ambiente permitido;
- allowlist de API/operacao;
- timeout obrigatorio;
- logs sanitizados;
- runtime secrets fora do Git;
- bloqueio de producao;
- testes cobrindo allow e deny.

Esses controles nao liberam execucao real por si so. Eles sao pre-condicoes para revisao e implementacao futura.

## Fronteiras de compatibilidade

Mudancas documentais e de guardrail nao devem alterar:

- rotas Flask;
- schema de cenarios;
- JSONs existentes;
- geracao deterministica;
- dry-run;
- adapter-run;
- `request_plan`;
- catalogo seguro;
- UI.

Qualquer campo novo em JSON deve ser opcional e precisa de MVP proprio.

## Direcao de extensao

A sequencia de evolucao preservada e:

1. guardrails e documentacao de arquitetura;
2. ontologia SmartOffers;
3. playbooks operacionais;
4. evidence planner;
5. supervisores e skills;
6. scenario intelligence;
7. adapter risk classifier;
8. primeira chamada real opt-in em QA4;
9. runner controlado com fila/status;
10. IA auxiliar local-first;
11. frontend moderno.
