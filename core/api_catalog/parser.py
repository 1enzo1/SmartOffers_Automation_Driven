import hashlib
import json
import re
import unicodedata
import zipfile
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

from .models import ApiCatalogEntry


HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "apikey",
    "token",
    "access-token",
    "client-secret",
    "client_secret",
    "password",
    "senha",
    "secret",
}

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s\"']+")
BRUNO_VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
SECRET_HINT_RE = re.compile(
    r"(?i)(authorization|bearer|token|password|passwd|senha|secret|client_secret|api[-_]?key)"
)


def parse_api_catalog_zip(zip_path):
    entries = []
    collection_environments = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not _is_supported_file(info.filename):
                continue

            raw = archive.read(info).decode("utf-8", errors="replace")
            if Path(info.filename).suffix.lower() in {".yml", ".yaml"} and _looks_like_environment_yml(raw):
                collection = _source_collection(info.filename)
                collection_environments.setdefault(collection, set()).update(
                    _environment_refs(info.filename, raw, "")
                )
                continue

            parsed = parse_catalog_file(info.filename, raw)
            if parsed:
                entries.append(parsed)

    entries = [_with_collection_environments(entry, collection_environments) for entry in entries]
    return sorted(entries, key=lambda item: (item.source_collection, item.name, item.api_id))


def parse_catalog_file(source_file, raw_text):
    suffix = Path(source_file).suffix.lower()
    if suffix == ".bru":
        return _parse_bru(source_file, raw_text)
    if suffix in {".yml", ".yaml"}:
        return _parse_yml(source_file, raw_text)
    return None


def _parse_bru(source_file, raw_text):
    method = _extract_bru_method(raw_text)
    if not method:
        return None

    name = _extract_first(r"(?m)^\s*name:\s*(.+?)\s*$", raw_text) or Path(source_file).stem
    url = _extract_first(r"(?m)^\s*url:\s*(.+?)\s*$", raw_text) or ""
    payload = _extract_json_payload(raw_text)
    headers = _extract_headers(raw_text)

    return _build_entry(
        source_file=source_file,
        raw_text=raw_text,
        name=name,
        method=method,
        url=url,
        headers=headers,
        payload=payload,
    )


def _parse_yml(source_file, raw_text):
    if _looks_like_environment_yml(raw_text):
        return None

    method = _extract_first(r"(?mi)^\s*method:\s*([A-Za-z]+)\s*$", raw_text)
    if not method or method.lower() not in HTTP_METHODS:
        return None

    name = (
        _extract_first(r"(?mi)^\s*name:\s*[\"']?(.+?)[\"']?\s*$", raw_text)
        or Path(source_file).stem
    )
    url = _extract_first(r"(?mi)^\s*url:\s*(.+?)\s*$", raw_text) or ""
    payload = _extract_json_payload(raw_text)
    headers = _extract_headers(raw_text)

    return _build_entry(
        source_file=source_file,
        raw_text=raw_text,
        name=name,
        method=method,
        url=url,
        headers=headers,
        payload=payload,
    )


def _build_entry(source_file, raw_text, name, method, url, headers, payload):
    collection = _source_collection(source_file)
    environment_refs = _environment_refs(source_file, raw_text, url)
    supported_environments = [
        env for env in ("QA1", "QA2", "QA3", "QA4") if env in environment_refs
    ]
    path = _safe_path(url) or "/"
    normalized_name = _clean_text(name)
    category = _guess_category(f"{collection} {normalized_name} {path}")

    return ApiCatalogEntry(
        api_id=_api_id(method, path, source_file, normalized_name),
        name=normalized_name,
        category=category,
        method=method.upper(),
        path=path,
        environment_refs=environment_refs,
        supported_environments=supported_environments,
        execution_status="blocked",
        notes=_notes(environment_refs),
        safe_for_real_execution=False,
        source_collection=collection,
        source_file=source_file,
        headers_expected=headers,
        payload_base=_sanitize_payload(payload),
    )


def _with_collection_environments(entry, collection_environments):
    inherited = list(collection_environments.get(entry.source_collection, set()))
    if not inherited:
        return entry

    environment_refs = _ordered_unique([*entry.environment_refs, *inherited])
    supported_environments = [
        env for env in ("QA1", "QA2", "QA3", "QA4") if env in environment_refs
    ]
    return replace(
        entry,
        environment_refs=environment_refs,
        supported_environments=supported_environments,
        notes=_notes(environment_refs),
    )


def _is_supported_file(filename):
    suffix = Path(filename).suffix.lower()
    return suffix in {".bru", ".yml", ".yaml"}


def _looks_like_environment_yml(raw_text):
    return bool(
        re.search(r"(?mi)^\s*variables:\s*$", raw_text)
        and re.search(r"(?mi)^\s*-\s*name:\s*", raw_text)
        and re.search(r"(?mi)^\s*value:\s*", raw_text)
    )


def _extract_bru_method(raw_text):
    for method in HTTP_METHODS:
        if re.search(rf"(?m)^\s*{method}\s*\{{", raw_text):
            return method
    return None


def _extract_first(pattern, text):
    match = re.search(pattern, text)
    if not match:
        return None
    return _strip_quotes(match.group(1).strip())


