"""Order-of-magnitude cost range estimation from catalogue pricing model."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from .common import load_catalogue


def _round_currency(val: Decimal | float | int | None) -> float | None:
    """Quantize to 2 decimal places using financial HALF_UP rounding."""
    if val is None:
        return None
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _normalize_quantity(qty: float, unit_str: str) -> float:
    """Normalize raw request counts to millions if unit is per-million."""
    if "million" in unit_str.lower() and qty >= 10000:
        return qty / 1_000_000.0
    return qty


def _extract_free_allowance(
    pricing_or_comp: dict[str, Any], unit_str: str, mode: str
) -> float:
    """Extract and normalize the monthly free allowance quantity based on mode."""
    if mode in ("consumed", "ineligible", "none"):
        return 0.0

    allowance = pricing_or_comp.get("free_allowance")
    if allowance is None:
        return 0.0

    if isinstance(allowance, dict):
        raw_qty = float(allowance.get("quantity", 0.0))
        allow_unit = str(allowance.get("unit", unit_str))
    else:
        raw_qty = float(allowance)
        allow_unit = unit_str

    if "million" in unit_str.lower() and "million" not in allow_unit.lower() and raw_qty >= 1000:
        return raw_qty / 1_000_000.0

    return raw_qty


def estimate_cost(
    arch: dict[str, Any],
    catalogue: dict[str, Any] | None = None,
    free_tier_mode: str | None = None,
) -> dict[str, Any]:
    """Compute monthly low and high estimates and per-service breakdown.

    Reads pricing data from the catalogue. Unverified or incomplete prices
    are represented as None and explicitly disclosed, never converted to 0.0.

    Free-tier allowances:
      - 'available' (default): assumes eligible account and unused monthly allowance.
      - 'consumed' / 'ineligible': assumes allowance is consumed or ineligible.
      - 'unknown': assumes conservative full on-demand rate with savings noted.
    """
    cat = catalogue if catalogue is not None else load_catalogue()
    cat_services = cat.get("services", {})

    # Determine global free tier mode
    global_mode = (
        free_tier_mode
        or arch.get("free_tier_mode")
        or arch.get("pricing_options", {}).get("free_tier_mode")
        or "available"
    ).lower()

    breakdown: dict[str, Any] = {}
    assumptions: dict[str, Any] = {}
    incomplete_services: list[str] = []

    total_low = Decimal("0.0")
    total_high = Decimal("0.0")
    total_savings_low = Decimal("0.0")
    total_savings_high = Decimal("0.0")
    has_verified_cost = False

    for s in arch.get("services", []):
        sid = s["id"]
        stype = s["type"]
        svc_meta = cat_services.get(stype, {})
        pricing = svc_meta.get("pricing", {})

        # Service-level free tier mode override if present
        svc_mode = s.get("free_tier_mode") or global_mode

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
                total_low += Decimal(str(low_cost))
                total_high += Decimal(str(high_cost))
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
            comp_low_dec = Decimal("0.0")
            comp_high_dec = Decimal("0.0")
            comp_savings_low = Decimal("0.0")
            comp_savings_high = Decimal("0.0")
            all_comp_verified = (status == "verified")

            for comp in components:
                c_price = comp.get("unit_price")
                c_status = comp.get("status", status)
                c_unit = comp.get("unit", unit)

                if c_price is None or c_status != "verified":
                    all_comp_verified = False
                    break

                try:
                    p_dec = Decimal(str(c_price))
                    if p_dec < Decimal("0.0"):
                        all_comp_verified = False
                        break

                    raw_low_q = float(comp.get("low_quantity", 1.0))
                    raw_high_q = float(comp.get("high_quantity", 1.0))

                    # Non-negative quantity validation
                    raw_low_q = max(0.0, raw_low_q)
                    raw_high_q = max(0.0, raw_high_q)
                    if raw_low_q > raw_high_q:
                        raw_low_q, raw_high_q = raw_high_q, raw_low_q

                    c_low_qty = _normalize_quantity(raw_low_q, c_unit)
                    c_high_qty = _normalize_quantity(raw_high_q, c_unit)

                    allowance_qty = _extract_free_allowance(comp, c_unit, svc_mode)

                    billable_low = max(0.0, c_low_qty - allowance_qty)
                    billable_high = max(0.0, c_high_qty - allowance_qty)

                    saved_low_qty = c_low_qty - billable_low
                    saved_high_qty = c_high_qty - billable_high

                    comp_low_dec += p_dec * Decimal(str(billable_low))
                    comp_high_dec += p_dec * Decimal(str(billable_high))
                    comp_savings_low += p_dec * Decimal(str(saved_low_qty))
                    comp_savings_high += p_dec * Decimal(str(saved_high_qty))
                except (TypeError, ValueError):
                    all_comp_verified = False
                    break

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

            low_cost = _round_currency(comp_low_dec)
            high_cost = _round_currency(comp_high_dec)
            has_verified_cost = True
            if low_cost is not None and high_cost is not None:
                total_low += Decimal(str(low_cost))
                total_high += Decimal(str(high_cost))
            total_savings_low += comp_savings_low
            total_savings_high += comp_savings_high

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
                "free_tier_mode": svc_mode,
                "potential_free_tier_savings_low": _round_currency(comp_savings_low),
                "potential_free_tier_savings_high": _round_currency(comp_savings_high),
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

        try:
            # Handle explicit test or caller overrides on the service node
            if "usage_quantity" in s:
                raw_lq = float(s["usage_quantity"])
                raw_hq = float(s["usage_quantity"])
            elif "requests" in s:
                raw_lq = float(s["requests"])
                raw_hq = float(s["requests"])
            elif "quantity" in s:
                raw_lq = float(s["quantity"])
                raw_hq = float(s["quantity"])
            else:
                raw_lq = (
                    float(usage_assumptions.get("low_quantity", 1))
                    if isinstance(usage_assumptions, dict)
                    else 1.0
                )
                raw_hq = (
                    float(usage_assumptions.get("high_quantity", 1))
                    if isinstance(usage_assumptions, dict)
                    else 1.0
                )

            # Prevent negative input quantities
            raw_lq = max(0.0, raw_lq)
            raw_hq = max(0.0, raw_hq)
            if raw_lq > raw_hq:
                raw_lq, raw_hq = raw_hq, raw_lq

            low_qty = _normalize_quantity(raw_lq, unit)
            high_qty = _normalize_quantity(raw_hq, unit)

            allowance_qty = _extract_free_allowance(pricing, unit, svc_mode)

            billable_low = max(0.0, low_qty - allowance_qty)
            billable_high = max(0.0, high_qty - allowance_qty)

            saved_low_qty = low_qty - billable_low
            saved_high_qty = high_qty - billable_high

            if isinstance(unit_price, dict):
                u_low_dec = Decimal(str(unit_price.get("low", 0.0)))
                u_high_dec = Decimal(str(unit_price.get("high", 0.0)))
                low_cost_dec = u_low_dec * Decimal(str(billable_low))
                high_cost_dec = u_high_dec * Decimal(str(billable_high))
                savings_low_dec = u_low_dec * Decimal(str(saved_low_qty))
                savings_high_dec = u_high_dec * Decimal(str(saved_high_qty))
            else:
                p_dec = Decimal(str(unit_price))
                if p_dec < Decimal("0.0"):
                    raise ValueError("Negative unit price")
                low_cost_dec = p_dec * Decimal(str(billable_low))
                high_cost_dec = p_dec * Decimal(str(billable_high))
                savings_low_dec = p_dec * Decimal(str(saved_low_qty))
                savings_high_dec = p_dec * Decimal(str(saved_high_qty))

            low_cost = _round_currency(low_cost_dec)
            high_cost = _round_currency(high_cost_dec)
            savings_low = _round_currency(savings_low_dec)
            savings_high = _round_currency(savings_high_dec)

            has_verified_cost = True
            if low_cost is not None and high_cost is not None:
                total_low += Decimal(str(low_cost))
                total_high += Decimal(str(high_cost))
            total_savings_low += savings_low_dec
            total_savings_high += savings_high_dec

            breakdown[sid] = {
                "service": stype,
                "status": "verified",
                "unit_price": unit_price,
                "unit": unit,
                "monthly_usd_low": low_cost,
                "monthly_usd_high": high_cost,
                "usage_assumption": desc,
                "source_url": source_url,
                "free_tier_mode": svc_mode,
                "billable_quantity_low": billable_low,
                "billable_quantity_high": billable_high,
                "potential_free_tier_savings_low": savings_low,
                "potential_free_tier_savings_high": savings_high,
            }
        except (TypeError, ValueError):
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
                "note": "Invalid usage quantity or unit price input",
            }

    is_complete = len(incomplete_services) == 0

    if is_complete:
        overall_low = _round_currency(total_low)
        overall_high = _round_currency(total_high)
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
        "free_tier_mode": global_mode,
        "potential_free_tier_savings_low": _round_currency(total_savings_low),
        "potential_free_tier_savings_high": _round_currency(total_savings_high),
        "exclusions": [
            "Data transfer out exceeding baseline",
            "Cross-AZ and cross-region replication traffic",
            "Premium/Enterprise support plans",
            "Government/local taxes and currency conversion fees",
        ],
    }

    if not is_complete and has_verified_cost:
        result["partial_verified_monthly_usd_low"] = _round_currency(total_low)
        result["partial_verified_monthly_usd_high"] = _round_currency(total_high)

    return result
