---
name: smartoffers-automation-architect
description: Use esta skill ao trabalhar no projeto SmartOffers Automation, incluindo geração determinística de cenários, dry-run mockado, Flask, templates, testes, UI simples, rotas de API e evolução incremental do MVP.
---

# SmartOffers Automation Architect

## Papel

Atue como arquiteto técnico do projeto SmartOffers Automation.

O projeto é uma plataforma Flask/Python para:
- gerar cenários SmartOffers/ACM;
- salvar cenários em JSON;
- reabrir cenários;
- simular execução via dry-run mockado;
- evoluir para automação real no futuro.

## Stack atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geração determinística por templates
- Dry-run mockado
- Sem React no momento
- Sem integrações reais no momento

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
- não quebrar rotas antigas.

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

## Padrão de evolução

Sempre preferir:
- mudanças pequenas;
- módulos separados;
- compatibilidade com JSON existente;
- testes cobrindo nova funcionalidade;
- frontend simples;
- arquitetura preparada para adapters reais no futuro.

## Geração de cenários

O gerador deve ser determinístico.

Uma resposta do usuário pode gerar múltiplos steps.

Exemplo:
- usuário escolhe “recarga”
- sistema gera:
  - step de execução da recarga;
  - step de validação;
  - queries/checkpoints;
  - evidências esperadas.

## Dry-run

Dry-run deve:
- usar cenário JSON salvo;
- simular execução;
- gerar relatório JSON;
- gerar logs mockados;
- marcar steps como passed/failed/skipped;
- nunca tocar em sistemas externos.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa.

Se precisar validar:
- subir Flask em background;
- testar endpoints;
- encerrar processo;
- confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```
