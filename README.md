# SmartOffers Automation Driven

SmartOffers_Automation_Driven e uma plataforma Flask/Python local-first e mock-first para geracao, simulacao, planejamento seguro e futura execucao controlada de cenarios SmartOffers/ACM.

O produto deve evoluir como um laboratorio seguro de automacao SmartOffers/ACM, nao apenas como um gerador ou simulador de testes. Ele transforma regras de campanha, eventos, APIs sanitizadas, evidencias operacionais e troubleshooting em cenarios deterministicos, dry-runs, adapter-runs mockados, `request_plan` seguro e, em MVP futuro, execucoes reais controladas.

Estado atual: MVP7.8.2 concluido, com protecao local de runtime secrets registrada no commit `de9d1e77cfba11b1b81aa9640cb36a7aacf5fd71`. A branch `qa/mvp4-integration` e a linha evolutiva atual do produto, apesar do nome historico ligado ao MVP4. A execucao real segue bloqueada por padrao, e o projeto nao faz chamadas reais para Oracle, APIs, Kafka, Jenkins ou rede externa.

## Objetivo

Centralizar e padronizar um ciclo seguro de automacao SmartOffers:

- gerar cenarios deterministicos a partir de respostas e templates;
- salvar e reabrir cenarios em JSON;
- simular execucao com dry-run mockado;
- executar adapter-run local e mockado;
- exportar artefatos QA/DET em JSON, DOCX e XLSX;
- consultar um catalogo seguro de APIs sanitizadas;
- montar `request_plan` SmartOffers deterministico sem rede real;
- organizar conhecimento de dominio em ontologia, playbooks, supervisores e skills do produto;
- manter uma base preparada para execucao real controlada em MVP futuro.

## Linha evolutiva atual

A branch `qa/mvp4-integration` e a branch base evolutiva atual do SmartOffers_Automation_Driven. O nome permanece por historico, mas a branch ja contem evolucoes posteriores, incluindo biblioteca de templates, dry-run mockado, exports QA/DET, adapters mockados, catalogo seguro de APIs e planejamento SmartOffers `mock_only`.

Nao iniciar novo MVP a partir de `main` sem confirmacao explicita. Antes de qualquer PR, confirmar que a branch contem o merge do MVP7.6 ou posterior.

## Direcao do produto

O projeto nao deve ser tratado apenas como ferramenta de testes. A direcao correta e um laboratorio seguro de automacao SmartOffers/ACM com geracao deterministica, planejamento mockado, evidencias esperadas, classificacao de risco, supervisores de dominio, playbooks operacionais e preparacao gradual para adapters reais.

A execucao real continua bloqueada por padrao. Qualquer evolucao para `mode=real` exige MVP especifico, opt-in explicito, ambiente permitido, allowlist de API/operacao, timeout obrigatorio, logs sanitizados, bloqueio de producao e testes cobrindo cenarios permitidos e negados.

## Roadmap ajustado

O roadmap futuro parte do estado atual MVP7.8.2. Os MVPs 7.6.x e 7.7.x ficam como historico concluido, nao como trabalho pendente.

- MVP7.8.3 - Runtime Preflight & First QA4 Real Smoke
- MVP7.8.4 - QA4 Sanity Runner Standard/Variant/Copy
- MVP7.8.5 - Real Campaign Scenario Pack 01
- MVP7.8.6 - Evidence Comparison & Runner Hardening
- MVP7.9.0 - SmartOffers Real Regression Suite v0
- v0.1 estavel interna

Prioridade de ambientes: QA4 primeiro; QA1 depois apenas com config completa; QA2/QA3 somente apos QA4 estavel.

Estimativas:

- real QA4 executavel: 2 a 3 dias uteis;
- sanity real padrao/variante/copy: 4 a 5 dias uteis;
- primeiros cenarios reais: 7 a 10 dias uteis;
- v0.1 estavel interna: 15 a 20 dias uteis.

## Stack

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- JSON como base de cenarios
- Adapters mockados
- `python-docx` e `openpyxl` para exportacoes

