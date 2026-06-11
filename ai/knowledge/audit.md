# Audit

## Objetivo

Definir auditoria como conjunto de rastros que permite entender o que foi planejado, processado, aceito, bloqueado ou simulado.

## Termos principais

| Termo | Uso conceitual |
| --- | --- |
| `audit_records` | Evidencia planejada de auditoria funcional. |
| `ACM_AUDIT_RECORDS` | Referencia conceitual de tabela de auditoria. |
| `ACM_HTTP_AUDIT` | Referencia conceitual para auditoria HTTP. |
| `ACM_WS_RQSTS_AUDIT` | Referencia conceitual para auditoria WS. |
| `correlation_id` | Chave planejada para correlacao de rastros. |

## Relacoes

- Auditoria conecta cliente, campanha, evento, integracao e processamento.
- Auditoria pode explicar falha de API, ausencia de evento, SMS nao enviado ou callback nao refletido.
- Auditoria deve ser lida como evidencia, nao como acao de execucao.

## Evidencias esperadas

- `audit_records`: registros conceituais por cliente e contrato.
- `api_contract`: plano de request quando houver validacao de API.
- Logs mockados de dry-run e adapter-run.
- Manifesto final em `expected_evidence_manifest`.

## Usos futuros

- Playbooks devem usar auditoria para ordenar hipoteses.
- Evidence Planner deve gerar camada `audit` quando o cenario incluir validacao de auditoria.

## Limites de seguranca

- Nao consultar auditoria real.
- Nao expor URL, host, IP, token, bearer, cookie ou payload real.
- Nao transformar auditoria em permissao para execucao real.
