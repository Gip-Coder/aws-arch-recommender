"""Tests for aws_arch.security rules and summary."""
import sys
from pathlib import Path

# Ensure src/ is on sys.path
SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from aws_arch.common import ROOT, load_json
from aws_arch.security import check_security, summarize_security

ARCH_EXAMPLE = load_json(ROOT / "examples/ecommerce_architecture.json")
REQ_EXAMPLE = load_json(ROOT / "examples/ecommerce_requirement.json")


def _find_rule(findings: list[dict], rule_id: str) -> dict:
    for f in findings:
        if f["id"] == rule_id:
            return f
    raise AssertionError(f"Rule {rule_id} not found in findings")


# -------------------------------------------------------------
# Explicit Assertion for Example E-Commerce Architecture
# -------------------------------------------------------------
def test_example_ecommerce_architecture_explicit_findings():
    """Verify example e-commerce architecture results explicitly.

    Failures are intentional, not accidental:
    - SEC-06 fails because req requires authentication, but Cognito is not in the design.
    - OPS-01 fails because CloudWatch is not declared in the starter design.
    All other 13 rules pass.
    """
    findings = check_security(ARCH_EXAMPLE, REQ_EXAMPLE)
    assert len(findings) == 15

    # Check finding schema for all rules
    for f in findings:
        assert set(f.keys()) == {"id", "pillar", "rule", "severity", "passed", "recommendation"}
        assert f["severity"] in {"high", "medium", "low"}
        assert f["pillar"] in {
            "Security",
            "Reliability",
            "Cost Optimization",
            "Performance Efficiency",
            "Operational Excellence",
        }
        if f["passed"]:
            assert f["recommendation"] is None
        else:
            assert isinstance(f["recommendation"], str) and len(f["recommendation"]) > 0

    # Explicit passed vs failed rules
    passed_ids = {f["id"] for f in findings if f["passed"]}
    failed_ids = {f["id"] for f in findings if not f["passed"]}

    assert failed_ids == {"SEC-06", "OPS-01"}
    assert passed_ids == {
        "SEC-01",
        "SEC-02",
        "SEC-03",
        "SEC-04",
        "SEC-05",
        "SEC-07",
        "REL-01",
        "REL-02",
        "REL-03",
        "COST-01",
        "COST-02",
        "PERF-01",
        "PERF-02",
    }

    # Verify summary
    summary = summarize_security(findings)
    assert summary["total"] == 15
    assert summary["passed"] == 13
    assert summary["failed"] == 2
    assert summary["pass_rate"] == 0.867
    assert summary["by_pillar"]["Security"]["total"] == 7
    assert summary["by_pillar"]["Security"]["passed"] == 6
    assert summary["by_pillar"]["Security"]["failed"] == 1
    assert summary["by_pillar"]["Operational Excellence"]["total"] == 1
    assert summary["by_pillar"]["Operational Excellence"]["failed"] == 1
    assert summary["by_pillar"]["Reliability"]["passed"] == 3


def test_check_security_handles_none_req():
    """check_security should handle req=None without raising."""
    findings = check_security(ARCH_EXAMPLE, None)
    assert len(findings) == 15
    # When req is None, authentication requirement is not triggered
    sec06 = _find_rule(findings, "SEC-06")
    assert sec06["passed"] is True


# -------------------------------------------------------------
# Positive and Negative Cases for Each Rule
# -------------------------------------------------------------
def test_sec01_least_privilege_iam():
    # Positive
    arch_pos = {"services": [], "security_controls": ["IAM least-privilege roles"]}
    assert _find_rule(check_security(arch_pos), "SEC-01")["passed"] is True

    # Negative
    arch_neg = {"services": [], "security_controls": ["admin full access"]}
    f = _find_rule(check_security(arch_neg), "SEC-01")
    assert f["passed"] is False
    assert "IAM" in f["recommendation"]


def test_sec02_encryption_at_rest():
    # Positive
    arch_pos = {"services": [], "security_controls": ["KMS encryption at rest"]}
    assert _find_rule(check_security(arch_pos), "SEC-02")["passed"] is True

    # Negative
    arch_neg = {"services": [], "security_controls": ["unencrypted storage"]}
    assert _find_rule(check_security(arch_neg), "SEC-02")["passed"] is False


def test_sec03_encryption_in_transit():
    # Positive
    arch_pos = {"services": [], "security_controls": ["TLS encryption in transit"]}
    assert _find_rule(check_security(arch_pos), "SEC-03")["passed"] is True

    # Negative
    arch_neg = {"services": [], "security_controls": ["plain http"]}
    assert _find_rule(check_security(arch_neg), "SEC-03")["passed"] is False


