# Real Execution Hardening Evidence Pack

Este documento consolida o MVP7.7.2 - Real Execution Hardening & Evidence Pack.

O objetivo e reforcar o gate manual criado nos MVPs 7.7.0, 7.7.1.0 e 7.7.1.1 sem executar QA4, sem chamada real e sem usar dado real.

## Escopo

- documentar evidencias esperadas para revisao manual;
- consolidar guardrails obrigatorios;
- reforcar isolamento do client manual;
- registrar criterios negativos para testes;
- manter `adapter-run mode=real` bloqueado.

## Fontes tecnicas

- `core/real_execution/readiness.py`
- `core/real_execution/runtime.py`
- `core/real_execution/allowlist.py`
- `core/real_execution/executor.py`
- `core/real_execution/real_http_client.py`
- `core/risk/adapter_risk_classifier.py`

## Evidencias esperadas

- suite automatizada passando;
- diff vazio nos caminhos proibidos;
- `RealHttpClient` nao exportado no pacote;
- `execute_first_qa4_call_manual` nao exportado no pacote;
- biblioteca de rede presente somente no client manual isolado;
- logs e evidencias usando apenas dados sanitizados;
- falhas de guardrail bloqueando antes do client;
- nenhum caminho automatico chamando client manual.

## Fora do escopo

- execucao QA4;
- chamada externa;
- automacao de chamada real;
- UI;
- rota;
- mudanca no adapter-run;
- mudanca no dry-run;
- mudanca no catalogo seguro;
- mudanca no `request_plan`.

## Fechamento

O MVP7.7.2 so pode ser aprovado se houver alteracao concreta em documentacao/testes de hardening, validacao automatizada e nenhuma regressao funcional.
