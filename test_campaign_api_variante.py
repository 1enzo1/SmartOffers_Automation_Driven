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
LEGACY_REAL_SCRIPT_ENV = "SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT"
LEGACY_REAL_SCRIPT_CONFIRMATION = "YES_I_UNDERSTAND"

# ==========================


def ensure_legacy_real_script_allowed():
    if os.getenv(LEGACY_REAL_SCRIPT_ENV) != LEGACY_REAL_SCRIPT_CONFIRMATION:
        raise SystemExit(
            "Execucao real bloqueada. Defina "
            f"{LEGACY_REAL_SCRIPT_ENV}={LEGACY_REAL_SCRIPT_CONFIRMATION} "
            "somente durante execucao manual autorizada."
        )


def conectar_db():
    oracledb.init_oracle_client(
        lib_dir=r"C:\Users\322249\OneDrive - OPEN LABS S.A\Documentos\PosPagoSazonal\auto\instantclient-basic-windows.x64-21.20.0.0.0dbru\instantclient_21_20"
    )

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
    return build_postpaid_payload(
        msisdn,
        offer,
        event_time=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )


def montar_payload_pre(msisdn):
    attribute_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return build_prepaid_payload(
        msisdn,
        event_time=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        attribute_time=attribute_time,
    )


# ==========================
# UTIL
# ==========================

def salvar_json(caminho,dados):
    with open(caminho,"w") as f:
        json.dump(dados,f,indent=4)


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


def registrar(msg):
    print(msg, flush=True)


# ==========================
# EXECUÇÃO
# ==========================

def executar_pos(tipo,numero,conn):

    msisdn = gerar_msisdn()
    offer, rank = random.choice(PLANOS)

    pasta = build_path(RUN_PATH, "pos", tipo, f"teste_{numero}_{msisdn}")
    os.makedirs(pasta,exist_ok=True)
    registrar(f"SCENARIO|START|pos/{tipo}|{numero}|{msisdn}|{pasta}")

    payload, external_id = montar_payload_pos(msisdn,offer)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_request.json",payload)
    salvar_json(f"{pasta}/01_response.json",r.json())
    registrar(f"STEP|pos/{tipo}|{numero}|01_request")
    registrar(f"STEP|pos/{tipo}|{numero}|01_response")

    print(f"[POS] {tipo} -> {msisdn}")

    time.sleep(10)

    id_customer = buscar_customer(conn, external_id)

    if not id_customer:
        resultado_analise = analisar_teste(pasta, tipo)
        salvar_analise(pasta, resultado_analise)
        if ANALISAR_EXECUCAO:
            registrar(f"ANALYSIS|pos/{tipo}|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
        registrar(f"SCENARIO|END|pos/{tipo}|{numero}|{msisdn}|{pasta}")
        return

    id_contract,_ = buscar_contrato(conn, id_customer)

    salvar_json(f"{pasta}/audit.json",validar_auditoria(conn,id_customer,id_contract))
    registrar(f"STEP|pos/{tipo}|{numero}|audit")

    resultado_analise = analisar_teste(pasta, tipo)
    salvar_analise(pasta, resultado_analise)
    if ANALISAR_EXECUCAO:
        registrar(f"ANALYSIS|pos/{tipo}|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
    registrar(f"SCENARIO|END|pos/{tipo}|{numero}|{msisdn}|{pasta}")


def executar_pre(numero,conn):

    msisdn = gerar_msisdn()

    pasta = build_path(RUN_PATH, "pre", f"teste_{numero}_{msisdn}")
    os.makedirs(pasta,exist_ok=True)
    registrar(f"SCENARIO|START|pre|{numero}|{msisdn}|{pasta}")

    payload, external_id = montar_payload_pre(msisdn)

    r = requests.post(URL,json=payload,headers=HEADERS)

    salvar_json(f"{pasta}/01_request.json",payload)
    salvar_json(f"{pasta}/01_response.json",r.json())
    registrar(f"STEP|pre|{numero}|01_request")
    registrar(f"STEP|pre|{numero}|01_response")

    print(f"[PRE] -> {msisdn}")

    time.sleep(10)

    id_customer = buscar_customer(conn, external_id)

    if not id_customer:
        resultado_analise = analisar_teste(pasta, "pre")
        salvar_analise(pasta, resultado_analise)
        if ANALISAR_EXECUCAO:
            registrar(f"ANALYSIS|pre|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
        registrar(f"SCENARIO|END|pre|{numero}|{msisdn}|{pasta}")
        return

    id_contract,_ = buscar_contrato(conn, id_customer)

    salvar_json(f"{pasta}/audit.json",validar_auditoria(conn,id_customer,id_contract))
    registrar(f"STEP|pre|{numero}|audit")

    resultado_analise = analisar_teste(pasta, "pre")
    salvar_analise(pasta, resultado_analise)
    if ANALISAR_EXECUCAO:
        registrar(f"ANALYSIS|pre|{numero}|{json.dumps(resultado_analise, ensure_ascii=False)}")
    registrar(f"SCENARIO|END|pre|{numero}|{msisdn}|{pasta}")


# ==========================
# MAIN
# ==========================

def main():
    ensure_legacy_real_script_allowed()

    print("\n====== INICIO TESTES ======\n")

    conn = conectar_db()

    try:
        for i in range(1,3):
            executar_pos("upsell",i,conn)

        for i in range(1,3):
            executar_pre(i,conn)
    finally:
        conn.close()

    print("\n====== FINALIZADO ======\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
