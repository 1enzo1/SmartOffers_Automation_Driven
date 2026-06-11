# QA4 First Call Contract

Este contrato descreve uma chamada real futura em QA4. Ele nao implementa chamada real no MVP7.7.0.

## API candidata conceitual

- `post-consulta-de-saldo-f3317b27b3`

Esta API permanece apenas como candidata conceitual. Ela nao esta aprovada para execucao real nesta entrega.

## Pre-condicoes futuras

- opt-in explicito;
- allowlist de API;
- allowlist de ambiente com `QA4`;
- metodo permitido;
- timeout configurado;
- retry igual a `0`;
- kill switch inativo;
- policy injetada em runtime seguro;
- classificacao de risco sem status `blocked`;
- logs sanitizados;
- ausencia de dado real versionado.

## Dados proibidos em repositorio

- host real;
- IP real;
- token;
- secret;
- credential;
- payload real;
- MSISDN real;
- account real;
- documento real;
- response body bruto.

## Fora do MVP7.7.0

- client HTTP;
- bibliotecas HTTP de runtime;
- leitura de `.env`;
- leitura de variaveis de ambiente;
- criacao de endpoint;
- alteracao de adapter-run;
- chamada real.
