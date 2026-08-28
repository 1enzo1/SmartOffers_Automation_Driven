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
## Operation-scoped Alpha transport contract

`REAL_TRANSPORT_ALLOWED=false` is the canonical default. A future separately
initiated send is eligible only for the exact QA4
`CREATE_OFFERS_CUSTOMER_SYNTHETIC_QA4` / `CREATE_OFFERS_CUSTOMER` tuple with
`ONE_QA4_OFFERS_CUSTOMER_CREATE_NO_AUTH_UI_RUN`, matching application
confirmation, production false, global no-auth false, operation-scoped no-auth
true, derived QA4 API URL destination attestation `MATCH` against an independent
approved destination fingerprint, allowlist match, one shared attempt
remaining, retry zero, and fallback false. The scoped
attestation is limited to this operation/scenario/API tuple and records only
source=`derived_qa4_api_url`, environment, operation/scenario/API identity, and
match booleans—never a destination value or fingerprint. The generic API
health path/hash checkpoint remains independently fail-closed for legacy health
readiness.
