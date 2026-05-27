BASE_EXECUTION_BLOCK = [
    {
        "action": "Preparar massa de cliente",
        "details": (
            "Gerar MSISDN, account e externalId para cliente "
            "{customer_label}/{document_type} com status {customer_status}."
        ),
        "expected_result": "Dados obrigatorios disponiveis para montar o payload.",
    },
    {
        "action": "Montar payload SmartOffers",
        "details": "Usar operation {operation}, evento {event_label} e prazo {deadline_label}.",
        "expected_result": "Payload JSON preenchido com campanha, cliente, oferta, prazo e correlacao.",
    },
]

PREPAID_RECHARGE_CONTEXT_BLOCK = [
    {
        "action": "Configurar contexto de recarga pre-paga",
        "details": "Preparar cenario de recarga '{recharge_scenario}' no canal {recharge_channel}.",
        "expected_result": "Massa pre-paga contem contexto de recarga esperado para a regra da campanha.",
    },
    {
        "action": "Aplicar valor de recarga de referencia",
        "details": "Usar valor {recharge_amount} apenas como dado planejado, sem chamar API real.",
        "expected_result": "Payload e evidencias esperadas indicam o valor de recarga planejado.",
    },
]

EVENT_EXECUTION_BLOCKS = {
    "habilitacao": [
        {
            "action": "Simular habilitacao do cliente",
            "details": "Criar entrada de habilitacao para campanha {campaign_id} no sistema {system}.",
            "expected_result": "Cliente fica elegivel para primeira avaliacao da campanha.",
        },
        {
            "action": "Confirmar vinculo inicial da campanha",
            "details": "Usar oferta base {initial_offer} como oferta inicial e alvo.",
            "expected_result": "Contrato da campanha nasce com atributos minimos esperados.",
        },
    ],
    "alteracao_perfil": [
        {
            "action": "Preparar alteracao de perfil",
            "details": "Partir da oferta {initial_offer} e alterar perfil para oferta alvo {target_offer}.",
            "expected_result": "Payload representa mudanca de perfil com dados de antes e depois.",
        },
        {
            "action": "Reprocessar elegibilidade apos alteracao",
            "details": "Validar que a campanha {campaign_id} recalcula atributos sem duplicar contrato.",
            "expected_result": "Cliente permanece na regra correta para o novo perfil.",
        },
    ],
    "mailing": [
        {
            "action": "Preparar arquivo/lista de mailing",
            "details": "Usar origem {mailing_source} e chave MAIL_{campaign_id}_{{msisdn}}.",
            "expected_result": "Cliente disponivel para importacao de mailing.",
        },
        {
            "action": "Validar campos minimos do mailing",
            "details": "Conferir campanha, MSISDN, documento, segmentacao e externalId planejados.",
            "expected_result": "Linha do mailing tem dados suficientes para correlacao posterior.",
        },
        {
            "action": "Processar mailing sem integracao real",
            "details": "Gerar plano de request e resultado esperado para processMailing.",
            "expected_result": "Plano indica cliente importado e elegivel pelo mailing.",
        },
    ],
    "recarga": [
        {
            "action": "Preparar evento de recarga",
            "details": "Montar recarga de {recharge_amount} no canal {recharge_channel} para cliente pre-pago.",
            "expected_result": "Payload contem valor, canal e correlacao da recarga.",
        },
        {
            "action": "Avaliar regra de campanha por recarga",
            "details": "Conferir se valor planejado atende o objetivo: {objective}.",
            "expected_result": "Regra de entrada da campanha fica documentada sem chamada externa.",
        },
        {
            "action": "Planejar mensagem de bonus",
            "details": "Registrar mensagem esperada somente se campanha exigir comunicacao.",
            "expected_result": "Evidencia esperada deixa claro se SMS/mensagem deve existir.",
        },
    ],
    "rehab": [
        {
            "action": "Preparar cliente para reabilitacao",
            "details": "Usar oferta {initial_offer} e status anterior que permita reabilitacao.",
            "expected_result": "Cliente tem historico suficiente para provar retorno ao estado ativo.",
        },
        {
            "action": "Processar reabilitacao sem troca de oferta",
            "details": "Manter oferta alvo {target_offer} e validar campanha {campaign_id}.",
            "expected_result": "Reabilitacao nao gera upgrade ou downgrade indevido.",
        },
    ],
    "upsell": [
        {
            "action": "Preparar upgrade de oferta",
            "details": "Partir da oferta {initial_offer} para oferta de maior rank {target_offer}.",
            "expected_result": "Payload diferencia oferta atual e oferta alvo.",
        },
        {
            "action": "Aplicar regra de bonificacao por upgrade",
            "details": "Documentar que a bonificacao so e esperada quando o rank aumenta.",
            "expected_result": "Cenario prova upgrade real antes de validar bonus.",
        },
    ],
    "downgrade": [
        {
            "action": "Preparar downgrade de oferta",
            "details": "Partir da oferta {initial_offer} para oferta de menor rank {target_offer}.",
            "expected_result": "Payload diferencia oferta atual e oferta alvo.",
        },
        {
            "action": "Bloquear bonificacao indevida",
            "details": "Documentar que downgrade nao deve acionar bonus de upgrade.",
            "expected_result": "Cenario prova ausencia de bonificacao indevida.",
        },
    ],
}

