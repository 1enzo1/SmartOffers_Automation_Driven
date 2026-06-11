# Callback Not Reflected

## Sintoma

Callback ou reflexo esperado de integracao nao aparece nas evidencias planejadas ou nao se conecta ao evento original.

## Quando usar

Use quando a jornada espera retorno de integracao, mensagem ou callback, mas a evidencia conceitual nao fecha a correlacao.

## Entidades da ontologia relacionadas

- Evento: `external_uid`, `event_type`, `operation`.
- Integracao: Kafka, SmartGateway, BKO ou fronteira externa conceitual.
- Auditoria: rastros funcionais e de integracao.
- Processamento: estado e atraso.
- Evidencia: `integration`, `audit`, `processing`, `manifest`.

## Hipoteses provaveis

- Correlacao do evento nao foi planejada.
- Evento ainda nao chegou na camada de processamento.
- Trace de integracao nao foi incluido no manifesto.
- Auditoria planejada nao cobre o callback.
- Existe atraso conceitual entre evento e reflexo.

## Evidencias seguras

- `kafka_trace`
- `audit_records`
- `received_events`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual callback ou reflexo era esperado?
- Existe chave de correlacao planejada?
- O evento original tem evidencia `received_events`?
- O callback depende de processamento assincrono?
- O manifesto inclui camada de integracao?

## Proximos passos mock/read-only

- Conferir correlacao entre evento planejado e evidencia de integracao.
- Conferir `kafka_trace` quando aplicavel.
- Conferir `audit_records` para rastrear tentativa ou ausencia.
- Conferir `schedule_checkpoint` se houver prazo futuro.
- Documentar lacuna se a integracao nao foi parte do cenario.

## Sinais de risco

- Pedido para publicar ou consumir mensagem real.
- Pedido para reprocessar callback.
- Ausencia de chave de correlacao planejada.
- Evidencia conflita com estado esperado da campanha.

## Limites de seguranca

- Nao publicar callback real.
- Nao consumir Kafka real.
- Nao executar reprocessamento.
- Nao alterar estado externo.

## Relacao futura com Evidence Planner

Este playbook deve gerar camada `integration`, conectada a `event`, `processing` e `audit`, com correlacao planejada e resultado esperado.
