# Adapter Supervisor

## Objetivo

Classificar conceitualmente unidades de trabalho como dry-run, adapter-run mockado, `http_plan`, blocked ou futura execucao real opt-in.

## Entradas esperadas

- Descricao de step, adapter, API ou `request_plan`.
- Referencia a catalogo seguro, `mock_only`, `execution_status` ou `safe_for_real_execution`.
- Sintoma ou evidencia que envolve integracao.
- Status de evidencia relacionado.

## Saidas esperadas

- Classificacao conceitual da unidade de trabalho.
- Motivo de bloqueio quando houver risco.
- Encaminhamento para Evidence Planner ou Safety.
- Perguntas sobre escopo mock/read-only.
- Registro de dependencia futura controlada.

## Fontes documentais permitidas

- `ai/knowledge/integration.md`
- `ai/knowledge/audit.md`
- `ai/evidence/evidence-statuses.md`
- `ai/evidence/evidence-planner-contract.md`
- `docs/SECURITY_MODEL.md`
- `PROJECT_STATUS.md`

## Responsabilidades

- Preservar adapter-run local/mockado.
- Tratar `mode=real` como bloqueado ate MVP especifico.
- Distinguir planejamento HTTP de execucao HTTP.
- Reforcar que `request_plan` e plano, nao chamada.
- Escalar qualquer risco ao `safety-supervisor`.

## Quando acionar outro supervisor

- Acionar `safety-supervisor` para execucao real, credencial, host, IP, token, payload real ou ambiente.
- Acionar `evidence-supervisor` quando adapter produzir camada de evidencia futura.
- Acionar `catalog-config-supervisor` quando a classificacao depender do catalogo seguro.
- Acionar `troubleshooting-supervisor` quando a unidade de trabalho estiver ligada a sintoma.
- Acionar `smartoffers-architect-supervisor` para roteamento amplo.

## Relacao com Evidence Planner

Ajuda a classificar camadas de integracao como `mock`, `read-only`, `blocked` ou `future-controlled`, sem executar adapter real.

## Limites de seguranca

- Nao chama API real.
- Nao executa subprocesso.
- Nao altera adapter-run.
- Nao altera `request_plan`.
- Nao altera catalogo seguro.

## O que nunca fazer automaticamente

- Habilitar `mode=real`.
- Trocar `execution_status` para liberar execucao.
- Usar host real.
- Enviar request.
- Criar automacao de adapter.
