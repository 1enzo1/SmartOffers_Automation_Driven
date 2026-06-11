# SMS Not Sent

## Sintoma

SMS ou mensagem esperada nao aparece como evidencia planejada ou nao acompanha o fluxo de campanha.

## Quando usar

Use quando a campanha deveria comunicar o cliente, mas a evidencia `sms_dispatch` nao aparece ou nao explica a comunicacao esperada.

## Entidades da ontologia relacionadas

- Cliente: `msisdn`, `customer_type`, `customer_status`.
- Campanha: `campaign_id`, jornada e elegibilidade.
- Evento: `event_type`, `operation`.
- Integracao: fronteira de comunicacao conceitual.
- Evidencia: `communication`, `audit`, `manifest`.

## Hipoteses provaveis

- Cenario foi gerado sem validacao de SMS.
- Cliente nao entrou na campanha antes da etapa de comunicacao.
- Evento nao produziu estado que dispara mensagem.
- Atributo ou metrica de elegibilidade bloqueou comunicacao.
- Evidencia de auditoria nao foi planejada para a etapa.

## Evidencias seguras

- `sms_dispatch`
- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `received_events`
- `expected_evidence_manifest`

## Perguntas de triagem

- A validacao `sms` foi selecionada?
- O cliente possui `msisdn` planejado como placeholder?
- A campanha exige mensagem para este tipo de evento?
- O cliente entrou na campanha antes da comunicacao?
- Ha auditoria planejada para confirmar a tentativa de comunicacao?

## Proximos passos mock/read-only

- Conferir se `sms_dispatch` esta no manifesto.
- Conferir contrato de campanha e atributos esperados.
- Conferir se o evento planejado e elegivel para comunicacao.
- Conferir auditoria conceitual antes de assumir falha de envio.
- Registrar lacuna de evidencia se SMS nao foi solicitado no cenario.

## Sinais de risco

- Pedido para reenviar SMS.
- Pedido para acionar gateway real.
- Pedido para usar numero real.
- Falta de consentimento ou contexto de comunicacao.

## Limites de seguranca

- Nao enviar mensagem real.
- Nao acionar gateway real.
- Nao usar linha real.
- Nao alterar campanha para forcar comunicacao.

## Relacao futura com Evidence Planner

Este playbook deve gerar camada `communication`, ligada a `customer`, `campaign` e `audit`, com evidencia esperada de tentativa de mensagem.
