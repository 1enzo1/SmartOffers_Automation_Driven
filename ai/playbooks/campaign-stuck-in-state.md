# Campaign Stuck In State

## Sintoma

Campanha ou contrato permanece em estado inesperado, sem avancar para o resultado planejado.

## Quando usar

Use quando as evidencias apontam que o cliente entrou na campanha, mas o estado nao acompanha a jornada esperada.

## Entidades da ontologia relacionadas

- Campanha: `current_state`, `id_contract`, jornada.
- Cliente: contrato e status.
- Evento: gatilho esperado.
- Processamento: checkpoint, prazo e atraso.
- Auditoria: rastros da transicao.

## Hipoteses provaveis

- Evento necessario nao foi processado conceitualmente.
- Prazo futuro ainda nao foi atingido.
- Caracteristica ou metrica bloqueou transicao.
- Auditoria de decisao nao foi planejada.
- Evidencias de campanha e processamento estao incompletas.

## Evidencias seguras

- `campaign_contract`
- `campaign_attributes`
- `received_events`
- `audit_records`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual estado era esperado?
- Qual evento deveria mover a campanha?
- Existe `schedule_checkpoint` para prazo futuro?
- A auditoria cobre a tentativa de transicao?
- O contrato aponta para a campanha correta?

## Proximos passos mock/read-only

- Conferir estado planejado no contrato de campanha.
- Conferir evento recebido e auditoria.
- Conferir atributos e metricas associadas.
- Conferir checkpoint de agendamento quando houver prazo.
- Registrar estado divergente como entrada para Evidence Planner.

## Sinais de risco

- Pedido para forcar estado.
- Pedido para executar transicao real.
- Falta de evento ou prazo claro.
- Estado esperado nao documentado no cenario.

## Limites de seguranca

- Nao alterar estado real.
- Nao executar job ou reprocessamento.
- Nao manipular contrato.
- Nao habilitar execucao real.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas `campaign`, `processing`, `audit` e `schedule`, com estado esperado e evidencias minimas.
