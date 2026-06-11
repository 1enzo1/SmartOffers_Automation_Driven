# SmartOffers Ontology

## Objetivo

Definir o vocabulario base do dominio SmartOffers para alinhar geracao de cenarios, playbooks operacionais, planejamento de evidencia e classificacao futura de risco.

Esta ontologia e conceitual. Ela nao executa nada, nao define schema obrigatorio para JSON de cenario e nao altera comportamento do produto.

## Entidades principais

| Entidade | Papel |
| --- | --- |
| Cliente | Pessoa ou linha avaliada pelo fluxo SmartOffers. |
| Campanha | Configuracao de negocio que define elegibilidade, jornada, oferta e resultado esperado. |
| Evento | Sinal de entrada que dispara avaliacao, mudanca de estado ou validacao. |
| Metrica | Dado calculado ou observado para validar regra ou resultado de campanha. |
| Caracteristica | Atributo configurado ou observado em cliente, campanha ou contrato. |
| Auditoria | Registro de rastreabilidade de API, processo, decisao ou mensagem. |
| Processamento | Caminho operacional que consome eventos, agenda acoes e atualiza estados. |
| Integracao | Fronteira com SmartOffers API, ACM Query, Kafka, BKO, SmartGateway ou Jenkins. |
| Evidencia | Artefato esperado para provar que um cenario foi planejado, simulado ou validado. |

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `domain_entity` | Entidade principal usada por playbooks, supervisores e Evidence Planner. |
| `relationship` | Vinculo conceitual entre cliente, campanha, evento, processamento e evidencia. |
| `evidence_layer` | Camada futura de prova planejada, sem execucao real. |
| `risk_boundary` | Limite usado para manter integracoes reais bloqueadas. |
| `mock_only` | Estado atual de planejamento e simulacao local. |

## Relacoes

- Cliente participa de uma campanha por contrato, identificadores e estado.
- Campanha define quais eventos, caracteristicas, metricas e evidencias sao relevantes.
- Evento aciona processamento e pode gerar auditoria, metrica, SMS, callback ou mudanca de estado.
- Processamento produz checkpoints e sinais para troubleshooting.
- Integracoes sao tratadas como fronteiras conceituais; no estado atual, permanecem mockadas ou bloqueadas.
- Evidencia consolida payload planejado, plano de API, consultas conceituais, auditorias e manifestos.

## Nomenclatura segura

Usar nomes conceituais e placeholders, nunca dados reais:

- `external_id`, `customer_id`, `account`, `msisdn`
- `campaign_id`, `campaign_name`, `id_contract`
- `event_type`, `ext_event_id`, `external_uid`
- `api_id`, `request_plan`, `http_plan`
- `SAFE_READ`, `MOCK_ONLY`, `PROD_BLOCKED`

## Evidencias esperadas

A ontologia deve orientar evidencias como:

- payload planejado;
- resposta mockada;
- resumo de execucao;
- validacao de cliente;
- contrato de campanha;
- atributos de campanha;
- auditoria;
- SMS ou mensagem;
- eventos recebidos;
- Kafka trace conceitual;
- checkpoint de agendamento;
- manifesto final.

## Usos futuros

- MVP7.6.3: converter sintomas em playbooks.
- MVP7.6.4: converter cenario em plano de evidencia.
- MVP7.6.5: orientar supervisores de dominio.
- MVP7.6.6: alimentar analise deterministica de cenario.
- MVP7.6.7: classificar risco antes de adapters reais futuros.

## Limites de seguranca

- Nao habilita `mode=real`.
- Nao consulta Oracle, APIs, Kafka ou Jenkins.
- Nao altera catalogo seguro.
- Nao cria contrato executavel.
- Nao substitui testes automatizados.
