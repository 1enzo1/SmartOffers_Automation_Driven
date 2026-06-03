from core.common.normalization import normalize_event_type, slug


MOCK_PLANNABLE_API_IDS = {
    "post-vivo-next-habilitacao-de-cliente-ade0841563",
    "post-vivo-next-habilitacao-de-linha-a79ab2e31c",
    "post-o-vivo-next-troca-de-oferta-fedbfb981e",
    "post-sincronismo-e8537bd912",
    "post-ativacao-de-campanha-por-api-2e656ee31c",
    "post-evento-de-recarga-6954ef3458",
    "post-consulta-de-saldo-f3317b27b3",
    "post-evento-vivo-turbo-e124494049",
    "post-transicao-de-estado-de-servico-aceite-3751798e76",
    "post-retorno-la-xml-e73a7721f4",
}


DEFAULT_HTTP_PLAN_API_IDS_BY_EVENT_TYPE = {
    "alteracao_perfil": "post-o-vivo-next-troca-de-oferta-fedbfb981e",
    "ativacao": "post-ativacao-de-campanha-por-api-2e656ee31c",
    "campanha": "post-ativacao-de-campanha-por-api-2e656ee31c",
    "downgrade": "post-o-vivo-next-troca-de-oferta-fedbfb981e",
    "habilitacao": "post-vivo-next-habilitacao-de-cliente-ade0841563",
    "mailing": "post-ativacao-de-campanha-por-api-2e656ee31c",
    "recarga": "post-evento-de-recarga-6954ef3458",
    "rehab": "post-sincronismo-e8537bd912",
    "saldo": "post-consulta-de-saldo-f3317b27b3",
    "upsell": "post-ativacao-de-campanha-por-api-2e656ee31c",
    "vivo_turbo": "post-evento-vivo-turbo-e124494049",
}


def is_mock_plannable(api_id):
    return str(api_id or "").strip() in MOCK_PLANNABLE_API_IDS


def list_mock_plannable_api_ids():
    return sorted(MOCK_PLANNABLE_API_IDS)


def resolve_default_http_plan_api_id(event_type):
    normalized = normalize_event_type(event_type)
    api_id = DEFAULT_HTTP_PLAN_API_IDS_BY_EVENT_TYPE.get(normalized)
    if api_id and is_mock_plannable(api_id):
        return api_id

    fallback = DEFAULT_HTTP_PLAN_API_IDS_BY_EVENT_TYPE.get(slug(event_type))
    if fallback and is_mock_plannable(fallback):
        return fallback

    return None
