# Alpha Governance

Snapshot canonico da transicao para a fase Alpha em 2026-08-21. Este documento
registra governanca e estado conhecido; nao altera runtime nem autoriza qualquer
chamada real.

## Baseline imutavel

- repositorio: `SmartOffers_Automation_Driven`;
- branch base evolutiva: `qa/mvp4-integration`;
- PR de integracao pre-alpha: `#17`;
- merge sem alteracao de arvore: `e1263595aa736de3855234b6f9a0379b944fe70e`;
- tag anotada: `v0.0.0-pre-alpha.1`;
- continuacao de governanca: `codex/alpha`.

A tag preserva o estado pre-alpha. Novos trabalhos partem da baseline integrada
e nao reescrevem a tag.

## Estado funcional aceito pelo Owner

- MVP7.8.3B: concluido no recorte DB-only;
- checkpoints DB ACM_CUSTOM, ACM, BDA e BASIC: registrados como `OK` na
  evidencia historica aceita pelo Owner;
- checkpoint API QA4: `NOT_READY`;
- `BASIC_SMOKE_OK=false`;
- `FULL_SMOKE_OK=false`;
- MVP7.8.4: autorizado para preparacao e implementacao mock-first.

Esses registros nao autorizam nova consulta, retry, HTTP, Oracle, Kafka,
Jenkins, subprocesso real ou outra operacao externa. Nenhum valor privado,
endpoint, DSN, SQL, hash, fingerprint, credencial ou response body pertence a
este documento.

## Fontes de verdade

Aplicar a seguinte precedencia:

1. instrucoes da plataforma e do Owner;
2. `AGENTS.md`;
3. estado Git integrado e contratos vigentes;
4. decisoes arquiteturais explicitas;
5. skills e demais documentos de apoio.

`PROJECT_STATUS.md` consolida o historico funcional. `ai/real-execution/*`
define contratos tecnicos, mas nenhum contrato ou token historico cria
autorizacao por si so. Em divergencia material, aplicar o guardrail mais
restritivo, registrar `CONTRACT_CONFLICT` e encaminhar ao Architect.

## Papeis do time de desenvolvimento

| Papel | Responsabilidade |
|---|---|
| Owner | Objetivo e autorizacoes dentro dos limites da plataforma. |
| Architect | Estrutura, politica, risco material e conflitos contratuais. |
| Execution Manager | Goals, cards, sequenciamento, reconciliacao e consolidacao. |
| Developer | Implementacao, testes, documentacao e Git no pacote aprovado. |
| Tester/Reviewer | Validacao independente de aceite, regressao, seguranca, compatibilidade e evidencia. |
| Researcher/Debugger | Investigacao delimitada, fatos e reproducao. |

O Architect nao e Gerente, Dev, executor ou Reviewer da propria decisao. O Dev
nao aprova independentemente a propria entrega. O Gerente nao amplia o envelope.
Conflitos Dev/Tester vao ao Gerente. O encaminhamento ao Architect exige uma
divergencia material de contrato ou risco demonstrada pelos fatos, nao apenas o
rotulo adotado por uma parte da review.

## Supervisores internos do produto

`ai/supervisors/*` contem contratos Markdown conceituais do proprio produto.
Eles nao sao os agentes de desenvolvimento acima, nao usam ferramentas e nao
possuem autoridade operacional. `smartoffers-architect-supervisor` permanece
separado do Architect de desenvolvimento.

## Classificacao vigente

- `SAFE_LOCAL`: trabalho local sem sistema externo;
- `MOCK_ONLY`: simulacao local;
- `QA4_READ_ONLY_FAST_TRACK`: classe contratual, nao autorizacao;
- `QA4_CONTROLLED_MUTATION`: mutacao QA4 bloqueada sem MVP/contrato especifico;
- `PROD_BLOCKED`: producao bloqueada;
- `DESTRUCTIVE_OPERATION`: decisao e autorizacao especificas obrigatorias.

No Alpha atual, Oracle, APIs, Kafka e Jenkins reais permanecem operacional e
contratualmente bloqueados. A existencia de executores manuais dormentes e sua
capacidade tecnica nao cria autorizacao, liberacao ou garantia operacional. O
identificador canonico do checkpoint API documental e
`SMARTOFFERS_API_QA4_TECHNICAL_READ_ONLY_01`.

