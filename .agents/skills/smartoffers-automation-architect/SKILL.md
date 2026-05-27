---
name: smartoffers-automation-architect
description: Use esta skill ao trabalhar no projeto SmartOffers Automation, incluindo geração determinística de cenários, dry-run mockado, exportação QA/DET, Flask, templates, testes, UI HTML/CSS/JS, rotas de API e evolução incremental do MVP.
---

# SmartOffers Automation Architect

## Papel

Atue como arquiteto técnico do projeto SmartOffers Automation.

O projeto é uma plataforma Flask/Python para:
- gerar cenários SmartOffers/ACM;
- salvar cenários em JSON;
- reabrir cenários;
- simular execução via dry-run mockado;
- exportar artefatos QA/DET em DOCX, XLSX e JSON;
- evoluir para automação real no futuro.

## Stack atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geração determinística por templates
- Dry-run mockado
- Exportação com python-docx e openpyxl
- Sem React no momento
- Sem integrações reais no momento

## Estrutura principal

- `templates/index.html`: UI principal.
- `core/generation/`: geração determinística de cenários.
- `core/simulation/`: dry-run mockado. Deve ser pacote, não arquivo `core/simulation.py`.
- `core/exporters/`: exportação DOCX/XLSX/JSON.
- `tests/`: suíte segura de testes.

## Regras obrigatórias

Não fazer:
- não chamar Oracle real;
- não chamar APIs reais;
- não chamar Kafka real;
- não chamar Jenkins real;
- não executar subprocessos reais para dry-run;
- não adicionar React agora;
- não criar build step frontend;
- não reestruturar o projeto inteiro sem necessidade;
- não quebrar rotas antigas;
- não recriar `core/simulation.py`.

## Rotas críticas

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
- `/api/scenarios/<id>/export/docx`
- `/api/scenarios/<id>/export/xlsx`
- `/api/scenarios/<id>/export/json`
- `/api/dry-runs/<id>`
- `/api/dry-runs/<id>/export/docx`
- `/api/dry-runs/<id>/export/xlsx`
- `/api/dry-runs/<id>/export/json`

## Padrão de evolução

Sempre preferir:
- mudanças pequenas;
- módulos separados;
- compatibilidade com JSON existente;
- testes cobrindo nova funcionalidade;
- frontend simples;
- arquitetura preparada para adapters reais no futuro.

Antes de novo MVP:
- confirmar branch base correta;
- buscar remoto com `git fetch --all --prune`;
- confirmar que a branch contém o último MVP mergeado;
- evitar aplicar MVP novo sobre base antiga.

## Geração de cenários

O gerador deve ser determinístico.

Uma resposta do usuário pode gerar múltiplos steps.

Exemplo:
- usuário escolhe “recarga”;
- sistema gera:
  - step de execução da recarga;
  - step de validação;
  - queries/checkpoints;
  - evidências esperadas.

Known limitation:
- `event_type == "recarga"` ainda pode permitir `recharge_scenario == "none"` no modo mockado.
- Não corrigir incidentalmente fora de um MVP específico.
- Tratar como futuro hardening para fase de execução real/adapters.

## Dry-run

Dry-run deve:
- usar cenário JSON salvo;
- simular execução;
- gerar relatório JSON;
- gerar logs mockados;
- marcar steps como passed/failed/skipped;
- respeitar overrides como `dry_run.status` e `dry_run_status`;
- nunca tocar em sistemas externos.

## Exportação QA/DET

Exports devem:
- usar cenário salvo e/ou relatório dry-run salvo;
- gerar DOCX, XLSX e JSON enriquecido;
- preservar dados de steps, payload, queries, checkpoints, evidências, warnings, logs e status.

Ao exportar queries/evidências:
- não considerar apenas `sql` e `lookup`;
- também preservar `request`, `endpoint`, `method`, `files`;
- se nenhuma chave conhecida existir, serializar o item completo como JSON compacto/legível.

## UI

Preservar:
- Gerador de Cenários;
- Cenários Salvos;
- Dry-run;
- Exportações;
- Execução Legada;
- sidebar recolhível;
- Suite de Testes na sidebar;
- botões Executar/Pausar/Continuar/Re-run/Limpar;
- toggle-pill;
- filtros Todos/Passed/Failed/Skipped;
- terminal com horário por linha.

Não regredir visual do MVP4.2 ao alterar `templates/index.html`.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa.

Se precisar validar:
- subir Flask em background;
- usar porta livre;
- testar endpoints;
- encerrar apenas o processo iniciado pela tarefa;
- confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```
