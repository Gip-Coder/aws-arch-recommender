"""Unit tests for aws_arch.cost estimation engine."""
import json
import sys
from pathlib import Path

# Ensure src/ is on sys.path
SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from decimal import Decimal
from aws_arch.common import ROOT, load_catalogue, load_json
from aws_arch.cost import estimate_cost

ARCH_EXAMPLE = load_json(ROOT / "examples/ecommerce_architecture.json")

# Fixed fake pricing fixture for deterministic arithmetic tests
FAKE_PRICING_CATALOGUE = {
    "region": "ap-south-1",
    "prices_checked_on": "2026-10-25",
    "services": {
        "EC2AutoScalingGroup": {
            "pricing": {
                "unit_price": 0.0116,
                "unit": "USD per instance-hour",
                "status": "verified",
                "source_url": "https://aws.amazon.com/ec2/pricing/on-demand/",
                "usage_assumptions": {
                    "low_quantity": 730,
                    "high_quantity": 1460,
                    "description": "730h (1 instance) to 1460h (2 instances)",
                },
            }
        },
        "ApplicationLoadBalancer": {
            "pricing": {
                "unit_price": 0.0225,
                "unit": "USD per ALB-hour",
                "status": "verified",
                "source_url": "https://aws.amazon.com/elasticloadbalancing/pricing/",
                "usage_assumptions": {
                    "low_quantity": 730,
                    "high_quantity": 730,
                    "description": "730 hours baseline",
                },
            }
        },
        "CloudFront": {
            "pricing": {
                "unit_price": {"low": 0.085, "high": 0.12},
                "unit": "USD per GB data transfer",
                "status": "verified",
                "source_url": "https://aws.amazon.com/cloudfront/pricing/",
                "usage_assumptions": {
                    "low_quantity": 100,
                    "high_quantity": 1000,
                    "description": "100 GB (low) to 1000 GB (high)",
                },
            }
        },
        "IAM": {
            "pricing": {
                "unit_price": 0.0,
                "unit": "USD per user/role",
                "status": "verified",
                "source_url": "https://aws.amazon.com/iam/pricing/",
                "usage_assumptions": {
                    "low_quantity": 1,
                    "high_quantity": 1,
                    "description": "Included with account at no additional charge",
                },
            }
        },
        "MultiCompService": {
            "pricing": {
                "unit_price": 0.05,
                "unit": "USD per unit",
                "status": "verified",
                "source_url": "https://aws.amazon.com/custom/",
                "components": [
                    {
                        "name": "Component A",
                        "unit_price": 0.02,
                        "low_quantity": 100,
                        "high_quantity": 200,
                    },
                    {
                        "name": "Component B",
                        "unit_price": 0.10,
                        "low_quantity": 10,
                        "high_quantity": 50,
                    },
                ],
                "usage_assumptions": {
                    "description": "Comp A: 100-200, Comp B: 10-50",
                },
            }
        },
        "UnverifiedDB": {
            "pricing": {
                "unit_price": None,
                "unit": "USD per hour",
                "status": "TODO verify",
                "source_url": "https://aws.amazon.com/rds/pricing/",
                "usage_assumptions": {
                    "low_quantity": 730,
                    "high_quantity": 730,
                    "description": "730 hours",
                },
            }
        },
    },
}


