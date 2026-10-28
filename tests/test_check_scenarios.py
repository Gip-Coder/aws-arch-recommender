import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.check_scenarios import validate_scenarios


def test_validate_scenarios_passes_with_valid_files(tmp_path):
    s_dir = tmp_path / "scenarios"
    s_dir.mkdir()
    valid_scenario = {
        "id": "test-valid-1",
        "input_text": "A standard web application",
        "expected_pattern": "three_tier_web",
        "expected_services": ["CloudFront", "ApplicationLoadBalancer", "RDS_MultiAZ"],
    }
    (s_dir / "test1.json").write_text(json.dumps(valid_scenario), encoding="utf-8")
    errors = validate_scenarios(s_dir)
    assert not errors, f"Unexpected errors: {errors}"


def test_validate_scenarios_catches_invalid_pattern(tmp_path):
    s_dir = tmp_path / "scenarios"
    s_dir.mkdir()
    invalid_pattern = {
        "id": "test-invalid-pattern",
        "input_text": "Sample text",
        "expected_pattern": "non_existent_pattern",
        "expected_services": ["CloudFront"],
    }
    (s_dir / "test.json").write_text(json.dumps(invalid_pattern), encoding="utf-8")
    errors = validate_scenarios(s_dir)
    assert any("not defined in catalogue/patterns.yaml" in e for e in errors)


def test_validate_scenarios_catches_invalid_service(tmp_path):
    s_dir = tmp_path / "scenarios"
    s_dir.mkdir()
    invalid_service = {
        "id": "test-invalid-service",
        "input_text": "Sample text",
        "expected_pattern": "three_tier_web",
        "expected_services": ["CloudFront", "NonExistentService"],
    }
    (s_dir / "test.json").write_text(json.dumps(invalid_service), encoding="utf-8")
    errors = validate_scenarios(s_dir)
    assert any("NonExistentService" in e for e in errors)


def test_validate_scenarios_catches_duplicate_ids(tmp_path):
    s_dir = tmp_path / "scenarios"
    s_dir.mkdir()
    scen1 = {
        "id": "duplicate-id",
        "input_text": "Text 1",
        "expected_pattern": "three_tier_web",
        "expected_services": ["CloudFront"],
    }
    scen2 = {
        "id": "duplicate-id",
        "input_text": "Text 2",
        "expected_pattern": "static_site_cdn",
        "expected_services": ["S3"],
    }
    (s_dir / "s1.json").write_text(json.dumps(scen1), encoding="utf-8")
    (s_dir / "s2.json").write_text(json.dumps(scen2), encoding="utf-8")
    errors = validate_scenarios(s_dir)
    assert any("Duplicate scenario id: 'duplicate-id'" in e for e in errors)
