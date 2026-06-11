# Evidence Layers

Este arquivo define as camadas conceituais de evidencia que o futuro Evidence Planner podera usar.

As camadas sao referencias operacionais seguras. Elas nao representam consultas executaveis, endpoints reais, payloads reais ou integracoes habilitadas.

## Camadas obrigatorias

### `customer_discovery`

Objetivo: identificar o cliente de forma conceitual e correlacionar sua participacao esperada em uma campanha.

Entidades relacionadas: cliente, campanha, caracteristica, evidencia.

Uso seguro: validar se o cenario possui identificadores mockados, segmento esperado e criterios de elegibilidade descritos.

Status esperado: `mock` ou `read-only`.

### `campaign_contract`

Objetivo: descrever contrato funcional da campanha, regras de entrada, oferta, jornada e saidas esperadas.

Entidades relacionadas: campanha, metrica, auditoria, evidencia.

Uso seguro: comparar o comportamento esperado com o contrato conceitual documentado.

Status esperado: `mock` ou `read-only`.

### `campaign_attributes`

Objetivo: organizar atributos de campanha que influenciam elegibilidade, vigencia, canal, oferta e processamento.

Entidades relacionadas: campanha, caracteristica, processamento, evidencia.

Uso seguro: verificar coerencia entre atributos declarados e sintoma analisado.

Status esperado: `mock` ou `read-only`.

### `received_events`

Objetivo: representar eventos recebidos que deveriam iniciar ou alterar a jornada SmartOffers.

Entidades relacionadas: evento, processamento, integracao, auditoria, evidencia.

Uso seguro: conferir existencia conceitual do evento no cenario e sua relacao com o playbook.

Status esperado: `mock`, `read-only` ou `blocked`.

### `audit_records`

Objetivo: representar registros de auditoria funcional, trilha de decisao e rastreabilidade conceitual.

Entidades relacionadas: auditoria, campanha, evento, processamento, evidencia.

Uso seguro: planejar quais registros sanitizados seriam esperados para explicar a decisao.

Status esperado: `read-only` ou `blocked`.

### `sms_dispatch`

Objetivo: representar evidencias de disparo, bloqueio ou ausencia de envio de mensagem.

Entidades relacionadas: cliente, campanha, integracao, auditoria, evidencia.

Uso seguro: documentar resultado esperado do disparo sem acessar gateway, payload real ou dado sensivel.

Status esperado: `mock`, `read-only` ou `blocked`.

### `kafka_trace`

Objetivo: representar rastreabilidade conceitual de publicacao, consumo ou atraso em fluxo NRT.

Entidades relacionadas: evento, processamento, integracao, auditoria, evidencia.

Uso seguro: planejar quais correlacoes seriam necessarias sem consumir topicos reais.

Status esperado: `blocked` ou `future-controlled`.

### `schedule_checkpoint`

Objetivo: representar checkpoints de scheduling, janela de processamento e atraso operacional.

Entidades relacionadas: processamento, campanha, metrica, auditoria, evidencia.

Uso seguro: documentar checkpoints esperados em modo mock/read-only.

Status esperado: `mock`, `read-only` ou `future-controlled`.

### `expected_evidence_manifest`

Objetivo: consolidar as evidencias esperadas para um sintoma, campanha ou cenario.

Entidades relacionadas: evidencia, campanha, evento, auditoria, processamento.

Uso seguro: montar um manifesto documental do que deve existir, do que esta bloqueado e do que depende de MVP futuro.

Status esperado: `mock` ou `future-controlled`.

## Limites de seguranca

- Nao executar consultas, chamadas HTTP, Kafka, Jenkins, jobs ou subprocessos.
- Nao incluir host real, IP, secret, token, credencial, payload real ou dado bruto de ambiente.
- Nao liberar execucao real por meio de uma camada de evidencia.
- Nao transformar este contrato em schema executavel neste MVP.
