import json
import os
import random
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    import oracledb  # type: ignore
except Exception:
    oracledb = None

URL = os.getenv("PROCESS_EVENT_URL", "http://10.129.174.95:8084/ws/integration/online/process")
TIMEOUT_SECONDS = int(os.getenv("PROCESS_EVENT_TIMEOUT", "30"))
HEADERS = {"content-type": "application/json"}
API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
API_RETRY_SLEEP = int(os.getenv("API_RETRY_SLEEP", "2"))

DB_HOST = os.getenv("DB_HOST", "10.129.174.97")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "SMARTDB")
DB_USER = os.getenv("DB_USER", "acm")
DB_PASS = os.getenv("DB_PASS", "acm")
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "8"))
DB_RETRY_SLEEP = int(os.getenv("DB_RETRY_SLEEP", "5"))


# Attribute IDs
ATTR_EXTERNAL_ID = "1597489127"
ATTR_ACCOUNT = "447500851"
ATTR_MSISDN = "1667261676"
ATTR_ACCOUNT_STATE = "908881601"
ATTR_CLIENT_TYPE = "2020041941"


@dataclass
class Scenario:
    name: str
    client_type: int
    account_state: int
    should_enter: bool


def log(tag: str, message: str) -> None:
    print(f"[{tag}] {message}")


def suggest_root_cause(
    scenario: Scenario,
    http_ok: bool,
    http_status: Optional[int],
    discovery_found: Optional[bool],
    campaign_found: Optional[bool],
) -> str:
    if not http_ok:
        if http_status is None:
            return "API failure: timeout/rede/endpoint indisponível."
        if http_status >= 500:
            return f"API failure: erro servidor ({http_status})."
        if http_status in (401, 403):
            return f"API failure: autenticação/autorização ({http_status})."
        return f"API failure: resposta inválida ({http_status})."

    if discovery_found is False:
        return (
            "DB delay ou falha de persistência: cliente não encontrado em CUST_DISCOVERY "
            f"após {DB_RETRY_ATTEMPTS} tentativas."
        )

    if discovery_found and campaign_found is not None:
        if scenario.should_enter and not campaign_found:
            return "Possible rule mismatch (ACCOUNT_STATE/CLIENT_TYPE) ou atraso de entrada em campanha."
        if (not scenario.should_enter) and campaign_found:
            return "Possible rule mismatch: cliente entrou em campanha quando não deveria."

    return "Causa inconclusiva: revisar payload, logs de integração e latência de processamento."


def generate_msisdn() -> str:
    # 11 digits (Brazil style): 119XXXXXXXX
    return "119" + str(random.randint(20000000, 99999999))


