# Skills

Skills sao capacidades reutilizaveis do produto para analise de dominio, planejamento de evidencias, troubleshooting e classificacao de risco.

No MVP7.6.1, esta pasta e apenas contrato Markdown.

## Skills previstas

- `campaign-analysis`
- `evidence-planning`
- `troubleshooting`
- `sql-evidence`
- `api-contract-analysis`
- `request-plan-analysis`
- `adapter-execution-planning`
- `catalog-config-analysis`
- `kafka-nrt-analysis`
- `bko-analysis`
- `risk-classification`

## Relacao com supervisores

No MVP7.6.5, supervisores podem referenciar estas skills como capacidades futuras, mas nenhuma skill e implementada ou executada.

- `smartoffers-architect-supervisor` pode orientar combinacao de skills futuras.
- `campaign-supervisor` pode depender de `campaign-analysis`.
- `evidence-supervisor` pode depender de `evidence-planning` e `sql-evidence`.
- `troubleshooting-supervisor` pode depender de `troubleshooting`.
- `catalog-config-supervisor` pode depender de `catalog-config-analysis`.
- `adapter-supervisor` pode depender de `api-contract-analysis`, `request-plan-analysis` e `adapter-execution-planning`.
- `safety-supervisor` pode depender de `risk-classification`.

Estas relacoes sao conceituais e nao criam agentes, chamadas externas, automacoes ou codigo funcional.

## Limites

Skills nao executam consultas reais, nao publicam eventos, nao disparam jobs, nao alteram catalogo e nao fazem chamadas de rede.
