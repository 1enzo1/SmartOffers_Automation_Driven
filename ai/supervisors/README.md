# Supervisors

Supervisores representam papeis de dominio do produto. Eles devem orientar interpretacao, planejamento, evidencias, troubleshooting e risco.

No MVP7.6.5, esta pasta detalha contratos conceituais de supervisores. Eles nao sao agentes autonomos, nao executam ferramentas e nao chamam LLM externo.

## Fontes documentais permitidas

- `ai/knowledge/`: ontologia SmartOffers.
- `ai/playbooks/`: playbooks operacionais.
- `ai/evidence/`: Evidence Planner Foundation.
- `docs/SUPERVISORS.md`: visao executiva historica.

## Supervisores

- [smartoffers-architect-supervisor.md](smartoffers-architect-supervisor.md): coordenacao conceitual entre supervisores.
- [campaign-supervisor.md](campaign-supervisor.md): interpretacao de campanhas, jornadas e atributos.
- [evidence-supervisor.md](evidence-supervisor.md): alinhamento com Evidence Planner e manifesto esperado.
- [troubleshooting-supervisor.md](troubleshooting-supervisor.md): triagem de sintomas e hipoteses seguras.
- [catalog-config-supervisor.md](catalog-config-supervisor.md): leitura conceitual de publicacao e configuracao.
- [adapter-supervisor.md](adapter-supervisor.md): classificacao de dry-run, adapter-run mockado, `http_plan`, bloqueio e futuro opt-in.
- [safety-supervisor.md](safety-supervisor.md): guardrails, risco e bloqueios obrigatorios.
- [supervisor-routing.md](supervisor-routing.md): regras conceituais de roteamento entre supervisores.

## Estrutura obrigatoria

Cada contrato de supervisor deve conter estas secoes, nesta ordem:

- `Objetivo`
- `Entradas esperadas`
- `Saidas esperadas`
- `Fontes documentais permitidas`
- `Responsabilidades`
- `Quando acionar outro supervisor`
- `Relacao com Evidence Planner`
- `Limites de seguranca`
- `O que nunca fazer automaticamente`

## Limites

Supervisores nao chamam Oracle, APIs, Kafka, Jenkins, rede ou subprocessos. Eles tambem nao habilitam `mode=real`.

Supervisores produzem orientacao, classificacao, perguntas, planos ou manifestos conceituais. Eles nao executam coleta, nao alteram catalogo, nao alteram cenarios, nao disparam mensagens e nao operam ambientes.