def now_event_time() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def now_attr_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_prepaid_payload_template(msisdn: str) -> Tuple[Dict[str, Any], str]:
    """Payload builder pattern: base template + scenario overrides."""
    account = msisdn[3:]
    external_id = f"NGIN_{account}_{int(time.time())}_{random.randint(100, 999)}"
    ts = now_attr_time()

    payload = {
        "operation": "processEvent",
        "extEventId": 866231225,
        "eventTime": now_event_time(),
        "attributes": {
            "1597489127": external_id,
            "447500851": account,
            "1667261676": msisdn,
            "2047205742": ts,
            "1068616960": ts,
            "1966426172": ts,
            "908881601": "3",  # overridden by scenario
            "427862433": "11",
            "1944018544": "NGIN",
            "2020041941": "1",  # overridden by scenario
            "29905344": "8",
            "1095579373": "SP",
            "741842957": "1",
            "1957846968": "0000000D",
            "1650737577": "1",
            "1358620105": "3",
            "1190622368": "559",
            "569463775": ts,
            "1760625139": "1",
            "1581479658": "S",
            "579515748": "FISICO",
        },
        "attributeDetails": {
            "1597489127": {"type": "String", "name": "EXTERNAL_ID"},
            "447500851": {"type": "String", "name": "ACCOUNT"},
            "2047205742": {"type": "Date", "name": "ACCOUNT_ACTIVATION_DATE"},
            "1068616960": {"type": "Date", "name": "ACCOUNT_PROVISION_DATE"},
            "908881601": {"type": "Long", "name": "ACCOUNT_STATE"},
            "1966426172": {"type": "Date", "name": "ACCOUNT_STATE_DATE"},
            "427862433": {"type": "String", "name": "AREA_CODE"},
            "1944018544": {"type": "String", "name": "CLIENT_OWNER"},
            "2020041941": {"type": "Long", "name": "CLIENT_TYPE"},
            "29905344": {"type": "Long", "name": "COMPANY_OPERATOR"},
            "1095579373": {"type": "String", "name": "GEOGRAPHICAL_STATE"},
            "1667261676": {"type": "Long", "name": "MSISDN"},
            "741842957": {"type": "Long", "name": "MULTI_OPERATION"},
            "1957846968": {"type": "String", "name": "NOTIFY_PERMISSIONS"},
            "1650737577": {"type": "Long", "name": "PORTABILITY_SITUATION"},
            "1358620105": {"type": "Long", "name": "PRODUCT_TYPE"},
            "1190622368": {"type": "Long", "name": "PROFILE"},
            "569463775": {"type": "Date", "name": "PROFILE_DATE"},
            "1760625139": {"type": "Long", "name": "REASON_CODE"},
            "1581479658": {"type": "String", "name": "GRUPO CONTROLE UNIVERSAL"},
            "579515748": {"type": "String", "name": "TIPO_CHIP"},
        },
    }

    return payload, external_id


def apply_scenario_to_payload(payload: Dict[str, Any], scenario: Scenario) -> Dict[str, Any]:
    payload["attributes"][ATTR_CLIENT_TYPE] = str(scenario.client_type)
    payload["attributes"][ATTR_ACCOUNT_STATE] = str(scenario.account_state)
    return payload


def send_event(payload: Dict[str, Any]) -> requests.Response:
    last_exception: Optional[Exception] = None

    for attempt in range(1, API_RETRY_ATTEMPTS + 1):
        try:
            log("STEP", f"API tentativa {attempt}/{API_RETRY_ATTEMPTS} com timeout={TIMEOUT_SECONDS}s")
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=TIMEOUT_SECONDS)

            # Retry on transient server errors
            if response.status_code >= 500 and attempt < API_RETRY_ATTEMPTS:
                log("ERROR", f"API status {response.status_code} (transiente). Nova tentativa em {API_RETRY_SLEEP}s.")
                time.sleep(API_RETRY_SLEEP)
                continue

            return response

        except requests.Timeout as exc:
            last_exception = exc
            log("ERROR", f"Timeout na API (tentativa {attempt}/{API_RETRY_ATTEMPTS}): {exc}")
            if attempt < API_RETRY_ATTEMPTS:
                time.sleep(API_RETRY_SLEEP)
        except requests.RequestException as exc:
            last_exception = exc
            log("ERROR", f"Erro de rede/API (tentativa {attempt}/{API_RETRY_ATTEMPTS}): {exc}")
            if attempt < API_RETRY_ATTEMPTS:
                time.sleep(API_RETRY_SLEEP)

    if last_exception:
        raise last_exception

    raise RuntimeError("Falha inesperada em send_event sem exceção capturada.")


def connect_db():
    if oracledb is None:
        log("STEP", "oracledb não disponível no ambiente; validação de DB será ignorada.")
        return None

    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)
        log("SUCCESS", "Conexão DB criada com sucesso.")
        return conn
    except Exception as exc:
        log("ERROR", f"Falha ao conectar DB: {exc}")
        log("ERROR", traceback.format_exc())
        return None


