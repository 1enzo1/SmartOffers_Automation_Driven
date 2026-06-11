# Scenario Intelligence Routing Rules

Este arquivo documenta as regras deterministicas do MVP7.6.6.

As regras sao locais, read-only e seguras. Elas nao substituem testes nem executam integracoes.

## Evento

Derivar `event_type` de `scenario.source_answers.event_type`. Se ausente, usar `scenario.payload.eventType`.

## Camadas de evidencia

Ler `scenario.queries[*].name` e preservar apenas camadas conhecidas:

- `customer_discovery`
- `campaign_contract`
- `campaign_attributes`
- `received_events`
- `audit_records`
- `sms_dispatch`
- `kafka_trace`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Playbooks sugeridos

- `recarga` com `sms_dispatch`: `sms-not-sent.md`
- `mailing`: `customer-not-in-campaign.md`
- `upsell` ou `downgrade`: `benefit-or-offer-not-updated.md`
- `rehab` ou `alteracao_perfil`: `campaign-stuck-in-state.md`
- `kafka_trace`: `callback-not-reflected.md`
- `schedule_checkpoint`: `processing-backlog-or-delay.md`
- manifesto de evidencia presente: `evidence-mismatch.md`

## Supervisores sugeridos

- Sempre incluir `smartoffers-architect-supervisor` e `safety-supervisor`.
- Incluir `campaign-supervisor` para campanha, oferta ou atributos.
- Incluir `evidence-supervisor` quando houver camadas de evidencia.
- Incluir `troubleshooting-supervisor` quando houver playbook sugerido.
- Incluir `adapter-supervisor` para `http_plan`, `api_contract`, `request_plan` ou `kafka_trace`.
- Incluir `catalog-config-supervisor` para `campaign_contract` ou `campaign_attributes`.

## Status geral

Precedencia obrigatoria:

```txt
blocked > future-controlled > read-only > mock
```

- `blocked`: indicador de `mode=real`, host/IP/secret/token/credential/payload real ou risco externo.
- `future-controlled`: sinal futuro explicito ou `kafka_trace`, sem desbloquear execucao.
- `read-only`: evidencias conceituais/query-like sem risco bloqueante.
- `mock`: padrao quando nao houver evidencia ou risco.

## Riscos

- `blocked_real_execution_signal`: usado quando o scenario contem indicio de execucao real, dado sensivel ou dependencia externa.
- `future_controlled_signal`: usado quando o scenario referencia controle futuro sem habilitar execucao.
- `future_controlled_kafka_trace`: usado quando `kafka_trace` aparece como evidencia conceitual dependente de guardrails futuros.
