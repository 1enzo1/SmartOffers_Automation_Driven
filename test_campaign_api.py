import requests
import random
import json
import os
import time
from datetime import datetime
import oracledb

BASE_PATH = os.getenv("PASTA_EXECUCAO", "evidencias_variante")

URL = "http://10.129.174.95:8084/ws/integration/online/process"

HEADERS = {
    "content-type": "application/json"
}

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

# ===== ORACLE CONFIG =====

DB_HOST="10.129.174.97"
DB_PORT=1521
DB_SERVICE="SMARTDB"
DB_USER="acm"
DB_PASS="acm"

oracledb.init_oracle_client(
    lib_dir=r"C:\Users\322249\OneDrive - OPEN LABS S.A\Documentos\PosPagoSazonal\auto\instantclient-basic-windows.x64-21.20.0.0.0dbru\instantclient_21_20"
)

# ==========================

def conectar_db():

    dsn = oracledb.makedsn(
        DB_HOST,
        DB_PORT,
        service_name=DB_SERVICE
    )

    conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=dsn
    )

    return conn


def gerar_msisdn():

    return "119" + str(random.randint(20000000,99999999))


def montar_payload(msisdn, offer):

    account = msisdn[3:]
    external_id = f"NEXT_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 986557550,
        "eventTime": "16-03-2026 23:00:00",
        # "eventTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "attributes": {
            "70060213": "1",
            "349876894": offer,
            "425747132": "EMAIL",
            "447500851": account,
            "908881601": "1",
            "1576075623": "DD",
            "1597489127": external_id,
            "1666101552": "1",
            "1667261676": msisdn,
            "1794057286": "1791234567",
            "1840045565": "5",
            "1997035279": "5",
            "2020041941": "2",
            "2118173840": "365123987"
        },
        "attributeDetails": {
            "70060213": {"type":"String","name":"DOCUMENT_TYPE"},
            "349876894": {"type":"String","name":"OFFER"},
            "425747132": {"type":"String","name":"SENDING_FORM"},
            "447500851": {"type":"String","name":"ACCOUNT"},
            "908881601": {"type":"Long","name":"ACCOUNT_STATE"},
            "1576075623": {"type":"String","name":"PAYMENT_METHOD"},
            "1597489127": {"type":"String","name":"External Id"},
            "1666101552": {"type":"String","name":"DOCUMENT_ID"},
            "1667261676": {"type":"Long","name":"MSISDN"},
            "1794057286": {"type":"String","name":"BILLING_ACCOUNT_STATE"},
            "1840045565": {"type":"Long","name":"BILLING_CYCLE_CUT_OFF_DAY"},
            "1997035279": {"type":"Long","name":"BILLING_CYCLE"},
            "2020041941": {"type":"Long","name":"CLIENT_TYPE"},
            "2118173840": {"type":"String","name":"BILLING_ACCOUNT"}
        }
    }

    return payload, external_id

def montar_payload_pre(msisdn):

    account = msisdn[3:]
    external_id = f"NGIN_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 866231225,
        "eventTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "attributes": {
            "29905344": "8",
            "427862433": "11",
            "447500851": account,
            "569463775": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "741842957": "1",
            "908881601": "2",  # ATIVO
            "1068616960": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "1095579373": "SP",
            "1190622368": "559",
            "1358620105": "3",
            "1581479658": "S",
            "1597489127": external_id,
            "1650737577": "1",
            "1667261676": msisdn,
            "1760625139": "1",
            "1944018544": "NGIN",
            "1957846968": "0000000D",
            "1966426172": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "2020041941": "1",  # PRÉ
            "2047205742": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return payload, external_id

def salvar_json(caminho,dados):

    with open(caminho,"w") as f:
        json.dump(dados,f,indent=4)


def validar_db(conn, external_id):

    cursor = conn.cursor()

    query = """
    SELECT *
    FROM CUST_DISCOVERY
    WHERE EXTERNAL_ID = :external_id
    """

    for tentativa in range(10):

        cursor.execute(query, external_id=external_id)

        rows = cursor.fetchall()

        if rows:
            cursor.close()
            return rows

        time.sleep(10)

    cursor.close()
    return []

def escolher_planos(offer_inicial, rank):

    maiores = [p for p in PLANOS if p[1] > rank]
    menores = [p for p in PLANOS if p[1] < rank]

    upsell = random.choice(maiores)[0] if maiores else offer_inicial
    downgrade = random.choice(menores)[0] if menores else offer_inicial
    rehab = offer_inicial

    return upsell, rehab, downgrade
def montar_payload_pre(msisdn):

    account = msisdn[3:]
    external_id = f"NGIN_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 866231225,
        "eventTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "attributes": {
            "29905344": "8",
            "427862433": "11",
            "447500851": account,
            "569463775": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "741842957": "1",
            "908881601": "2",  # ATIVO
            "1068616960": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "1095579373": "SP",
            "1190622368": "559",
            "1358620105": "3",
            "1581479658": "S",
            "1597489127": external_id,
            "1650737577": "1",
            "1667261676": msisdn,
            "1760625139": "1",
            "1944018544": "NGIN",
            "1957846968": "0000000D",
            "1966426172": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "2020041941": "1",  # PRÉ
            "2047205742": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return payload, external_id

def executar_cenario(tipo,numero,conn):
    
    msisdn = gerar_msisdn()

    offer_inicial, rank = random.choice(PLANOS)

    pasta = f"evidencias/{tipo}/teste_{numero}_{msisdn}"

    os.makedirs(pasta,exist_ok=True)

    payload, external_id = montar_payload(msisdn,offer_inicial)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_create_request.json",payload)

    try:
        salvar_json(f"{pasta}/01_create_response.json",r.json())
    except:
        open(f"{pasta}/01_create_response.txt","w").write(r.text)

    print(f"{tipo} criação -> {msisdn} offer {offer_inicial}")

    time.sleep(20)

    rows = validar_db(conn,external_id)

    salvar_json(f"{pasta}/02_db_validation.json",{"rows":str(rows)})

    upsell, rehab, downgrade = escolher_planos(offer_inicial,rank)

    if tipo == "upsell":
        offer_final = upsell
    elif tipo == "rehab":
        offer_final = rehab
    else:
        offer_final = downgrade

    payload2,_ = montar_payload(msisdn,offer_final)

    r2 = requests.post(URL,json=payload2,headers=HEADERS)

    salvar_json(f"{pasta}/03_{tipo}_request.json",payload2)

    try:
        salvar_json(f"{pasta}/03_{tipo}_response.json",r2.json())
    except:
        open(f"{pasta}/03_{tipo}_response.txt","w").write(r2.text)

    print(f"{tipo} alteração -> {offer_final}")
    


print("\n====== INICIO TESTES CAMPANHA ======\n")

if not os.path.exists("evidencias"):
    os.makedirs("evidencias")

conn = conectar_db()

for i in range(1,6):
    executar_cenario("upsell",i,conn)

for i in range(1,6):
    executar_cenario("rehab",i,conn)

for i in range(1,6):
    executar_cenario("downgrade",i,conn)

print("\n====== TESTES FINALIZADOS ======\n")

conn.close()
