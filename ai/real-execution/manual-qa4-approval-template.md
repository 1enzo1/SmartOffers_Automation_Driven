# Manual QA4 Approval Template

Este template registra aprovacao sanitizada para revisao humana. Ele nao deve conter dado pessoal, endpoint, material de autenticacao, massa real ou corpo bruto.

## Approval

| Campo | Valor |
| --- | --- |
| `approved` | `<TRUE_OR_FALSE>` |
| `risk_acceptance` | `<TRUE_OR_FALSE>` |
| `approver_ref` | `<APPROVER_REF_SANITIZED>` |
| `ticket_ref` | `<TICKET_REF_SANITIZED>` |
| `approved_api_id` | `<APPROVED_API_ID>` |
| `approved_environment` | `<QA4>` |
| `approved_at_ref` | `<APPROVED_AT_REF_SANITIZED>` |
| `scope_ref` | `<MANUAL_QA4_SCOPE_REF>` |
| `single_call_only` | `<TRUE_OR_FALSE>` |
| `retry_policy` | `<ZERO_RETRY>` |
| `evidence_policy` | `<SANITIZED_ONLY>` |

## Validacao

- [ ] Approval concedido para uma unica tentativa manual.
- [ ] Ambiente aprovado e QA4.
- [ ] API aprovada corresponde a allowlist.
- [ ] Retry automatico nao autorizado.
- [ ] Evidencia permitida e apenas sanitizada.
- [ ] Kill switch deve ser conferido antes do client manual.
- [ ] Dados brutos permanecem fora do repositorio e fora do retorno.

## Resultado da revisao

| Campo | Valor |
| --- | --- |
| `approval_decision` | `<APPROVED_OR_BLOCKED>` |
| `blocked_reason` | `<SANITIZED_REASON_OR_EMPTY>` |