Sem React, sem build step frontend e sem integracoes reais habilitadas.

## Como preparar o ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Como rodar

Para desenvolvimento local:

```powershell
python app.py
```

Rotas principais:

- `GET /`
- `GET /api/questions`
- `GET /api/templates`
- `GET /api/templates/<template_id>`
- `POST /api/scenarios/generate`
- `GET /api/scenarios`
- `GET /api/scenarios/<id>`
- `POST /api/scenarios/<id>/dry-run`
- `POST /api/scenarios/<id>/adapter-run`
- `GET /api/dry-runs/<id>`
- `GET /api/scenarios/<id>/export/<format>`
- `GET /api/dry-runs/<id>/export/<format>`
- `GET /api/adapters`
- `GET /api/adapters/health`
- `GET /api/api-catalog`
- `GET /api/api-catalog/<api_id>`
- `GET /executar`
- `GET /listar_testes`
- `GET /ver_teste`
- `GET /abrir_pasta`

## Como testar

```powershell
python -m pytest tests -q
```

Ao validar Flask em tarefas automatizadas, suba o processo em background, faca cleanup ao final e confirme que a porta usada ficou livre.

## Estrutura principal

```txt
.
|-- app.py
|-- core/
|   |-- adapters/
|   |-- api_catalog/
|   |-- common/
|   |-- execution/
|   |-- exporters/
|   |-- generation/
|   |-- legacy_execution/
|   |-- simulation/
|   `-- templates/
|-- ai/
|   |-- knowledge/
|   |-- playbooks/
|   |-- safety/
|   |-- skills/
|   `-- supervisors/
|-- docs/
|-- templates/
|   `-- index.html
|-- tests/
|-- agents/
|-- .agents/
`-- AGENTS.md
```

## Modulos

`core/generation/` gera cenarios deterministicos, perguntas, templates e normalizacao de payloads.

`core/simulation/` roda dry-run local usando o JSON salvo, sem tocar em sistemas externos.

`core/exporters/` produz artefatos JSON, DOCX e XLSX para cenarios e dry-runs.

`core/adapters/` concentra adapters fake para SmartOffers, Oracle, Kafka, Jenkins e evidencias.

`core/execution/` orquestra adapter-run, normaliza steps e agrega status.

`core/api_catalog/` contem o catalogo sanitizado de APIs, modelos, servico e policy `mock_only`.

`ai/` contem contratos conceituais e operacionais para supervisores, skills, conhecimento, playbooks e safety. No MVP7.6.1, essa pasta nao contem implementacao Python nem LLM externo.

`docs/` contem a documentacao de arquitetura, roadmap, modelo de seguranca e supervisores.

`templates/index.html` contem a UI Flask atual em HTML/CSS/JavaScript puro.

`core/utils/evidence_payload_contract.py` contem diagnostico puro e deterministico de payloads de evidencia, sem abrir ZIP bruto, sem chamada real e sem dado sensivel.

## MVP7.6: SmartOffers request planning mockado

O MVP7.6 faz o `FakeSmartOffersAdapter` consumir o catalogo seguro para montar `request_plan` deterministico apenas em steps `smartoffers.http_plan`.

Regras atuais:

- `smartoffers.http_plan` com `api_id` permitido gera `request_plan`;
- `smartoffers.http_plan` com `api_id` fora da policy fica `blocked`;
- `smartoffers.http_plan` com `api_id` inexistente fica `blocked`;
- `smartoffers.http_plan` sem `api_id` tenta resolver por `event_type` valido do gerador;
- `smartoffers.execution` segue execucao fake normal e nao aplica policy de catalogo;
- `mode=real` continua bloqueado com erro controlado;
- nenhum host real, IP, URL real, token, senha, cookie, bearer ou secret deve aparecer no plano.

Contrato resumido de `request_plan`:

