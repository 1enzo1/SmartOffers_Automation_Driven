# SmartOffers Automation Driven

Plataforma Flask/Python para geracao, simulacao, planejamento mockado e futura execucao controlada de cenarios SmartOffers/ACM.

O projeto evolui de forma incremental: primeiro gera cenarios deterministicos, depois simula execucao localmente, exporta evidencias QA/DET e prepara adapters seguros para uma futura execucao real com opt-in explicito.

Estado atual: MVP7.6 concluido. A execucao real segue bloqueada por padrao, e o projeto nao faz chamadas reais para Oracle, APIs, Kafka, Jenkins ou rede externa.

## Objetivo

Centralizar e padronizar o ciclo de testes SmartOffers:

- gerar cenarios deterministicos a partir de respostas e templates;
- salvar e reabrir cenarios em JSON;
- simular execucao com dry-run mockado;
- executar adapter-run local e mockado;
- exportar artefatos QA/DET em JSON, DOCX e XLSX;
- consultar um catalogo seguro de APIs sanitizadas;
- montar `request_plan` SmartOffers deterministico sem rede real;
- manter uma base preparada para execucao real controlada em MVP futuro.

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

`templates/index.html` contem a UI Flask atual em HTML/CSS/JavaScript puro.

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
*.local
.test_smoke/
```

## Status e roadmap

O historico de MVPs, decisoes, APIs mock_only e proximos passos ficam em [PROJECT_STATUS.md](PROJECT_STATUS.md).
