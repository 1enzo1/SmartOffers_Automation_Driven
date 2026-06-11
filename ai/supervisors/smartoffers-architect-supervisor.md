# SmartOffers Architect Supervisor

## Objetivo

Coordenar a leitura conceitual de uma intencao SmartOffers e decidir quais supervisores devem atuar.

Este supervisor organiza o fluxo entre campanha, evidencia, troubleshooting, catalogo, adapter e seguranca sem executar acao funcional.

## Entradas esperadas

- Descricao de objetivo, sintoma, campanha ou cenario.
- Referencias a entidades da ontologia, como cliente, campanha, evento, processamento, integracao e evidencia.
- Playbook relacionado, quando ja identificado.
- Necessidade declarada de plano de evidencia, triagem ou classificacao de risco.

## Saidas esperadas

- Roteamento conceitual para um ou mais supervisores.
- Perguntas de esclarecimento seguras.
- Lista de fontes documentais relevantes.
- Indicacao de bloqueios ou necessidade de acionar `safety-supervisor`.
- Resumo de escopo para MVP futuro, quando aplicavel.

## Fontes documentais permitidas

- `ai/knowledge/ontology.md`
- `ai/playbooks/README.md`
- `ai/evidence/evidence-planner-contract.md`
- `ai/evidence/playbook-mapping.md`
- `ai/evidence/evidence-statuses.md`
- `docs/SUPERVISORS.md`

## Responsabilidades

- Identificar a intencao principal.
- Selecionar supervisor primario e supervisores de apoio.
- Evitar sobreposicao de responsabilidades.
- Manter o fluxo local-first e mock-first.
- Registrar quando a solicitacao pertence a MVP futuro.

## Quando acionar outro supervisor

- Acionar `campaign-supervisor` para regras, jornada, atributos e elegibilidade.
- Acionar `evidence-supervisor` para plano de evidencia ou manifesto esperado.
- Acionar `troubleshooting-supervisor` para sintomas operacionais.
- Acionar `catalog-config-supervisor` para publicacao, configuracao ou catalogo.
- Acionar `adapter-supervisor` para dry-run, adapter-run mockado ou `request_plan`.
- Acionar `safety-supervisor` para qualquer risco, execucao real, dado sensivel ou integracao externa.

## Relacao com Evidence Planner

Direciona o uso do Evidence Planner quando a intencao exigir evidencias esperadas, camadas de prova ou classificacao de status `mock`, `read-only`, `blocked` ou `future-controlled`.

## Limites de seguranca

- Nao decide execucao real.
- Nao chama ferramentas.
- Nao acessa ambiente.
- Nao altera catalogo, JSON de cenario, dry-run, adapter-run ou `request_plan`.
- Nao cria agente autonomo nem LLM externo.

## O que nunca fazer automaticamente

- Habilitar `mode=real`.
- Chamar API, Oracle, Kafka, Jenkins, rede ou subprocesso.
- Gerar credencial, token, secret ou payload real.
- Alterar comportamento funcional.
- Prosseguir quando `safety-supervisor` indicar bloqueio.
