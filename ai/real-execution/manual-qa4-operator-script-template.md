# Manual QA4 Operator Script Template

Este template e um roteiro humano, nao um script executavel. Preencha somente placeholders sanitizados em artefato local nao versionado.

## Identificacao da sessao

| Campo | Placeholder |
| --- | --- |
| `session_ref` | `<SESSION_REF_SANITIZED>` |
| `branch_ref` | `<BRANCH_REF>` |
| `commit_ref` | `<COMMIT_REF>` |
| `operator_ref` | `<OPERATOR_REF_SANITIZED>` |
| `ticket_ref` | `<TICKET_REF_SANITIZED>` |
| `approval_ref` | `<APPROVAL_REF_SANITIZED>` |
| `environment_ref` | `<QA4_ENVIRONMENT_REF>` |
| `api_id` | `<APPROVED_API_ID>` |

## Pre-checks

- [ ] Branch e commit conferidos.
- [ ] Suite automatizada conferida.
- [ ] `adapter-run mode=real` conferido como bloqueado.
- [ ] Approval sanitizado conferido.
- [ ] Allowlist da API candidata conferida.
- [ ] Kill switch conferido antes do client manual.
- [ ] Runtime privado preparado fora do repositorio.
- [ ] Nenhum dado bruto copiado para docs, testes, logs ou evidencia.

## Gates

| Gate | Entrada permitida | Resultado esperado |
| --- | --- | --- |
| Risk classifier | `<SANITIZED_WORK_ITEM>` | `<RISK_STATUS>` |
| Readiness gate | `<SANITIZED_REQUEST_AND_POLICY>` | `<READINESS_DECISION>` |
| Allowlist | `<APPROVED_API_ID_AND_METHOD>` | `<ALLOWLIST_DECISION>` |
| Runtime refs | `<SANITIZED_RUNTIME_REFS>` | `<RUNTIME_REFS_DECISION>` |
| Runtime privado | `<IN_MEMORY_PRIVATE_RUNTIME_PRESENT>` | `<PRIVATE_RUNTIME_DECISION>` |
| Approval | `<SANITIZED_APPROVAL>` | `<APPROVAL_DECISION>` |

## Abortos

Abortar se qualquer item abaixo ocorrer:

- gate retorna `blocked`;
- readiness diferente de `ready_for_manual_review`;
- risk classifier retorna `blocked`;
- allowlist diverge;
- approval ausente ou divergente;
- kill switch ativo;
- timeout diferente do permitido;
- retry diferente de zero;
- tentativa de registrar dado bruto;
- tentativa de usar caminho automatico.

## Registro final

Preencher apenas `manual-qa4-evidence-template.md` com valores sanitizados. O corpo de resposta bruto nunca deve ser registrado.

