# Campaign

## Objetivo

Definir campanha como unidade de negocio que orienta regras, jornada, oferta, elegibilidade e evidencias SmartOffers.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `campaign_id` | Identificador planejado da campanha no cenario. |
| `campaign_name` | Nome funcional da campanha. |
| `id_contract` | Contrato conceitual que liga cliente e campanha. |
| `current_state` | Estado operacional esperado na jornada. |
| `initial_offer` | Oferta antes do evento ou avaliacao. |
| `target_offer` | Oferta esperada depois da regra. |
| `deadline_rule` | Prazo de validacao: `d0`, `d1`, `d3`, `d5`, `d7` ou `future`. |

## Relacoes

- Campanha pertence a uma jornada de evento.
- Campanha usa caracteristicas e metricas para elegibilidade.
- Campanha produz contrato ou estado observavel para evidencia.
- Campanha pode depender de catalogo/configuracao, mas o MVP7.6.2 nao executa loader, rollback ou publicacao.

## Evidencias esperadas

- `campaign_contract`: confirma vinculo entre cliente e campanha.
- `campaign_attributes`: confirma atributos planejados da campanha.
- `audit_records`: confirma rastreabilidade da jornada.
- `schedule_checkpoint`: confirma agendamento quando `deadline_rule` for futuro.

## Usos futuros

- Playbooks devem usar campanha para sintomas de elegibilidade, estado travado e beneficio nao atualizado.
- Evidence Planner deve sugerir camadas de contrato, caracteristicas, metricas e auditoria.

## Limites de seguranca

- Nao alterar catalogo real.
- Nao executar rollback ou publicacao.
- Nao usar IDs reais sensiveis.
- Nao chamar APIs reais para ativar campanha.