def fetch_discovery_and_campaign(conn, external_id: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    if conn is None:
        return None, []

    query_discovery = """
        SELECT CUSTOMER_ID, EXTERNAL_ID
        FROM CUST_DISCOVERY
        WHERE EXTERNAL_ID = :external_id
    """

    query_campaign = """
        SELECT ID_CUSTOMER, ID_CONTRACT, CREATED_DATE, UPDATED_DATE
        FROM CUST_CAMPAIGNS
        WHERE ID_CUSTOMER = :id_customer
    """

    cursor = None

    try:
        cursor = conn.cursor()
        for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
            log("STEP", f"DB tentativa {attempt}/{DB_RETRY_ATTEMPTS} para external_id={external_id}")
            try:
                cursor.execute(query_discovery, {"external_id": external_id})
                row = cursor.fetchone()
            except Exception as exc:
                log("ERROR", f"Erro ao consultar CUST_DISCOVERY na tentativa {attempt}: {exc}")
                if attempt < DB_RETRY_ATTEMPTS:
                    time.sleep(DB_RETRY_SLEEP)
                continue

            if row:
                customer_id = row[0]
                discovery = {"CUSTOMER_ID": row[0], "EXTERNAL_ID": row[1]}

                try:
                    cursor.execute(query_campaign, {"id_customer": customer_id})
                    campaigns_rows = cursor.fetchall() or []
                except Exception as exc:
                    log("ERROR", f"Erro ao consultar CUST_CAMPAIGNS para customer_id={customer_id}: {exc}")
                    if attempt < DB_RETRY_ATTEMPTS:
                        time.sleep(DB_RETRY_SLEEP)
                    continue
                campaigns = [
                    {
                        "ID_CUSTOMER": r[0],
                        "ID_CONTRACT": r[1],
                        "CREATED_DATE": str(r[2]),
                        "UPDATED_DATE": str(r[3]),
                    }
                    for r in campaigns_rows
                ]
                return discovery, campaigns

            log("STEP", f"External_id ainda não encontrado em CUST_DISCOVERY. Aguardando {DB_RETRY_SLEEP}s...")
            time.sleep(DB_RETRY_SLEEP)
    except Exception as exc:
        log("ERROR", f"Falha inesperada durante validação DB: {exc}")
        log("ERROR", traceback.format_exc())
    finally:
        if cursor is not None:
            cursor.close()

    return None, []


def run_scenario(scenario: Scenario, conn) -> Dict[str, Any]:
    log("SCENARIO", f"{scenario.name} | client_type={scenario.client_type} | account_state={scenario.account_state} | should_enter={scenario.should_enter}")

    msisdn = generate_msisdn()
    payload, external_id = build_prepaid_payload_template(msisdn)
    payload = apply_scenario_to_payload(payload, scenario)

    log("STEP", f"MSISDN gerado: {msisdn}; external_id: {external_id}")
    log("STEP", "Enviando request processEvent...")

    result: Dict[str, Any] = {
        "scenario": scenario.name,
        "msisdn": msisdn,
        "external_id": external_id,
        "expected_should_enter": scenario.should_enter,
        "http_ok": False,
        "http_status": None,
        "response_text": "",
        "db_discovery_found": None,
        "db_campaign_found": None,
        "validation_reason": "",
        "root_cause_suggestion": "",
        "actual_should_enter": None,
        "passed": False,
        "limited_validation": False,
    }

    try:
        response = send_event(payload)
        result["http_status"] = response.status_code
        result["response_text"] = response.text[:500]
        result["http_ok"] = response.status_code in (200, 201, 202)
        if result["http_ok"]:
            log("SUCCESS", f"API respondeu {response.status_code}.")
        else:
            log("ERROR", f"API respondeu {response.status_code}. body={response.text[:300]}")
            return result
    except Exception as exc:
        log("ERROR", f"Falha no request: {exc}")
        log("ERROR", traceback.format_exc())
        return result

    log("STEP", "Validando DB (CUST_DISCOVERY / CUST_CAMPAIGNS) quando disponível...")
    discovery, campaigns = fetch_discovery_and_campaign(conn, external_id)

    if conn is None:
        # Regra de validação real exige DB (CUST_DISCOVERY + CUST_CAMPAIGNS).
        result["limited_validation"] = True
        result["validation_reason"] = "DB indisponível: não foi possível validar comportamento real da campanha."
        result["root_cause_suggestion"] = "DB indisponível no ambiente de teste."
        result["actual_should_enter"] = None
        result["passed"] = False
        log("ERROR", f"FAIL | {result['validation_reason']}")
        log("CAUSE", result["root_cause_suggestion"])
        return result

    discovery_found = discovery is not None
    campaign_found = len(campaigns) > 0

    result["db_discovery_found"] = discovery_found
    result["db_campaign_found"] = campaign_found
    result["actual_should_enter"] = campaign_found

    # Validation rules:
    # 1) Customer must exist in CUST_DISCOVERY
    # 2) Enter campaign only when expected
    discovery_ok = discovery_found
    campaign_behavior_ok = campaign_found == scenario.should_enter
    result["passed"] = result["http_ok"] and discovery_ok and campaign_behavior_ok

    if not result["http_ok"]:
        result["validation_reason"] = "HTTP request não foi bem-sucedido."
    elif not discovery_ok:
        result["validation_reason"] = "Cliente não encontrado em CUST_DISCOVERY."
    elif not campaign_behavior_ok:
        result["validation_reason"] = (
            f"Comportamento inválido em CUST_CAMPAIGNS. expected_enter={scenario.should_enter}, found_campaign={campaign_found}."
        )
    else:
        result["validation_reason"] = "Validação completa OK."

    result["root_cause_suggestion"] = suggest_root_cause(
        scenario=scenario,
        http_ok=result["http_ok"],
        http_status=result["http_status"],
        discovery_found=discovery_found,
        campaign_found=campaign_found,
    )

    if result["passed"]:
        log(
            "SUCCESS",
            f"PASS | discovery={discovery_found} campaign={campaign_found} expected_enter={scenario.should_enter}",
        )
    else:
        log(
            "ERROR",
            f"FAIL | discovery={discovery_found} campaign={campaign_found} expected_enter={scenario.should_enter} | reason={result['validation_reason']}",
        )
        log("CAUSE", result["root_cause_suggestion"])

    return result


def main() -> int:
    scenarios = [
        Scenario("Pre + Barred", client_type=1, account_state=3, should_enter=True),
        Scenario("Pre + Cancelled", client_type=1, account_state=4, should_enter=True),
        Scenario("Pre + Deactivated", client_type=1, account_state=8, should_enter=True),
        Scenario("Pre + Active", client_type=1, account_state=2, should_enter=False),
        Scenario("Post + Barred", client_type=2, account_state=3, should_enter=False),
        Scenario("Control + Barred", client_type=3, account_state=3, should_enter=False),
    ]

    log("STEP", f"Iniciando teste emergencial de retenção pré-pago. Cenários={len(scenarios)}")
    log("STEP", f"URL alvo: {URL}")

    conn = None
    results: List[Dict[str, Any]] = []

    try:
        conn = connect_db()
        for scenario in scenarios:
            try:
                results.append(run_scenario(scenario, conn))
            except Exception as exc:
                log("ERROR", f"Falha inesperada no cenário '{scenario.name}': {exc}")
                log("ERROR", traceback.format_exc())
                results.append(
                    {
                        "scenario": scenario.name,
                        "expected_should_enter": scenario.should_enter,
                        "passed": False,
                        "error": str(exc),
                    }
                )
    except Exception as exc:
        log("ERROR", f"Falha geral na execução do teste: {exc}")
        log("ERROR", traceback.format_exc())
    finally:
        if conn is not None:
            try:
                conn.close()
                log("STEP", "Conexão DB encerrada.")
            except Exception as exc:
                log("ERROR", f"Erro ao encerrar conexão DB: {exc}")

    passed = sum(1 for r in results if r.get("passed"))
    failed = len(results) - passed

    log("STEP", "Resumo final:")
    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        log(
            "SUCCESS" if status == "PASS" else "ERROR",
            f"{status} | scenario={r.get('scenario')} | expected_enter={r.get('expected_should_enter')} | actual_enter={r.get('actual_should_enter')} | reason={r.get('validation_reason', '')}",
        )
    print(json.dumps(results, indent=2, ensure_ascii=False))
    log("SUCCESS" if failed == 0 else "ERROR", f"Total={len(results)} | Passed={passed} | Failed={failed}")

    # If something catastrophic happened before any scenario, fail loudly
    if not results:
        return 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
