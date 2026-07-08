# Multi-resource Runtime Contract

Este contrato pertence ao MVP7.8.3A.1 - Multi-resource Runtime Contract.

Ele define preflight seletivo por perfil/fluxo para execucao QA manual futura. Esta entrega nao executa chamada real, nao chama API, nao abre conexao Oracle, nao chama Kafka, nao chama Jenkins e nao libera `adapter-run mode=real`.

## Perfil oficial inicial

`smartoffers_basic_smoke`

Objetivo do perfil:

- representar o primeiro smoke QA4 aprovado pelo caminho minimo controlado;
- exigir SmartOffers API;
- exigir ACM_CUSTOM com acesso read-only;
- exigir Oracle client local;
- manter todos os valores reais fora do Git, dos logs, dos retornos e dos testes.

## Recursos obrigatorios

O perfil `smartoffers_basic_smoke` exige somente referencias de runtime:

- `SMARTOFFERS_QA4_API_URL`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD`
- `SMARTOFFERS_ORACLE_CLIENT_LIB_DIR`

O perfil nao exige:

- `SMARTOFFERS_QA4_FTM_ENGINE_URL`
- `SMARTOFFERS_QA4_ACMV4_DB_*`
- `SMARTOFFERS_QA4_BDA_DB_*`

Esses recursos ficam para perfis/fluxos futuros, porque o primeiro smoke nao deve ser bloqueado por dependencias que ainda nao usa.

Esses nomes sao referencias locais. O repositorio nao deve conter URL, host, IP, DSN, usuario real, senha real, token, cookie, payload real, MSISDN, account, documento ou response body bruto.

## Alias legado temporario

`SMARTOFFERS_QA4_DB_DSN`, `SMARTOFFERS_QA4_DB_USER` e `SMARTOFFERS_QA4_DB_PASSWORD` podem ser aceitos temporariamente como alias legado para ACM_CUSTOM.

Regras:

- nao sao o contrato oficial novo;
- devem ser tratados como legado/deprecado;
- nao sobrescrevem `SMARTOFFERS_QA4_ACM_CUSTOM_DB_*` quando as refs explicitas existem;
- nao expandem para ACMV4 ou BDA;
- devem ser removidos em fase futura apos estabilizacao do contrato multi-resource.

## Preflight

O preflight deve retornar somente:

- status `READY` ou `BLOCKED`;
- ambiente;
- perfil;
- fluxo;
- recursos verificados;
- nomes das refs verificadas;
- nomes das refs ausentes.

O preflight nao deve retornar valores reais.

## Normalizacao para runner legado

Quando o preflight estiver `READY`, as refs do perfil podem ser normalizadas em memoria para os nomes esperados pelos scripts legados:

- `SMARTOFFERS_API_URL`
- `SMARTOFFERS_DB_DSN`
- `SMARTOFFERS_DB_USER`
- `SMARTOFFERS_DB_PASSWORD`
- `SMARTOFFERS_ORACLE_CLIENT_LIB_DIR`

Essa normalizacao nao libera execucao real por si so. O guard `SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT=YES_I_UNDERSTAND`, confirmacao manual e bloqueios existentes continuam obrigatorios.

## Fora do MVP7.8.3A.1

- chamada QA4 real;
- chamada API real;
- conexao Oracle real;
- leitura ou escrita em BD real;
- Kafka real;
- Jenkins real;
- novos endpoints Flask;
- alteracao de catalogo seguro;
- alteracao de `safe_for_real_execution`;
- alteracao de `execution_status`;
- liberacao de `adapter-run mode=real`.
