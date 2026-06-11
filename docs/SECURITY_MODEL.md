# Security Model

## Principio

O projeto e seguro por padrao. Qualquer acao real deve estar bloqueada ate um MVP especifico liberar controles explicitos.

## Bloqueios permanentes no estado atual

- Nao chamar Oracle real.
- Nao chamar APIs reais.
- Nao chamar Kafka real.
- Nao chamar Jenkins real.
- Nao executar subprocessos reais para dry-run.
- Nao habilitar `mode=real`.
- Nao expor IPs internos, URLs reais, tokens, senhas, cookies, bearer ou secrets.
- Nao versionar ZIPs brutos de APIs ou JSONs brutos de ambiente.

## Categorias de risco futuras

`SAFE_READ`: leitura planejada ou simulada, sem mutacao e sem rede real no estado atual.

`MOCK_ONLY`: acao permitida apenas para simulacao local.

`HOMOLOG_CONTROLLED`: acao futura restrita a ambiente homologado com controles adicionais.

`REAL_QA_OPT_IN`: acao futura real em QA4, com opt-in explicito e allowlist.

`PROD_BLOCKED`: qualquer acao contra producao.

`DESTRUCTIVE_OPERATION`: mutacao, delete, rollback, publicacao ou operacao irreversivel. Deve permanecer bloqueada ate decisao explicita de produto.

## Regras para MVP7.6.1

MVP7.6.1 e documental. Ele nao cria adapters reais, nao altera catalogo para liberar execucao, nao cria endpoints e nao muda contratos de JSON.

Arquivos em `ai/` sao contratos conceituais. Eles nao executam nada.

## Condicoes futuras para MVP7.7

Antes de qualquer chamada real opt-in em QA4, o projeto deve ter:

- ontologia SmartOffers;
- playbooks operacionais;
- evidence planner;
- safety supervisor;
- adapter risk classifier;
- policy explicita de API permitida;
- bloqueio de producao;
- sanitizacao de logs;
- timeout obrigatorio;
- testes de allow e deny.

Sem essas condicoes, `mode=real` deve continuar bloqueado.
