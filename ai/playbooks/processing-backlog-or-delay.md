# Processing Backlog Or Delay

## Sintoma

Processamento aparenta atraso, fila, backlog ou ausencia de checkpoint no tempo esperado.

## Quando usar

Use quando o evento foi planejado, mas a evidencia de processamento ou agendamento nao acompanha o prazo esperado.

## Entidades da ontologia relacionadas

- Processamento: NRT, scheduling, checkpoint, particionamento conceitual.
- Evento: `event_type`, `external_uid`, `subpartition_id`.
- Auditoria: rastros de processamento.
- Integracao: fila ou fronteira conceitual.
- Evidencia: `processing`, `audit`, `integration`.

## Hipoteses provaveis

- Prazo do cenario exige espera planejada.
- Evento nao entrou na camada de processamento.
- Subparticao ou fila conceitual esta atrasada.
- Auditoria de processamento nao foi planejada.
- Evidencia de agendamento esta ausente.

## Evidencias seguras

- `received_events`
- `audit_records`
- `kafka_trace`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual `deadline_rule` foi usado?
- Ha `schedule_checkpoint` esperado?
- O evento aparece como recebido no plano de evidencia?
- Existe correlacao para trace de integracao?
- O sintoma e atraso ou ausencia total de processamento?

## Proximos passos mock/read-only

- Conferir prazo e checkpoint planejado.
- Conferir `received_events` e `audit_records`.
- Conferir `kafka_trace` como rastro conceitual.
- Separar atraso esperado de lacuna de evidencia.
- Registrar necessidade de camada `processing` no futuro Evidence Planner.

## Sinais de risco

- Pedido para limpar fila real.
- Pedido para reprocessar registros.
- Pedido para consultar particionamento real.
- Ausencia de prazo ou correlacao planejada.

## Limites de seguranca

- Nao executar fila real.
- Nao reprocessar eventos.
- Nao consultar NRT real.
- Nao executar scripts ou jobs.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas `processing`, `integration`, `audit` e `schedule`, com distincao entre atraso esperado e evidencia ausente.
