# Playbook Mapping

Este arquivo mapeia os playbooks operacionais do MVP7.6.3 para camadas conceituais de evidencia.

O mapeamento orienta o futuro Evidence Planner, mas nao executa coleta, consulta, chamada externa ou automacao.

## Mapa de playbooks

| Playbook | Camadas principais | Camadas de apoio |
| --- | --- | --- |
| `customer-not-in-campaign.md` | `customer_discovery`, `campaign_contract`, `campaign_attributes` | `audit_records`, `expected_evidence_manifest` |
| `sms-not-sent.md` | `sms_dispatch`, `campaign_contract`, `customer_discovery` | `audit_records`, `expected_evidence_manifest` |
| `event-not-processed.md` | `received_events`, `audit_records`, `schedule_checkpoint` | `kafka_trace`, `expected_evidence_manifest` |
| `callback-not-reflected.md` | `audit_records`, `received_events`, `campaign_contract` | `kafka_trace`, `expected_evidence_manifest` |
| `benefit-or-offer-not-updated.md` | `campaign_contract`, `campaign_attributes`, `audit_records` | `customer_discovery`, `expected_evidence_manifest` |
| `campaign-stuck-in-state.md` | `campaign_contract`, `campaign_attributes`, `schedule_checkpoint` | `audit_records`, `expected_evidence_manifest` |
| `processing-backlog-or-delay.md` | `schedule_checkpoint`, `received_events`, `kafka_trace` | `audit_records`, `expected_evidence_manifest` |
| `catalog-publication-config-issue.md` | `campaign_contract`, `campaign_attributes`, `audit_records` | `expected_evidence_manifest` |
| `evidence-mismatch.md` | `expected_evidence_manifest`, `audit_records`, `campaign_contract` | `customer_discovery`, `received_events`, `sms_dispatch`, `schedule_checkpoint` |

## Uso futuro pelo planner

O futuro Evidence Planner deve:

- iniciar pelo playbook escolhido ou sintoma detectado;
- selecionar camadas principais primeiro;
- adicionar camadas de apoio somente quando ajudarem a explicar a divergencia;
- classificar cada camada com status seguro;
- registrar bloqueios quando uma evidencia depender de sistema externo real;
- produzir um manifesto conceitual e sanitizado.

## Limites

Este mapeamento nao cria prioridade executavel, nao agenda coleta, nao consulta ambientes e nao altera comportamento do produto.
