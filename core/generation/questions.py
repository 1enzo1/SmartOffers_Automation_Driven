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
                "label": "Objetivo",
                "type": "textarea",
                "required": True,
                "placeholder": "Validar bonificacao apenas para upgrade",
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
                    {"value": "rehab", "label": "Reabilitacao"},
                    {"value": "upsell", "label": "Upgrade / Upsell"},
                    {"value": "downgrade", "label": "Downgrade"},
                ],
            }
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
                    {"value": "kafka", "label": "Kafka"},
                    {"value": "sms", "label": "SMS"},
                    {"value": "audit", "label": "Auditoria"},
                    {"value": "campaign_attributes", "label": "Campaign Attributes"},
                    {"value": "received_events", "label": "Eventos recebidos"},
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
                    {"value": "future", "label": "Agendamento futuro"},
                ],
            }
        ],
    },
]


def get_questions():
    return QUESTIONS
