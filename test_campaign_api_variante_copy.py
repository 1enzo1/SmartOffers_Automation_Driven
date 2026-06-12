import requests
import random
import json
import os
import time
from datetime import datetime
import oracledb
import os
from core.utils.evidence_paths import build_path, create_run_path, get_base_path
from core.utils.evidence_analysis import analisar_teste, salvar_analise
from core.utils.evidence_payload_builders import build_postpaid_payload, build_prepaid_payload

BASE_PATH = get_base_path("evidencias_variante")
RUN_PATH = create_run_path(BASE_PATH)
ANALISAR_EXECUCAO = os.getenv("ANALISAR_EXECUCAO", "0") == "1"

# ==========================
# CONFIG
# ==========================
CONFIG = {
    "rodar_pos": True,
    "rodar_pre": True,
    "qtd_testes": 3,
    "pos": {
        "tipo_cenarios": ["upsell", "rehab", "downgrade"]
    },
    "pre": {
        "profile": "559",
        "account_state": "2"
    }
}

URL = "http://10.129.174.95:8084/ws/integration/online/process"
HEADERS = {"content-type": "application/json"}

PLANOS = [
("122429157",20430),
("122429137",20450),
("484138733",20500),
("105310872",21000),
("104375982",21500),
("105180782",21600),
("105205612",21700),
("105205572",22000),
("104912332",22500),
("105205532",22700),
("104912252",22700),
("104912352",23000),
("104912292",24000),
("104912272",24000),
("104912312",24300),
("104376062",25000),
("104376082",26000)
]

# ==========================
# ORACLE
# ==========================
DB_HOST="10.129.174.97"
DB_PORT=1521
DB_SERVICE="SMARTDB"
DB_USER="acm"
DB_PASS="acm"

oracledb.init_oracle_client(
    lib_dir=r"C:\Users\322249\OneDrive - OPEN LABS S.A\Documentos\PosPagoSazonal\auto\instantclient-basic-windows.x64-21.20.0.0.0dbru\instantclient_21_20"
)

def conectar_db():
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)
    return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)

# ==========================
# UTIL
# ==========================
def gerar_msisdn():
    return "119" + str(random.randint(20000000,99999999))

def salvar_json(caminho,dados):
    with open(caminho,"w") as f:
        json.dump(dados,f,indent=4)

def executar_query_debug(conn, nome, query, params=None):

    cursor = conn.cursor()
    cursor.execute(query + " FETCH FIRST 100 ROWS ONLY", params or {})

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()

    result = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            row_dict[columns[i]] = str(value)
        result.append(row_dict)

    cursor.close()

    return {
        "nome": nome,
        "total": len(result),
        "rows": result
    }


def registrar(msg):
    print(msg, flush=True)

# ==========================
# PAYLOAD POS
# ==========================
def montar_payload_pos(msisdn, offer):
    return build_postpaid_payload(
        msisdn,
        offer,
        event_time=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )

# ==========================
# PAYLOAD PRE
# ==========================
def montar_payload_pre(msisdn):
    return build_prepaid_payload(
        msisdn,
        event_time=datetime.now().strftime("%d-%m-%Y") + " 23:00:00",
        attribute_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        profile=CONFIG["pre"]["profile"],
        account_state=CONFIG["pre"]["account_state"],
    )

# ==========================
# REGRAS POS
# ==========================
def escolher_planos(offer_inicial, rank):

    maiores = [p for p in PLANOS if p[1] > rank]
    menores = [p for p in PLANOS if p[1] < rank]

    upsell = random.choice(maiores)[0] if maiores else offer_inicial
    downgrade = random.choice(menores)[0] if menores else offer_inicial
    rehab = offer_inicial

    return upsell, rehab, downgrade

