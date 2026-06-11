# Event Not Processed

## Sintoma

Evento planejado nao apresenta rastro de processamento, auditoria ou efeito esperado na campanha.

## Quando usar

Use quando o cenario tem `event_type` definido, mas as evidencias de entrada, processamento ou estado esperado nao aparecem.

## Entidades da ontologia relacionadas

- Evento: `event_type`, `ext_event_id`, `operation`, `external_uid`.
- Cliente: `external_id`, `account`, `msisdn`.
- Processamento: scheduling, NRT, checkpoint.
- Auditoria: `audit_records`.
- Evidencia: `processing`, `audit`, `api_plan`, `manifest`.

## Hipoteses provaveis

- Evento nao foi planejado com a operacao correta.
- Tipo de cliente nao e compativel com o evento.
- Rastro de evento recebido nao foi incluido.
- Processamento depende de prazo futuro.
- Plano de API nao foi gerado para o `event_type`.

## Evidencias seguras

- `api_contract`
- `received_events`
- `audit_records`
- `kafka_trace`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual `event_type` foi planejado?
- A operacao esperada e `processEvent`, `processMailing` ou `processRecharge`?
- O evento depende de `deadline_rule` futuro?
- Ha `request_plan` ou `api_contract` esperado?
- Existe evidencia planejada de evento recebido?

## Proximos passos mock/read-only

- Conferir payload planejado e operacao.
- Conferir `api_contract` quando validacao de API existir.
- Conferir `received_events` e `audit_records` no manifesto.
- Conferir `schedule_checkpoint` quando o prazo nao for imediato.
- Registrar lacuna se o cenario nao pediu validacao de evento.

## Sinais de risco

- Pedido para republicar evento.
- Pedido para executar chamada real.
- Pedido para manipular fila ou particao real.
- Evento de recarga planejado para cliente nao pre-pago.

## Limites de seguranca

- Nao publicar evento real.
- Nao consumir fila real.
- Nao chamar API real.
- Nao alterar `request_plan` ou catalogo.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas `api_plan`, `processing`, `audit` e `integration`, com checkpoints para evento recebido e processamento esperado.
