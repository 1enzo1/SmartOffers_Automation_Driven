import hashlib
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from .models import ApiCatalogEntry


HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
SAFE_HEADER_VALUE_NAMES = {
    "content-type",
}
PATH_PARAM_PLACEHOLDER = "<PATH_PARAM>"
SENSITIVE_PATH_SEGMENT_HINTS = {
    "account",
    "accounts",
    "auth",
    "authorization",
    "client",
    "clients",
    "contract",
    "contracts",
    "cpf",
    "cnpj",
    "customer",
    "customers",
    "document",
    "documents",
    "msisdn",
    "phone",
    "phones",
    "session",
    "sessions",
    "subscriber",
    "subscribers",
    "token",
    "tokens",
    "user",
    "users",
}

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s\"']+")
BRUNO_VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
SECRET_HINT_RE = re.compile(
    r"(?i)(authorization|bearer|token|password|passwd|senha|secret|client_secret|api[-_]?key)"
)
UUID_RE = re.compile(
    r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
ALPHANUM_IDENTIFIER_RE = re.compile(r"(?i)^[a-z0-9][a-z0-9_-]{5,}$")


def parse_api_catalog_zip(zip_path, environment_json_paths=None):
    entries = []
    source_files = []
    collection_environment_refs = {}
    collection_environment_variables = {}
    global_environment_variables = {}

    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not _is_supported_file(info.filename):
                continue

            raw = archive.read(info).decode("utf-8", errors="replace")
            source_files.append((info.filename, raw))
            environment = _parse_environment_definition(info.filename, raw)
            if environment:
                collection = _source_collection(info.filename)
                collection_environment_refs.setdefault(collection, []).extend(
                    environment["environment_refs"]
                )
                collection_environment_variables.setdefault(collection, {}).update(
                    environment["environment_variables"]
                )
                continue

    for environment_path in environment_json_paths or []:
        raw = Path(environment_path).read_text(encoding="utf-8")
        environment = _parse_environment_definition(str(environment_path), raw)
        if environment:
            global_environment_variables.update(environment["environment_variables"])

    for source_file, raw in source_files:
        if _parse_environment_definition(source_file, raw):
            continue

        collection = _source_collection(source_file)
        environment_variables = {
            **global_environment_variables,
            **collection_environment_variables.get(collection, {}),
        }
        parsed = parse_catalog_file(
            source_file,
            raw,
            environment_variables=environment_variables,
            inherited_environment_refs=collection_environment_refs.get(collection, []),
        )
        if parsed:
            entries.append(parsed)

    return sorted(entries, key=lambda item: (item.source_collection, item.name, item.api_id))


def parse_catalog_file(
    source_file,
    raw_text,
    environment_variables=None,
    inherited_environment_refs=None,
):
    suffix = Path(source_file).suffix.lower()
    if suffix == ".bru":
        return _parse_bru(source_file, raw_text, environment_variables, inherited_environment_refs)
    if suffix in {".yml", ".yaml"}:
        return _parse_yml(source_file, raw_text, environment_variables, inherited_environment_refs)
    return None


def _parse_bru(source_file, raw_text, environment_variables=None, inherited_environment_refs=None):
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
        environment_variables=environment_variables,
        inherited_environment_refs=inherited_environment_refs,
    )


def _parse_yml(source_file, raw_text, environment_variables=None, inherited_environment_refs=None):
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
        environment_variables=environment_variables,
        inherited_environment_refs=inherited_environment_refs,
    )


def _build_entry(
    source_file,
    raw_text,
    name,
    method,
    url,
    headers,
    payload,
    environment_variables=None,
    inherited_environment_refs=None,
):
    collection = _source_collection(source_file)
    environment_variables = environment_variables or {}
    inherited_environment_refs = inherited_environment_refs or []
    url_variables = _url_variables(url)
    base_environment_refs = _base_environment_refs(
        source_file,
        raw_text,
        url,
        environment_variables,
        inherited_environment_refs,
    )
    host_placeholders = _host_placeholders(url, environment_variables, base_environment_refs)
    environment_refs = _environment_refs(
        source_file,
        raw_text,
        url,
        environment_variables,
        inherited_environment_refs,
        host_placeholders,
    )
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
        environment_variables=sorted(
            variable for variable in url_variables if variable in environment_variables
        ),
        host_placeholder=host_placeholders[0] if host_placeholders else "",
        host_placeholders=host_placeholders,
        payload_base=_sanitize_payload(payload),
    )


def _is_supported_file(filename):
    suffix = Path(filename).suffix.lower()
    return suffix in {".bru", ".yml", ".yaml", ".json"}


def _looks_like_environment_yml(raw_text):
    return bool(
        re.search(r"(?mi)^\s*variables:\s*$", raw_text)
        and re.search(r"(?mi)^\s*-\s*name:\s*", raw_text)
        and re.search(r"(?mi)^\s*value:\s*", raw_text)
    )