## Taxonomia de trabalho Alpha

A taxonomia fechada e `TASK_CLASS=MECHANICAL|DEVELOPMENT|DEBUG|RESEARCH|REVIEW`.
Nenhuma outra classe pode ser usada no board ou nos pacotes Alpha.

## Autoridade historica reconciliada

A frase historica "Architect General issues `EXECUTION_APPROVED`" esta
reconciliada e nao representa autoridade vigente. O Architect define o envelope
de risco; qualquer liberacao futura explicita cabe a um papel operacional
autorizado, somente depois que uma fonte superior e o contrato entao vigente a
permitirem. No Alpha atual nao existe essa liberacao.

## Divergencias e reconciliacoes Alpha

### `CONTRACT_CONFLICT-001` - RESOLVIDO

O contrato/executor ACM anterior exigia `BASIC_SMOKE_OK`, enquanto o contrato
API anterior exigia `ACM_DB_CHECKPOINT_OK` e declarava que `BASIC_SMOKE_OK` so
seria consolidado depois da API. Isso formava uma dependencia circular para
uma nova execucao completa.

Decisao Alpha registrada na sincronizacao anterior: nao inferir um bypass a
partir de evidencia historica e manter qualquer nova execucao bloqueada. O card
`ALPHA-MVP784-002` removeu o predecessor da admissao ACM, removeu o predecessor
indefinido das admissoes BDA manual/mock e API, e substituiu status informados
pelo caller por evidencia estruturada, sempre mock-first.

O Tester independente aceitou os 12 criterios no head `983bace`, com
`676 passed`, probes adversariais de referencia opaca e diff checks limpos. O
Execution Manager encerra `CONTRACT_CONFLICT-001` com esse aceite. A resolucao
nao libera transporte real, producao, retry, mutacao, credenciais alternativas
ou qualquer operacao externa.

### `STATE_DIVERGENCE-001` - documentos historicos

README, roadmap e arquitetura registravam MVP7.8.3A.1 como estado corrente,
enquanto o Owner aceitou MVP7.8.3B DB-only. Este snapshot e
`PROJECT_STATUS.md` atualizado prevalecem para a fase Alpha; secoes historicas
continuam como historico, nao como autorizacao.

## Board Alpha

| Prioridade | Goal | TASK_CLASS | Estado | Owner operacional | Saida esperada |
|---|---|---|---|---|---|
| P0 | ALPHA-PR18-FIX-001 | `TASK_CLASS=REVIEW` | `STATE=COMPLETED` | Tester -> Execution Manager | Precisao aceita e PR #18 mergeado em `d3065e5`, sem alterar runtime. |
| P1 | ALPHA-MVP784-002 - DAG canonico para `CONTRACT_CONFLICT-001` | `TASK_CLASS=DEVELOPMENT` | `STATE=COMPLETED` | Dev -> Tester -> Manager | DAG mock-first aceito no head `983bace`; conflito resolvido, operacao real bloqueada. |
| P1 | Preparar API health checkpoint | `TASK_CLASS=RESEARCH` | Bloqueado por readiness externo | Manager | Confirmacao segura do service owner; nenhum endpoint no Git/chat. |
| P1 | MVP7.8.4 Sanity Runner Standard/Variant/Copy | `TASK_CLASS=DEVELOPMENT` | Autorizado para desenvolvimento mock-first | Manager -> Dev -> Tester | Runner deterministico, compatibilidade e suite verde. |
| P2 | Evidence comparison e hardening | `TASK_CLASS=DEVELOPMENT` | Pendente do runner | Manager | Evidencia sanitizada e regras de comparacao. |

## Roteamento do proximo goal

O primeiro card de reconciliacao do MVP7.8.4 esta concluido. O Gerente pode
avancar para o proximo card `TASK_CLASS=DEVELOPMENT` ja autorizado no board,
mantendo execucao local/mock-first. Qualquer alteracao de envelope de risco ou
runtime real retorna ao Architect. Nao usar uma janela QA4 nem solicitar
secrets para essa continuidade.