def test_sec04_s3_public_access():
    # Positive: S3 with Block Public Access control
    arch_pos = {
        "services": [{"id": "b", "type": "S3", "role": "assets"}],
        "security_controls": ["no public S3 buckets"],
    }
    assert _find_rule(check_security(arch_pos), "SEC-04")["passed"] is True

    # Positive: S3 served behind CloudFront
    arch_pos2 = {
        "services": [
            {"id": "cdn", "type": "CloudFront", "role": "cdn"},
            {"id": "b", "type": "S3", "role": "assets"},
        ],
        "security_controls": [],
    }
    assert _find_rule(check_security(arch_pos2), "SEC-04")["passed"] is True

    # Negative: S3 alone without protection
    arch_neg = {"services": [{"id": "b", "type": "S3", "role": "assets"}], "security_controls": []}
    assert _find_rule(check_security(arch_neg), "SEC-04")["passed"] is False


def test_sec05_public_entry_point_protection():
    # Positive: ALB with TLS control
    arch_pos = {
        "services": [{"id": "alb", "type": "ApplicationLoadBalancer", "role": "lb"}],
        "security_controls": ["HTTPS listener with TLS certificate"],
    }
    assert _find_rule(check_security(arch_pos), "SEC-05")["passed"] is True

    # Negative: ALB without any TLS or WAF control
    arch_neg = {
        "services": [{"id": "alb", "type": "ApplicationLoadBalancer", "role": "lb"}],
        "security_controls": [],
    }
    assert _find_rule(check_security(arch_neg), "SEC-05")["passed"] is False


def test_sec06_authentication_service():
    req_auth = {"security_compliance": ["authentication"]}

    # Positive: Cognito present
    arch_pos = {"services": [{"id": "auth", "type": "Cognito", "role": "idp"}], "security_controls": []}
    assert _find_rule(check_security(arch_pos, req_auth), "SEC-06")["passed"] is True

    # Negative: Auth required by req, but no Cognito or auth control
    arch_neg = {"services": [], "security_controls": []}
    assert _find_rule(check_security(arch_neg, req_auth), "SEC-06")["passed"] is False


def test_sec07_database_public_isolation():
    # Positive: private DB connected through app tier
    arch_pos = {
        "services": [
            {"id": "cdn", "type": "CloudFront", "role": "cdn"},
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "db", "type": "RDS", "role": "db"},
        ],
        "connections": [
            {"from": "cdn", "to": "app"},
            {"from": "app", "to": "db"},
        ],
    }
    assert _find_rule(check_security(arch_pos), "SEC-07")["passed"] is True

    # Negative 1: Direct public connection from CloudFront to RDS
    arch_neg1 = {
        "services": [
            {"id": "cdn", "type": "CloudFront", "role": "cdn"},
            {"id": "db", "type": "RDS", "role": "db"},
        ],
        "connections": [{"from": "cdn", "to": "db"}],
    }
    assert _find_rule(check_security(arch_neg1), "SEC-07")["passed"] is False

    # Negative 2: Requirement explicitly asks for public database
    req_public_db = {"app_type": "app with public database requested"}
    assert _find_rule(check_security(arch_pos, req_public_db), "SEC-07")["passed"] is False


def test_rel01_multi_az_database():
    req_ha = {"availability": "high"}

    # Positive: Multi-AZ RDS when high availability is requested
    arch_pos = {"services": [{"id": "db", "type": "RDS_MultiAZ", "role": "db"}]}
    assert _find_rule(check_security(arch_pos, req_ha), "REL-01")["passed"] is True

    # Negative: Single-AZ RDS when high availability is requested
    arch_neg = {"services": [{"id": "db", "type": "RDS", "role": "db"}]}
    assert _find_rule(check_security(arch_neg, req_ha), "REL-01")["passed"] is False


def test_rel02_compute_auto_scaling():
    req_high_traffic = {"expected_users": 100000, "traffic_pattern": "steady"}

    # Positive: EC2AutoScalingGroup
    arch_pos = {"services": [{"id": "app", "type": "EC2AutoScalingGroup", "role": "compute"}]}
    assert _find_rule(check_security(arch_pos, req_high_traffic), "REL-02")["passed"] is True

    # Negative: Raw non-scalable EC2 for 100k users
    arch_neg = {"services": [{"id": "app", "type": "EC2", "role": "compute"}]}
    assert _find_rule(check_security(arch_neg, req_high_traffic), "REL-02")["passed"] is False


