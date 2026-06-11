# Runtime Secret Contract

Este contrato pertence ao MVP7.7.1.0 - Runtime Secret Contract.

O objetivo e definir como dados sensiveis de uma chamada QA4 futura deverao chegar ao produto sem serem versionados. Esta entrega nao executa chamada real e nao cria client real.

## Entrada de runtime

O runtime deve ser recebido por parametro injetado, nunca por leitura de ambiente, `.env` ou arquivo externo.

Campos conceituais obrigatorios:

- `QA4_HOST_REF`: referencia segura para endpoint QA4.
- `AUTH_REF`: referencia segura para material de autenticacao.
- `SENSITIVE_HEADERS_REF`: referencia segura para cabecalhos sensiveis.
- `TEST_PAYLOAD_REF`: referencia segura para massa de teste aprovada.
- `CORRELATION_ID`: identificador sintetico da revisao.

## Valores proibidos

Nao versionar:

- endpoint real;
- endereco de rede real;
- material de autenticacao;
- credencial;
- massa real;
- linha, conta ou documento real;
- cabecalho sensivel;
- corpo bruto de resposta.

## Regras

- referencias devem ser conceituais e sanitizadas;
- referencias nao podem conter valores brutos;
- a saida do validador deve informar apenas presenca, status e codigos de bloqueio;
- logs devem ser sanitizados por construcao;
- o fake client e obrigatorio nesta etapa.

## Fora do MVP7.7.1.0

- client HTTP real;
- chamada QA4 real;
- endpoint Flask;
- alteracao de adapter-run;
- liberacao de `mode=real`;
- leitura de secrets reais.
