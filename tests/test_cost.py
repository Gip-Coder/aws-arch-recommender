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


def test_catalogue_yaml_all_services_verified_with_official_sources():
    """Verify that every service in catalogue.yaml has verified status and valid AWS source."""
    cat = load_catalogue()
    assert cat["region"] == "ap-south-1"
    assert cat["prices_checked_on"] == "2026-10-25"
    services = cat.get("services", {})
    assert len(services) == 17

    for name, data in services.items():
        assert "pricing" in data, f"{name} is missing pricing block"
        pricing = data["pricing"]
        assert "source_url" in pricing and pricing["source_url"].startswith("https://aws.amazon.com/"), (
            f"{name} must have an official AWS source_url"
        )
        assert pricing.get("status") == "verified", f"{name} is not verified"
        assert pricing.get("unit_price") is not None, f"{name} verified price must not be null"
        assert "usage_assumptions" in pricing, f"{name} is missing usage_assumptions"


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
