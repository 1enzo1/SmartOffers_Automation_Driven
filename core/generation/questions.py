QUESTIONS = [
    {
        "step": "campanha",
        "title": "Campanha",
        "fields": [
            {
                "name": "campaign_name",
                "label": "Nome da campanha",
                "type": "text",
                "required": True,
                "placeholder": "Squad162 Upsell",
            },
            {
                "name": "campaign_id",
                "label": "Numero/ID da campanha",
                "type": "text",
                "required": True,
                "placeholder": "162",
            },
            {
                "name": "system",
                "label": "Sistema relacionado",
                "type": "text",
                "required": False,
                "placeholder": "SmartOffers",
                "default": "SmartOffers",
            },
            {
                "name": "objective",
                "label": "Regra/objetivo da campanha",
                "type": "textarea",
                "required": True,
                "placeholder": "Bonificar apenas cliente que fez upgrade real de oferta",
            },
        ],
    },
    {
        "step": "cliente",
        "title": "Cliente",
        "fields": [
            {
                "name": "customer_type",
                "label": "Tipo do cliente",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "pos", "label": "Pos-pago"},
                    {"value": "pre", "label": "Pre-pago"},
                    {"value": "controle", "label": "Controle"},
                ],
            },
            {
                "name": "document_type",
                "label": "Documento",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "PF", "label": "PF"},
                    {"value": "PJ", "label": "PJ"},
                ],
            },
            {
                "name": "customer_status",
                "label": "Status inicial da linha",
                "type": "select",
                "required": False,
                "default": "ativo",
                "options": [
                    {"value": "ativo", "label": "Ativo"},
                    {"value": "bloqueado", "label": "Bloqueado"},
                    {"value": "suspenso", "label": "Suspenso"},
                    {"value": "reabilitado", "label": "Reabilitado"},
                ],
            },
        ],
    },
    {
        "step": "evento",
        "title": "Evento",
        "fields": [
            {
                "name": "event_type",
                "label": "Tipo de evento",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "habilitacao", "label": "Habilitacao"},
                    {"value": "alteracao_perfil", "label": "Alteracao de perfil"},
                    {"value": "mailing", "label": "Mailing"},
                    {
                        "value": "recarga",
                        "label": "Recarga",
                        "visible_when": {"customer_type": "pre"},
                    },
                    {"value": "rehab", "label": "Reabilitacao"},
                    {"value": "upsell", "label": "Upgrade / Upsell"},
                    {"value": "downgrade", "label": "Downgrade"},
                ],
            }
        ],
    },
    {
        "step": "contexto",
        "title": "Contexto da regra",
        "fields": [
            {
                "name": "current_offer",
                "label": "Oferta atual",
                "type": "text",
                "required": False,
                "placeholder": "122429157",
                "visible_when": {
                    "event_type": ["alteracao_perfil", "rehab", "upsell", "downgrade"]
                },
            },
            {
                "name": "target_offer",
                "label": "Oferta alvo",
                "type": "text",
                "required": False,
                "placeholder": "104376082",
                "visible_when": {
                    "event_type": ["alteracao_perfil", "rehab", "upsell", "downgrade"]
                },
            },
            {
                "name": "mailing_source",
                "label": "Origem do mailing",
                "type": "select",
                "required": False,
                "default": "upload_manual",
                "visible_when": {"event_type": "mailing"},
                "options": [
                    {"value": "upload_manual", "label": "Upload manual"},
                    {"value": "base_segmentada", "label": "Base segmentada"},
                    {"value": "lista_controle", "label": "Lista de controle"},
                ],
            },
            {
                "name": "recharge_scenario",
                "label": "Contexto de recarga",
                "type": "select",
                "required": False,
                "default": "none",
                "visible_when": {"customer_type": "pre"},
                "options": [
                    {"value": "none", "label": "Sem recarga no cenario"},
                    {"value": "with_recharge", "label": "Com recarga valida"},
                    {"value": "insufficient_recharge", "label": "Recarga insuficiente"},
                    {"value": "without_recharge", "label": "Cliente sem recarga"},
                ],
            },
            {
                "name": "recharge_amount",
                "label": "Valor da recarga",
                "type": "text",
                "required": False,
                "placeholder": "20.00",
                "visible_when": {
                    "customer_type": "pre",
                    "recharge_scenario": ["with_recharge", "insufficient_recharge"],
                },
            },
            {
                "name": "recharge_channel",
                "label": "Canal da recarga",
                "type": "select",
                "required": False,
                "default": "POS",
                "visible_when": {
                    "customer_type": "pre",
                    "recharge_scenario": ["with_recharge", "insufficient_recharge"],
                },
                "options": [
                    {"value": "POS", "label": "POS"},
                    {"value": "APP", "label": "App"},
                    {"value": "USSD", "label": "USSD"},
                ],
            },
        ],
    },
    {
        "step": "validacoes",
        "title": "Validacoes",
        "fields": [
            {
                "name": "validations",
                "label": "Validacoes necessarias",
                "type": "checkbox_group",
                "required": True,
                "options": [
                    {"value": "database", "label": "Banco de dados"},
                    {"value": "api", "label": "API"},
                    {"value": "campaign_attributes", "label": "Campaign Attributes"},
                    {"value": "audit", "label": "Auditoria"},
                    {"value": "sms", "label": "SMS/mensagem"},
                    {"value": "received_events", "label": "Eventos recebidos"},
                    {"value": "kafka", "label": "Kafka"},
                    {"value": "schedule", "label": "Agendamento futuro"},
                    {"value": "evidence", "label": "Evidencias esperadas"},
                ],
            }
        ],
    },
    {
        "step": "prazo",
        "title": "Prazo",
        "fields": [
            {
                "name": "deadline_rule",
                "label": "Regra de prazo",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "d0", "label": "D+0"},
                    {"value": "d1", "label": "D+1"},
                    {"value": "d3", "label": "D+3"},
                    {"value": "d5", "label": "D+5"},
                    {"value": "d7", "label": "D+7"},
                    {"value": "future", "label": "Agendamento futuro"},
                ],
            }
        ],
    },
]


def get_questions():
    return QUESTIONS
