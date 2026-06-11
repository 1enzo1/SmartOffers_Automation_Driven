# Metric

## Objetivo

Definir metrica como dado calculado, observado ou esperado para validar comportamento de campanha.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `metric_name` | Nome funcional da metrica. |
| `metric_value` | Valor esperado ou observado de forma conceitual. |
| `customer_id` | Cliente associado a metrica. |
| `campaign_id` | Campanha associada a metrica. |
| `calculation_window` | Janela de avaliacao, quando aplicavel. |

## Relacoes

- Metrica pode depender de evento, campanha, caracteristicas e processamento.
- Metrica pode explicar elegibilidade, beneficio, bloqueio ou ausencia de comunicacao.
- Metrica se conecta a evidencias de auditoria e contrato.

## Evidencias esperadas

- Consulta conceitual de metricas por cliente/campanha.
- Comparacao entre metrica esperada e regra de campanha.
- Referencia em `resumo_analise.json` quando evidencias forem consolidadas.

## Usos futuros

- Playbooks devem usar metricas para diagnosticar beneficio nao atualizado, elegibilidade ausente ou campanha travada.
- Evidence Planner deve criar camada `metrics` quando o cenario exigir prova quantitativa.

## Limites de seguranca

- Nao consultar base real de metricas.
- Nao incluir valores reais de cliente.
- Nao inferir decisao de negocio sem evidencia planejada.
