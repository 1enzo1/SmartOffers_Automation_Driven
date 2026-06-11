# Benefit Or Offer Not Updated

## Sintoma

Beneficio, oferta ou estado comercial esperado nao foi atualizado de acordo com a campanha planejada.

## Quando usar

Use quando o cenario espera transicao de oferta, bonus ou atualizacao de beneficio, mas as evidencias nao confirmam a mudanca.

## Entidades da ontologia relacionadas

- Campanha: `initial_offer`, `target_offer`, `campaign_id`.
- Cliente: segmento, status e contrato.
- Caracteristica: atributos de campanha e payload.
- Metrica: valores que explicam elegibilidade.
- Evidencia: `campaign`, `metric`, `audit`, `manifest`.

## Hipoteses provaveis

- Cliente nao era elegivel para a oferta alvo.
- Caracteristica obrigatoria nao foi planejada ou validada.
- Metrica esperada nao foi considerada.
- Evento gerou estado diferente do esperado.
- Auditoria nao foi planejada para explicar a decisao.

## Evidencias seguras

- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `customer_discovery`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual era a oferta inicial e a oferta alvo?
- A campanha exige atributo ou metrica especifica?
- O evento esperado foi processado conceitualmente?
- A evidencia de contrato confirma a campanha correta?
- O manifesto inclui auditoria da decisao?

## Proximos passos mock/read-only

- Conferir `campaign_contract` e transicao de oferta planejada.
- Conferir `campaign_attributes` para regras especificas.
- Conferir `audit_records` para decisao esperada.
- Conferir se a ontologia de metricas aponta evidencia ausente.
- Registrar divergencia se o cenario nao incluiu camada necessaria.

## Sinais de risco

- Pedido para ajustar oferta real.
- Pedido para aplicar beneficio manualmente.
- Falta de evidencia de elegibilidade.
- Divergencia entre objetivo e regras da campanha.

## Limites de seguranca

- Nao alterar oferta real.
- Nao aplicar beneficio.
- Nao executar mutacao em catalogo ou cliente.
- Nao chamar API real.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas `campaign`, `characteristic`, `metric` e `audit`, com expected_result para oferta ou beneficio.