SCHEDULE_EXECUTION_BLOCK = [
    {
        "action": "Planejar checkpoint de agendamento",
        "details": "Prazo {deadline_label} exige consulta apos a data planejada antes de concluir o teste.",
        "expected_result": "Cenario contem marco de validacao futuro sem executar agendamento real.",
    }
]

FINAL_EXECUTION_BLOCK = [
    {
        "action": "Registrar evidencias esperadas",
        "details": "Salvar request, response simulada, consultas planejadas e resumo de analise.",
        "expected_result": "Pacote de evidencias pronto para execucao manual ou futura automacao.",
    }
]

VALIDATION_BLOCKS = {
    "api": [
        {
            "validation": "Validar contrato da API",
            "details": "Conferir operation, extEventId, eventType, correlacao e body esperado.",
            "expected_result": "Payload seria aceito pela API SmartOffers sem erro funcional.",
        }
    ],
    "database": [
        {
            "validation": "Validar discovery do cliente",
            "details": "Consultar CUST_DISCOVERY pelo externalId planejado.",
            "expected_result": "Cliente encontrado com identificadores coerentes.",
        },
        {
            "validation": "Validar contrato da campanha",
            "details": "Consultar CUST_CAMPAIGNS por id_customer e campanha {campaign_id}.",
            "expected_result": "Contrato aponta para a campanha e estado esperado do evento.",
        },
    ],
    "campaign_attributes": [
        {
            "validation": "Validar Campaign Attributes obrigatorios",
            "details": "Conferir campanha, oferta inicial, oferta alvo, prazo e segmento.",
            "expected_result": "Atributos refletem o payload planejado.",
        },
        {
            "validation": "Validar atributos especificos do evento",
            "details": "Conferir atributos esperados para {event_label}, incluindo recarga ou mailing quando aplicavel.",
            "expected_result": "Atributos especificos do evento ficam rastreaveis.",
        },
    ],
    "audit": [
        {
            "validation": "Validar auditoria",
            "details": "Consultar ACM_AUDIT_RECORDS por customerId/contractId e evento {event_type}.",
            "expected_result": "Evento auditado com status e timestamps coerentes.",
        }
    ],
    "sms": [
        {
            "validation": "Validar SMS/mensagem",
            "details": "Conferir fila/log de mensagem para MSISDN e campanha {campaign_id}.",
            "expected_result": "Mensagem enviada apenas quando a regra da campanha exigir.",
        }
    ],
    "received_events": [
        {
            "validation": "Validar eventos recebidos",
            "details": "Consultar historico de eventos por externalId e correlacao.",
            "expected_result": "Evento recebido e correlacionado com a campanha correta.",
        }
    ],
    "kafka": [
        {
            "validation": "Validar rastreio Kafka",
            "details": "Pesquisar chave do evento nos topicos SmartOffers planejados.",
            "expected_result": "Mensagem publicada sem duplicidade ou erro de schema.",
        }
    ],
    "schedule": [
        {
            "validation": "Validar agendamento futuro",
            "details": "Checar se o prazo {deadline_label} gerou checkpoint futuro e data esperada.",
            "expected_result": "Cenario so e considerado concluido apos o checkpoint agendado.",
        }
    ],
    "evidence": [
        {
            "validation": "Validar evidencias esperadas",
            "details": "Conferir manifest com payload, resposta, consultas, mensagens e resumo.",
            "expected_result": "Todas as evidencias necessarias para auditoria do teste estao previstas.",
        }
    ],
}
