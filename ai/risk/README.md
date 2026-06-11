# Adapter Risk Classifier

Esta pasta define os contratos conceituais do MVP7.6.7 para classificacao deterministica de risco antes de qualquer adapter-run real futuro.

O classificador e local, read-only e mock-first. Ele nao executa adapter, nao chama rede, nao altera catalogo e nao libera `mode=real`.

## Contratos

- [adapter-risk-classifier-contract.md](adapter-risk-classifier-contract.md): formato conceitual de entrada e saida.
- [risk-rules.md](risk-rules.md): regras deterministicas de risco e precedencia.

## Fontes permitidas

- `core/intelligence/analyze_scenario`: resultado conceitual opcional, sem dependencia obrigatoria.
- `ai/evidence/`: status e camadas de evidencia.
- `ai/supervisors/adapter-supervisor.md`: responsabilidades de adapter.
- `ai/supervisors/safety-supervisor.md`: guardrails e bloqueios.
- Catalogo seguro atual, apenas como entrada sanitizada.

## Limites

- Nao habilita execucao real.
- Nao cria endpoint.
- Nao altera dry-run, adapter-run, catalogo seguro ou `request_plan`.
- Nao chama Oracle, APIs, Kafka, Jenkins, rede, subprocessos ou LLM.
- Nao inicia MVP7.7.
