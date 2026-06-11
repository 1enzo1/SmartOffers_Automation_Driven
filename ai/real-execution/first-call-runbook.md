# First QA4 Call Runbook

Este runbook descreve o fluxo futuro para uma primeira chamada QA4. No MVP7.7.1.0 ele e apenas contrato operacional e usa fake client.

## API candidata

- `post-consulta-de-saldo-f3317b27b3`

A API permanece candidata conceitual. Ela nao esta aprovada para chamada real nesta etapa.

## Fluxo seguro

1. Confirmar opt-in explicito.
2. Validar runtime seguro injetado.
3. Validar allowlist real conceitual separada do catalogo sanitizado.
4. Classificar risco com `classify_adapter_risk`.
5. Avaliar readiness com `evaluate_real_execution_readiness`.
6. Confirmar kill switch inativo.
7. Preparar request sanitizado.
8. Usar apenas fake client no MVP7.7.1.0.
9. Registrar log sanitizado.

## Rollback e kill switch

- kill switch ativo bloqueia antes do client;
- falha de runtime bloqueia antes do client;
- falha de allowlist bloqueia antes do client;
- risco `blocked` bloqueia antes do client;
- readiness `blocked` bloqueia antes do client.

## Evidencias exigidas antes do MVP7.7.1.1

- aprovacao manual da massa de teste fora do repositorio;
- confirmacao de ambiente QA4;
- confirmacao de endpoint via runtime seguro;
- confirmacao de segredo via runtime seguro;
- evidencia de logs sanitizados;
- evidencia de que testes unitarios usam somente fake client.

## Logs permitidos

- identificador da API;
- metodo;
- ambiente;
- decisao;
- codigos de bloqueio;
- status simulado;
- correlation id mascarado.

## Logs proibidos

- endpoint real;
- endereco de rede real;
- material de autenticacao;
- credencial;
- massa real;
- linha, conta ou documento real;
- cabecalho sensivel;
- corpo bruto de resposta.