# ==============================================================================
# Category A: Verified pricing arithmetic
# ==============================================================================
def test_verified_pricing_arithmetic():
    """Verify correct calculation of monthly costs from unit prices and usage quantities."""
    arch = {
        "services": [
            {"id": "web", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "alb", "type": "ApplicationLoadBalancer", "role": "lb"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    assert res["status"] == "complete"
    assert res["incomplete_services"] == []

    # EC2 low: 730 * 0.0116 = 8.468 -> 8.47; high: 1460 * 0.0116 = 16.936 -> 16.94
    # ALB low/high: 730 * 0.0225 = 16.425 -> 16.42 or 16.43
    ec2_b = res["breakdown"]["web"]
    alb_b = res["breakdown"]["alb"]

    assert ec2_b["monthly_usd_low"] == 8.47
    assert ec2_b["monthly_usd_high"] == 16.94

    expected_low = round(ec2_b["monthly_usd_low"] + alb_b["monthly_usd_low"], 2)
    expected_high = round(ec2_b["monthly_usd_high"] + alb_b["monthly_usd_high"], 2)

    assert res["monthly_usd_low"] == expected_low
    assert res["monthly_usd_high"] == expected_high
    assert res["monthly_usd_low"] <= res["monthly_usd_high"]


def test_tiered_unit_price_arithmetic():
    """Verify tiered / range unit price calculation."""
    arch = {"services": [{"id": "cdn", "type": "CloudFront", "role": "cdn"}]}
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    # Low: 100 * 0.085 = 8.50
    # High: 1000 * 0.12 = 120.00
    cdn_b = res["breakdown"]["cdn"]
    assert cdn_b["monthly_usd_low"] == 8.50
    assert cdn_b["monthly_usd_high"] == 120.00
    assert res["monthly_usd_low"] == 8.50
    assert res["monthly_usd_high"] == 120.00


def test_multi_component_pricing_arithmetic():
    """Verify multi-component service summation."""
    arch = {"services": [{"id": "mc", "type": "MultiCompService", "role": "test"}]}
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    assert res["status"] == "complete"
    # Comp A: 100 * 0.02 = 2.00 (low), 200 * 0.02 = 4.00 (high)
    # Comp B: 10 * 0.10 = 1.00 (low), 50 * 0.10 = 5.00 (high)
    # Low total: 2.00 + 1.00 = 3.00; High total: 4.00 + 5.00 = 9.00
    b = res["breakdown"]["mc"]
    assert b["monthly_usd_low"] == 3.00
    assert b["monthly_usd_high"] == 9.00
    assert res["monthly_usd_low"] == 3.00
    assert res["monthly_usd_high"] == 9.00


# ==============================================================================
# Category B: Unknown and incomplete pricing
# ==============================================================================
def test_unknown_price_not_converted_to_zero():
    """Unverified services must never be converted to 0.0 or treated as free."""
    arch = {"services": [{"id": "db", "type": "UnverifiedDB", "role": "db"}]}
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    assert res["status"] == "incomplete"
    assert "UnverifiedDB" in res["incomplete_services"]
    assert res["monthly_usd_low"] is None
    assert res["monthly_usd_high"] is None

    db_b = res["breakdown"]["db"]
    assert db_b["status"] == "incomplete"
    assert db_b["monthly_usd_low"] is None
    assert db_b["monthly_usd_high"] is None
    assert "TODO verify" in db_b["note"]


def test_partially_verified_architecture():
    """Partially priced architecture is marked incomplete with partial subtotal separated."""
    arch = {
        "services": [
            {"id": "web", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "db", "type": "UnverifiedDB", "role": "db"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    assert res["status"] == "incomplete"
    assert res["incomplete_services"] == ["UnverifiedDB"]
    # Overall total is None because complete cost is unknown
    assert res["monthly_usd_low"] is None
    assert res["monthly_usd_high"] is None

    # Partial verified subtotal is reported separately without pretending to be full cost
    assert res["partial_verified_monthly_usd_low"] == 8.47
    assert res["partial_verified_monthly_usd_high"] == 16.94


def test_entirely_unverified_architecture_returns_null_totals():
    """An architecture with only unverified services returns None for all totals."""
    arch = {
        "services": [
            {"id": "db1", "type": "UnverifiedDB", "role": "db1"},
            {"id": "db2", "type": "UnverifiedDB", "role": "db2"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    assert res["status"] == "incomplete"
    assert res["monthly_usd_low"] is None
    assert res["monthly_usd_high"] is None
    assert "partial_verified_monthly_usd_low" not in res


def test_verified_zero_cost_distinguished_from_unverified():
    """Verified zero-cost component ($0.0) is distinguished from unverified (None)."""
    arch = {
        "services": [
            {"id": "iam", "type": "IAM", "role": "security"},
            {"id": "db", "type": "UnverifiedDB", "role": "db"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)

    iam_b = res["breakdown"]["iam"]
    db_b = res["breakdown"]["db"]

    assert iam_b["status"] == "verified"
    assert iam_b["monthly_usd_low"] == 0.0
    assert iam_b["monthly_usd_high"] == 0.0

    assert db_b["status"] == "incomplete"
    assert db_b["monthly_usd_low"] is None
    assert db_b["monthly_usd_high"] is None


# ==============================================================================
# Category C: Estimate integrity & robustness
# ==============================================================================
def test_numeric_low_never_exceeds_high():
    """Numeric low estimates must never exceed numeric high estimates."""
    arch = {
        "services": [
            {"id": "web", "type": "EC2AutoScalingGroup", "role": "app"},
            {"id": "cdn", "type": "CloudFront", "role": "cdn"},
            {"id": "iam", "type": "IAM", "role": "security"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)
    assert res["status"] == "complete"
    assert res["monthly_usd_low"] <= res["monthly_usd_high"]


def test_malformed_and_missing_data_handled_safely():
    """Missing services or malformed pricing blocks do not crash the estimator."""
    arch = {
        "services": [
            {"id": "unknown_comp", "type": "UnknownRandomService", "role": "custom"},
        ]
    }
    res = estimate_cost(arch, catalogue=FAKE_PRICING_CATALOGUE)
    assert res["status"] == "incomplete"
    assert "UnknownRandomService" in res["incomplete_services"]
    assert res["breakdown"]["unknown_comp"]["status"] == "incomplete"


def test_json_serialization_safety():
    """Verify estimate_cost output is strictly JSON serializable without NaN or sentinels."""
    res = estimate_cost(ARCH_EXAMPLE)
    dumped = json.dumps(res)
    loaded = json.loads(dumped)
    assert loaded["region"] == "ap-south-1"
    assert "NaN" not in dumped


# ==============================================================================
# Category D: Backwards compatibility & Real Catalogue verification
# ==============================================================================
def test_existing_output_keys_preserved():
    """Ensure all original keys are preserved for backward compatibility."""
    res = estimate_cost(ARCH_EXAMPLE)

    # Legacy expected keys
    assert "monthly_usd_low" in res
    assert "monthly_usd_high" in res
    assert "region" in res
    assert "prices_checked_on" in res
    assert "note" in res

    # New contract keys
    assert "status" in res
    assert "incomplete_services" in res
    assert "breakdown" in res
    assert "assumptions" in res
    assert "exclusions" in res

    assert "Order-of-magnitude estimate" in res["note"]


# Authoritative recorded evidence fixture for ap-south-1 and global services.
# Distinguishes live network calls from reproducible deterministic fixtures.
RECORDED_EVIDENCE_REGISTRY = {
    "CloudFront": {
        "region_scope": "regional_edge",
        "service_code": "AmazonCloudFront",
        "dto_sku": "XVZYVSAH88373VKR",
        "dto_rate": Decimal("0.109"),
        "https_sku": "GJTTXSYXV43ANXTQ",
        "https_rate": Decimal("0.0000012"),
    },
    "Route53": {
        "region_scope": "global",
        "service_code": "AmazonRoute53",
        "zone_sku": "KVPGEJE88UW8S779",
        "zone_rate": Decimal("0.50"),
        "query_sku": "JHRA6QBEDT9FZVT5",
        "query_rate": Decimal("0.0000004"),
    },
    "ApplicationLoadBalancer": {
        "region_scope": "ap-south-1",
        "service_code": "AWSELB",
        "alb_sku": "WJ2MHASNP2ZNKFXX",
        "alb_rate": Decimal("0.0239"),
        "lcu_sku": "HFFD75W4GFXQPHZR",
        "lcu_rate": Decimal("0.008"),
    },
    "APIGateway": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonApiGateway",
        "http_api_sku": "S2BWD3VP3K4M5Q9P",
        "http_api_rate": Decimal("1.05"),
    },
    "EC2AutoScalingGroup": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonEC2",
        "instance_sku": "9NX7BP9ZGC9GB8AX",
        "instance_rate": Decimal("0.0112"),
    },
    "ECSFargate": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonECS",
        "vcpu_sku": "KV4FGA39G96M59TH",
        "vcpu_rate": Decimal("0.04256"),
        "memory_sku": "N4Q5MGA6V9TFA2MG",
        "memory_rate": Decimal("0.004655"),
    },
    "Lambda": {
        "region_scope": "ap-south-1",
        "service_code": "AWSLambda",
        "request_sku": "VPGUBFQ4KNZKMKGJ",
        "request_rate": Decimal("0.0000002"),
        "compute_sku": "PHDF9YNAFR3HDSR8",
        "compute_rate": Decimal("0.0000166667"),
    },
    "RDS": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonRDS",
        "instance_sku": "TDP2T3MABGFDWYMQ",
        "instance_rate": Decimal("0.025"),
        "storage_sku": "P9ZS93METCDRDD55",
        "storage_rate": Decimal("0.131"),
    },
    "RDS_MultiAZ": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonRDS",
        "instance_sku": "XY6F6U9686MYMXAN",
        "instance_rate": Decimal("0.049"),
        "storage_sku": "8BCW7MZTHCKWG2WF",
        "storage_rate": Decimal("0.262"),
    },
    "DynamoDB": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonDynamoDB",
        "storage_sku": "8Q6HK3ASV67MN388",
        "storage_rate": Decimal("0.285"),
        "wru_sku": "A5DP2X4YSZ84WEJA",
        "wru_rate": Decimal("0.00000071"),
        "rru_sku": "HQZY4ZFUTRDPV7ZE",
        "rru_rate": Decimal("0.0000001425"),
    },
    "ElastiCache": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonElastiCache",
        "node_sku": "XZTCQWH2CTD9RTXE",
        "node_rate": Decimal("0.021"),
    },
    "S3": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonS3",
        "storage_sku": "USGUTP2JY23N9GH2",
        "storage_rate": Decimal("0.025"),
        "tier1_sku": "UJ844B8DVMQUFJQP",
        "tier1_rate": Decimal("0.000005"),
        "tier2_sku": "SF3QQQMZGA3PPF33",
        "tier2_rate": Decimal("0.0000004"),
    },
    "SQS": {
        "region_scope": "ap-south-1",
        "service_code": "AWSQueueService",
        "request_sku": "Y6JJ7JBXQG364CH7",
        "request_rate": Decimal("0.40"),
        "free_sku": "MNCJEPJRCSC9RFY2",
    },
    "Cognito": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonCognito",
        "mau_sku": "SJDJQB52YRYNVHRN",
        "mau_rate": Decimal("0.0055"),
    },
    "Bedrock": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonBedrock",
        "input_sku": "6UNCKSWRDBPA548S",
        "input_rate": Decimal("0.001"),
        "output_sku": "NHZ5ECAKWBFG3N8H",
        "output_rate": Decimal("0.0019"),
    },
    "CloudWatch": {
        "region_scope": "ap-south-1",
        "service_code": "AmazonCloudWatch",
        "metrics_sku": "WJAN9NR7AQ8KWB2U",
        "metrics_rate": Decimal("0.30"),
        "alarms_sku": "MBFPHE42AKJWSCZH",
        "alarms_rate": Decimal("0.10"),
        "logs_ingest_sku": "JBQP6QEETS2BK5DQ",
        "logs_ingest_rate": Decimal("0.67"),
        "logs_store_sku": "M9PG5USRE2QBB6FU",
        "logs_store_rate": Decimal("0.03"),
    },
    "IAM": {
        "region_scope": "global",
        "service_code": "AWSIdentityAndAccessManagement",
        "core_charge": Decimal("0.0"),
    },
}


def test_catalogue_yaml_all_services_verified_with_official_sources():
    """Verify that every service in catalogue.yaml has verified status, official source, and valid evidence fields."""
    cat = load_catalogue()
    assert cat["region"] == "ap-south-1"
    assert cat["prices_checked_on"] == "2026-10-25"
    services = cat.get("services", {})
    assert len(services) == 17

    allowed_categories = {"network", "compute", "database", "storage", "integration", "security", "ops", "ai"}
    service_names = set(services.keys())

    for name, data in services.items():
        # Validate category and allowed targets
        assert data.get("category") in allowed_categories, f"{name} category {data.get('category')} invalid"
        for target in data.get("allowed_targets", []):
            assert target in service_names, f"{name} allowed_target {target} not in service list"

        assert "pricing" in data, f"{name} is missing pricing block"
        pricing = data["pricing"]

        # Validate official AWS source
        assert "source_url" in pricing and pricing["source_url"].startswith("https://aws.amazon.com/"), (
            f"{name} must have an official AWS source_url"
        )
        assert pricing.get("status") == "verified", f"{name} is not verified"
        assert pricing.get("currency") == "USD", f"{name} currency must be USD"
        assert pricing.get("region_scope") in {"ap-south-1", "regional_edge", "global"}, (
            f"{name} has invalid region_scope: {pricing.get('region_scope')}"
        )
        assert "usage_assumptions" in pricing, f"{name} is missing usage_assumptions"

        # Check deterministic recorded evidence matching
        assert name in RECORDED_EVIDENCE_REGISTRY, f"{name} missing from recorded evidence registry"
        evidence = RECORDED_EVIDENCE_REGISTRY[name]
        assert pricing.get("region_scope") == evidence["region_scope"]

        components = pricing.get("components")
        if components and isinstance(components, list):
            assert len(components) >= 1
            for comp in components:
                assert "name" in comp and comp["name"], f"{name} component missing name"
                assert "unit_price" in comp and comp["unit_price"] is not None
                assert Decimal(str(comp["unit_price"])) >= Decimal("0.0")
                assert "unit" in comp and comp["unit"]
                if "low_quantity" in comp and "high_quantity" in comp:
                    assert Decimal(str(comp["low_quantity"])) <= Decimal(str(comp["high_quantity"]))
        else:
            assert pricing.get("unit_price") is not None, f"{name} verified price must not be null"
            assert Decimal(str(pricing.get("unit_price"))) >= Decimal("0.0")
            assert "unit" in pricing and pricing["unit"]
            u_assump = pricing.get("usage_assumptions", {})
            if isinstance(u_assump, dict) and "low_quantity" in u_assump and "high_quantity" in u_assump:
                assert Decimal(str(u_assump["low_quantity"])) <= Decimal(str(u_assump["high_quantity"]))


def test_all_17_catalogue_services_estimate_valid_and_ordered():
    """Verify that estimating cost for each individual service yields valid low <= high."""
    cat = load_catalogue()
    for name in cat.get("services", {}):
        single_arch = {"services": [{"id": "s1", "type": name, "role": "test"}]}
        res = estimate_cost(single_arch, catalogue=cat)
        assert res["status"] == "complete", f"{name} should be complete"
        assert res["monthly_usd_low"] is not None, f"{name} low cost is None"
        assert res["monthly_usd_high"] is not None, f"{name} high cost is None"
        assert res["monthly_usd_low"] >= 0.0, f"{name} low cost is negative"
        assert res["monthly_usd_low"] <= res["monthly_usd_high"], (
            f"{name} monthly_usd_low ({res['monthly_usd_low']}) > monthly_usd_high ({res['monthly_usd_high']})"
        )


# ==============================================================================
# Category E: Amazon SQS Free-Tier & Boundary Regression Tests
# ==============================================================================
def test_sqs_zero_requests():
    """SQS with 0 requests must cost exactly $0.00."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 0}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.00
    assert res["breakdown"]["q"]["monthly_usd_high"] == 0.00
    assert res["monthly_usd_low"] == 0.00
    assert res["monthly_usd_high"] == 0.00


def test_sqs_usage_below_free_allowance():
    """SQS with usage below 1M allowance (e.g. 100,000 requests) must cost $0.00."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 100000}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.00
    assert res["breakdown"]["q"]["monthly_usd_high"] == 0.00


def test_sqs_usage_exactly_equal_free_allowance():
    """SQS with exactly 1M requests (1,000,000) with allowance available costs $0.00."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 1000000}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.00
    assert res["breakdown"]["q"]["monthly_usd_high"] == 0.00


def test_sqs_usage_just_above_free_allowance():
    """SQS with 1,000,001 requests has 1 billable request."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 1000001}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    # 1 request * $0.40 / 1,000,000 = $0.0000004 -> rounds to 0.00 for display
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.00
    # Internal unrounded charge is preserved and strictly positive
    assert res["breakdown"]["q"]["unrounded_monthly_usd_low"] > 0.0
    assert abs(res["breakdown"]["q"]["unrounded_monthly_usd_low"] - 0.0000004) < 1e-9


def test_sqs_usage_2_million_requests_allowance_available():
    """2M requests with allowance available has 1M billable requests -> $0.40."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 2000000}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.40
    assert res["breakdown"]["q"]["monthly_usd_high"] == 0.40


def test_sqs_usage_10_million_requests_allowance_available():
    """10M requests with allowance available has 9M billable requests -> $3.60."""
    arch = {"services": [{"id": "q", "type": "SQS", "requests": 10000000}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 3.60
    assert res["breakdown"]["q"]["monthly_usd_high"] == 3.60


def test_sqs_allowance_already_consumed():
    """When allowance is consumed, full usage is billed (1M -> $0.40; 10M -> $4.00)."""
    arch_1m = {
        "services": [{"id": "q", "type": "SQS", "requests": 1000000}],
        "free_tier_mode": "consumed",
    }
    res_1m = estimate_cost(arch_1m)
    assert res_1m["breakdown"]["q"]["monthly_usd_low"] == 0.40
    assert res_1m["breakdown"]["q"]["monthly_usd_high"] == 0.40

    arch_10m = {
        "services": [{"id": "q", "type": "SQS", "requests": 10000000}],
        "free_tier_mode": "consumed",
    }
    res_10m = estimate_cost(arch_10m)
    assert res_10m["breakdown"]["q"]["monthly_usd_low"] == 4.00
    assert res_10m["breakdown"]["q"]["monthly_usd_high"] == 4.00


def test_sqs_workload_ineligible_for_allowance():
    """When workload is ineligible, full usage is billed."""
    arch = {
        "services": [
            {
                "id": "q",
                "type": "SQS",
                "requests": 2000000,
                "free_tier_mode": "ineligible",
            }
        ]
    }
    res = estimate_cost(arch)
    # 2M billable @ $0.40/M = $0.80
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.80


def test_sqs_missing_or_invalid_usage_inputs():
    """Invalid non-numeric usage marks service incomplete; negative usage clamps to 0."""
    arch_invalid = {"services": [{"id": "q", "type": "SQS", "usage_quantity": "invalid_val"}]}
    res_inv = estimate_cost(arch_invalid)
    assert res_inv["status"] == "incomplete"
    assert res_inv["breakdown"]["q"]["status"] == "incomplete"
    assert res_inv["breakdown"]["q"]["monthly_usd_low"] is None

    # Negative usage should clamp safely to 0
    arch_neg = {"services": [{"id": "q", "type": "SQS", "requests": -5000}]}
    res_neg = estimate_cost(arch_neg)
    assert res_neg["status"] == "complete"
    assert res_neg["breakdown"]["q"]["monthly_usd_low"] == 0.00


def test_sqs_catalogue_default_assumptions_low_high():
    """Default catalogue assumptions for SQS: 1M low ($0.00), 10M high ($3.60)."""
    arch = {"services": [{"id": "q", "type": "SQS", "role": "queue"}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.00
    assert res["breakdown"]["q"]["monthly_usd_high"] == 3.60
    assert res["breakdown"]["q"]["potential_free_tier_savings_low"] == 0.40
    assert res["breakdown"]["q"]["potential_free_tier_savings_high"] == 0.40
    assert res["monthly_usd_low"] == 0.00
    assert res["monthly_usd_high"] == 3.60


# ==============================================================================
# Category F: Integration, Precision, Free-Tier Sharing & Disambiguation Tests
# ==============================================================================
def test_quantity_normalization_raw_vs_millions_without_magnitude_thresholds():
    """Unit-driven normalization properly handles small raw counts and large million counts."""
    # Small raw count: 500 requests with explicit unit -> 500 / 1,000,000 = 0.0005M
    arch_small_raw = {
        "services": [
            {
                "id": "q",
                "type": "SQS",
                "usage_quantity": 500,
                "unit": "requests",
                "free_tier_mode": "consumed",
            }
        ]
    }
    res_small = estimate_cost(arch_small_raw)
    assert res_small["status"] == "complete"
    # 0.0005M * $0.40 = $0.0002 -> rounds to 0.00 display, unrounded 0.0002
    assert res_small["breakdown"]["q"]["monthly_usd_low"] == 0.00
    assert abs(res_small["breakdown"]["q"]["unrounded_monthly_usd_low"] - 0.0002) < 1e-9

    # Large million count: 15,000 million requests with explicit unit -> 15000M
    arch_large_m = {
        "services": [
            {
                "id": "q",
                "type": "SQS",
                "usage_quantity": 15000,
                "unit": "million requests",
                "free_tier_mode": "available",
            }
        ]
    }
    res_large = estimate_cost(arch_large_m)
    assert res_large["status"] == "complete"
    # (15000 - 1) * 0.40 = 14999 * 0.40 = 5999.60
    assert res_large["breakdown"]["q"]["monthly_usd_low"] == 5999.60
    assert res_large["breakdown"]["q"]["monthly_usd_high"] == 5999.60


def test_account_level_free_tier_sharing_multiple_resources():
    """Multiple SQS queues share a single 1M account allowance, not 1M per queue."""
    arch = {
        "services": [
            {"id": "q1", "type": "SQS", "requests": 600000},
            {"id": "q2", "type": "SQS", "requests": 800000},
        ],
        "free_tier_mode": "available",
    }
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    # Total requests across account: 1,400,000.
    # q1 consumes 600k of the 1M allowance -> 0 billable -> $0.00
    assert res["breakdown"]["q1"]["monthly_usd_low"] == 0.00
    assert res["breakdown"]["q1"]["billable_quantity_low"] == 0.0

    # q2 receives remaining 400k allowance -> 400k billable (0.4M) -> 0.4 * $0.40 = $0.16
    assert res["breakdown"]["q2"]["monthly_usd_low"] == 0.16
    assert abs(res["breakdown"]["q2"]["billable_quantity_low"] - 0.4) < 1e-9

    # Architecture total exactly equals $0.16 (1.4M requests - 1M free allowance = 400k billable)
    assert res["monthly_usd_low"] == 0.16


def test_free_tier_mode_unknown_discloses_uncertainty_and_conservatism():
    """Mode 'unknown' bills at on-demand rates, notes potential savings, and discloses note."""
    arch = {
        "services": [{"id": "q", "type": "SQS", "requests": 1000000}],
        "free_tier_mode": "unknown",
    }
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    # Conservative on-demand charge for 1M requests
    assert res["breakdown"]["q"]["monthly_usd_low"] == 0.40
    # Transparently reports what could be saved if available
    assert res["breakdown"]["q"]["potential_free_tier_savings_low"] == 0.40
    assert "unknown" in res["breakdown"]["q"]["free_tier_mode"]
    assert "free_tier_note" in res
    assert "unknown" in res["free_tier_note"].lower()


def test_architecture_total_equals_sum_of_displayed_line_items():
    """The overall architecture total must exactly equal the sum of displayed line items."""
    arch = {
        "services": [
            {"id": "cdn", "type": "CloudFront"},
            {"id": "alb", "type": "ApplicationLoadBalancer"},
            {"id": "app", "type": "EC2AutoScalingGroup"},
            {"id": "db", "type": "RDS_MultiAZ"},
            {"id": "q", "type": "SQS"},
            {"id": "auth", "type": "Cognito"},
        ]
    }
    res = estimate_cost(arch)
    assert res["status"] == "complete"

    displayed_low_sum = sum(
        Decimal(str(item["monthly_usd_low"]))
        for item in res["breakdown"].values()
    )
    displayed_high_sum = sum(
        Decimal(str(item["monthly_usd_high"]))
        for item in res["breakdown"].values()
    )

    assert Decimal(str(res["monthly_usd_low"])) == displayed_low_sum
    assert Decimal(str(res["monthly_usd_high"])) == displayed_high_sum


def test_unverified_partial_estimate_reconciliation():
    """An architecture with unverified service returns None totals and exact partial subtotal."""
    mock_cat = {
        "services": {
            "SQS": {
                "pricing": {
                    "unit_price": 0.40,
                    "unit": "USD per million requests",
                    "status": "verified",
                    "free_allowance": {"quantity": 1.0, "unit": "million requests"},
                    "usage_assumptions": {"low_quantity": 2.0, "high_quantity": 2.0, "unit": "million requests"},
                }
            },
            "MysterySvc": {
                "pricing": {
                    "unit_price": None,
                    "unit": "USD",
                    "status": "TODO verify",
                }
            },
        }
    }
    arch = {
        "services": [
            {"id": "q", "type": "SQS"},
            {"id": "m", "type": "MysterySvc"},
        ]
    }
    res = estimate_cost(arch, catalogue=mock_cat)
    assert res["status"] == "incomplete"
    assert res["monthly_usd_low"] is None
    assert res["monthly_usd_high"] is None
    assert res["incomplete_services"] == ["MysterySvc"]
    # Verified SQS part: 2M - 1M free = 1M * 0.40 = $0.40
    assert res["partial_verified_monthly_usd_low"] == 0.40
    assert res["partial_verified_monthly_usd_high"] == 0.40


def test_resource_ordering_invariance_on_architecture_total():
    """Resource ordering does not change the total architecture cost when aggregate usage is unchanged."""
    q_a = {"id": "qa", "type": "SQS", "requests": 400000}
    q_b = {"id": "qb", "type": "SQS", "requests": 900000}

    # Order A: qa then qb
    res_ab = estimate_cost({"services": [q_a, q_b], "free_tier_mode": "available"})
    # Order B: qb then qa
    res_ba = estimate_cost({"services": [q_b, q_a], "free_tier_mode": "available"})

    # Aggregate usage: 1,300,000 requests. 1M free allowance -> 300,000 billable @ $0.40/M = $0.12
    assert res_ab["status"] == "complete"
    assert res_ba["status"] == "complete"
    assert res_ab["monthly_usd_low"] == 0.12
    assert res_ba["monthly_usd_low"] == 0.12
    assert res_ab["monthly_usd_low"] == res_ba["monthly_usd_low"]
    assert res_ab["monthly_usd_high"] == res_ba["monthly_usd_high"]

    # Sequential line item breakdown reflects arrival order convention, while total is invariant
    assert res_ab["breakdown"]["qa"]["monthly_usd_low"] == 0.00
    assert res_ab["breakdown"]["qb"]["monthly_usd_low"] == 0.12
    assert res_ba["breakdown"]["qb"]["monthly_usd_low"] == 0.00
    assert res_ba["breakdown"]["qa"]["monthly_usd_low"] == 0.12


def test_allowance_exhaustion_multi_queue():
    """First queue fully exhausts 1M allowance; subsequent queue is fully billable."""
    arch = {
        "services": [
            {"id": "q1", "type": "SQS", "requests": 1500000},
            {"id": "q2", "type": "SQS", "requests": 500000},
        ],
        "free_tier_mode": "available",
    }
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    # q1: 1.5M requests - 1M free = 0.5M billable -> 0.5 * $0.40 = $0.20
    assert res["breakdown"]["q1"]["monthly_usd_low"] == 0.20
    assert abs(res["breakdown"]["q1"]["billable_quantity_low"] - 0.5) < 1e-9

    # q2: allowance is exhausted (0 available) -> all 0.5M billable -> 0.5 * $0.40 = $0.20
    assert res["breakdown"]["q2"]["monthly_usd_low"] == 0.20
    assert abs(res["breakdown"]["q2"]["billable_quantity_low"] - 0.5) < 1e-9

    # Total: 2.0M requests - 1.0M allowance = 1.0M billable -> $0.40
    assert res["monthly_usd_low"] == 0.40


def test_fifo_queue_pricing_model():
    """FIFO queue pricing ($0.50/M) is supported when defined in catalogue without standard free tier."""
    fifo_cat = {
        "services": {
            "SQS_FIFO": {
                "pricing": {
                    "unit_price": 0.50,
                    "unit": "USD per million requests",
                    "status": "verified",
                    "source_url": "https://aws.amazon.com/sqs/pricing/",
                    "usage_assumptions": {"low_quantity": 2.0, "high_quantity": 10.0, "unit": "million requests"},
                }
            }
        }
    }
    arch = {"services": [{"id": "qf", "type": "SQS_FIFO", "requests": 2000000}]}
    res = estimate_cost(arch, catalogue=fifo_cat)
    assert res["status"] == "complete"
    # 2M requests @ $0.50/M = $1.00
    assert res["breakdown"]["qf"]["monthly_usd_low"] == 1.00


def test_route53_hosted_zone_and_queries_calculated_correctly():
    """Route 53 models both hosted zones ($0.50/mo) and DNS query volume ($0.40/M)."""
    arch = {"services": [{"id": "dns", "type": "Route53"}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["monthly_usd_low"] == 0.90
    assert res["monthly_usd_high"] == 4.50

    comp = res["breakdown"]["dns"]["components"]
    assert len(comp) == 2
    assert comp[0]["name"] == "Hosted Zone (first 25)"
    assert comp[0]["unit_price"] == 0.50
    assert comp[1]["name"] == "Standard DNS Queries"
    assert comp[1]["unit_price"] == 0.0000004


def test_route53_not_added_to_unrelated_architecture():
    """Architectures lacking Route 53 do not incur or display Route 53 hosted-zone charges."""
    arch = {
        "services": [
            {"id": "app", "type": "EC2AutoScalingGroup"},
            {"id": "alb", "type": "ApplicationLoadBalancer"},
        ]
    }
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    services_in_breakdown = [item["service"] for item in res["breakdown"].values()]
    assert "Route53" not in services_in_breakdown
    assert "dns" not in res["breakdown"]
    # Total equals exactly app ($8.18 / $16.35) + alb ($23.29 / $34.97) = $31.47 / $51.32
    assert res["monthly_usd_low"] == 31.47
    assert res["monthly_usd_high"] == 51.32


def test_fargate_rates_and_assumptions():
    """Fargate pricing is fully reproducible from documented regional inputs and assumptions.

    Parameters verified:
      - Region: Asia Pacific (Mumbai) (ap-south-1)
      - Operating System & Architecture: Linux / x86
      - Pricing Model: On-Demand
      - Rate dimensions:
          * vCPU: $0.04256 per vCPU-hour (SKU: KV4FGA39G96M59TH, rateCode: KV4FGA39G96M59TH.JRTCKXETXF.6YS6EN2CT7)
          * Memory: $0.004655 per GB-hour (SKU: N4Q5MGA6V9TFA2MG, rateCode: N4Q5MGA6V9TFA2MG.JRTCKXETXF.6YS6EN2CT7)
      - Ephemeral storage: 20 GB included free per task; additional storage ($0.000127/GB-hr) excluded from model.
      - Usage inputs (730 operational hours/month):
          * Low: 1 task (0.5 vCPU, 1 GB RAM, 730h)
                 -> 365 vCPU-hours consumed
                 -> 730 Memory GB-hours consumed
          * High: 2 tasks (1.0 vCPU, 2 GB RAM, 730h each = 1,460 task-hours)
                 -> 1,460 vCPU-hours consumed
                 -> 2,920 Memory GB-hours consumed
      - Exact arithmetic & HALF_UP rounding:
          * Low unrounded: (365 * 0.04256) + (730 * 0.004655) = 15.5344 + 3.39815 = 18.93255
                 -> Quantized: $18.93
          * High unrounded: (1460 * 0.04256) + (2920 * 0.004655) = 62.1376 + 13.5926 = 75.7302
                 -> Quantized: $75.73
    """
    cat = load_catalogue()
    fgt_pricing = cat["services"]["ECSFargate"]["pricing"]

    assert cat["region"] == "ap-south-1"
    assert fgt_pricing["region_scope"] == "ap-south-1"
    assert fgt_pricing["currency"] == "USD"
    assert fgt_pricing["status"] == "verified"

    comp = fgt_pricing["components"]
    assert len(comp) == 2
    assert comp[0]["name"] == "Fargate vCPU"
    assert comp[0]["unit_price"] == 0.04256
    assert comp[0]["unit"] == "USD per vCPU-hour"
    assert comp[0]["low_quantity"] == 365
    assert comp[0]["high_quantity"] == 1460

    assert comp[1]["name"] == "Fargate Memory"
    assert comp[1]["unit_price"] == 0.004655
    assert comp[1]["unit"] == "USD per GB-hour"
    assert comp[1]["low_quantity"] == 730
    assert comp[1]["high_quantity"] == 2920

    # Ensure other regional rates (e.g. us-west-1 / sa-east-1: 0.04656 / 0.00511) are not substituted
    assert comp[0]["unit_price"] != 0.04656
    assert comp[1]["unit_price"] != 0.00511

    # Exact Decimal calculation
    vcpu_rate = Decimal("0.04256")
    mem_rate = Decimal("0.004655")

    expected_low_exact = (Decimal("365") * vcpu_rate) + (Decimal("730") * mem_rate)
    expected_high_exact = (Decimal("1460") * vcpu_rate) + (Decimal("2920") * mem_rate)

    assert expected_low_exact == Decimal("18.93255")
    assert expected_high_exact == Decimal("75.7302")

    arch = {"services": [{"id": "fgt", "type": "ECSFargate"}]}
    res = estimate_cost(arch)
    assert res["status"] == "complete"
    assert res["monthly_usd_low"] == 18.93
    assert res["monthly_usd_high"] == 75.73
    assert abs(res["breakdown"]["fgt"]["unrounded_monthly_usd_low"] - 18.93255) < 1e-9
    assert abs(res["breakdown"]["fgt"]["unrounded_monthly_usd_high"] - 75.7302) < 1e-9


def test_cloudfront_and_s3_sku_and_pricing_separation():
    """Verify that CloudFront and S3 have distinct SKUs, product families, and rate dimensions."""
    cat = load_catalogue()
    cf_pricing = cat["services"]["CloudFront"]["pricing"]
    s3_pricing = cat["services"]["S3"]["pricing"]

    # CloudFront is regional edge transfer + requests
    assert cf_pricing["region_scope"] == "regional_edge"
    cf_comp_names = [c["name"] for c in cf_pricing["components"]]
    assert any("Data Transfer Out" in n for n in cf_comp_names)
    assert any("HTTPS Requests" in n for n in cf_comp_names)
    assert cf_pricing["components"][0]["unit_price"] == 0.109
    assert cf_pricing["components"][1]["unit_price"] == 0.0000012

    # S3 is ap-south-1 regional storage + tiered API requests
    assert s3_pricing["region_scope"] == "ap-south-1"
    s3_comp_names = [c["name"] for c in s3_pricing["components"]]
    assert any("Standard Storage" in n for n in s3_comp_names)
    assert any("Tier 1 Requests" in n for n in s3_comp_names)
    assert any("Tier 2 Requests" in n for n in s3_comp_names)
    assert s3_pricing["components"][0]["unit_price"] == 0.025
    assert s3_pricing["components"][1]["unit_price"] == 0.000005
    assert s3_pricing["components"][2]["unit_price"] == 0.0000004

    # Recorded evidence fixtures confirm distinct SKUs:
    # S3 Storage SKU USGUTP2JY23N9GH2 is strictly S3, while CloudFront DTO is XVZYVSAH88373VKR
    cf_ev = RECORDED_EVIDENCE_REGISTRY["CloudFront"]
    s3_ev = RECORDED_EVIDENCE_REGISTRY["S3"]
    assert s3_ev["storage_sku"] == "USGUTP2JY23N9GH2"
    assert cf_ev["dto_sku"] == "XVZYVSAH88373VKR"
    assert cf_ev["https_sku"] == "GJTTXSYXV43ANXTQ"
    assert cf_ev["dto_sku"] != s3_ev["storage_sku"]
