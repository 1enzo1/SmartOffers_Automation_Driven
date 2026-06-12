# Manual Execution Checklist

Este checklist deve ser usado apenas por operador humano em uma etapa futura aprovada. Ele nao autoriza chamada real neste commit.

## Antes de considerar execucao manual

- confirmar branch e commit aprovados;
- confirmar `adapter-run mode=real` bloqueado;
- confirmar suite automatizada passando;
- confirmar allowlist com uma unica API candidata;
- confirmar kill switch inativo somente para a sessao manual;
- confirmar approval sanitizado;
- confirmar runtime em memoria fora do repositorio;
- confirmar evidencia sanitizada.

## Ordem obrigatoria

1. Preparar `runtime_refs` sanitizado.
2. Preparar `runtime_secrets` somente em memoria.
3. Validar approval sanitizado.
4. Validar allowlist.
5. Executar risk classifier com work item sanitizado.
6. Executar readiness gate com request/policy sanitizados.
7. Validar timeout curto.
8. Validar retry zero.
9. Validar kill switch.
10. Chamar client manual apenas se todos os gates passarem.
11. Registrar somente evidencia sanitizada.

## Abortos obrigatorios

- qualquer campo obrigatorio ausente;
- approval divergente;
- allowlist invalida;
- risk classifier `blocked`;
- readiness diferente de `ready_for_manual_review`;
- timeout divergente;
- retry diferente de zero;
- client nao manual;
- tentativa de registrar dado bruto.

## Evidencia minima

- API;
- metodo;
- ambiente;
- decisao;
- referencias mascaradas;
- status code;
- duracao;
- `real_call_executed`;
- `body_recorded=false`;
- erro sanitizado, se houver.
