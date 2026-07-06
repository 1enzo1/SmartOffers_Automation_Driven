# Multi-resource Runtime Contract

Este contrato pertence ao MVP7.8.3A.1 - Multi-resource Runtime Contract.

Ele define preflight seletivo por perfil/fluxo para execucao QA manual futura. Esta entrega nao executa chamada real, nao chama API, nao abre conexao Oracle, nao chama Kafka, nao chama Jenkins e nao libera `adapter-run mode=real`.

## Perfil oficial inicial

`qa4_first_smoke_api_acm_custom_ro`

Objetivo do perfil:

- representar o primeiro smoke QA4 aprovado;
- exigir SmartOffers API;
- exigir ACM_CUSTOM com acesso read-only;
- exigir Oracle client local;
- manter todos os valores reais fora do Git, dos logs, dos retornos e dos testes.

## Recursos obrigatorios

O perfil `qa4_first_smoke_api_acm_custom_ro` exige somente referencias de runtime:

- `SMARTOFFERS_QA4_API_URL`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER`
- `SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD`
- `SMARTOFFERS_ORACLE_CLIENT_LIB_DIR`

Esses nomes sao referencias locais. O repositorio nao deve conter URL, host, IP, DSN, usuario real, senha real, token, cookie, payload real, MSISDN, account, documento ou response body bruto.

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
