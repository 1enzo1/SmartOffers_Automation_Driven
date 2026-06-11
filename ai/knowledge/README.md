# SmartOffers Knowledge

Esta pasta contem a ontologia SmartOffers do produto SmartOffers_Automation_Driven.

No MVP7.6.2, a ontologia e somente Markdown. Ela define vocabulario, relacoes e limites operacionais para orientar MVP7.6.3 Operational Playbooks e MVP7.6.4 Evidence Planner.

## Contratos

- [ontology.md](ontology.md): visao geral da ontologia e relacoes entre entidades.
- [customer.md](customer.md): cliente, identificadores, segmento e correlacao.
- [campaign.md](campaign.md): campanha, contrato, jornada, oferta e elegibilidade.
- [event.md](event.md): evento, operacao, tipos atuais, prazo e correlacao.
- [metric.md](metric.md): metricas de campanha e uso futuro em validacao.
- [characteristic.md](characteristic.md): atributos e caracteristicas de cliente/campanha.
- [audit.md](audit.md): auditoria funcional, HTTP/WS e rastreabilidade.
- [processing.md](processing.md): processamento, scheduling, NRT e checkpoints.
- [integration.md](integration.md): integracoes conceituais e limites de adapter.
- [evidence.md](evidence.md): camadas de evidencia e base para Evidence Planner.

## Regras de uso

- Tratar todos os nomes de tabelas, eventos e integracoes como referencia conceitual segura.
- Nao incluir hosts reais, IPs, secrets, credenciais, tokens, cookies, bearer, payloads reais ou dados brutos de ambiente.
- Nao executar consultas, chamadas de rede, jobs, scripts, Kafka, Oracle, APIs reais ou Jenkins.
- Nao criar Python funcional, schemas executaveis, fixtures, endpoints, automacoes ou JSONs de cenario.
- Manter compatibilidade com os contratos existentes de geracao, dry-run, adapter-run, exports e `request_plan`.

## Vocabulario operacional atual

A ontologia usa nomes ja presentes no produto:

- `customer_discovery`
- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `received_events`
- `sms_dispatch`
- `kafka_trace`
- `schedule_checkpoint`
- `expected_evidence_manifest`

## Relacao com proximos MVPs

MVP7.6.3 deve usar esta ontologia como fonte para playbooks operacionais.

MVP7.6.4 deve usar esta ontologia como base para camadas do Evidence Planner.

Nenhum desses usos deve habilitar execucao real por si so.
