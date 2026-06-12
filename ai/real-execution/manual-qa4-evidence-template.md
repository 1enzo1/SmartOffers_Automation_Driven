# Manual QA4 Evidence Template

Este template registra apenas evidencia sanitizada de uma futura tentativa manual QA4. Ele nao deve conter request bruto, resposta bruta ou material privado.

## Evidence

| Campo | Valor |
| --- | --- |
| `session_ref` | `<SESSION_REF_SANITIZED>` |
| `api_id` | `<APPROVED_API_ID>` |
| `method` | `<APPROVED_METHOD>` |
| `environment` | `<QA4>` |
| `decision` | `<BLOCKED_OR_MANUAL_REVIEW_READY_OR_SENT>` |
| `approval_reference` | `<APPROVAL_REF_MASKED>` |
| `ticket_reference` | `<TICKET_REF_MASKED>` |
| `correlation_reference` | `<CORRELATION_REF_MASKED>` |
| `risk_status` | `<RISK_STATUS>` |
| `readiness_decision` | `<READINESS_DECISION>` |
| `allowlist_decision` | `<ALLOWLIST_DECISION>` |
| `kill_switch_state` | `<KILL_SWITCH_STATE_SANITIZED>` |
| `status_code` | `<STATUS_CODE_OR_EMPTY>` |
| `elapsed_ms` | `<ELAPSED_MS_OR_EMPTY>` |
| `real_call_executed` | `<TRUE_OR_FALSE>` |
| `body_recorded` | `false` |
| `error` | `<SANITIZED_ERROR_OR_EMPTY>` |

## Invariantes

- `body_recorded` deve permanecer `false`;
- `real_call_executed` so pode ser `true` se o client manual retornou resposta sanitizada;
- bloqueio antes do client deve manter `real_call_executed=false`;
- erro deve ser registrado apenas como codigo ou classe sanitizada;
- evidencia nao deve conter request bruto, resposta bruta, endereco de rede, material de autenticacao, massa real, linha, conta ou documento.

## Anexos permitidos

- referencia de approval sanitizada;
- referencia de ticket sanitizada;
- resultado sanitizado dos gates;
- hash do commit aprovado.

