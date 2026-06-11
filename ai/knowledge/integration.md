# Integration

## Objetivo

Definir integracoes como fronteiras externas ou internas que o produto entende de forma conceitual, mantendo execucao real bloqueada.

## Integracoes previstas

| Integracao | Uso conceitual |
| --- | --- |
| SmartOffers API | Planejamento seguro via `request_plan` e `http_plan`. |
| ACM Query | Referencia para consultas de leitura planejadas. |
| Kafka | Trace conceitual de mensagens por chave de correlacao. |
| BKO | Referencia operacional para acao manual ou massiva futura. |
| SmartGateway | Fronteira conceitual para entrada ou roteamento. |
| Jenkins | Referencia historica de automacao bloqueada. |
| Oracle | Fonte conceitual para evidencias de leitura, nunca chamada real no estado atual. |

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `api_id` | Identificador sanitizado de API no catalogo seguro. |
| `request_plan` | Plano mockado de request, sem rede real. |
| `http_plan` | Tipo de step usado para planejamento de API. |
| `lookup` | Busca conceitual em camada de integracao, sempre mockada no estado atual. |
| `adapter` | Fronteira tecnica que deve permanecer fake ate MVP especifico. |

## Relacoes

- Integracoes recebem sinais de cliente, campanha, evento e processamento.
- Integracoes produzem auditoria, mensagens, callbacks, estados ou evidencias.
- Integracoes devem ser classificadas por risco antes de qualquer adapter real futuro.

## Evidencias esperadas

- `api_contract`: plano seguro de contrato API.
- `kafka_trace`: lookup conceitual de mensagem.
- `audit_records`: rastros de chamada, decisao ou processamento.
- `expected_evidence_manifest`: lista de artefatos esperados.

## Usos futuros

- Playbooks devem apontar integracoes como camadas de investigacao, nao como alvos de execucao automatica.
- Evidence Planner deve mapear integracoes para camadas de evidencia e risco.
- Adapter Risk Classifier deve usar esta ontologia para separar `MOCK_ONLY`, `SAFE_READ`, `PROD_BLOCKED` e `DESTRUCTIVE_OPERATION`.

## Limites de seguranca

- Nao chamar APIs reais.
- Nao conectar Oracle real.
- Nao publicar ou consumir Kafka real.
- Nao executar Jenkins.
- Nao incluir hosts, IPs, tokens, cookies, bearer ou credenciais.
- `mode=real` permanece bloqueado.
