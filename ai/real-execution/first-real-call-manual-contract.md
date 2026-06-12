# First QA4 Real Call Manual Contract

Este contrato pertence ao MVP7.7.1.1 - First QA4 Real Call Gate.

Ele cria o gate manual controlado para uma chamada QA4 futura. A implementacao desta etapa nao executa chamada real em testes, CI, Self Review ou importacao de modulo.

## Separacao de runtime

`runtime_secrets` contem valores reais somente em memoria durante uma execucao manual aprovada. Ele nunca deve ser versionado, logado, retornado, persistido, documentado com valores reais ou enviado para risk/readiness.

`runtime_refs` contem apenas referencias sanitizadas e flags. Ele e a unica representacao permitida para risk classifier, readiness gate, logs e evidencia.

## Client real isolado

`RealHttpClient` fica em `core/real_execution/real_http_client.py`.

Regras:

- nao exportar no pacote;
- nao importar em testes unitarios padrao;
- nao usar no adapter-run;
- nao implementar retry;
- exigir timeout;
- nao guardar requisicao bruta;
- nao retornar corpo bruto.

## Approval obrigatorio

O approval manual deve conter apenas referencias sanitizadas:

- `approved=True`;
- `risk_acceptance=True`;
- `approver_ref`;
- `ticket_ref`;
- `approved_api_id`;
- `approved_environment=QA4`;
- `approved_at_ref`.

## Evidencia sanitizada

A evidencia pode registrar identificador de API, metodo, ambiente, decisao, referencias mascaradas, status code, duracao, `real_call_executed` e `body_recorded=false`.

Ela nunca deve conter endpoint, endereco de rede, material de autenticacao, credencial, cabecalhos reais, massa real, linha, conta, documento ou corpo bruto.

## Execucao manual futura

A chamada real de fato fica fora da suite automatizada e fora de CI. Um operador humano deve fornecer runtime seguro em memoria, approval sanitizado e abortar se qualquer guardrail falhar.
