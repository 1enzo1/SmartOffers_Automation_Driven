from pathlib import Path

from tests.conftest import TIER_FILE_MAP


MANUAL_FILES = {
    "test_qa4_acm_manual_smoke.py",
    "test_qa4_bda_manual_smoke.py",
    "test_qa4_manual_smoke.py",
    "test_first_qa4_real_call_manual_gate.py",
}


def test_every_test_file_has_one_explicit_primary_tier():
    files = {p.name for p in Path("tests").glob("test_*.py")}
    assert files == set(TIER_FILE_MAP)
    assert all(tier in {"tier0", "tier1", "tier2", "tier3"} for tier in TIER_FILE_MAP.values())


def test_routine_tiers_exclude_manual_external_modules():
    routine = {name for name, tier in TIER_FILE_MAP.items() if tier in {"tier0", "tier1", "tier2"}}
    assert not routine.intersection(MANUAL_FILES)
    assert MANUAL_FILES == {name for name, tier in TIER_FILE_MAP.items() if tier == "tier3"}
