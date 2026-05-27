CUSTOMER_LABELS = {
    "pos": "Pos-pago",
    "pre": "Pre-pago",
    "controle": "Controle",
}

DOCUMENT_LABELS = {
    "PF": "PF",
    "PJ": "PJ",
}

EVENT_LABELS = {
    "habilitacao": "Habilitacao",
    "alteracao_perfil": "Alteracao de perfil",
    "mailing": "Mailing",
    "recarga": "Recarga",
    "rehab": "Reabilitacao",
    "upsell": "Upgrade / Upsell",
    "downgrade": "Downgrade",
}

EVENT_ALIASES = {
    "upgrade": "upsell",
    "upsell": "upsell",
    "downgrade": "downgrade",
    "rehab": "rehab",
    "reabilitacao": "rehab",
    "mailing": "mailing",
    "recarga": "recarga",
    "recharge": "recarga",
    "habilitacao": "habilitacao",
    "alteracao_perfil": "alteracao_perfil",
    "alteracao_de_perfil": "alteracao_perfil",
}

VALIDATION_LABELS = {
    "database": "Banco de dados",
    "api": "API",
    "campaign_attributes": "Campaign Attributes",
    "audit": "Auditoria",
    "sms": "SMS/mensagem",
    "received_events": "Eventos recebidos",
    "kafka": "Kafka",
    "schedule": "Agendamento futuro",
    "evidence": "Evidencias esperadas",
}

VALIDATION_ALIASES = {
    "db": "database",
    "banco": "database",
    "banco_de_dados": "database",
    "api": "api",
    "campaign_attributes": "campaign_attributes",
    "attributes": "campaign_attributes",
    "auditoria": "audit",
    "audit": "audit",
    "sms": "sms",
    "mensagem": "sms",
    "mensageria": "sms",
    "received_events": "received_events",
    "eventos_recebidos": "received_events",
    "kafka": "kafka",
    "agendamento": "schedule",
    "schedule": "schedule",
    "evidencias": "evidence",
    "evidence": "evidence",
}

VALIDATION_ORDER = list(VALIDATION_LABELS.keys())

DEADLINE_LABELS = {
    "d0": "D+0",
    "d1": "D+1",
    "d3": "D+3",
    "d5": "D+5",
    "d7": "D+7",
    "future": "Agendamento futuro",
}

DEADLINE_ALIASES = {
    "d0": "d0",
    "d_0": "d0",
    "0": "d0",
    "d1": "d1",
    "d_1": "d1",
    "1": "d1",
    "d3": "d3",
    "d_3": "d3",
    "3": "d3",
    "d5": "d5",
    "d_5": "d5",
    "5": "d5",
    "d7": "d7",
    "d_7": "d7",
    "7": "d7",
    "future": "future",
    "futuro": "future",
    "agendamento_futuro": "future",
}

SCHEDULED_DEADLINES = {"d1", "d3", "d5", "d7", "future"}

EVENT_RULES = {
    "habilitacao": {
        "operation": "processEvent",
        "action": "Processar habilitacao SmartOffers",
        "offer_strategy": "baseline",
        "expected_state": "Cliente habilitado, elegivel e vinculado a campanha correta.",
    },
    "alteracao_perfil": {
        "operation": "processEvent",
        "action": "Processar alteracao de perfil",
        "offer_strategy": "profile_change",
        "expected_state": "Perfil atualizado e elegibilidade recalculada sem perda de atributos.",
    },
    "mailing": {
        "operation": "processMailing",
        "action": "Processar mailing da campanha",
        "offer_strategy": "mailing",
        "expected_state": "Cliente importado pelo mailing e correlacionado a campanha.",
    },
    "recarga": {
        "operation": "processRecharge",
        "action": "Processar recarga pre-paga",
        "offer_strategy": "recharge",
        "expected_state": "Recarga reconhecida e campanha acionada conforme regra.",
    },
    "rehab": {
        "operation": "processEvent",
        "action": "Processar reabilitacao",
        "offer_strategy": "same_rank",
        "expected_state": "Cliente reabilitado sem troca indevida de oferta.",
    },
    "upsell": {
        "operation": "processEvent",
        "action": "Processar upgrade/upsell",
        "offer_strategy": "rank_up",
        "expected_state": "Cliente bonificado apenas quando houver upgrade real de oferta.",
    },
    "downgrade": {
        "operation": "processEvent",
        "action": "Processar downgrade",
        "offer_strategy": "rank_down",
        "expected_state": "Cliente sem bonificacao indevida em downgrade.",
    },
}

OFFER_STRATEGIES = {
    "baseline": {"initial_offer": "122429157", "target_offer": "122429157"},
    "profile_change": {"initial_offer": "122429157", "target_offer": "122429137"},
    "mailing": {"initial_offer": "MAILING_LIST", "target_offer": "MAILING_LIST"},
    "recharge": {"initial_offer": "RECARGA_BASE", "target_offer": "RECARGA_BONUS"},
    "same_rank": {"initial_offer": "122429157", "target_offer": "122429157"},
    "rank_up": {"initial_offer": "122429157", "target_offer": "104376082"},
    "rank_down": {"initial_offer": "104376082", "target_offer": "122429157"},
}

CUSTOMER_EVENT_IDS = {
    "pre": 866231225,
    "pos": 986557550,
    "controle": 986557550,
}

EVENT_EVENT_IDS = {
    "recarga": 866231226,
}
