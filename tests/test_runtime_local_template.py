import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_GITIGNORE_PATTERNS = {
    "local_secrets/",
    ".env.local",
    "*.local.env",
    "smartoffers_runtime_local.ps1",
    "*.dbp",
    ".dbeaver/",
    "**/.dbeaver/",
    ".dbeaver-data-sources.xml",
    "*dbeaver*data-sources*.xml",
    "*DBeaver*data-sources*.xml",
    "*connection*.zip",
    "*connections*.zip",
    "*evidence*.zip",
    "*evidencia*.zip",
    "*.zip",
}

REQUIRED_RUNTIME_ENV_VARS = {
    "SMARTOFFERS_QA4_API_URL",
    "SMARTOFFERS_QA4_DB_DSN",
    "SMARTOFFERS_QA4_DB_USER",
    "SMARTOFFERS_QA4_DB_PASSWORD",
    "SMARTOFFERS_ORACLE_CLIENT_LIB_DIR",
    "SMARTOFFERS_QA1_API_URL",
}


def test_gitignore_blocks_local_runtime_secret_files():
    patterns = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert REQUIRED_GITIGNORE_PATTERNS <= patterns


def test_runtime_template_uses_only_placeholder_assignments():
    template = ROOT / "docs" / "runtime" / "smartoffers_runtime_local.example.ps1"
    content = template.read_text(encoding="utf-8")

    for env_var in REQUIRED_RUNTIME_ENV_VARS:
        assert env_var in content

    active_assignments = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("$env:")
    ]
    assert active_assignments

    for assignment in active_assignments:
        match = re.fullmatch(r'\$env:([A-Z0-9_]+)\s*=\s*"(<[A-Z0-9_]+>)"', assignment)
        assert match, assignment
        assert match.group(1) == match.group(2).strip("<>")

    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", content)
    assert "://" not in content
