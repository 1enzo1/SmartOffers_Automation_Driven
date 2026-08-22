# Supervisors

## Objetivo

Supervisores sao contratos de dominio do produto. Eles descrevem como o SmartOffers_Automation_Driven deve entender campanhas, evidencias, troubleshooting, catalogo, adapters e risco.

No MVP7.6.1, supervisores sao Markdown. Eles nao executam LLM externo, nao chamam sistemas reais e nao alteram comportamento do app.

Eles nao sao os agentes do fluxo de desenvolvimento. Architect, Execution
Manager, Developer, Tester/Reviewer e Researcher/Debugger sao papeis de trabalho
definidos em `AGENTS.md`; os contratos abaixo continuam sem ferramentas,
autonomia, poder de aprovacao ou autoridade operacional.

## Supervisores previstos

### smartoffers-architect-supervisor

Responsavel por receber uma intencao de dominio e indicar conceitualmente quais
supervisores ou skills do produto seriam relevantes. Nao e o Architect de
desenvolvimento e os dois papeis nao devem ser fundidos.

Exemplos:

- gerar teste para campanha de recarga;
- investigar cliente sem SMS;
- avaliar tentativa de executar API real.

### campaign-supervisor

Responsavel por interpretar campanha, jornada, estados, gatilhos, SMS, metricas e caracteristicas.

### evidence-supervisor

Responsavel por transformar cenario em plano de evidencias esperado, ainda sem consultar Oracle real.

### troubleshooting-supervisor

Responsavel por transformar sintomas operacionais em hipoteses, evidencias seguras e proximos passos.

Sintomas previstos:

- cliente nao entrou na campanha;
- SMS nao saiu;
- evento nao processou;
- callback Kafka nao refletiu;
- beneficio nao atualizou;
- campanha travou em estado;
- fila ou backlog NRT.

### catalog-config-supervisor

Responsavel por entender publicacao, Load/Active, configuration loader, versao, rollback e risco de catalogo.

### adapter-supervisor

Responsavel por decidir se uma unidade de trabalho e dry-run, adapter-run mockado, `http_plan`, blocked ou futura execucao real opt-in.

### safety-supervisor

Responsavel por classificar risco e bloquear operacoes fora da politica.

Categorias vigentes:

- `SAFE_LOCAL`
- `MOCK_ONLY`
- `QA4_READ_ONLY_FAST_TRACK`
- `QA4_CONTROLLED_MUTATION`
- `PROD_BLOCKED`
- `DESTRUCTIVE_OPERATION`

## Skills previstas

- `campaign-analysis`
- `evidence-planning`
- `troubleshooting`
- `sql-evidence`
- `api-contract-analysis`
- `request-plan-analysis`
- `adapter-execution-planning`
- `catalog-config-analysis`
- `kafka-nrt-analysis`
- `bko-analysis`
- `risk-classification`

## Regra de seguranca

Nenhum supervisor ou skill pode habilitar execucao real por si so. Qualquer acao real exige MVP especifico, opt-in, ambiente permitido, policy explicita, testes e bloqueio de producao.

No estado Alpha atual, chamadas reais a Oracle, APIs, Kafka e Jenkins permanecem
bloqueadas. Ver `ALPHA_GOVERNANCE.md`.