def test_rel03_decouple_spiky_workloads():
    req_spiky = {"traffic_pattern": "spiky"}

    # Positive: SQS present
    arch_pos = {"services": [{"id": "q", "type": "SQS", "role": "queue"}]}
    assert _find_rule(check_security(arch_pos, req_spiky), "REL-03")["passed"] is True

    # Negative: Spiky traffic without SQS or buffering control
    arch_neg = {"services": [{"id": "app", "type": "EC2AutoScalingGroup", "role": "app"}]}
    assert _find_rule(check_security(arch_neg, req_spiky), "REL-03")["passed"] is False


def test_cost01_avoid_over_provisioning_minimal_budget():
    req_min_budget = {"budget_sensitivity": "minimise"}

    # Positive: Lightweight Lambda + DynamoDB for minimal budget
    arch_pos = {
        "services": [
            {"id": "fn", "type": "Lambda", "role": "api"},
            {"id": "db", "type": "DynamoDB", "role": "data"},
        ]
    }
    assert _find_rule(check_security(arch_pos, req_min_budget), "COST-01")["passed"] is True

    # Negative: Heavy EC2 ASG + ALB + Multi-AZ RDS for minimal budget
    arch_neg = {
        "services": [
            {"id": "alb", "type": "ApplicationLoadBalancer", "role": "lb"},
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "db", "type": "RDS_MultiAZ", "role": "db"},
        ]
    }
    assert _find_rule(check_security(arch_neg, req_min_budget), "COST-01")["passed"] is False


def test_cost02_static_asset_offloading():
    req_web = {"app_type": "e-commerce web application"}

    # Positive: CloudFront used for web app
    arch_pos = {"services": [{"id": "cdn", "type": "CloudFront", "role": "cdn"}]}
    assert _find_rule(check_security(arch_pos, req_web), "COST-02")["passed"] is True

    # Negative: Web app with only compute and database (no CDN or S3)
    arch_neg = {
        "services": [
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "db", "type": "RDS", "role": "db"},
        ]
    }
    assert _find_rule(check_security(arch_neg, req_web), "COST-02")["passed"] is False


def test_perf01_cdn_configured():
    req_fast = {"performance": "low-latency"}

    # Positive: CloudFront present
    arch_pos = {"services": [{"id": "cdn", "type": "CloudFront", "role": "cdn"}]}
    assert _find_rule(check_security(arch_pos, req_fast), "PERF-01")["passed"] is True

    # Negative: Low-latency requested but no CDN
    arch_neg = {"services": [{"id": "app", "type": "EC2AutoScalingGroup", "role": "app"}]}
    assert _find_rule(check_security(arch_neg, req_fast), "PERF-01")["passed"] is False


def test_perf02_database_read_caching():
    req_mega = {"expected_users": 1000000}

    # Positive: ElastiCache present for high-traffic RDS
    arch_pos = {
        "services": [
            {"id": "db", "type": "RDS", "role": "db"},
            {"id": "cache", "type": "ElastiCache", "role": "cache"},
        ]
    }
    assert _find_rule(check_security(arch_pos, req_mega), "PERF-02")["passed"] is True

    # Negative: 1M users with relational DB and no caching
    arch_neg = {"services": [{"id": "db", "type": "RDS", "role": "db"}]}
    assert _find_rule(check_security(arch_neg, req_mega), "PERF-02")["passed"] is False


def test_ops01_centralized_monitoring():
    # Positive: CloudWatch present
    arch_pos = {"services": [{"id": "mon", "type": "CloudWatch", "role": "ops"}], "security_controls": []}
    assert _find_rule(check_security(arch_pos), "OPS-01")["passed"] is True

    # Positive: monitoring declared in controls
    arch_pos2 = {"services": [], "security_controls": ["Centralized CloudWatch logging and metrics"]}
    assert _find_rule(check_security(arch_pos2), "OPS-01")["passed"] is True

    # Negative: No CloudWatch and no monitoring in controls
    arch_neg = {"services": [{"id": "app", "type": "Lambda", "role": "fn"}], "security_controls": []}
    assert _find_rule(check_security(arch_neg), "OPS-01")["passed"] is False


def test_summarize_security_helper():
    sample_findings = [
        {"id": "SEC-01", "pillar": "Security", "passed": True},
        {"id": "SEC-02", "pillar": "Security", "passed": False},
        {"id": "REL-01", "pillar": "Reliability", "passed": True},
    ]
    summary = summarize_security(sample_findings)
    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["pass_rate"] == 0.667
    assert summary["by_pillar"]["Security"]["total"] == 2
    assert summary["by_pillar"]["Security"]["passed"] == 1
    assert summary["by_pillar"]["Security"]["failed"] == 1
    assert summary["by_pillar"]["Reliability"]["passed"] == 1
