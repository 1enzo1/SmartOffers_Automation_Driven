# First QA4 Call Runbook

Este runbook descreve o fluxo futuro para uma primeira chamada QA4. No MVP7.7.1.0 ele era apenas contrato operacional com fake client. No MVP7.7.1.1 ele passa a documentar o gate manual controlado, ainda sem execucao real automatizada.

## API candidata

- `post-consulta-de-saldo-f3317b27b3`

A API permanece candidata conceitual. Ela nao esta aprovada para chamada real nesta etapa.

## Fluxo seguro

1. Confirmar opt-in explicito.
2. Separar `runtime_refs` sanitizado de `runtime_secrets` em memoria.
3. Validar runtime sanitizado e runtime real em memoria.
4. Validar allowlist real conceitual separada do catalogo sanitizado.
5. Classificar risco com `classify_adapter_risk`, usando apenas work item sanitizado.
6. Avaliar readiness com `evaluate_real_execution_readiness`, usando apenas request/policy sanitizados.
7. Confirmar kill switch inativo.
8. Validar approval humano sanitizado.
9. Preparar request sanitizado.
10. Chamar client manual somente se todos os gates passarem.
11. Registrar apenas evidencia sanitizada.

## Rollback e kill switch

- kill switch ativo bloqueia antes do client;
- falha de runtime bloqueia antes do client;
- falha de allowlist bloqueia antes do client;
- risco `blocked` bloqueia antes do client;
- readiness `blocked` bloqueia antes do client.
- approval ausente ou divergente bloqueia antes do client;
- runtime real incompleto bloqueia antes do client.

## Evidencias exigidas antes do MVP7.7.1.1

- aprovacao manual da massa de teste fora do repositorio;
- confirmacao de ambiente QA4;
- confirmacao de endpoint via runtime seguro;
- confirmacao de segredo via runtime seguro;
- evidencia de logs sanitizados;
- evidencia de que testes unitarios usam somente fake client.
- evidencia de approval humano sanitizado.
- evidencia de que `adapter-run mode=real` continua bloqueado.

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
