# Catalog Publication Config Issue

## Sintoma

Publicacao, configuracao ou catalogo aparenta divergencia em relacao a regra esperada da campanha.

## Quando usar

Use quando o problema parece estar em configuracao, Load/Active, versao, atributos de campanha ou regra publicada, mas sem executar operacao real.

## Entidades da ontologia relacionadas

- Campanha: configuracao, jornada e elegibilidade.
- Caracteristica: atributos de campanha e contrato.
- Integracao: catalogo/configuracao como fronteira controlada.
- Auditoria: rastreabilidade de publicacao conceitual.
- Evidencia: `campaign`, `characteristic`, `audit`, `manifest`.

## Hipoteses provaveis

- Configuracao esperada nao foi refletida no contrato.
- Atributo de campanha esta ausente ou divergente.
- Versao ou publicacao conceitual nao corresponde ao cenario.
- Regra de elegibilidade nao esta alinhada com evento ou segmento.
- Evidencia de auditoria/configuracao nao foi planejada.

## Evidencias seguras

- `campaign_attributes`
- `campaign_contract`
- `audit_records`
- `expected_evidence_manifest`

## Perguntas de triagem

- Qual regra de campanha deveria estar ativa?
- O atributo esperado aparece no contrato?
- A divergencia e de configuracao ou de processamento?
- O cenario exige evidencia de catalogo/configuracao?
- Existe risco de operacao destrutiva?

## Proximos passos mock/read-only

- Conferir atributos planejados da campanha.
- Conferir contrato e estado esperado.
- Conferir auditoria conceitual de configuracao quando existir.
- Classificar qualquer acao de publicacao como fora do escopo atual.
- Registrar lacuna para playbook futuro mais detalhado de catalogo.

## Sinais de risco

- Pedido para publicar configuracao.
- Pedido para executar rollback.
- Pedido para alterar catalogo real.
- Pedido para rodar job de loader.

## Limites de seguranca

- Nao publicar configuracao.
- Nao executar rollback.
- Nao alterar catalogo seguro.
- Nao disparar Jenkins ou loader.

## Relacao futura com Evidence Planner

Este playbook deve gerar camadas `campaign`, `characteristic`, `audit` e `integration`, marcando acoes de publicacao como bloqueadas.
