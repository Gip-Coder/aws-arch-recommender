from pathlib import Path
import pytest
from aws_arch.common import ROOT
from aws_arch.pipeline import list_cached_scenarios, load_cached_scenario, run_downstream
from aws_arch.validator import validate_architecture


def test_list_scenarios_contains_core_three():
    scenarios = list_cached_scenarios()
    assert "ecommerce" in scenarios
    assert "serverless_api" in scenarios
    assert "static_site" in scenarios


def test_all_cached_scenarios_files_exist():
    for name in ["ecommerce", "serverless_api", "static_site"]:
        txt_file = ROOT / "examples" / f"{name}.input.txt"
        req_file = ROOT / "examples" / f"{name}.requirement.json"
        arch_file = ROOT / "examples" / f"{name}.architecture.json"
        assert txt_file.exists(), f"Missing input text for {name}"
        assert req_file.exists(), f"Missing requirement JSON for {name}"
        assert arch_file.exists(), f"Missing architecture JSON for {name}"
        assert len(txt_file.read_text().strip()) > 0


def test_all_cached_scenarios_validate_and_pass_downstream(tmp_path):
    for name in ["ecommerce", "serverless_api", "static_site"]:
        req, arch = load_cached_scenario(name)
        errors = validate_architecture(arch)
        assert not errors, f"Scenario '{name}' failed validation: {errors}"

        # Run downstream pipeline and assert valid is True
        out_dir = tmp_path / name
        report = run_downstream(req, arch, out_dir)
        assert report["valid"] is True
        assert (out_dir / "report.json").exists()
        assert len(report["services"]) >= 2
        assert report["cost"]["monthly_usd_low"] >= 0
