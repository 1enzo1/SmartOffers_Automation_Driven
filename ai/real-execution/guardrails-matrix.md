# Real Execution Guardrails Matrix

Esta matriz resume os guardrails do caminho manual de execucao real.

| Guardrail | Camada | Falha esperada |
| --- | --- | --- |
| Client manual isolado | `real_http_client.py` | Bloquear client nao manual |
| Pacote nao exporta client real | `__init__.py` | Import automatico indisponivel |
| Pacote nao exporta execucao manual | `__init__.py` | Uso automatico indisponivel |
| Runtime separado | `runtime.py` | Bloquear runtime incompleto |
| Approval obrigatorio | `executor.py` | Bloquear antes do client |
| Kill switch | `readiness.py` | Bloquear antes do client |
| Allowlist unica | `allowlist.py` | Bloquear API divergente |
| Timeout curto | `allowlist.py` | Bloquear divergencia |
| Retry zero | `allowlist.py` | Bloquear retry |
| Risk sanitizado | `executor.py` | Bloquear risco `blocked` |
| Readiness sanitizado | `readiness.py` | Bloquear se nao pronto |
| Evidencia sanitizada | `executor.py` | Nao registrar dado bruto |
| Adapter-run bloqueado | `core/execution/` | `mode=real` rejeitado |

## Regra de precedencia

Qualquer falha de guardrail bloqueia antes do client. A execucao manual so pode avancar quando todas as validacoes passam.

## Regra de teste

Testes automatizados usam dummy/fake client. Eles nao podem importar nem instanciar o client manual real.
