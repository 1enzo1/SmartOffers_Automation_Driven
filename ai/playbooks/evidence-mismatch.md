# Evidence Mismatch

## Sintoma

Evidencia planejada diverge do resultado esperado, esta ausente no manifesto ou nao fecha a correlacao entre entidades.

## Quando usar

Use quando o problema nao e claramente cliente, campanha, evento ou processamento, mas uma divergencia entre esperado e evidencia.

## Entidades da ontologia relacionadas

- Evidencia: camadas, arquivos esperados e manifesto.
- Cliente: correlacao por identificadores.
- Campanha: contrato, atributos e estado.
- Evento: operacao e rastro.
- Auditoria: explicacao da decisao.

## Hipoteses provaveis

- Cenario foi gerado sem validacao necessaria.
- Manifesto nao inclui a camada esperada.
- Evidencia aponta entidade diferente da esperada.
- Resultado esperado nao esta claro no cenario.
- Existe lacuna entre payload, contrato, auditoria e resumo.

## Evidencias seguras

- `expected_evidence_manifest`
- `customer_discovery`
- `campaign_contract`
- `campaign_attributes`
- `audit_records`
- `received_events`
- `sms_dispatch`
- `kafka_trace`
- `schedule_checkpoint`

## Perguntas de triagem

- Qual evidencia divergiu?
- Qual era o resultado esperado?
- A camada de evidencia foi solicitada no cenario?
- A divergencia e de ausencia, conteudo ou correlacao?
- Existe checkpoint futuro que explique a diferenca?

## Proximos passos mock/read-only

- Conferir manifesto de evidencias esperadas.
- Mapear a evidencia divergente para a entidade da ontologia.
- Conferir se a validacao correspondente foi selecionada.
- Separar erro de planejamento de erro de interpretacao.
- Registrar lacuna para Evidence Planner.

## Sinais de risco

- Pedido para ajustar evidencia manualmente.
- Pedido para buscar dado real para fechar lacuna.
- Evidencia aponta identificador real.
- Resultado esperado nao foi definido antes da validacao.

## Limites de seguranca

- Nao fabricar evidencia.
- Nao consultar sistemas reais.
- Nao alterar cenario salvo para esconder divergencia.
- Nao executar integracao externa.

## Relacao futura com Evidence Planner

Este playbook deve ser entrada direta para o Evidence Planner, gerando checagem de camadas obrigatorias, lacunas e resultado esperado por entidade.
