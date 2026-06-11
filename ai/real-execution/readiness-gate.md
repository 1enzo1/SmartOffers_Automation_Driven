# Real Execution Readiness Gate

O readiness gate e uma camada deterministica para validar se uma intencao futura de execucao real esta pronta para revisao humana.

Ele nao chama rede, nao le ambiente real, nao cria client HTTP e nao altera adapter-run.

## Entrada conceitual

- `api_id`: identificador sanitizado da API candidata.
- `method`: metodo esperado pela policy.
- `environment`: ambiente pretendido.
- `requested_mode`: intencao conceitual, como `real`.
- `explicit_opt_in`: confirmacao explicita para avaliar readiness.
- `timeout_seconds`: timeout pretendido.
- `retry_count`: quantidade de retries.
- `risk_assessment`: resultado opcional de `classify_adapter_risk`.

## Policy conceitual

- `runtime_flags`: flags simuladas, incluindo `REAL_EXECUTION_ENABLED` e kill switch.
- `allowed_environments`: ambientes permitidos para revisao.
- `allowed_api_ids`: APIs candidatas permitidas para revisao.
- `allowed_methods_by_api_id`: metodo permitido por API.
- `timeout_limits`: limites de timeout.
- `required_retry_count`: retry esperado, por padrao `0`.
- `required_guardrails`: guardrails obrigatorios.

## Decisoes

- `blocked`: alguma pre-condicao falhou.
- `ready_for_manual_review`: todas as pre-condicoes simuladas passaram, mas nenhuma chamada real esta liberada.

## Bloqueios obrigatorios

- opt-in ausente ou incompleto;
- `REAL_EXECUTION_ENABLED` ausente ou falso no dict simulado;
- kill switch ativo;
- ambiente diferente de `QA4`;
- API fora da allowlist;
- metodo divergente;
- timeout ausente ou invalido;
- retry diferente de `0`;
- risco classificado como `blocked`;
- host, IP, token, secret, credential, payload real, MSISDN, account, bearer, cookie ou response body bruto;
- tentativa de fallback para execucao.

## Saida segura

O retorno deve conter listas ordenadas e sem duplicidade, log sanitizado e `ready_for_real_call=false`.

O `next_step` deve orientar revisao conceitual/read-only. Ele nunca deve sugerir executar adapter real, job real, API real, Kafka real ou Oracle real.
