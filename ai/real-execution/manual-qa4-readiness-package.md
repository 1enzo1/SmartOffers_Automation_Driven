# Manual QA4 Execution Readiness Package

Este pacote consolida a preparacao para uma futura execucao manual QA4. Ele nao autoriza execucao real, nao cria automacao e nao substitui aprovacao humana.

## Objetivo

- organizar os artefatos minimos para revisao operacional;
- manter a chamada futura fora da suite automatizada e fora do CI;
- preservar o modelo mock-first/local-first;
- garantir que a execucao manual futura dependa de operador humano, runtime privado em memoria, approval sanitizado, readiness gate, risk classifier, allowlist e kill switch;
- registrar apenas evidencia sanitizada.

## Artefatos do pacote

- `manual-qa4-operator-script-template.md`: roteiro manual com placeholders;
- `manual-qa4-approval-template.md`: template de aprovacao sanitizada;
- `manual-qa4-evidence-template.md`: template de evidencia sanitizada;
- `manual-execution-checklist.md`: checklist operacional do MVP7.7.2;
- `guardrails-matrix.md`: matriz de bloqueios e responsabilidades;
- `sanitized-evidence-contract.md`: contrato de campos permitidos em evidencia.

## Sequencia obrigatoria

1. Confirmar branch, commit aprovado e suite automatizada passando.
2. Confirmar que `adapter-run mode=real` continua bloqueado.
3. Confirmar que o operador tem approval sanitizado valido.
4. Preparar referencias sanitizadas em memoria, usando apenas placeholders no repositorio.
5. Preparar runtime privado fora do repositorio, somente durante a sessao manual aprovada.
6. Validar allowlist da API candidata.
7. Executar risk classifier apenas com work item sanitizado.
8. Executar readiness gate apenas com request e policy sanitizados.
9. Confirmar kill switch antes do client manual.
10. Abortar diante de qualquer divergencia.
11. Registrar somente evidencia sanitizada.

## Bloqueios permanentes

- nenhuma execucao automatica;
- nenhuma execucao em teste unitario;
- nenhuma execucao em CI;
- nenhum dado bruto persistido;
- nenhuma integracao com adapter-run neste pacote;
- nenhuma alteracao de dry-run, catalogo seguro ou `request_plan`;
- nenhuma chamada Oracle, Kafka ou Jenkins.

## Condicao para seguir para chamada real futura

O pacote apenas deixa a revisao manual pronta. A chamada real futura ainda exige autorizacao operacional fora do repositorio, runtime privado em memoria, approval sanitizado, kill switch validado e evidencia sanitizada.

