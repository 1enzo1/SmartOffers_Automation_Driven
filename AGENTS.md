# SmartOffers Automation

## Diretrizes Permanentes

Este projeto e uma plataforma Flask/Python para gerar cenarios SmartOffers/ACM, salvar e reabrir JSONs de cenario, simular execucao via dry-run mockado, executar adapter-run local/mockado, exportar artefatos QA/DET e evoluir gradualmente para automacao real controlada.

O produto atual e `SmartOffers_Automation_Driven`. PortalQA e uma referencia historica e nao deve orientar a arquitetura atual.

## Branch Evolutiva

A branch `qa/mvp4-integration` e a branch base evolutiva atual, apesar do nome historico. Nao criar MVP novo a partir de `main` sem confirmacao. Antes de qualquer PR, confirmar que a branch contem o merge do MVP7.6 ou posterior.

Baseline imutavel da fase anterior: tag `v0.0.0-pre-alpha.1` no merge
`e1263595aa736de3855234b6f9a0379b944fe70e`. A continuacao de governanca Alpha
parte dessa baseline na branch `codex/alpha`. Consultar
`docs/ALPHA_GOVERNANCE.md` para o snapshot, board e divergencias vigentes; nao
tratar o nome historico da branch base como estado do MVP.

## Direcao de Dominio

Nao tratar o projeto apenas como gerador de testes. Toda evolucao deve preservar a direcao de laboratorio seguro SmartOffers/ACM, local-first e mock-first, com geracao deterministica, planejamento mockado, evidencia esperada, classificacao de risco e preparacao gradual para execucao real controlada.

Execucao real continua bloqueada por padrao. Qualquer futura execucao real exige MVP especifico, opt-in explicito, ambiente permitido, allowlist, timeout, logs sanitizados, bloqueio de producao e testes cobrindo allow/deny.

Supervisores, skills, ontologia, playbooks e safety do produto devem ser introduzidos primeiro como contratos Markdown em `ai/`, sem LLM externo e sem execucao real.

## Stack Atual

- Python
- Flask
- HTML/CSS/JavaScript puro
- Pytest
- Geracao deterministica por templates
- Dry-run mockado
- Adapter-run mockado
- Sem React e sem build step frontend no momento

## Regras Obrigatorias

- Nao chamar Oracle real.
- Nao chamar APIs reais.
- Nao chamar Kafka real.
- Nao chamar Jenkins real.
- Nao executar subprocessos reais para dry-run.
- Nao habilitar `mode=real` sem MVP explicito.
- Nao habilitar execucao real sem opt-in explicito, ambiente permitido, allowlist, timeout, logs sanitizados e bloqueio de producao.
- Nao alterar `safe_for_real_execution` sem MVP especifico.
- Nao alterar `execution_status` do catalogo para liberar execucao real sem MVP especifico.
- Nao versionar runtime secrets, `.env`, `.dbp`, export DBeaver sensivel ou ZIP bruto de conexao/evidencia.
- Nao adicionar React agora.
- Nao criar build step frontend.
- Nao reestruturar o projeto inteiro sem necessidade.
- Nao quebrar rotas antigas.
- Nao quebrar compatibilidade com JSONs existentes.

## Rotas Criticas

Manter funcionando:

- `/`
- `/executar`
- `/listar_testes`
- `/ver_teste`
- `/abrir_pasta`
- `/api/questions`
- `/api/scenarios`
- `/api/scenarios/generate`
- `/api/scenarios/<id>`
- `/api/scenarios/<id>/dry-run`
- `/api/scenarios/<id>/adapter-run`
- `/api/scenarios/<id>/export/docx`
- `/api/scenarios/<id>/export/xlsx`
- `/api/scenarios/<id>/export/json`
- `/api/dry-runs/<id>`
- `/api/dry-runs/<id>/export/docx`
- `/api/dry-runs/<id>/export/xlsx`
- `/api/dry-runs/<id>/export/json`
- `/api/adapters`
- `/api/adapters/health`
- `/api/api-catalog`
- `/api/api-catalog/<api_id>`

## Padrao de Evolucao

Preferir mudancas pequenas, modulos separados, compatibilidade com JSON existente, testes cobrindo nova funcionalidade, frontend simples e arquitetura preparada para adapters reais no futuro.

Mudancas de documentacao e guardrails nao devem alterar comportamento de geracao, dry-run, adapter-run, exports, catalogo ou UI.

## Geracao de Cenarios

O gerador deve ser deterministico. Uma resposta do usuario pode gerar multiplos steps, queries, checkpoints e evidencias esperadas.

