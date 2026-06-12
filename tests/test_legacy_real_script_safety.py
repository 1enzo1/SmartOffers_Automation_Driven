import ast
import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCRIPTS = (
    "test_campaign_api_variante.py",
    "test_campaign_api_variante_copy.py",
)
GUARD_ENV = "SMARTOFFERS_ALLOW_LEGACY_REAL_SCRIPT"
GUARD_VALUE = "YES_I_UNDERSTAND"


def test_legacy_scripts_do_not_execute_real_paths_on_import(monkeypatch):
    for script_name in LEGACY_SCRIPTS:
        module = _load_script_with_blocking_fakes(script_name, monkeypatch)

        assert module.LEGACY_REAL_SCRIPT_ENV == GUARD_ENV
        assert module.LEGACY_REAL_SCRIPT_CONFIRMATION == GUARD_VALUE
        assert callable(module.montar_payload_pos)
        assert callable(module.montar_payload_pre)


def test_legacy_scripts_abort_without_manual_guard(monkeypatch):
    monkeypatch.delenv(GUARD_ENV, raising=False)

    for script_name in LEGACY_SCRIPTS:
        module = _load_script_with_blocking_fakes(script_name, monkeypatch)

        with pytest.raises(SystemExit) as exc_info:
            module.ensure_legacy_real_script_allowed()

        assert "Execucao real bloqueada" in str(exc_info.value)


def test_legacy_scripts_keep_manual_execution_path_when_guard_is_set(monkeypatch):
    monkeypatch.setenv(GUARD_ENV, GUARD_VALUE)

    for script_name in LEGACY_SCRIPTS:
        module = _load_script_with_blocking_fakes(script_name, monkeypatch)
        calls = []

        class FakeConnection:
            def close(self):
                calls.append("close")

        monkeypatch.setattr(module, "conectar_db", lambda: calls.append("connect") or FakeConnection())
        monkeypatch.setattr(module, "executar_pos", lambda *args: calls.append(("pos", args[0])))
        monkeypatch.setattr(module, "executar_pre", lambda *args: calls.append("pre"))

        assert module.main() == 0
        assert calls[0] == "connect"
        assert "close" in calls
        assert any(call == "pre" or call[0] == "pos" for call in calls if call != "connect")


def test_legacy_scripts_read_normalized_runtime_env(monkeypatch):
    for script_name in LEGACY_SCRIPTS:
        module = _load_script_with_blocking_fakes(script_name, monkeypatch)
        calls = []

        monkeypatch.setenv("SMARTOFFERS_API_URL", "fake-normalized-api-url")
        monkeypatch.setenv("SMARTOFFERS_DB_DSN", "fake-normalized-db-dsn")
        monkeypatch.setenv("SMARTOFFERS_DB_USER", "fake-normalized-db-user")
        monkeypatch.setenv("SMARTOFFERS_DB_PASSWORD", "fake-normalized-db-password")
        monkeypatch.setenv("SMARTOFFERS_ORACLE_CLIENT_LIB_DIR", "fake-oracle-client-dir")

        fake_oracledb = types.SimpleNamespace(
            init_oracle_client=lambda **kwargs: calls.append(("init", kwargs)),
            connect=lambda **kwargs: calls.append(("connect", kwargs)) or object(),
        )
        monkeypatch.setattr(module, "oracledb", fake_oracledb)

        assert module.get_smartoffers_api_url() == "fake-normalized-api-url"
        module.conectar_db()

        assert calls[0] == ("init", {"lib_dir": "fake-oracle-client-dir"})
        assert calls[1] == (
            "connect",
            {
                "user": "fake-normalized-db-user",
                "password": "fake-normalized-db-password",
                "dsn": "fake-normalized-db-dsn",
            },
        )


def test_legacy_scripts_fail_fast_when_normalized_runtime_env_is_missing(monkeypatch):
    for script_name in LEGACY_SCRIPTS:
        module = _load_script_with_blocking_fakes(script_name, monkeypatch)
        monkeypatch.delenv("SMARTOFFERS_API_URL", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            module.get_smartoffers_api_url()

        assert "Config runtime ausente: SMARTOFFERS_API_URL" in str(exc_info.value)


def test_legacy_scripts_guard_before_db_connection_in_main():
    for script_name in LEGACY_SCRIPTS:
        tree = _parse_script(script_name)
        main_func = _function_def(tree, "main")

        first_statement = main_func.body[0]
        assert _call_name(first_statement) == "ensure_legacy_real_script_allowed"
        assert "conectar_db" in _call_names(main_func)


def test_legacy_scripts_only_run_main_under_dunder_main():
    for script_name in LEGACY_SCRIPTS:
        tree = _parse_script(script_name)
        module_body_calls = [
            _call_name(statement)
            for statement in tree.body
            if not isinstance(statement, (ast.FunctionDef, ast.Import, ast.ImportFrom, ast.Assign))
        ]

        assert "conectar_db" not in module_body_calls
        assert "executar_pos" not in module_body_calls
        assert "executar_pre" not in module_body_calls
        assert any(_is_dunder_main_guard(statement) for statement in tree.body)


def _load_script_with_blocking_fakes(script_name, monkeypatch):
    fake_requests = types.ModuleType("requests")

    def fail_post(*args, **kwargs):
        raise AssertionError("requests.post must not run during import or guarded tests")

    fake_requests.post = fail_post

    fake_oracledb = types.ModuleType("oracledb")
    fake_oracledb.init_oracle_client = _fail_oracle_call
    fake_oracledb.makedsn = _fail_oracle_call
    fake_oracledb.connect = _fail_oracle_call

    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    monkeypatch.setitem(sys.modules, "oracledb", fake_oracledb)

    module_name = f"_legacy_safety_{Path(script_name).stem}"
    spec = importlib.util.spec_from_file_location(module_name, ROOT / script_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _fail_oracle_call(*args, **kwargs):
    raise AssertionError("oracledb must not run during import or guarded tests")


def _parse_script(script_name):
    return ast.parse((ROOT / script_name).read_text(encoding="utf-8"))


def _function_def(tree, name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _call_name(node):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        return _func_name(node.value.func)
    if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
        return _func_name(node.exc.func)
    return None


def _call_names(node):
    return {
        _func_name(child.func)
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
    }


def _func_name(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_dunder_main_guard(node):
    if not isinstance(node, ast.If):
        return False
    comparison = node.test
    if not isinstance(comparison, ast.Compare):
        return False
    left_is_name = isinstance(comparison.left, ast.Name) and comparison.left.id == "__name__"
    has_main_literal = any(
        isinstance(comparator, ast.Constant) and comparator.value == "__main__"
        for comparator in comparison.comparators
    )
    calls_main = any(_func_name(child.func) == "main" for child in ast.walk(node) if isinstance(child, ast.Call))
    return left_is_name and has_main_literal and calls_main
