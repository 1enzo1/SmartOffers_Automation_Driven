# Project Status

Registro de andamento, decisoes e proximos passos do SmartOffers Automation Driven.

## Estado atual

- Branch base atual: `qa/mvp4-integration`
- MVP atual concluido: MVP7.6
- PR do MVP7.6: `#12`
- Merge commit do MVP7.6: `5c0566ff3ad32cb18480c714dd703ce78f10b8eb`
- Execucao real: bloqueada
- Catalogo de APIs: sanitizado e versionado em `core/api_catalog/catalog.json`
- Dados brutos de ambiente/API: nao versionados

## MVPs concluidos

| MVP | Status | Resumo |
| --- | --- | --- |
| MVP1 | Concluido | Gerador base de cenarios |
| MVP2 | Concluido | Templates e perguntas condicionais |
| MVP3 | Concluido | Dry-run mockado |
| MVP4 / MVP4.2 | Concluido | UI principal e ajustes visuais |
| MVP5 | Concluido | Exportacao QA/DET em JSON, DOCX e XLSX |
| MVP6 | Concluido | Biblioteca de Templates SmartOffers |
| MVP6.5 | Concluido | Refactor Foundation |
| MVP7 | Concluido | Adapters Foundation |
| MVP7.5 | Concluido | Catalogo seguro de APIs |
| MVP7.6 | Concluido | SmartOffersAdapter config-driven mockado |

## MVP7.6

O MVP7.6 adicionou planejamento mockado para o SmartOffersAdapter usando o catalogo seguro do MVP7.5.

Entregas:

- policy separada para APIs `mock_only`;
- 10 APIs SmartOffers liberadas somente para planejamento mockado;
- `request_plan` deterministico a partir do catalogo;
- resolucao por `api_id` explicito;
- fallback por `event_type` para steps `smartoffers.http_plan` gerados pelo sistema;
- bloqueio controlado para API fora da policy;
- bloqueio controlado para `api_id` inexistente;
- agregacao de adapter-run tratando `blocked` como status nao-passing;
- `mode=real` ainda bloqueado;
- `smartoffers.execution` preservado como execucao fake normal;
- `smartoffers.http_plan` restrito a planejamento de API.

Arquivos centrais do MVP7.6:

- `core/api_catalog/policy.py`
- `core/adapters/fake.py`
- `core/execution/service.py`
- `tests/test_adapters.py`

## APIs mock_only do MVP7.6

Estas APIs continuam com `execution_status=blocked` e `safe_for_real_execution=false` no catalogo. A policy permite apenas montar plano mockado.

```txt
post-ativacao-de-campanha-por-api-2e656ee31c
post-consulta-de-saldo-f3317b27b3
post-evento-de-recarga-6954ef3458
post-evento-vivo-turbo-e124494049
post-o-vivo-next-troca-de-oferta-fedbfb981e
post-retorno-la-xml-e73a7721f4
post-sincronismo-e8537bd912
post-transicao-de-estado-de-servico-aceite-3751798e76
post-vivo-next-habilitacao-de-cliente-ade0841563
post-vivo-next-habilitacao-de-linha-a79ab2e31c
```

## Mapeamentos default por event_type

Steps `smartoffers.http_plan` sem `api_id` podem resolver um plano seguro por `event_type`, desde que o destino esteja na policy `mock_only`.

| event_type | api_id |
| --- | --- |
| `alteracao_perfil` | `post-o-vivo-next-troca-de-oferta-fedbfb981e` |
| `ativacao` | `post-ativacao-de-campanha-por-api-2e656ee31c` |
| `campanha` | `post-ativacao-de-campanha-por-api-2e656ee31c` |
| `downgrade` | `post-o-vivo-next-troca-de-oferta-fedbfb981e` |
| `habilitacao` | `post-vivo-next-habilitacao-de-cliente-ade0841563` |
| `mailing` | `post-ativacao-de-campanha-por-api-2e656ee31c` |
| `recarga` | `post-evento-de-recarga-6954ef3458` |
| `rehab` | `post-sincronismo-e8537bd912` |
| `saldo` | `post-consulta-de-saldo-f3317b27b3` |
| `upsell` | `post-ativacao-de-campanha-por-api-2e656ee31c` |
| `vivo_turbo` | `post-evento-vivo-turbo-e124494049` |

## Decisoes de seguranca

- O catalogo versionado deve permanecer sanitizado.
- `catalog.json` nao deve ser alterado para liberar execucao real no MVP7.6.
- `execution_status` permanece `blocked` para as APIs catalogadas.
- `safe_for_real_execution` permanece `false` para as APIs catalogadas.
- `request_plan` usa placeholders de host, nao hosts reais.
- `mode=real` permanece bloqueado no endpoint de adapter-run.
- Fluxos mockados nao devem chamar rede, Oracle, Kafka, Jenkins nem subprocessos reais.

## Fluxo recomendado de desenvolvimento

1. Criar branch a partir de `qa/mvp4-integration`.
2. Implementar apenas o escopo do MVP atual.
3. Rodar `python -m pytest tests -q`.
4. Quando necessario, fazer smoke Flask em background com cleanup.
5. Confirmar porta livre ao final do smoke.
6. Confirmar `git status` limpo.
7. Abrir PR draft.
8. Resolver reviews sem expandir escopo.
9. Marcar Ready for review apenas sem threads abertas.
10. Mergear na branch base correta.

## Proximos MVPs

### MVP7.6.1 - Codex SmartOffers Guardrails

Objetivo: reforcar instrucoes, skills e revisao de escopo para manter o desenvolvimento dentro das regras do projeto.

Possiveis entregas:

- atualizar `.agents/skills/smartoffers-automation-architect/SKILL.md`;
- criar uma skill de safety/scope review, se fizer sentido;
- classificar acoes por risco;
- registrar roadmap;
- impedir expansao de PR sem confirmacao.

### MVP7.6.5 - AI Supervisors Foundation

Objetivo: criar estrutura inicial de agentes e skills do produto, ainda sem LLM externo e sem integracoes reais.

Estrutura prevista:

```txt
ai/
  architects/
  agents/
  skills/
  knowledge/
  playbooks/
  safety/
```

### MVP7.7 - Primeira chamada real opt-in em QA4

Objetivo: permitir a primeira chamada real controlada em QA4, somente com opt-in e guardrails.

Condicoes esperadas:

```txt
mode=real
environment=QA4
REAL_EXECUTION_ENABLED=true
API explicitamente liberada
timeout configurado
logs sanitizados
producao bloqueada
```

### MVP8 - Runner distribuido / filas

Objetivo: evoluir execucao para modelo assincrono/controlado, com fila e acompanhamento de status.

### MVP9 - IA auxiliar local-first

Objetivo: incorporar IA auxiliar com uso controlado, apoiada por knowledge base, playbooks e supervisores.

### MVP10 - Frontend moderno

Objetivo: avaliar uma UI mais robusta somente quando o backend estiver maduro o suficiente.

## Documentos futuros

Quando o roadmap pedir mais detalhe, criar:

- `ARCHITECTURE.md` para adapters, catalogo, generation, simulation, exports e execution service;
- `SECURITY_MODEL.md` para regras de execucao real, dados sensiveis, `mode=real`, QA4 e bloqueio de producao.
