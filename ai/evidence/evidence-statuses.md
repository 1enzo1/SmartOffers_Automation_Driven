# Evidence Statuses

Este arquivo define os status seguros que o futuro Evidence Planner podera atribuir a cada camada de evidencia.

No MVP7.6.4, os status sao apenas contrato documental.

## `mock`

Use quando a evidencia puder ser representada por dados simulados, cenario salvo, dry-run mockado ou documento conceitual.

Permite:

- planejar evidencia esperada;
- explicar comportamento simulado;
- referenciar artefatos gerados localmente.

Nao permite:

- consultar ambiente real;
- chamar API real;
- consumir Kafka;
- usar credenciais;
- executar subprocessos reais.

## `read-only`

Use quando a evidencia futura puder ser analisada de forma somente leitura e sanitizada.

Permite:

- descrever artefato esperado;
- definir perguntas de triagem;
- orientar revisao manual segura.

Nao permite:

- alterar estado;
- publicar evento;
- disparar mensagem;
- executar job;
- acessar dado sensivel sem controle explicito.

## `blocked`

Use quando a evidencia exigir sistema externo real, credencial, dado sensivel, payload real, host real, topico real ou acao com risco operacional.

Permite:

- registrar o motivo do bloqueio;
- indicar dependencia de guardrail futuro;
- evitar inferencia insegura.

Nao permite:

- contornar a restricao;
- substituir bloqueio por execucao manual;
- habilitar `mode=real`.

## `future-controlled`

Use quando a evidencia pode ser candidata a MVP futuro com allowlist, opt-in, ambiente controlado, timeout, logs sanitizados e testes dedicados.

Permite:

- registrar intencao futura;
- indicar adaptador conceitual;
- preparar criterios de seguranca.

Nao permite:

- ativar execucao real neste MVP;
- alterar catalogo seguro;
- criar endpoint;
- criar automacao.

## Regras gerais

- `blocked` prevalece quando houver risco de chamada real ou dado sensivel.
- `future-controlled` nao e autorizacao de execucao.
- `mock` e `read-only` devem ser preferidos para o laboratorio local-first.
- Status nao devem alterar comportamento de geracao, dry-run, adapter-run ou `request_plan`.
