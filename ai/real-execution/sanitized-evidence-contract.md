# Sanitized Evidence Contract

Este contrato define a evidencia permitida para o gate manual QA4.

## Campos permitidos

- `api_id`
- `method`
- `environment`
- `decision`
- `approval_reference`
- `ticket_reference`
- `correlation_reference`
- `status_code`
- `elapsed_ms`
- `real_call_executed`
- `body_recorded`
- `error`

## Regras de mascaramento

- referencias devem ser curtas e mascaradas;
- erros devem registrar somente classe ou codigo;
- corpo de resposta nunca deve ser gravado;
- request bruto nunca deve ser gravado;
- valores de runtime em memoria nunca devem aparecer no retorno.

## Campos proibidos

- endpoint bruto;
- endereco de rede;
- material de autenticacao;
- credencial;
- cabecalho bruto;
- massa bruta;
- linha;
- conta;
- documento;
- corpo bruto de resposta.

## Invariantes

- `runtime_secrets` nao aparece no retorno;
- `real_call_executed` so fica `true` quando o send retorna resposta;
- erro antes do send mantem `real_call_executed=false`;
- erro apos send deve ser sanitizado;
- logs e evidencia devem ter a mesma superficie sanitizada.
