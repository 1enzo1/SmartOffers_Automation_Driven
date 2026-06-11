# SmartOffers Automation

## Diretrizes Permanentes

Este projeto e uma plataforma Flask/Python para gerar cenarios SmartOffers/ACM, salvar e reabrir JSONs de cenario, simular execucao via dry-run mockado, executar adapter-run local/mockado, exportar artefatos QA/DET e evoluir gradualmente para automacao real controlada.

O produto atual e `SmartOffers_Automation_Driven`. PortalQA e uma referencia historica e nao deve orientar a arquitetura atual.

## Branch Evolutiva

A branch `qa/mvp4-integration` e a branch base evolutiva atual, apesar do nome historico. Nao criar MVP novo a partir de `main` sem confirmacao. Antes de qualquer PR, confirmar que a branch contem o merge do MVP7.6 ou posterior.

## Direcao de Dominio

Nao tratar o projeto apenas como gerador de testes. Toda evolucao deve preservar a direcao de laboratorio seguro SmartOffers/ACM, com geracao deterministica, planejamento mockado, evidencia esperada, classificacao de risco e preparacao gradual para execucao real controlada.

Supervisores, skills, ontologia, playbooks e safety do produto devem ser introduzidos primeiro como contratos Markdown em `ai/`, sem LLM externo e sem execucao real.

## Stack Atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geracao deterministica por templates
- Dry-run mockado
- Adapter-run mockado
- Sem React e sem build step frontend no momento

## Regras Obrigatorias

- Nao chamar Oracle real.
- Nao chamar APIs reais.
- Nao chamar Kafka real.
- Nao chamar Jenkins real.
- Nao executar subprocessos reais para dry-run.
- Nao habilitar `mode=real` sem MVP explicito.
- Nao alterar `safe_for_real_execution` sem MVP especifico.
- Nao alterar `execution_status` do catalogo para liberar execucao real sem MVP especifico.
- Nao adicionar React agora.
- Nao criar build step frontend.
- Nao reestruturar o projeto inteiro sem necessidade.
- Nao quebrar rotas antigas.
- Nao quebrar compatibilidade com JSONs existentes.

## Rotas Criticas

Manter funcionando:

- `/`
- `/executar`
- `/listar_testes`
- `/ver_teste`
- `/abrir_pasta`
- `/api/questions`
- `/api/scenarios`
- `/api/scenarios/generate`
- `/api/scenarios/<id>`
- `/api/scenarios/<id>/dry-run`
- `/api/scenarios/<id>/adapter-run`
- `/api/scenarios/<id>/export/docx`
- `/api/scenarios/<id>/export/xlsx`
- `/api/scenarios/<id>/export/json`
- `/api/dry-runs/<id>`
- `/api/dry-runs/<id>/export/docx`
- `/api/dry-runs/<id>/export/xlsx`
- `/api/dry-runs/<id>/export/json`
- `/api/adapters`
- `/api/adapters/health`
- `/api/api-catalog`
- `/api/api-catalog/<api_id>`

## Padrao de Evolucao

Preferir mudancas pequenas, modulos separados, compatibilidade com JSON existente, testes cobrindo nova funcionalidade, frontend simples e arquitetura preparada para adapters reais no futuro.

Mudancas de documentacao e guardrails nao devem alterar comportamento de geracao, dry-run, adapter-run, exports, catalogo ou UI.

## Geracao de Cenarios

O gerador deve ser deterministico. Uma resposta do usuario pode gerar multiplos steps, queries, checkpoints e evidencias esperadas.

Campos existentes de JSON devem continuar compativeis. Novos campos so podem ser opcionais e precisam de MVP proprio.

## Dry-run

Dry-run deve usar cenario JSON salvo, simular execucao localmente, gerar relatorio JSON, produzir logs mockados, marcar steps como `passed`, `failed` ou `skipped` e nunca tocar em sistemas externos.

## Adapter-run

Adapter-run deve permanecer local e mockado ate MVP especifico de execucao real. `mode=real` deve continuar bloqueado.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa. Se precisar validar, subir Flask em background, testar endpoints, encerrar o processo iniciado pela tarefa e confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```
