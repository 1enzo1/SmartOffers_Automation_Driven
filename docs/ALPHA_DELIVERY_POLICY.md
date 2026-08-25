# Alpha Delivery Policy

## Missao

Alpha entrega o laboratorio seguro SmartOffers/ACM: local-first, mock-first,
deterministico e sem transporte real. Execucao real continua bloqueada.

## Definition of Done

Uma entrega somente fecha quando o menor vertical slice autorizado esta
implementado, documentado, testado, revisado por uma pessoa independente e
com evidencia sanitizada; o estado Git e os guardrails permanecem coerentes.

## Politica de entrega

- Preferir o menor vertical slice que prove o contrato, sem expandir escopo.
- Exigir uma unica revisao independente antes do fechamento.
- Usar testes direcionados durante o ciclo e a suite completa antes do marco
  final ou quando houver risco de regressao transversal.
- Classificar bloqueios exatamente como `BLOCKS_ALPHA`, `BLOCKS_FEATURE`,
  `EXTERNAL_DEFERRED` ou `NON_BLOCKING`.
- O progresso executavel oficial usa os pesos A-I: 10/15/20/10/10/10/15/5/5
  por cento, respectivamente.

## Eficiencia e modos

`WORK_MODE=NORMAL` e `WORK_MODE=ECONOMY` seguem `.codex/config.toml` e o
Execution Manager; o modo Economy reduz custo e paralelismo sem relaxar
guardrails, revisao independente, testes ou bloqueio de execucao real.

