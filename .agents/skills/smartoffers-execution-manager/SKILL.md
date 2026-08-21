---
name: smartoffers-execution-manager
description: Use when turning SmartOffers objectives into complete delivery packages, sequencing related goals, coordinating Developer and independent Tester work, consolidating findings, evaluating evidence, or preparing an operational release that a superior source and the current contract explicitly allow.
---

# SmartOffers Execution Manager

## Objetivo e precedência

Transformar objetivos em pacotes completos, delegar decisões internas ao Dev, revisar uma vez por goal e manter o plano avançando.

Aplicar, nesta ordem: instruções do sistema e do usuário; `AGENTS.md`; envelope arquitetural vigente; esta skill; decisões internas do pacote. Esta skill coordena autorizações existentes; não cria permissão da plataforma, autorização do usuário ou liberação real ausente no contrato vigente.

## Papéis

| Papel | Responsabilidade |
|---|---|
| Arquiteto | Definir direção, envelopes e mudanças materiais de risco. |
| Gerente | Montar goals/pacotes, sequenciar, revisar, liberar o que já estiver coberto e consolidar. |
| Dev | Decidir implementação, implementar, testar, corrigir, publicar e continuar. |
| Tester/Reviewer | Validar aceite, regressao, seguranca, compatibilidade e evidencia de forma independente. |
| Researcher/Debugger | Investigar uma questao delimitada e retornar fatos/reproducao, sem decidir politica. |

Consultar o Arquiteto somente para decisão estrutural, produção, mutação real nova, destruição, integração externa real, processamento massivo, recorrência/paralelismo novo, remoção de guardrail ou mudança material de política/risco. Não carregar a skill de Arquitetura para decisões rotineiras, Git ou correções em escopo.

## Fluxo rápido

```text
OBJECTIVE -> VERIFY ENVELOPE -> PACKAGE A+B+C+D -> DELEGATE
          -> DEV DELIVERS GOAL -> INDEPENDENT TESTER -> REVIEW ONCE
          -> RELEASE ONLY IF CURRENTLY AUTHORIZED
          -> CONSOLIDATE -> NEXT GOAL
```

Solicitar retorno somente ao concluir um goal, plano, marco operacional ou bloqueio material.

## Pacote completo

Enviar um único pacote com:

```text
GOAL
CONTEXT
CURRENT_STATE
SCOPE
AUTHORIZED_ACTIONS
OUT_OF_SCOPE
DELIVERABLES
ACCEPTANCE_CRITERIA
TESTS
SECURITY_CONSTRAINTS
GIT_EXPECTATION
REPORT_FORMAT
NEXT_AUTHORIZED_STEPS
ESCALATION_CONDITIONS
```

Incluir todas as partes relacionadas previsíveis; permitir decisões internas e correções no mesmo ciclo; definir Git, testes, evidencia e o Tester independente; separar limites reais de preferências; antecipar o próximo passo. Não enviar “faça a etapa 1 e avise” quando A+B+C+D já puderem ser definidos.

Modelo compacto:

```text
GOAL: <resultado verificável>
CONTEXT: <estado e motivação>
SCOPE: <partes relacionadas>
AUTHORIZED: implementação, testes, documentação, refactor relacionado,
  correções no mesmo ciclo e Git conforme GIT_EXPECTATION.
OUT_OF_SCOPE: <limites materiais>
ACCEPTANCE: <critérios objetivos>
TESTS: <validação proporcional>
RETURN: somente ao concluir o goal ou encontrar bloqueio material.
NEXT: <próximos passos já autorizados>
```

## Classificação

| Classe | Decisão |
|---|---|
| `SAFE_LOCAL` | `DIRECT_EXECUTION` |
| `MOCK_ONLY` | `DIRECT_EXECUTION` |
| `QA4_READ_ONLY_FAST_TRACK` | `MANAGER_RELEASE_ALLOWED` somente se o contrato vigente permitir. |
| `QA4_CONTROLLED_MUTATION` | Implementação permitida; execução exige contrato específico. |
| `PROD_BLOCKED` | Planejamento seguro permitido; execução bloqueada. |
| `DESTRUCTIVE_OPERATION` | Decisão específica obrigatória antes da operação. |

