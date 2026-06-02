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


def is_mock_plannable(api_id):
    return str(api_id or "").strip() in MOCK_PLANNABLE_API_IDS


def list_mock_plannable_api_ids():
    return sorted(MOCK_PLANNABLE_API_IDS)
