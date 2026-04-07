import json
import os

choice = input("Escolha a base path:\n1 - '1. Evidências'\n2 - '2. Evidências variante'\n> ")
BASE_PATH = "evidencias" if choice == "1" else "evidencias_variante"

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
        with open(path) as f:
            return json.load(f)
    except:
        return None


def get_offer(payload):
    try:
        return payload["attributes"]["349876894"]
    except:
        return None


def analisar_teste(pasta, tipo):

    create = carregar_json(os.path.join(pasta, "01_create_response.json"))
    change_req = carregar_json(os.path.join(pasta, "04_change_offer_request.json"))
    campaign = carregar_json(os.path.join(pasta, "03_campaign_lookup.json"))
    audit = carregar_json(os.path.join(pasta, "05_audit_records.json"))
    metrics = carregar_json(os.path.join(pasta, "06_metrics.json"))

    api_ok = create and create.get("body", {}).get("result") is not False
    entrou_campanha = campaign and len(campaign.get("dados", [])) > 0
    tem_auditoria = audit and len(audit) > 0
    tem_metrica = metrics and len(metrics) > 0

    mudou_estado = False

    if entrou_campanha:
        dados = campaign["dados"][0]
        mudou_estado = dados.get("CURRENT_STATE") != dados.get("LAST_STATE")

    # offers
    offer_inicial = None
    offer_final = None

    if change_req:
        offer_final = get_offer(change_req)

    # validação cenário
    valido = True
    motivo = ""

    if tipo == "upsell":
        valido = PLANOS.get(offer_final, 0) > PLANOS.get(offer_inicial, 0)
        motivo = "Upsell inválido"

    elif tipo == "downgrade":
        valido = PLANOS.get(offer_final, 0) < PLANOS.get(offer_inicial, 0)
        motivo = "Downgrade inválido"

    elif tipo == "rehab":
        valido = offer_final == offer_inicial
        motivo = "Rehab inválido"

    # diagnóstico
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

    elif not tem_metrica:
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


def executar():

    for tipo in os.listdir(BASE_PATH):

        tipo_path = os.path.join(BASE_PATH, tipo)

        for teste in os.listdir(tipo_path):

            pasta = os.path.join(tipo_path, teste)

            resultado = analisar_teste(pasta, tipo)

            print("\n========================")
            print(f"{tipo} - {teste}")
            print(json.dumps(resultado, indent=2))


if __name__ == "__main__":
    executar()