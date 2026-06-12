import requests
import random
import json
import os
import time
from datetime import datetime
import oracledb
from core.utils.evidence_paths import build_path, create_run_path, get_base_path
from core.utils.evidence_analysis import analisar_teste, salvar_analise
from core.utils.evidence_payload_builders import build_postpaid_payload, build_prepaid_payload

BASE_PATH = get_base_path("evidencias_variante")
RUN_PATH = create_run_path(BASE_PATH)
ANALISAR_EXECUCAO = os.getenv("ANALISAR_EXECUCAO", "0") == "1"

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

LEGACY_REAL_SCRIPT_ENV = "SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT"
LEGACY_REAL_SCRIPT_CONFIRMATION = "YES_I_UNDERSTAND"
API_URL_ENV = "SMARTOFFERS_API_URL"
DB_DSN_ENV = "SMARTOFFERS_DB_DSN"
DB_USER_ENV = "SMARTOFFERS_DB_USER"
DB_PASSWORD_ENV = "SMARTOFFERS_DB_PASSWORD"
ORACLE_CLIENT_LIB_DIR_ENV = "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR"

# ==========================


def ensure_legacy_real_script_allowed():
    if os.getenv(LEGACY_REAL_SCRIPT_ENV) != LEGACY_REAL_SCRIPT_CONFIRMATION:
        raise SystemExit(
            "Execucao real bloqueada. Defina "
            f"{LEGACY_REAL_SCRIPT_ENV}={LEGACY_REAL_SCRIPT_CONFIRMATION} "
            "somente durante execucao manual autorizada."
        )


def get_required_runtime_env(name):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise SystemExit(f"Config runtime ausente: {name}")
    return value


def get_smartoffers_api_url():
    return get_required_runtime_env(API_URL_ENV)


def conectar_db():
    oracle_client_lib_dir = os.getenv(ORACLE_CLIENT_LIB_DIR_ENV)
    if oracle_client_lib_dir:
        oracledb.init_oracle_client(lib_dir=oracle_client_lib_dir)

    return oracledb.connect(
        user=get_required_runtime_env(DB_USER_ENV),
        password=get_required_runtime_env(DB_PASSWORD_ENV),
        dsn=get_required_runtime_env(DB_DSN_ENV),
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

    r = requests.post(get_smartoffers_api_url(),json=payload,headers=HEADERS)

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

    r = requests.post(get_smartoffers_api_url(),json=payload,headers=HEADERS)

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