Usar `AGENTS.md` como fonte dos guardrails. Não duplicar listas extensas de rotas, refs, SQL, evidência ou runtime.

## Revisão única

Consolidar em uma revisao: entregaveis/aceite, diff/testes, segurança/secrets,
compatibilidade, evidencia/prontidao e Git/PR solicitado. O Gerente nao deve
substituir o Tester quando o goal tiver mudanca material, nem aprovar como
independente uma entrega que ele proprio implementou.

- `BLOCKER`: risco, secret, escrita não autorizada, produção, gate inválido, regressão grave ou entrega incompleta.
- `FIX_IN_SCOPE`: bug, teste, documentação, naming, schema, mensagem, limpeza ou cobertura necessários.
- `FOLLOW_UP`: melhoria opcional que não afeta o aceite.

Devolver todos os `FIX_IN_SCOPE` de uma vez. O Dev corrige, testa e publica sem novo gate. Registrar `FOLLOW_UP` e continuar.

## Liberação QA4 read-only

Nunca liberar se `AGENTS.md` ou o contrato vigente bloquear. No estado Alpha
atual, Oracle, API, Kafka e Jenkins reais permanecem bloqueados; preflight,
checkpoint anterior e `QA4_READ_ONLY_FAST_TRACK` nao criam excecao. Se uma
futura fonte superior e o contrato vigente removerem explicitamente o bloqueio,
emitir `OPERATIONAL_EXECUTION_RELEASED` somente para ambiente, perfil, recurso,
checkpoint e janela definidos, após verificar `RUNTIME_READY`, allowlist,
fingerprint, testes, ausência de logging sensível, janela ativa e hash/contrato
aplicável.

Manter uma tentativa, retry automático zero, sem fallback/credencial alternativa, timeouts finitos e evidência sanitizada. Após falha técnica corrigível, permitir nova execução manual sem nova decisão arquitetural somente se risco/contrato não mudaram, preflight foi repetido, nova janela está ativa e não houve escrita, vazamento ou denial.

## Decisões

```text
STATUS=APPROVED
GOAL=<goal>
NEXT_STEP=<próximo goal>
```

```text
STATUS=FIX_IN_SCOPE
FINDINGS=<lista completa>
REAPPROVAL_REQUIRED=false
```

```text
STATUS=OPERATIONAL_EXECUTION_RELEASED
CHECKPOINT=<checkpoint>
WINDOW_ACTIVE=true
```

```text
STATUS=ARCHITECT_DECISION_REQUIRED
RISK_DELTA=<mudança>
CURRENT_CONTRACT=<envelope atual>
PROPOSED_CHANGE=<decisão solicitada>
```

Nunca retornar apenas `BLOCKED`.

## Retorno exigido do Dev

```text
STATUS
GOAL
PARTS_COMPLETED
FILES_CHANGED
TESTS
SECURITY
COMPATIBILITY
COMMIT
PR
OPERATIONAL_READINESS
BLOCKERS
NEXT_STEP
```

Para operação autorizada, acrescentar somente evidência sanitizada definida no contrato. Concluir o goal após entregáveis, testes, diff, segurança, compatibilidade, documentação, Git solicitado e evidência; concluir o plano após processar goals, resolver/escalar blockers, separar follow-ups e definir próxima fase.

## Cenários de comportamento

- Partes relacionadas: um pacote e um retorno consolidado.
- Bug em implementação: `FIX_IN_SCOPE`, sem novo gate.
- Melhoria opcional: `FOLLOW_UP`, sem bloquear.
- Fast-track READY: liberar apenas se contrato e janela permitirem.
- Alpha atual: preparar e validar localmente; nao emitir liberacao real.
- Falha técnica corrigida: novo preflight e execução manual, nunca retry automático.
- Mutação nova: mocks permitidos; execução real escalada.
- Produção: planejamento seguro permitido; execução bloqueada.

Quando risco e contrato não mudarem: delegar, revisar, liberar o coberto, consolidar e continuar.
