# Characteristic

## Objetivo

Definir caracteristica como atributo configurado, recebido ou calculado que influencia campanha, cliente, evento ou contrato.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `characteristic_name` | Nome funcional do atributo. |
| `characteristic_value` | Valor planejado ou esperado. |
| `campaign_attributes` | Validacao de atributos de campanha. |
| `payload.attributes` | Atributos planejados no payload do cenario. |
| `id_contract` | Contrato conceitual usado para correlacao. |

## Relacoes

- Caracteristicas podem vir do payload, do contrato de campanha ou de configuracao.
- Caracteristicas explicam elegibilidade, segmentacao, oferta, prazo e comunicacao.
- Caracteristicas se relacionam com metricas e auditoria.

## Evidencias esperadas

- `campaign_attributes`: conferir atributos da campanha no contrato.
- Payload planejado com `campaignId`, `customerSegment`, `initialOffer`, `targetOffer`, `deadlineRule` e atributos especificos do evento.
- Manifesto de evidencias quando atributos forem obrigatorios.

## Usos futuros

- Playbooks devem verificar caracteristicas quando a campanha nao aplicar a regra esperada.
- Evidence Planner deve mapear caracteristicas para camada `campaign_attributes`.

## Limites de seguranca

- Nao consultar tabela real.
- Nao versionar dump de caracteristicas.
- Nao usar atributos reais sensiveis em exemplos.
