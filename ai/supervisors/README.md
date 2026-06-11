# Supervisors

Supervisores representam papeis de dominio do produto. Eles devem orientar interpretacao, planejamento, evidencias, troubleshooting e risco.

No MVP7.6.1, esta pasta e apenas contrato Markdown.

## Supervisores previstos

- `smartoffers-architect-supervisor`
- `campaign-supervisor`
- `evidence-supervisor`
- `troubleshooting-supervisor`
- `catalog-config-supervisor`
- `adapter-supervisor`
- `safety-supervisor`

## Limites

Supervisores nao chamam Oracle, APIs, Kafka, Jenkins, rede ou subprocessos. Eles tambem nao habilitam `mode=real`.