def _extract_headers(raw_text):
    headers = []
    current_name = None
    for line in raw_text.splitlines():
        name_match = re.match(r"\s*-\s*name:\s*(.+?)\s*$", line) or re.match(
            r"\s*name:\s*(.+?)\s*$", line
        )
        if name_match:
            current_name = _strip_quotes(name_match.group(1).strip())
            continue

        value_match = re.match(r"\s*value:\s*(.+?)\s*$", line)
        if current_name and value_match:
            headers.append(
                {
                    "name": current_name,
                    "value": _sanitize_header_value(current_name, value_match.group(1).strip()),
                }
            )
            current_name = None

    return _dedupe_dicts(headers)


def _extract_json_payload(raw_text):
    marker = re.search(r"(?is)(body:json\s*\{|data:\s*\|[-+]?)", raw_text)
    start_at = marker.end() if marker else 0
    json_start = raw_text.find("{", start_at)
    if json_start < 0:
        return {}

    json_text = _balanced_object(raw_text, json_start)
    if not json_text:
        return {}

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return {"raw": "<UNPARSED_JSON_BODY>"}


def _balanced_object(text, start):
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def _sanitize_payload(value, parent_key=""):
    if isinstance(value, dict):
        return {str(key): _sanitize_payload(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item, parent_key) for item in value[:3]]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return "<NUMBER>"
    if isinstance(value, str):
        if parent_key in {"type", "name", "operation"} and not SECRET_HINT_RE.search(value):
            return _mask_sensitive_text(value)
        return "<STRING>"
    return "<VALUE>"


def _sanitize_header_value(name, value):
    normalized = _normalize(name)
    if normalized in SENSITIVE_HEADER_NAMES or SECRET_HINT_RE.search(value):
        return "<REDACTED>"
    return _mask_sensitive_text(_strip_quotes(value))


def _safe_path(url):
    url = _strip_quotes(str(url).strip())
    if not url:
        return "/"

    for variable in BRUNO_VAR_RE.findall(url):
        placeholder = f"<{variable.upper()}_HOST>"
        url = BRUNO_VAR_RE.sub(placeholder, url, count=1)

    parsed = urlparse(url)
    if parsed.path:
        return parsed.path

    match = re.search(r"(?:https?://)?(?:<[^>]+>|[^/\s\"']+)(/[^\s\"']*)", url)
    if match:
        return match.group(1)

    return "/"


def _environment_refs(source_file, raw_text, url):
    haystack = f"{source_file}\n{raw_text}\n{url}"
    refs = []
    for env in ("QA1", "QA2", "QA3", "QA4"):
        if re.search(rf"(?i)\b{env}\b", haystack):
            refs.append(env)

    if re.search(r"(?i)\bprod\b", haystack):
        refs.append("PROD_REFERENCE_ONLY")
    if re.search(r"(?i)\blocalhost\b|127\.0\.0\.1|0\.0\.0\.0", haystack):
        refs.append("LOCALHOST_REFERENCE_ONLY")

    if IP_RE.search(haystack) or URL_RE.search(haystack) or BRUNO_VAR_RE.search(haystack):
        refs.append(_host_placeholder(refs))

    return _ordered_unique(refs)


def _host_placeholder(refs):
    for env in ("QA4", "QA3", "QA2", "QA1"):
        if env in refs:
            return f"<{env}_HOST>"
    return "<HOST>"


def _source_collection(source_file):
    parts = Path(source_file).parts
    return parts[0] if len(parts) > 1 else ""


def _guess_category(text):
    normalized = _normalize(text)
    rules = [
        ("habilitacao", ("habilitacao", "vivo next")),
        ("campanha", ("campanha", "promocao", "transicao")),
        ("recarga", ("recarga", "saldo", "limiar")),
        ("voz_dados", ("voz", "dados")),
        ("cobranca", ("cobranca", "cca")),
        ("la_xml", ("retorno la", "xml")),
        ("sva", ("sva",)),
        ("portabilidade", ("portabilidade",)),
        ("smartoffers", ("smartoffers",)),
        ("uif", ("uif",)),
    ]
    for category, tokens in rules:
        if any(token in normalized for token in tokens):
            return category
    return "outros"


def _notes(environment_refs):
    notes = [
        "Catalogado para analise local. Execucao real bloqueada no MVP7.5.",
    ]
    if "PROD_REFERENCE_ONLY" in environment_refs:
        notes.append("Referencia PROD mantida apenas como nome de colecao.")
    if "LOCALHOST_REFERENCE_ONLY" in environment_refs:
        notes.append("Referencia localhost mantida apenas como metadado.")
    return " ".join(notes)


def _api_id(method, path, source_file, name):
    source = f"{method.upper()}|{path}|{source_file}|{name}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    slug = _slugify(f"{method}-{name}")[:48].strip("-") or "api"
    return f"{slug}-{digest}"


def _slugify(value):
    normalized = _normalize(value)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def _normalize(value):
    ascii_text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore")
    return ascii_text.decode("ascii").lower()


def _clean_text(value):
    return _mask_sensitive_text(_strip_quotes(str(value).strip()))


def _strip_quotes(value):
    return value.strip().strip('"').strip("'")


def _mask_sensitive_text(value):
    value = URL_RE.sub("<URL>", str(value))
    value = IP_RE.sub("<IP>", value)
    value = SECRET_HINT_RE.sub("<SECRET_HINT>", value)
    return value


def _dedupe_dicts(items):
    seen = set()
    unique = []
    for item in items:
        key = tuple(sorted(item.items()))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _ordered_unique(items):
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique
