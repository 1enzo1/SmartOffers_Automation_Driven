import subprocess
from pathlib import Path


FORBIDDEN_SUFFIXES = (".dbp", ".zip")
FORBIDDEN_NAMES = {".env"}
HIGH_CONFIDENCE_PATTERNS = (
    "-----BEGIN PRIVATE KEY-----",
    "Authorization: Bearer ",
    "password = \"",
    "password=\"",
)


def _tracked_files():
    result = subprocess.run(
        ["git", "ls-files"], check=True, text=True, capture_output=True
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def test_tracked_tree_excludes_runtime_secret_artifacts():
    files = _tracked_files()
    assert not any(path.name in FORBIDDEN_NAMES for path in files)
    assert not any("local_secrets" in path.parts for path in files)
    assert not any(path.suffix.lower() in FORBIDDEN_SUFFIXES for path in files)


def test_tracked_text_has_no_high_confidence_secret_material():
    for path in _tracked_files():
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            lowered = line.lower()
            if any(token in lowered for token in ("fake-", "placeholder", "example", "dummy")):
                continue
            for pattern in HIGH_CONFIDENCE_PATTERNS:
                assert pattern not in line, f"tracked file violates secret rule: {path.name}"
