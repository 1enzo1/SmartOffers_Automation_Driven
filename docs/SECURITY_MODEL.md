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

## Categorias de risco vigentes

`SAFE_LOCAL`: trabalho local sem sistema externo.

`MOCK_ONLY`: simulacao local; contato real proibido.

`QA4_READ_ONLY_FAST_TRACK`: classe contratual para leitura QA4. Nao e
autorizacao operacional e, no Alpha atual, o transporte real continua bloqueado.

`QA4_CONTROLLED_MUTATION`: mutacao QA4. Implementacao mockada pode ser preparada;
execucao exige MVP e autorizacoes especificas.

`PROD_BLOCKED`: qualquer acao contra producao.

`DESTRUCTIVE_OPERATION`: mutacao irreversivel ou de alto impacto. Exige decisao
e autorizacao especificas antes da operacao.

`SAFE_READ`, `HOMOLOG_CONTROLLED` e `REAL_QA_OPT_IN` sao nomes historicos. Ao
abrir trabalho novo, mapear para a taxonomia acima e preservar o guardrail mais
restritivo.

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

Contratos, preflights, checkpoints ou tokens anteriores nao substituem
autorizacao atual. Ver `ALPHA_GOVERNANCE.md` para o estado canonico e as
divergencias abertas.
