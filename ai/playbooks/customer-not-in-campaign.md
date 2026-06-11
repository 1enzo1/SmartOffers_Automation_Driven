# Customer Not In Campaign

## Sintoma

Cliente esperado nao aparece vinculado a campanha ou nao apresenta contrato/estado compativel com o cenario planejado.

## Quando usar

Use quando o cenario indica elegibilidade, mas a evidencia esperada de campanha nao aparece no plano, export ou simulacao.

## Entidades da ontologia relacionadas

- Cliente: `external_id`, `customer_id`, `account`, `msisdn`, `customer_type`.
- Campanha: `campaign_id`, `id_contract`, `current_state`.
- Evento: `event_type`, `operation`.
- Evidencia: `customer`, `campaign`, `audit`, `manifest`.

## Hipoteses provaveis

- Cliente nao foi descoberto pela chave planejada.
- Campanha ou contrato esperado nao foi associado ao cliente.
- Evento planejado nao gerou o estado esperado.
- Caracteristicas ou metricas de elegibilidade nao batem com a regra da campanha.
- Prazo de avaliacao ainda depende de checkpoint futuro.

## Evidencias seguras

- `customer_discovery`
- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `received_events`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual `campaign_id` foi planejado?
- O `external_id` esperado esta presente no payload planejado?
- O tipo de cliente e compativel com o `event_type`?
- O prazo e `d0` ou exige `schedule_checkpoint`?
- Ha auditoria planejada para a jornada?

## Proximos passos mock/read-only

- Conferir o payload planejado e o resumo do cenario.
- Validar se `customer_discovery` existe no manifesto esperado.
- Validar se `campaign_contract` usa a mesma campanha planejada.
- Conferir `campaign_attributes` quando a regra depender de atributos.
- Conferir `audit_records` e `received_events` como rastros conceituais.

## Sinais de risco

- Pedido para consultar base real.
- Pedido para forcar entrada do cliente na campanha.
- Ausencia de identificador planejado para correlacao.
- Divergencia entre segmento do cliente e tipo de evento.

## Limites de seguranca

- Nao alterar contrato de campanha.
- Nao executar consulta real.
- Nao publicar evento.
- Nao executar adapter real.
- Nao usar dados reais de cliente.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas futuras `customer`, `campaign`, `audit` e `manifest`, com queries planejadas e resultado esperado sem execucao real.
