# SmartOffers Automation

## Diretrizes Permanentes

Este projeto é uma plataforma Flask/Python para gerar cenários SmartOffers/ACM, salvar e reabrir JSONs de cenário, simular execução via dry-run mockado e evoluir gradualmente para automação real.

## Stack Atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geração determinística por templates
- Dry-run mockado
- Sem React e sem build step frontend no momento

## Regras Obrigatórias

- Não chamar Oracle real.
- Não chamar APIs reais.
- Não chamar Kafka real.
- Não chamar Jenkins real.
- Não executar subprocessos reais para dry-run.
- Não adicionar React agora.
- Não criar build step frontend.
- Não reestruturar o projeto inteiro sem necessidade.
- Não quebrar rotas antigas.

## Rotas Críticas

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

## Padrão de Evolução

Preferir mudanças pequenas, módulos separados, compatibilidade com JSON existente, testes cobrindo nova funcionalidade, frontend simples e arquitetura preparada para adapters reais no futuro.

## Geração de Cenários

O gerador deve ser determinístico. Uma resposta do usuário pode gerar múltiplos steps, queries, checkpoints e evidências esperadas.

## Dry-run

Dry-run deve usar cenário JSON salvo, simular execução localmente, gerar relatório JSON, produzir logs mockados, marcar steps como `passed`, `failed` ou `skipped` e nunca tocar em sistemas externos.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa. Se precisar validar, subir Flask em background, testar endpoints, encerrar o processo e confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```
