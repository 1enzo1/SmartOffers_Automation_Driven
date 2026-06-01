import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path

from core.api_catalog.catalog import load_api_catalog
from core.api_catalog.parser import parse_api_catalog_zip, parse_catalog_file


def test_parser_masks_sensitive_hosts_headers_and_payload_values():
    scheme = "https"
    host = "qa4.example.invalid"
    credential = "credential" + "-value"
    raw = f"""
info:
  name: "Ativacao mockada"
  type: http
http:
  method: post
  url: {scheme}://{host}/ws/integration/online/process
  headers:
    - name: Content-Type
      value: application/json
    - name: Authorization
      value: {credential}
  body:
    type: json
    data: |-
      {{
        "operation": "processEvent",
        "extEventId": 123,
        "attributes": {{
          "1597489127": "ABC123"
        }}
      }}
"""

    entry = parse_catalog_file("SmartOffers Copy/Ativacao QA4.yml", raw)
    data = entry.to_dict()

    assert data["method"] == "POST"
    assert data["path"] == "/ws/integration/online/process"
    assert data["safe_for_real_execution"] is False
    assert data["execution_status"] == "blocked"
    assert data["environment_refs"] == ["QA4", "<QA4_HOST>"]
    assert data["supported_environments"] == ["QA4"]
    assert data["host_placeholder"] == "<QA4_HOST>"
    assert {"name": "Authorization", "value": "<REDACTED>"} in data["headers_expected"]
    assert data["payload_base"]["extEventId"] == "<NUMBER>"
    assert data["payload_base"]["attributes"]["1597489127"] == "<STRING>"
    serialized = json.dumps(data, ensure_ascii=False)
    assert host not in serialized
    assert credential not in serialized


def test_parser_uses_qa4_environment_json_without_exposing_values():
    base = Path(".pytest_tmp") / f"api_catalog_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
        env_ip = ".".join(["10", "20", "30", "40"])
        gateway_ip = ".".join(["192", "168", "1", "10"])
        env_path = base / "QA4_Copy.json"
        env_path.write_text(
            json.dumps(
                {
                    "name": "QA4 Copy",
                    "variables": [
                        {"name": "SMART_OFFERS_INT", "value": env_ip},
                        {"name": "GATEWAY", "value": gateway_ip},
                    ],
                }
            ),
            encoding="utf-8",
        )

        zip_path = base / "apis.zip"
        bru_text = """
meta {
  name: Ativacao via variavel
  type: http
}

post {
  url: {{SMART_OFFERS_INT}}/ws/integration/online/process
  body: json
}

body:json {
  {"operation": "processEvent", "extEventId": 123}
}
"""
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("SmartOffers Copy/Ativacao variavel.bru", bru_text)

        entries = parse_api_catalog_zip(zip_path, environment_json_paths=[env_path])
        data = entries[0].to_dict()
        serialized = json.dumps(data, ensure_ascii=False)

        assert data["path"] == "/ws/integration/online/process"
        assert data["environment_refs"] == ["QA4", "<QA4_SMART_OFFERS_INT_HOST>"]
        assert data["supported_environments"] == ["QA4"]
        assert data["environment_variables"] == ["SMART_OFFERS_INT"]
        assert data["host_placeholder"] == "<QA4_SMART_OFFERS_INT_HOST>"
        assert data["host_placeholders"] == ["<QA4_SMART_OFFERS_INT_HOST>"]
        assert env_ip not in serialized
        assert gateway_ip not in serialized
        assert data["execution_status"] == "blocked"
        assert data["safe_for_real_execution"] is False
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_versioned_catalog_does_not_expose_sensitive_values():
    data = {"apis": load_api_catalog()}
    serialized = json.dumps(data, ensure_ascii=False)

    assert data["apis"]
    assert not re.search(r"https?://", serialized)
    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", serialized)
    assert all(api["safe_for_real_execution"] is False for api in data["apis"])
    assert all(api["execution_status"] == "blocked" for api in data["apis"])
    assert not Path("QA4_Copy.json").exists()
    assert "SMART_OFFERS_INT" in serialized


def test_api_catalog_endpoint_lists_apis(app_client_factory):
    client, _ = app_client_factory("api-catalog")

    response = client.get("/api/api-catalog")

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == len(data["apis"])
    assert data["total"] > 0
    assert {
        "api_id",
        "name",
        "category",
        "method",
        "path",
        "environment_refs",
        "supported_environments",
        "execution_status",
        "safe_for_real_execution",
    }.issubset(data["apis"][0])


def test_api_catalog_endpoint_returns_detail_by_api_id(app_client_factory):
    client, _ = app_client_factory("api-catalog")
    first_api = client.get("/api/api-catalog").get_json()["apis"][0]

    response = client.get(f"/api/api-catalog/{first_api['api_id']}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["api"]["api_id"] == first_api["api_id"]
    assert data["api"]["safe_for_real_execution"] is False


def test_api_catalog_endpoint_returns_404_for_missing_api(app_client_factory):
    client, _ = app_client_factory("api-catalog")

    response = client.get("/api/api-catalog/api-inexistente")

    assert response.status_code == 404
    assert response.get_json()["erro"] == "api nao encontrada"
