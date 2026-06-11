# Evidence

## Objetivo

Definir evidencia como artefato esperado para demonstrar que um cenario foi planejado, simulado, validado ou diagnosticado de forma segura.

## Camadas de evidencia

| Camada | Uso conceitual |
| --- | --- |
| `payload` | Payload planejado, sem dados reais. |
| `api_plan` | `request_plan` ou contrato HTTP mockado. |
| `customer` | Descoberta e identificadores conceituais do cliente. |
| `campaign` | Contrato, estado e atributos de campanha. |
| `audit` | Rastreabilidade funcional, HTTP ou WS. |
| `processing` | Evento recebido, scheduling, NRT ou checkpoint. |
| `communication` | SMS ou mensagem planejada. |
| `integration` | Kafka, SmartGateway, BKO ou Jenkins como fronteira conceitual. |
| `manifest` | Lista final de artefatos esperados. |

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `evidence_file` | Arquivo esperado no planejamento ou exportacao. |
| `evidence_layer` | Agrupamento conceitual de provas por dominio. |
| `query_template` | Consulta planejada para MVP futuro, sem execucao real. |
| `expected_result` | Resultado esperado para validar a evidencia. |
| `manifest` | Lista consolidada de evidencias esperadas. |

## Arquivos atuais esperados

- `01_payload_request.json`
- `02_api_response.json`
- `03_execution_summary.json`
- `04_database_validation.json`
- `05_campaign_attributes.json`
- `06_audit_records.json`
- `07_kafka_trace.json`
- `08_sms_dispatch.json`
- `09_received_events.json`
- `10_api_contract_validation.json`
- `11_schedule_checkpoint.json`
- `12_expected_evidence_manifest.json`
- `resumo_analise.json`

## Relacoes

- Evidencia conecta todas as entidades da ontologia.
- Evidencia deve preservar o que foi planejado e simulado, nao executar sistemas reais.
- Evidencia deve ser suficiente para orientar playbooks e Evidence Planner.

## Usos futuros

- MVP7.6.3 deve usar evidencias para definir passos seguros de troubleshooting.
- MVP7.6.4 deve usar este contrato para gerar `evidence_plan` deterministico.
- MVP7.6.7 deve usar camadas de evidencia como entrada de classificacao de risco.

## Limites de seguranca

- Evidencia nao deve conter dados reais sensiveis.
- Evidencia nao deve ser obtida por chamada externa automatica.
- Evidencia nao deve habilitar mutacao, publicacao, job ou execucao real.
