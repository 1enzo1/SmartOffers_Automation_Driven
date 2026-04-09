import requests
import random
import json
import os
import time
from datetime import datetime
import oracledb
import os
from logging_helper import log_success, log_error

BASE_PATH = os.getenv("PASTA_EXECUCAO", "evidencias_variante")

URL = "http://10.129.174.95:8084/ws/integration/online/process"

HEADERS = {
    "content-type": "application/json"
}

ERROS = 0

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
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

    return oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=dsn
    )


def gerar_msisdn():
    return "119" + str(random.randint(20000000,99999999))


# ==========================
# PAYLOADS
# ==========================

def montar_payload_pos(msisdn, offer):

    account = msisdn[3:]
    external_id = f"NEXT_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 986557550,
        "eventTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
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
            "908881601": "2",
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
            "2020041941": "1",
            "2047205742": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return payload, external_id


# ==========================
# UTIL
# ==========================

def salvar_json(caminho,dados):
    with open(caminho,"w") as f:
        json.dump(dados,f,indent=4)


def registrar_erro(msg):
    global ERROS
    ERROS += 1
    log_error("global", "runtime", msg)


def query_table_as_text(conn, query, params=None):

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
    return result


# ==========================
# DB
# ==========================

def buscar_customer(conn, external_id):

    cursor = conn.cursor()

    query = """
    SELECT CUSTOMER_ID
    FROM CUST_DISCOVERY
    WHERE EXTERNAL_ID = :external_id
    """

    for _ in range(10):
        cursor.execute(query, external_id=external_id)
        row = cursor.fetchone()

        if row:
            cursor.close()
            return row[0]

        time.sleep(5)

    cursor.close()
    return None


def buscar_contrato(conn, id_customer):

    rows = query_table_as_text(conn, """
        SELECT *
        FROM CUST_CAMPAIGNS
        WHERE ID_CUSTOMER = :id_customer
    """, {"id_customer": id_customer})

    if not rows:
        return None, []

    return rows[0].get("ID_CONTRACT"), rows


def validar_auditoria(conn, id_customer, id_contract):

    return query_table_as_text(conn, """
        SELECT *
        FROM ACM_AUDIT_RECORDS
        WHERE CUSTOMER_ID = :id_customer
        AND CONTRACT_ID = :id_contract
    """, {
        "id_customer": id_customer,
        "id_contract": id_contract
    })


def validar_metricas(conn, id_customer):

    return query_table_as_text(conn, """
        SELECT *
        FROM CUST_METRICS
        WHERE ID_CUSTOMER = :id_customer
    """, {"id_customer": id_customer})


def validar_caracteristicas(conn, id_contract):

    return query_table_as_text(conn, """
        SELECT *
        FROM CUST_CAMPAIGN_CHARACTERISTICS
        WHERE ID_CAMPAIGN_CONTRACT = :id_contract
    """, {"id_contract": id_contract})


# ==========================
# EXECUÇÃO
# ==========================

def executar_pos(tipo,numero,conn):

    msisdn = gerar_msisdn()
    offer, rank = random.choice(PLANOS)

    pasta = f"evidencias_variante/pos/{tipo}/teste_{numero}_{msisdn}"
    os.makedirs(pasta,exist_ok=True)

    payload, external_id = montar_payload_pos(msisdn,offer)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_request.json",payload)
    salvar_json(f"{pasta}/01_response.json",r.json())
    if not r.ok:
        registrar_erro(f"HTTP {r.status_code} during create")
        log_error(f"pos-{tipo}", "create", "request failed", msisdn=msisdn, offer=offer, external_id=external_id, extra={"http_status": r.status_code})

    log_success(f"pos-{tipo}", "create", "request sent", msisdn=msisdn, offer=offer, external_id=external_id)

    time.sleep(10)

    id_customer = buscar_customer(conn, external_id)

    if not id_customer:
        registrar_erro(f"CUST_DISCOVERY não encontrado para EXTERNAL_ID={external_id}")
        log_error(f"pos-{tipo}", "db_validate_discovery", "customer not found", msisdn=msisdn, offer=offer, external_id=external_id)
        return

    id_contract,_ = buscar_contrato(conn, id_customer)
    if not id_contract:
        registrar_erro(f"CUST_CAMPAIGNS sem contrato para CUSTOMER_ID={id_customer}")
        log_error(f"pos-{tipo}", "db_validate_campaign", "contract not found", msisdn=msisdn, offer=offer, external_id=external_id, extra={"id_customer": id_customer})
        return

    audit_rows = validar_auditoria(conn,id_customer,id_contract)
    salvar_json(f"{pasta}/audit.json",audit_rows)
    if not audit_rows:
        registrar_erro(f"ACM_AUDIT_RECORDS vazio para CUSTOMER_ID={id_customer}, CONTRACT_ID={id_contract}")
        log_error(f"pos-{tipo}", "db_validate_audit", "audit rows missing", msisdn=msisdn, offer=offer, external_id=external_id, extra={"id_customer": id_customer, "id_contract": id_contract})


def executar_pre(numero,conn):

    msisdn = gerar_msisdn()

    pasta = f"evidencias_variante/pre/teste_{numero}_{msisdn}"
    os.makedirs(pasta,exist_ok=True)

    payload, external_id = montar_payload_pre(msisdn)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_request.json",payload)
    salvar_json(f"{pasta}/01_response.json",r.json())
    if not r.ok:
        registrar_erro(f"HTTP {r.status_code} during create")
        log_error("pre", "create", "request failed", msisdn=msisdn, external_id=external_id, extra={"http_status": r.status_code})

    log_success("pre", "create", "request sent", msisdn=msisdn, external_id=external_id)

    time.sleep(10)

    id_customer = buscar_customer(conn, external_id)

    if not id_customer:
        registrar_erro(f"CUST_DISCOVERY não encontrado para EXTERNAL_ID={external_id}")
        log_error("pre", "db_validate_discovery", "customer not found", msisdn=msisdn, external_id=external_id)
        return

    id_contract,_ = buscar_contrato(conn, id_customer)
    if not id_contract:
        registrar_erro(f"CUST_CAMPAIGNS sem contrato para CUSTOMER_ID={id_customer}")
        log_error("pre", "db_validate_campaign", "contract not found", msisdn=msisdn, external_id=external_id, extra={"id_customer": id_customer})
        return

    audit_rows = validar_auditoria(conn,id_customer,id_contract)
    salvar_json(f"{pasta}/audit.json",audit_rows)
    if not audit_rows:
        registrar_erro(f"ACM_AUDIT_RECORDS vazio para CUSTOMER_ID={id_customer}, CONTRACT_ID={id_contract}")
        log_error("pre", "db_validate_audit", "audit rows missing", msisdn=msisdn, external_id=external_id, extra={"id_customer": id_customer, "id_contract": id_contract})


# ==========================
# MAIN
# ==========================

log_success("suite", "start", "inicio testes")

conn = conectar_db()

for i in range(1,3):
    executar_pos("upsell",i,conn)

for i in range(1,3):
    executar_pre(i,conn)

conn.close()

log_success("suite", "end", "finalizado", extra={"errors": ERROS})
if ERROS > 0:
    raise SystemExit(1)