def _parse_environment_definition(source_file, raw_text):
    suffix = Path(source_file).suffix.lower()
    if suffix in {".yml", ".yaml"} and _looks_like_environment_yml(raw_text):
        name = _extract_first(r"(?mi)^\s*name:\s*(.+?)\s*$", raw_text) or source_file
        variables = re.findall(r"(?mi)^\s*-\s*name:\s*([A-Za-z0-9_.-]+)\s*$", raw_text)
        return _build_environment_definition(name, variables)

    if suffix == ".json":
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return None

        variables_data = data.get("variables") if isinstance(data, dict) else None
        if not isinstance(variables_data, list):
            return None

        variables = [
            str(item.get("name", "")).strip()
            for item in variables_data
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
        if not variables:
            return None

        name = str(data.get("name") or source_file)
        return _build_environment_definition(name, variables)

    return None


def _build_environment_definition(name, variables):
    environment_refs = []
    for env in ("QA1", "QA2", "QA3", "QA4"):
        if re.search(rf"(?i)\b{env}\b", name):
            environment_refs.append(env)

    environment = environment_refs[0] if environment_refs else ""
    allowed_variables = {}
    for variable in variables:
        normalized = variable.upper()
        allowed_variables[normalized] = {
            "environment": environment,
            "placeholder": _variable_host_placeholder(normalized, environment),
        }

    return {
        "environment_refs": environment_refs,
        "environment_variables": allowed_variables,
    }


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
    in_headers = False
    headers_indent = 0
    headers_brace_block = False

    for line in raw_text.splitlines():
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip())
        if in_headers:
            if headers_brace_block and re.match(r"\s*}\s*$", line):
                in_headers = False
                headers_brace_block = False
                current_name = None
                continue
            if (
                not headers_brace_block
                and indent <= headers_indent
                and not re.match(r"\s*headers\s*:\s*$", line, flags=re.I)
            ):
                in_headers = False
                current_name = None

        if not in_headers:
            headers_match = re.match(r"\s*headers\s*(:|\{)\s*$", line, flags=re.I)
            if headers_match:
                in_headers = True
                headers_indent = indent
                headers_brace_block = headers_match.group(1) == "{"
            continue

        direct_match = re.match(r"\s*([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", line)
        if direct_match and not re.match(r"\s*(name|value)\s*:", line, flags=re.I):
            headers.append(
                {
                    "name": _strip_quotes(direct_match.group(1).strip()),
                    "value": _sanitize_header_value(
                        direct_match.group(1).strip(),
                        direct_match.group(2).strip(),
                    ),
                }
            )
            current_name = None
            continue

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
    if not marker:
        return {}

    start_at = marker.end()
    json_start = _find_json_start(raw_text, start_at)
    if json_start < 0:
        return {}

    json_text = _balanced_json_value(raw_text, json_start)
    if not json_text:
        return {}

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return {"raw": "<UNPARSED_JSON_BODY>"}


def _find_json_start(text, start):
    match = re.search(r"[\{\[]", text[start:])
    if not match:
        return -1
    return start + match.start()


def _balanced_json_value(text, start):
    pairs = {"{": "}", "[": "]"}
    expected = []
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
        elif char in pairs:
            expected.append(pairs[char])
        elif char in pairs.values():
            if not expected or char != expected[-1]:
                return ""
            expected.pop()
            if not expected:
                return text[start : index + 1]
    return ""


def _sanitize_payload(value, parent_key="", path=()):
    if isinstance(value, dict):
        return {
            str(key): _sanitize_payload(item, str(key), (*path, str(key)))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_payload(item, parent_key, path) for item in value[:3]]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return "<NUMBER>"
    if isinstance(value, str):
        if _is_safe_payload_label(parent_key, path) and not SECRET_HINT_RE.search(value):
            return _mask_sensitive_text(value)
        return "<STRING>"
    return "<VALUE>"


def _is_safe_payload_label(parent_key, path):
    if parent_key == "operation":
        return True

    return (
        len(path) >= 3
        and path[-3] == "attributeDetails"
        and parent_key in {"type", "name"}
    )


def _sanitize_header_value(name, value):
    normalized_name = _normalize(name)
    sanitized_value = _mask_sensitive_text(_strip_quotes(str(value).strip()))

    if normalized_name not in SAFE_HEADER_VALUE_NAMES:
        return "<REDACTED>"
    if SECRET_HINT_RE.search(sanitized_value):
        return "<REDACTED>"
    return sanitized_value