# ==========================
# EXECUÇÃO POS
# ==========================
def executar_pos(tipo, numero, conn):

    msisdn = gerar_msisdn()
    offer_inicial, rank = random.choice(PLANOS)

    pasta = build_path(RUN_PATH, "pos", tipo, f"teste_{numero}_{msisdn}")
    os.makedirs(pasta, exist_ok=True)
    registrar(f"SCENARIO|START|pos/{tipo}|{numero}|{msisdn}|{pasta}")

    payload, external_id = montar_payload_pos(msisdn, offer_inicial)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_create_request.json",payload)
    salvar_json(f"{pasta}/01_create_response.json",r.json())
    registrar(f"STEP|pos/{tipo}|{numero}|01_request")
    registrar(f"STEP|pos/{tipo}|{numero}|01_response")

    print(f"[POS-{tipo}] criação -> {msisdn}")

    time.sleep(10)

    # DB VALIDATION
    discovery = executar_query_debug(conn,"DISCOVERY",
        "SELECT * FROM CUST_DISCOVERY WHERE EXTERNAL_ID = :external_id",
        {"external_id": external_id}
    )

    salvar_json(f"{pasta}/02_discovery.json", discovery)
    registrar(f"STEP|pos/{tipo}|{numero}|02_discovery")

    if not discovery["rows"]:
        resultado_analise = analisar_teste(pasta, tipo)
        salvar_analise(pasta, resultado_analise)
        if ANALISAR_EXECUCAO:
            registrar(f"ANALYSIS|pos/{tipo}|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
        registrar(f"SCENARIO|END|pos/{tipo}|{numero}|{msisdn}|{pasta}")
        return

    id_customer = discovery["rows"][0]["CUSTOMER_ID"]

    campaign = executar_query_debug(conn,"CAMPAIGN",
        "SELECT * FROM CUST_CAMPAIGNS WHERE ID_CUSTOMER = :id_customer",
        {"id_customer": id_customer}
    )

    salvar_json(f"{pasta}/03_campaign.json", campaign)
    registrar(f"STEP|pos/{tipo}|{numero}|03_campaign")

    upsell, rehab, downgrade = escolher_planos(offer_inicial, rank)

    if tipo == "upsell":
        offer_final = upsell
    elif tipo == "rehab":
        offer_final = rehab
    else:
        offer_final = downgrade

    payload2,_ = montar_payload_pos(msisdn, offer_final)

    r2 = requests.post(URL,json=payload2,headers=HEADERS)

    salvar_json(f"{pasta}/04_change_request.json",payload2)
    salvar_json(f"{pasta}/04_change_response.json",r2.json())
    registrar(f"STEP|pos/{tipo}|{numero}|04_change_request")
    registrar(f"STEP|pos/{tipo}|{numero}|04_change_response")

    print(f"[POS-{tipo}] alteração -> {offer_final}")

    resultado_analise = analisar_teste(pasta, tipo)
    salvar_analise(pasta, resultado_analise)
    if ANALISAR_EXECUCAO:
        registrar(f"ANALYSIS|pos/{tipo}|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
    registrar(f"SCENARIO|END|pos/{tipo}|{numero}|{msisdn}|{pasta}")

# ==========================
# EXECUÇÃO PRE
# ==========================
def executar_pre(numero, conn):

    msisdn = gerar_msisdn()

    pasta = build_path(RUN_PATH, "pre", f"teste_{numero}_{msisdn}")
    os.makedirs(pasta, exist_ok=True)
    registrar(f"SCENARIO|START|pre|{numero}|{msisdn}|{pasta}")

    payload, external_id = montar_payload_pre(msisdn)

    r = requests.post(URL, json=payload, headers=HEADERS)

    salvar_json(f"{pasta}/01_request.json", payload)
    salvar_json(f"{pasta}/01_response.json", r.json())
    registrar(f"STEP|pre|{numero}|01_request")
    registrar(f"STEP|pre|{numero}|01_response")

    print(f"[PRE] {msisdn}")

    time.sleep(10)

    discovery = executar_query_debug(conn,"DISCOVERY",
        "SELECT * FROM CUST_DISCOVERY WHERE EXTERNAL_ID = :external_id",
        {"external_id": external_id}
    )

    salvar_json(f"{pasta}/02_discovery.json", discovery)
    registrar(f"STEP|pre|{numero}|02_discovery")

    resultado_analise = analisar_teste(pasta, "pre")
    salvar_analise(pasta, resultado_analise)
    if ANALISAR_EXECUCAO:
        registrar(f"ANALYSIS|pre|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
    registrar(f"SCENARIO|END|pre|{numero}|{msisdn}|{pasta}")

# ==========================
# MAIN
# ==========================
print("\n====== INICIO TESTES ======\n")

conn = conectar_db()

if CONFIG["rodar_pos"]:
    for tipo in CONFIG["pos"]["tipo_cenarios"]:
        for i in range(1, CONFIG["qtd_testes"] + 1):
            executar_pos(tipo, i, conn)

if CONFIG["rodar_pre"]:
    for i in range(1, CONFIG["qtd_testes"] + 1):
        executar_pre(i, conn)

conn.close()

print("\n====== FINALIZADO ======\n")
