# Customer

## Objetivo

Definir como o produto entende cliente no contexto SmartOffers/ACM.

Cliente e a entidade analisada em cenarios de campanha, eventos, metricas, auditoria, processamento e evidencia.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `external_id` | Identificador externo usado para correlacao segura entre payload, eventos e descoberta de cliente. |
| `customer_id` | Identificador interno conceitual retornado por descoberta ou consulta planejada. |
| `account` | Conta ou linha associada ao cliente. |
| `msisdn` | Linha telefonica usada em eventos, SMS e correlacao. |
| `customer_type` | Segmento atual: `pre`, `pos` ou `controle`. |
| `document_type` | Tipo documental planejado: `PF` ou `PJ`. |
| `customer_status` | Estado operacional planejado para o cliente. |

## Relacoes

- Cliente se relaciona com campanha por contrato e elegibilidade.
- Cliente se relaciona com evento por `external_id`, `msisdn`, `account` e tipo de segmento.
- Cliente se relaciona com evidencias por `customer_discovery`, `campaign_contract`, SMS e auditoria.
- Cliente pre-pago e obrigatorio para cenario de `recarga` no gerador atual.

## Evidencias esperadas

- `customer_discovery`: localizar o cliente por `external_id`.
- `campaign_contract`: confirmar vinculo do cliente com a campanha.
- `sms_dispatch`: conferir tentativa conceitual de comunicacao.
- `received_events`: conferir historico conceitual de eventos recebidos.

## Usos futuros

- Playbooks devem usar cliente como ponto inicial para sintomas como "cliente nao entrou na campanha" ou "SMS nao saiu".
- Evidence Planner deve criar camadas de evidencia de descoberta, contrato, status e comunicacao.

## Limites de seguranca

- Nao registrar `msisdn`, account ou documento real.
- Nao consultar Oracle real.
- Nao usar dados pessoais reais em exemplos.
- Usar placeholders como `{{msisdn}}`, `{{account}}` e `{{external_id}}`.
