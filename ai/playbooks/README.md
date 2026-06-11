# Operational Playbooks

Playbooks descrevem roteiros operacionais seguros para troubleshooting e validacao SmartOffers.

No MVP7.6.3, esta pasta continua somente Markdown. Os playbooks usam a ontologia em `ai/knowledge/` como fonte principal e preparam base para o MVP7.6.4 Evidence Planner.

## Playbooks

- [customer-not-in-campaign.md](customer-not-in-campaign.md): cliente nao entrou na campanha.
- [sms-not-sent.md](sms-not-sent.md): SMS ou mensagem nao enviado.
- [event-not-processed.md](event-not-processed.md): evento nao processado.
- [callback-not-reflected.md](callback-not-reflected.md): callback nao refletiu.
- [benefit-or-offer-not-updated.md](benefit-or-offer-not-updated.md): beneficio ou oferta nao atualizou.
- [campaign-stuck-in-state.md](campaign-stuck-in-state.md): campanha travada em estado.
- [processing-backlog-or-delay.md](processing-backlog-or-delay.md): backlog ou atraso de processamento.
- [catalog-publication-config-issue.md](catalog-publication-config-issue.md): problema de publicacao ou configuracao.
- [evidence-mismatch.md](evidence-mismatch.md): divergencia entre esperado e evidencia.

## Estrutura obrigatoria

Cada playbook deve conter exatamente estas secoes, nesta ordem:

- `Sintoma`
- `Quando usar`
- `Entidades da ontologia relacionadas`
- `Hipoteses provaveis`
- `Evidencias seguras`
- `Perguntas de triagem`
- `Proximos passos mock/read-only`
- `Sinais de risco`
- `Limites de seguranca`
- `Relacao futura com Evidence Planner`

## Regras de seguranca

- Usar somente Markdown/ASCII.
- Tratar todos os passos como mock/read-only.
- Nao chamar Oracle, APIs, Kafka, Jenkins, rede ou subprocessos.
- Nao habilitar `mode=real`.
- Nao criar codigo funcional, schemas executaveis, fixtures, endpoints, automacoes ou JSONs de cenario.
- Nao usar dados reais ou dados sensiveis de ambiente.

## Vocabulario compartilhado

Os playbooks devem referenciar evidencias seguras existentes na ontologia:

- `customer_discovery`
- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `received_events`
- `sms_dispatch`
- `kafka_trace`
- `schedule_checkpoint`
- `expected_evidence_manifest`