Campos existentes de JSON devem continuar compativeis. Novos campos so podem ser opcionais e precisam de MVP proprio.

## Dry-run

Dry-run deve usar cenario JSON salvo, simular execucao localmente, gerar relatorio JSON, produzir logs mockados, marcar steps como `passed`, `failed` ou `skipped` e nunca tocar em sistemas externos.

## Adapter-run

Adapter-run deve permanecer local e mockado ate MVP especifico de execucao real. `mode=real` deve continuar bloqueado.

## Flask

Nunca deixar Flask rodando em foreground ao final da tarefa. Se precisar validar, subir Flask em background, testar endpoints, encerrar o processo iniciado pela tarefa e confirmar que a porta ficou livre.

## Testes

Executar:

```powershell
python -m pytest tests -q
```

## Organização das skills SmartOffers

### Desenvolvimento

Use:

```text
.agents/skills/smartoffers-automation-developer/SKILL.md
```

para implementação, correções, testes, documentação, Git, PR, preflight,
preparacao QA4 mock-first e evidencias sanitizadas. A skill nao autoriza
transporte real.

O Dev possui autonomia para implementar, corrigir, testar e publicar dentro do
escopo recebido. Deve retornar somente ao concluir um goal, plano, marco
operacional ou bloqueio material.

### Gerenciamento da execução

Use `.agents/skills/smartoffers-execution-manager/SKILL.md` para:

- organizar goals;
- montar pacotes completos para o Dev;
- sequenciar entregas;
- revisar evidências e consolidar feedback;
- preparar liberacoes operacionais apenas quando uma fonte superior e o
  contrato atual permitirem; no estado Alpha vigente, transporte real continua
  bloqueado;
- acompanhar planos com múltiplas partes;
- decidir continuidade para o próximo goal.

O Gerente deve delegar várias tarefas relacionadas de uma vez e solicitar
retorno somente ao concluir um goal, plano ou marco operacional.

### Arquitetura

Use `.agents/skills/smartoffers-automation-architect/SKILL.md` somente quando
houver decisão estrutural, novo envelope de risco, produção, mutação real nova,
operação destrutiva, integração externa real, processamento massivo, remoção de
guardrail ou mudança material de política.

O Arquiteto nao executa trabalho rotineiro, nao faz Git como responsabilidade do
papel, nao libera operacao real e nao aprova a propria evidencia.

### Teste e revisao independentes

Para cada goal material, designar um Tester/Reviewer diferente de quem
implementou. O Tester valida aceite, regressao, seguranca, compatibilidade,
evidencia e Git solicitado; nao corrige a propria finding como parte da mesma
aprovacao. Findings de implementacao vao ao Gerente/Dev. Divergencias materiais
de contrato ou risco vao ao Arquiteto.

Researcher e Debugger sao papeis temporarios para investigacao delimitada. Eles
entregam fatos, reproducao e hipoteses, sem autoridade para mudar politica ou
executar fora do pacote.

### Supervisores internos do produto

Os artefatos em `ai/supervisors/*` sao contratos conceituais do produto. Nao sao
agentes do time de desenvolvimento, nao usam ferramentas e nao possuem
autoridade operacional. Em particular, `smartoffers-architect-supervisor` nao e
o Arquiteto definido acima e os dois papeis nao devem ser fundidos.

### Fonte de verdade

Aplicar: instrucoes da plataforma/usuario; este `AGENTS.md`; estado Git e
contratos vigentes; decisoes arquiteturais explicitas; skills. Contrato
historico, evidencia anterior ou skill nunca cria autorizacao real. Em conflito,
preservar a regra mais restritiva e registrar a divergencia no board canonico.

### Precedência

- Implementação: Developer Skill.
- Coordenação, revisão e liberação operacional: Execution Manager Skill.
- Mudança material de arquitetura ou risco: Architect Skill.

Não carregar a skill de Arquitetura para decisões rotineiras já cobertas pelo
Gerente ou Dev. `AGENTS.md` e as autorizações da plataforma permanecem acima
das skills; nenhuma skill amplia sozinha a permissão para execução real.

## Fluxo final recomendado

```text
ARQUITETO
define envelope e direção
        ↓
GERENTE
monta goal completo e delega
        ↓
DEV
implementa + testa + corrige + publica
        ↓
TESTER
valida de forma independente
        ↓
GERENTE
revisa uma vez + libera + consolida
        ↓
PRÓXIMO GOAL
```

O retorno padrão do Dev ao Gerente é:

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
