# Roadmap

## Estado atual

O SmartOffers_Automation_Driven esta em MVP7.6 concluido na branch evolutiva `qa/mvp4-integration`. A branch tem nome historico, mas representa a linha atual do produto.

Execucao real permanece bloqueada por padrao.

## Direcao

O produto deve evoluir de gerador/simulador de testes para laboratorio seguro de automacao SmartOffers/ACM, com conhecimento de dominio, evidencias planejadas, classificacao de risco e adapters preparados para execucao real controlada no futuro.

## Sequencia 7.6.x

### MVP7.6.1 - Guardrails e alinhamento da linha evolutiva

Registrar direcao de produto, branch base, seguranca, limites de escopo, documentacao de arquitetura e estrutura Markdown inicial para `ai/`.

Nao altera comportamento funcional.

### MVP7.6.2 - SmartOffers Ontology

Criar vocabulario interno do produto para cliente, campanha, evento, metricas, caracteristicas, auditoria, processamento, NRT, Kafka, BKO, SmartGateway e ACM Query.

### MVP7.6.3 - Operational Playbooks

Criar playbooks para sintomas operacionais, como cliente nao entrou em campanha, SMS nao enviado, evento nao processado, callback nao refletiu, beneficio nao atualizou e publicacao de catalogo.

### MVP7.6.4 - Evidence Planner Foundation

Preparar plano deterministico de evidencias por camada, sem consultar Oracle real. O plano deve orientar quais leituras seguras seriam necessarias em fase futura.

### MVP7.6.5 - AI Supervisors Foundation

Criar supervisores do produto como contratos de dominio, ainda sem LLM externo e sem integracoes reais.

### MVP7.6.6 - Scenario Intelligence Layer

Adicionar analise deterministica de cenario com dominio, fluxo principal, camadas de evidencia esperadas, risco e supervisores sugeridos.

### MVP7.6.7 - Adapter Risk Classifier

Classificar risco antes de qualquer adapter-run real futuro. A classificacao deve bloquear producao, mutacoes e operacoes destrutivas.

## MVP7.7 - Primeira chamada real opt-in em QA4

MVP7.7 so deve iniciar depois da sequencia 7.6.x.

Condicoes minimas:

- `REAL_EXECUTION_ENABLED=true`;
- `environment=QA4`;
- `mode=real`;
- API explicitamente liberada;
- policy de allow/deny;
- timeout obrigatorio;
- logs sanitizados;
- payload revisavel;
- producao bloqueada;
- testes cobrindo allow e deny.

## MVPs posteriores

MVP8 deve tratar runner controlado com fila/status.

MVP9 deve tratar IA auxiliar local-first com governanca.

MVP10 deve avaliar frontend moderno apenas quando o backend estiver maduro.
