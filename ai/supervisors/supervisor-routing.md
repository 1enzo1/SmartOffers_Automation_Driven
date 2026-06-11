# Supervisor Routing

Este contrato define roteamento conceitual entre supervisores SmartOffers.

O roteamento e documental. Ele nao cria agente autonomo, orquestrador, LLM externo, ferramenta, endpoint, automacao ou execucao.

## Supervisores cobertos

- `smartoffers-architect-supervisor`
- `campaign-supervisor`
- `evidence-supervisor`
- `troubleshooting-supervisor`
- `catalog-config-supervisor`
- `adapter-supervisor`
- `safety-supervisor`

## Regras de entrada

| Entrada | Supervisor primario | Supervisores de apoio |
| --- | --- | --- |
| Intencao ampla, cenario novo ou duvida de arquitetura | `smartoffers-architect-supervisor` | `safety-supervisor`, conforme risco |
| Campanha, jornada, oferta, beneficio, atributo ou elegibilidade | `campaign-supervisor` | `evidence-supervisor`, `troubleshooting-supervisor` |
| Evidencia, manifesto, camada ou plano de prova | `evidence-supervisor` | `campaign-supervisor`, `troubleshooting-supervisor`, `safety-supervisor` |
| Sintoma operacional ou divergencia | `troubleshooting-supervisor` | `evidence-supervisor`, `campaign-supervisor`, `adapter-supervisor` |
| Publicacao, configuracao, loader, versao ou rollback | `catalog-config-supervisor` | `campaign-supervisor`, `safety-supervisor` |
| Adapter, `request_plan`, `http_plan`, API mock_only ou mode | `adapter-supervisor` | `catalog-config-supervisor`, `safety-supervisor` |
| Credencial, dado real, host, IP, payload real, execucao real ou producao | `safety-supervisor` | Nenhum antes do bloqueio inicial |

## Escalonamento para Safety

Acionar `safety-supervisor` sempre que houver:

- pedido de `mode=real`;
- Oracle, API, Kafka, Jenkins, rede ou subprocesso real;
- host real, IP, secret, token, credencial ou payload real;
- dado bruto de ambiente;
- mudanca de catalogo seguro;
- alteracao de `execution_status` ou `safe_for_real_execution`;
- risco de producao;
- tentativa de transformar status `blocked` em execucao.

## Saidas do roteamento

- supervisor primario;
- supervisores de apoio;
- fontes documentais relevantes;
- status conceitual de risco;
- limites de seguranca;
- proximo passo mock/read-only.

## Limites

O roteamento nao executa nada. Ele nao substitui testes, nao altera comportamento funcional e nao autoriza integracoes reais.
