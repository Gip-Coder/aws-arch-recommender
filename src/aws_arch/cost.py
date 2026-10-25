"""Order-of-magnitude cost range estimation from catalogue pricing model."""
from typing import Any
from .common import load_catalogue


def estimate_cost(arch: dict, catalogue: dict | None = None) -> dict[str, Any]:
    """Compute monthly low and high estimates and per-service breakdown.

    Reads pricing data from the catalogue. Unverified or incomplete prices
    are represented as None and explicitly disclosed, never converted to 0.0.
    """
    cat = catalogue if catalogue is not None else load_catalogue()
    cat_services = cat.get("services", {})

    breakdown: dict[str, Any] = {}
    assumptions: dict[str, Any] = {}
    incomplete_services: list[str] = []

    total_low: float = 0.0
    total_high: float = 0.0
    has_verified_cost = False

    for s in arch.get("services", []):
        sid = s["id"]
        stype = s["type"]
        svc_meta = cat_services.get(stype, {})
        pricing = svc_meta.get("pricing", {})

        unit_price = pricing.get("unit_price")
        unit = pricing.get("unit", "USD")
        status = pricing.get("status", "TODO verify")
        source_url = pricing.get("source_url")
        usage_assumptions = pricing.get("usage_assumptions", {})
        components = pricing.get("components")

        # Legacy fallback if catalogue has cost: [low, high]
        legacy_cost = svc_meta.get("cost")
        if unit_price is None and not components and legacy_cost and isinstance(legacy_cost, list) and len(legacy_cost) == 2:
            if legacy_cost[0] is not None and legacy_cost[1] is not None:
                low_cost = float(legacy_cost[0])
                high_cost = float(legacy_cost[1])
                status = "verified"
                has_verified_cost = True
                total_low += low_cost
                total_high += high_cost
                breakdown[sid] = {
                    "service": stype,
                    "status": status,
                    "unit_price": legacy_cost,
                    "unit": unit,
                    "monthly_usd_low": low_cost,
                    "monthly_usd_high": high_cost,
                    "source_url": source_url,
                }
                continue

        desc = (
            usage_assumptions.get("description", str(usage_assumptions))
            if isinstance(usage_assumptions, dict)
            else str(usage_assumptions)
        )
        assumptions[sid] = desc

        # Multi-component pricing model
        if components and isinstance(components, list):
            comp_low = 0.0
            comp_high = 0.0
            all_comp_verified = (status == "verified")
            for comp in components:
                c_price = comp.get("unit_price")
                c_status = comp.get("status", status)
                if c_price is None or c_status != "verified":
                    all_comp_verified = False
                    break
                c_low_qty = float(comp.get("low_quantity", 1.0))
                c_high_qty = float(comp.get("high_quantity", 1.0))
                comp_low += float(c_price) * c_low_qty
                comp_high += float(c_price) * c_high_qty

            if not all_comp_verified:
                incomplete_services.append(stype)
                breakdown[sid] = {
                    "service": stype,
                    "status": "incomplete",
                    "unit_price": unit_price,
                    "unit": unit,
                    "monthly_usd_low": None,
                    "monthly_usd_high": None,
                    "usage_assumption": desc,
                    "source_url": source_url,
                    "components": components,
                    "note": "Pricing unverified (TODO verify)",
                }
                continue

            low_cost = round(comp_low, 2)
            high_cost = round(comp_high, 2)
            has_verified_cost = True
            total_low += low_cost
            total_high += high_cost

            breakdown[sid] = {
                "service": stype,
                "status": "verified",
                "unit_price": unit_price,
                "unit": unit,
                "monthly_usd_low": low_cost,
                "monthly_usd_high": high_cost,
                "usage_assumption": desc,
                "source_url": source_url,
                "components": components,
            }
            continue

        # Single-dimension pricing model
        if unit_price is None or status != "verified":
            incomplete_services.append(stype)
            breakdown[sid] = {
                "service": stype,
                "status": "incomplete",
                "unit_price": None,
                "unit": unit,
                "monthly_usd_low": None,
                "monthly_usd_high": None,
                "usage_assumption": desc,
                "source_url": source_url,
                "note": "Pricing unverified (TODO verify)",
            }
            continue

        low_qty = (
            float(usage_assumptions.get("low_quantity", 1))
            if isinstance(usage_assumptions, dict)
            else 1.0
        )
        high_qty = (
            float(usage_assumptions.get("high_quantity", 1))
            if isinstance(usage_assumptions, dict)
            else 1.0
        )

        if isinstance(unit_price, dict):
            u_low = float(unit_price.get("low", 0.0))
            u_high = float(unit_price.get("high", 0.0))
            low_cost = round(u_low * low_qty, 2)
            high_cost = round(u_high * high_qty, 2)
        else:
            u_price = float(unit_price)
            low_cost = round(u_price * low_qty, 2)
            high_cost = round(u_price * high_qty, 2)

        has_verified_cost = True
        total_low += low_cost
        total_high += high_cost

        breakdown[sid] = {
            "service": stype,
            "status": "verified",
            "unit_price": unit_price,
            "unit": unit,
            "monthly_usd_low": low_cost,
            "monthly_usd_high": high_cost,
            "usage_assumption": desc,
            "source_url": source_url,
        }

    is_complete = len(incomplete_services) == 0

    if is_complete:
        overall_low: float | None = round(total_low, 2)
        overall_high: float | None = round(total_high, 2)
        status_str = "complete"
    else:
        status_str = "incomplete"
        # Never convert unknown price into 0.0 or present partial total as full total
        overall_low = None
        overall_high = None

    result: dict[str, Any] = {
        "monthly_usd_low": overall_low,
        "monthly_usd_high": overall_high,
        "region": cat.get("region", "ap-south-1"),
        "prices_checked_on": cat.get("prices_checked_on", "TODO"),
        "status": status_str,
        "note": "Order-of-magnitude estimate; verify against official AWS pricing.",
        "incomplete_services": sorted(list(set(incomplete_services))),
        "breakdown": breakdown,
        "assumptions": assumptions,
        "exclusions": [
            "Data transfer out exceeding baseline",
            "Cross-AZ and cross-region replication traffic",
            "Premium/Enterprise support plans",
            "Government/local taxes and currency conversion fees",
        ],
    }

    if not is_complete and has_verified_cost:
        result["partial_verified_monthly_usd_low"] = round(total_low, 2)
        result["partial_verified_monthly_usd_high"] = round(total_high, 2)

    return result
