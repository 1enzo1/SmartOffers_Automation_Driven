# Safety

Safety define guardrails e categorias de risco para o produto.

No MVP7.6.1, esta pasta e apenas contrato Markdown.

## Categorias previstas

- `SAFE_READ`
- `MOCK_ONLY`
- `HOMOLOG_CONTROLLED`
- `REAL_QA_OPT_IN`
- `PROD_BLOCKED`
- `DESTRUCTIVE_OPERATION`

## Regra central

O estado atual do produto e local-only/mock-only. Qualquer execucao real deve permanecer bloqueada ate MVP especifico com opt-in explicito, allowlist, testes, timeout, logs sanitizados e bloqueio de producao.
