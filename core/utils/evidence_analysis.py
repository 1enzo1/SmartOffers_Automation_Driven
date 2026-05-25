import json
import os


PLANOS = {
    "122429157": 20430,
    "122429137": 20450,
    "484138733": 20500,
    "105310872": 21000,
    "104375982": 21500,
    "105180782": 21600,
    "105205612": 21700,
    "105205572": 22000,
    "104912332": 22500,
    "105205532": 22700,
    "104912252": 22700,
    "104912352": 23000,
    "104912292": 24000,
    "104912272": 24000,
    "104912312": 24300,
    "104376062": 25000,
    "104376082": 26000
}


def carregar_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def carregar_primeiro(pasta, nomes):
    for nome in nomes:
        dados = carregar_json(os.path.join(pasta, nome))
        if dados is not None:
            return dados
    return None


def get_offer(payload):
    try:
        return payload["attributes"]["349876894"]
    except Exception:
        return None


def analisar_teste(pasta, tipo):
    create = carregar_primeiro(pasta, ["01_create_response.json", "01_response.json"])
    change_req = carregar_primeiro(
        pasta,
        [
            "03_upsell_request.json",
            "03_rehab_request.json",
            "03_downgrade_request.json",
            "04_change_request.json",
            "04_change_offer_request.json",
        ],
    )
    campaign = carregar_primeiro(pasta, ["03_campaign.json", "03_campaign_lookup.json"])
    audit = carregar_primeiro(pasta, ["audit.json", "05_audit_records.json"])
    metrics = carregar_primeiro(pasta, ["06_metrics.json"])
    discovery = carregar_primeiro(pasta, ["02_db_validation.json", "02_discovery.json"])

    api_ok = create and create.get("body", {}).get("result") is not False
    entrou_campanha = (
        campaign and len(campaign.get("dados", [])) > 0
    ) or (
        discovery and len(discovery.get("rows", [])) > 0
    ) or (
        discovery and len(discovery.get("dados", [])) > 0
    )
    tem_auditoria = audit and len(audit) > 0
    tem_metrica = metrics and len(metrics) > 0

    mudou_estado = False

    if entrou_campanha and campaign and campaign.get("dados"):
        dados = campaign["dados"][0]
        mudou_estado = dados.get("CURRENT_STATE") != dados.get("LAST_STATE")

    offer_inicial = None
    offer_final = None

    if change_req:
        offer_final = get_offer(change_req)

    if tipo == "upsell":
        valido = PLANOS.get(offer_final, 0) > PLANOS.get(offer_inicial, 0)
        motivo = "Upsell inválido"
    elif tipo == "downgrade":
        valido = PLANOS.get(offer_final, 0) < PLANOS.get(offer_inicial, 0)
        motivo = "Downgrade inválido"
    elif tipo == "rehab":
        valido = offer_final == offer_inicial
        motivo = "Rehab inválido"
    else:
        valido = True
        motivo = ""

    if not api_ok:
        status = "ERRO_AMBIENTE"
        diag = "API falhou"
        sugestao = "verificar payload ou ambiente"
    elif not entrou_campanha:
        status = "ERRO_REGRA"
        diag = "cliente não entrou na campanha"
        sugestao = "validar regra de entrada"
    elif not tem_auditoria:
        status = "DELAY_PROCESSAMENTO"
        diag = "nenhum evento registrado"
        sugestao = "aguardar ou verificar fila"
    elif not tem_metrica and tipo in {"upsell", "downgrade", "rehab"}:
        status = "ERRO_REGRA"
        diag = "não houve bonificação"
        sugestao = "verificar regra de bonificação"
    else:
        status = "SUCESSO"
        diag = "fluxo completo"
        sugestao = "ok"

    return {
        "status": status,
        "cenario": tipo,
        "valido": valido,
        "motivo": motivo,
        "validacoes": {
            "api_ok": api_ok,
            "entrou_campanha": entrou_campanha,
            "mudou_estado": mudou_estado,
            "tem_auditoria": tem_auditoria,
            "tem_metrica": tem_metrica
        },
        "diagnostico": diag,
        "sugestao": sugestao
    }


def salvar_analise(pasta, resultado):
    caminho = os.path.join(pasta, "resumo_analise.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    return caminho
