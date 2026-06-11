# Processing

## Objetivo

Definir processamento como caminho operacional que consome eventos, avalia regras, atualiza estados, agenda acoes e gera evidencias.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `processEvent` | Operacao planejada para eventos gerais. |
| `processMailing` | Operacao planejada para mailing. |
| `processRecharge` | Operacao planejada para recarga. |
| `schedule_checkpoint` | Evidencia planejada de agendamento. |
| `subpartition_id` | Referencia conceitual de particao para troubleshooting. |
| `last_record_processed` | Referencia conceitual para controle de processamento. |

## Relacoes

- Processamento consome evento e produz estado de campanha, metricas, auditoria e evidencias.
- Processamento pode depender de NRT, filas, particionamento e janela de prazo.
- Processamento agendado depende de `deadline_rule`.

## Evidencias esperadas

- `schedule_checkpoint`: quando houver prazo futuro.
- `received_events`: quando o historico de evento for relevante.
- `audit_records`: quando for necessario provar rastreabilidade.
- `resumo_analise.json`: consolidacao futura de sinais.

## Usos futuros

- Playbooks devem usar processamento para sintomas de evento nao processado, backlog NRT ou campanha travada.
- Evidence Planner deve sugerir camadas `processing` e `schedule` quando aplicavel.

## Limites de seguranca

- Nao executar fila real.
- Nao consultar NRT real.
- Nao disparar jobs.
- Nao alterar estado de processamento.
