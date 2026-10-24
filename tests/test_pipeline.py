import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aws_arch.common import ROOT, load_json, check_schema
from aws_arch.validator import validate_architecture
from aws_arch.security import check_security
from aws_arch.cost import estimate_cost

ARCH = load_json(ROOT / "examples/ecommerce_architecture.json")
REQ = load_json(ROOT / "examples/ecommerce_requirement.json")

def test_examples_match_schema():
    check_schema(ARCH, "architecture"); check_schema(REQ, "requirement")

def test_valid_architecture_has_no_errors():
    assert validate_architecture(ARCH) == []

def test_hallucinated_service_rejected():
    bad = {**ARCH, "services": ARCH["services"] + [{"id": "x", "type": "AWSMagicBox", "role": "?"}]}
    assert any("not in the curated catalogue" in e for e in validate_architecture(bad))

def test_orphan_detected():
    bad = {**ARCH, "services": ARCH["services"] + [{"id": "q", "type": "SQS", "role": "queue"}]}
    assert any("Orphaned" in e for e in validate_architecture(bad))

def test_invalid_connection_rejected():
    bad = {**ARCH, "connections": ARCH["connections"] + [{"from": "db", "to": "app"}]}
    assert any("not an allowed connection" in e for e in validate_architecture(bad))

def test_cost_range_ordered():
    c = estimate_cost(ARCH); assert c["monthly_usd_low"] <= c["monthly_usd_high"]

def test_security_findings_for_example():
    findings = check_security(ARCH, REQ)
    assert len(findings) == 15
    failed_ids = {f["id"] for f in findings if not f["passed"]}
    assert failed_ids == {"SEC-06", "OPS-01"}