```json
{
  "api_id": "post-evento-de-recarga-6954ef3458",
  "name": "Evento de Recarga",
  "category": "recarga",
  "method": "POST",
  "path": "/ws/integration/online/process",
  "environment": "QA4",
  "environment_variables": ["SMART_OFFERS_INT"],
  "host_placeholder": "<QA4_SMART_OFFERS_INT_HOST>",
  "host_placeholders": ["<QA4_SMART_OFFERS_INT_HOST>"],
  "payload_base": {},
  "headers_expected": [],
  "execution_status": "blocked",
  "safe_for_real_execution": false,
  "source": "api-catalog",
  "planning_mode": "mock_only"
}
```

## MVP7.7.3: Manual QA4 execution readiness package

O MVP7.7.3 criou o pacote final de prontidao para uma futura execucao manual QA4, ainda sem executar QA4, sem chamada real, sem dado real e sem automacao.

Entregas principais:

- pacote de readiness manual QA4;
- template de roteiro operacional humano;
- template de aprovacao manual sanitizada;
- template de evidencia manual sanitizada;
- testes garantindo placeholders, ausencia de valores reais e manutencao do bloqueio de `adapter-run mode=real`.

## MVP7.7.4: Documentation sync and evidence regression analysis

O MVP7.7.4 sincroniza documentacao e registra a analise sanitizada da regressao entre uma evidencia padrao funcional e evidencias variante/copy que falharam.

Entregas principais:

- `README.md` e `PROJECT_STATUS.md` atualizados com o estado real dos MVPs;
- analise em `ai/evidence/mvp7-7-4-evidence-regression-analysis.md`;
- utilitario puro `core/utils/evidence_payload_contract.py`;
- testes deterministicos em `tests/test_evidence_payload_contract.py`.

Conclusao tecnica do diagnostico:

- a evidencia padrao contem `attributeDetails` em todos os requests inspecionados;
- cada atributo enviado no padrao possui metadata correspondente;
- variante e copy possuem `attributes`, mas nao possuem `attributeDetails`;
- `eventTime` existe nos tres conjuntos com a mesma forma de string;
- a copy reduz o payload `pre` em relacao a variante;
- a causa provavel e payload incompleto nas variantes, nao uma falha isolada de BD.

O MVP7.7.4 nao corrige producao, nao altera adapter-run, nao altera dry-run, nao chama QA4 e nao chama BD real.

## Supervisores e skills

A partir da linha 7.6.x, o projeto passa a organizar conhecimento SmartOffers em supervisores e skills. Esses artefatos nao habilitam IA externa, execucao real, Oracle, Kafka, Jenkins ou chamadas de rede. Eles servem como camada de dominio para orientar geracao de cenarios, planejamento de evidencia, classificacao de risco e evolucao futura dos adapters.

Supervisores previstos:

- `smartoffers-architect-supervisor`
- `campaign-supervisor`
- `evidence-supervisor`
- `troubleshooting-supervisor`
- `catalog-config-supervisor`
- `adapter-supervisor`
- `safety-supervisor`

Skills previstas:

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

## Regras de seguranca

Nao fazer:

- chamar Oracle real;
- chamar APIs reais;
- chamar Kafka real;
- chamar Jenkins real;
- executar subprocessos reais para dry-run;
- versionar ZIPs brutos de APIs;
- versionar JSONs brutos de ambiente;
- expor IPs internos ou secrets;
- alterar `safe_for_real_execution` sem MVP especifico;
- alterar `execution_status` no catalogo sem MVP especifico;
- habilitar `mode=real` sem opt-in e controles dedicados.

Arquivos sensiveis nao versionaveis:

```txt
APIsUtilizaveis.zip
QA4_Copy.json
.env
.env.*
.env.local
*.local.env
local_secrets/
smartoffers_runtime_local.ps1
*.dbp
*.zip
DBeaver exports sensiveis
*.local
.test_smoke/
```

## Status e roadmap

O historico de MVPs, decisoes, APIs mock_only e proximos passos ficam em [PROJECT_STATUS.md](PROJECT_STATUS.md).
