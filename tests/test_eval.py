import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.run_eval import compute_metrics


def test_compute_metrics_perfect_match():
    expected = {
        "id": "perfect-scenario",
        "expected_pattern": "three_tier_web",
        "expected_services": ["CloudFront", "ApplicationLoadBalancer", "EC2AutoScalingGroup", "RDS_MultiAZ"],
    }
    arch = {
        "pattern": "three_tier_web",
        "services": [
            {"id": "cdn", "type": "CloudFront", "role": "cdn"},
            {"id": "alb", "type": "ApplicationLoadBalancer", "role": "alb"},
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "db", "type": "RDS_MultiAZ", "role": "db"},
        ],
        "connections": [
            {"from": "cdn", "to": "alb"},
            {"from": "alb", "to": "app"},
            {"from": "app", "to": "db"},
        ],
        "security_controls": ["IAM least privilege", "encryption at rest", "encryption in transit"],
    }
    metrics = compute_metrics(expected, arch, actual_req=None, response_time_sec=1.23)
    assert metrics["pattern_match"] == 1.0
    assert metrics["service_accuracy"] == 1.0
    assert metrics["service_precision"] == 1.0
    assert metrics["architecture_valid"] == 1.0
    assert metrics["response_time_sec"] == 1.23


def test_compute_metrics_empty_expected_and_recommended():
    # Edge case: empty expected and empty recommended services
    expected = {"id": "empty", "expected_services": [], "expected_pattern": "static_site_cdn"}
    arch = {"pattern": "static_site_cdn", "services": [], "connections": []}
    metrics = compute_metrics(expected, arch)
    assert metrics["service_accuracy"] == 1.0
    assert metrics["service_precision"] == 1.0


def test_compute_metrics_partial_accuracy_and_precision():
    expected = {
        "id": "partial",
        "expected_pattern": "serverless_rest_api",
        "expected_services": ["APIGateway", "Lambda", "DynamoDB"],
    }
    # Recommended has Lambda and DynamoDB (2 matched out of 3 expected -> 66.7%), plus CloudWatch (1 extra -> 2 of 3 recommended -> 66.7%)
    arch = {
        "pattern": "wrong_pattern",
        "services": [
            {"id": "fn", "type": "Lambda", "role": "fn"},
            {"id": "tbl", "type": "DynamoDB", "role": "tbl"},
            {"id": "logs", "type": "CloudWatch", "role": "logs"},
        ],
        "connections": [
            {"from": "fn", "to": "tbl"},
        ],
    }
    metrics = compute_metrics(expected, arch)
    assert metrics["pattern_match"] == 0.0
    assert round(metrics["service_accuracy"], 2) == 0.67
    assert round(metrics["service_precision"], 2) == 0.67
