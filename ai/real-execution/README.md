# Real Execution Readiness

Esta area documenta o MVP7.7.0 - Real Execution Readiness Gate.

O objetivo e preparar a primeira revisao controlada para execucao real futura em QA4, sem executar chamada real, sem configurar host real e sem ler segredo de runtime.

## Fontes permitidas

- `core/intelligence/analyze_scenario`
- `core/risk/classify_adapter_risk`
- `ai/evidence/`
- `ai/supervisors/adapter-supervisor.md`
- `ai/supervisors/safety-supervisor.md`
- `docs/SECURITY_MODEL.md`
- catalogo seguro atual, somente como referencia sanitizada

## Limites

- `mode=real` permanece bloqueado no produto.
- O readiness gate avalia intencao e pre-condicoes, mas nao executa adapter real.
- Nenhum host, IP, token, secret, credential, payload real, MSISDN, account ou documento real deve ser versionado.
- Feature flags, opt-in, kill switch e allowlist entram por parametro injetado.
- O MVP7.7.1 nao faz parte desta entrega.

## Artefatos

- `readiness-gate.md`: contrato do gate, decisoes e bloqueios.
- `qa4-first-call-contract.md`: contrato futuro da primeira chamada QA4, ainda conceitual.
- `mvp7-8-4-gate-dag-contract.md`: DAG canonico Alpha mock-only, evidencia
  estruturada, admissao API e consolidacao terminal do Manager.

## Resultado esperado

O gate pode retornar `ready_for_manual_review` quando todas as pre-condicoes simuladas passam, mas `ready_for_real_call` permanece `false`. A revisao humana futura nao e execucao automatica.
