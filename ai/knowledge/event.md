# Event

## Objetivo

Definir evento como sinal de entrada que aciona avaliacao, processamento, mudanca de estado ou validacao no fluxo SmartOffers.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `event_type` | Tipo funcional do evento no gerador. |
| `event_id` | Identificador conceitual do evento processado. |
| `ext_event_id` | Identificador externo planejado no payload. |
| `external_uid` | Chave de correlacao externa quando existir. |
| `consumer_id` | Consumidor ou origem conceitual do evento. |
| `subpartition_id` | Particao/subparticao conceitual para troubleshooting NRT. |
| `operation` | Operacao planejada: `processEvent`, `processMailing` ou `processRecharge`. |

## Tipos atuais

- `habilitacao`
- `alteracao_perfil`
- `mailing`
- `recarga`
- `rehab`
- `upsell`
- `downgrade`

## Relacoes

- Evento usa cliente e campanha para decidir elegibilidade.
- Evento pode produzir auditoria, metricas, SMS, callback, estado de campanha ou agendamento.
- Evento `recarga` exige cliente `pre` no gerador atual.
- Evento sem `api_id` pode mapear para `request_plan` mockado por `event_type`.

## Evidencias esperadas

- `api_contract`: contrato planejado de API.
- `received_events`: historico conceitual de eventos.
- `audit_records`: rastros da decisao.
- `kafka_trace`: correlacao conceitual de mensagem.
- `schedule_checkpoint`: quando houver prazo futuro.

## Usos futuros

- Playbooks devem partir de sintomas como "evento nao processou" ou "callback nao refletiu".
- Evidence Planner deve vincular tipo de evento a camadas de API, auditoria, processamento e integracao.

## Limites de seguranca

- Nao publicar eventos reais.
- Nao consumir Kafka real.
- Nao chamar SmartOffers API real.
- Nao registrar payload real.