def _safe_path(url):
    url = _strip_quotes(str(url).strip())
    if not url:
        return "/"

    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return _sanitize_path_segments(parsed.path or "/")

    if url.startswith("/"):
        return _sanitize_path_segments(urlparse(url).path or "/")

    match = re.search(r"(?:\{\{\s*[A-Za-z0-9_.-]+\s*\}\}|<[^>]+>|[^/\s\"']+)(/[^\s\"'?#]*)", url)
    if match:
        return _sanitize_path_segments(match.group(1) or "/")

    if parsed.path and "/" in parsed.path:
        return _sanitize_path_segments(parsed.path)

    return "/"


def _sanitize_path_segments(path):
    segments = path.split("/")
    sanitized = [
        PATH_PARAM_PLACEHOLDER if should_redact else segment
        for segment, should_redact in _iter_sanitized_path_segments(segments)
    ]
    return "/".join(sanitized) or "/"


def _iter_sanitized_path_segments(segments):
    sensitive_context = False
    for segment in segments:
        should_redact = _path_segment_is_value(segment, sensitive_context)
        yield segment, should_redact
        sensitive_context = _path_segment_indicates_entity(segment) or should_redact


def _path_segment_is_value(segment, sensitive_context=False):
    if not segment:
        return False

    if re.fullmatch(r"\d{8,}", segment):
        return True

    if not sensitive_context:
        return False

    normalized = _normalize(segment)
    compact = re.sub(r"[^a-z0-9]", "", normalized)
    return bool(UUID_RE.fullmatch(normalized) or ALPHANUM_IDENTIFIER_RE.fullmatch(normalized) and _looks_like_identifier_token(compact))


def _path_segment_indicates_entity(segment):
    normalized = _normalize(segment)
    if normalized in SENSITIVE_PATH_SEGMENT_HINTS:
        return True

    parts = [part for part in re.split(r"[^a-z0-9]+", normalized) if part]
    return any(part in SENSITIVE_PATH_SEGMENT_HINTS for part in parts)


def _looks_like_identifier_token(compact_segment):
    return (
        len(compact_segment) >= 6
        and any(char.isalpha() for char in compact_segment)
        and any(char.isdigit() for char in compact_segment)
    )


def _environment_refs(
    source_file,
    raw_text,
    url,
    environment_variables=None,
    inherited_environment_refs=None,
    host_placeholders=None,
):
    environment_variables = environment_variables or {}
    inherited_environment_refs = inherited_environment_refs or []
    host_placeholders = host_placeholders or []
    haystack = f"{source_file}\n{raw_text}\n{url}"
    refs = _base_environment_refs(
        source_file,
        raw_text,
        url,
        environment_variables,
        inherited_environment_refs,
    )

    if re.search(r"(?i)\bprod\b", haystack):
        refs.append("PROD_REFERENCE_ONLY")
    if re.search(r"(?i)\blocalhost\b|127\.0\.0\.1|0\.0\.0\.0", haystack):
        refs.append("LOCALHOST_REFERENCE_ONLY")

    if IP_RE.search(haystack) or URL_RE.search(haystack) or BRUNO_VAR_RE.search(haystack):
        refs.extend(host_placeholders or [_host_placeholder(refs)])

    return _ordered_unique(refs)


def _base_environment_refs(source_file, raw_text, url, environment_variables, inherited_environment_refs):
    haystack = f"{source_file}\n{raw_text}\n{url}"
    refs = list(inherited_environment_refs)
    for env in ("QA1", "QA2", "QA3", "QA4"):
        if re.search(rf"(?i)\b{env}\b", haystack):
            refs.append(env)

    for variable in _url_variables(url):
        environment = environment_variables.get(variable, {}).get("environment")
        if environment:
            refs.append(environment)

    return _ordered_unique(refs)


def _host_placeholder(refs):
    for env in ("QA4", "QA3", "QA2", "QA1"):
        if env in refs:
            return f"<{env}_HOST>"
    return "<HOST>"


def _host_placeholders(url, environment_variables, inherited_environment_refs=None):
    inherited_environment_refs = inherited_environment_refs or []
    placeholders = []
    for variable in _url_variables(url):
        info = environment_variables.get(variable)
        if info:
            placeholders.append(info["placeholder"])
        else:
            environment = _first_supported_environment(inherited_environment_refs)
            placeholders.append(_variable_host_placeholder(variable, environment))

    if placeholders:
        return _ordered_unique(placeholders)

    refs = _ordered_unique(inherited_environment_refs)
    if URL_RE.search(str(url)) or IP_RE.search(str(url)):
        return [_host_placeholder(refs)]
    return []


def _url_variables(url):
    return [variable.upper() for variable in BRUNO_VAR_RE.findall(str(url or ""))]


def _variable_host_placeholder(variable, environment=""):
    if environment:
        return f"<{environment}_{variable.upper()}_HOST>"
    return f"<{variable.upper()}_HOST>"


def _first_supported_environment(environment_refs):
    for env in ("QA4", "QA3", "QA2", "QA1"):
        if env in environment_refs:
            return env
    return ""


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
