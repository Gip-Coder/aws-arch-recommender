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


def _normalize_quantity(
    qty: Decimal | float | int,
    pricing_unit: str,
    quantity_unit: str | None = None,
) -> Decimal:
    """Normalize usage quantity to the pricing dimension unit based on explicit units.

    Does not rely on ambiguous magnitude thresholds (e.g. qty >= 10000).
    Converts strictly based on explicit unit metadata or catalogue definitions.
    """
    try:
        qty_dec = Decimal(str(qty))
    except (TypeError, ValueError, ArithmeticError) as e:
        raise ValueError(f"Invalid quantity: {qty}") from e

    p_unit = pricing_unit.strip().lower()
    q_unit = (quantity_unit or "").strip().lower()

    # If unit is per million (e.g. "USD per million requests", "million requests")
    if "million" in p_unit:
        if q_unit:
            # Explicit raw count units
            if any(k in q_unit for k in ["requests", "request", "req", "count", "queries", "query", "calls", "call", "units", "unit"]) and "million" not in q_unit:
                return qty_dec / Decimal("1000000")
            # Explicit million units
            if "million" in q_unit or q_unit in ["m", "millions"]:
                return qty_dec
            # Explicit thousand units
            if "thousand" in q_unit or "1,000" in q_unit or "1k" in q_unit or "k" in q_unit:
                return qty_dec / Decimal("1000")
            return qty_dec
        # When quantity_unit is omitted, caller has passed quantity in pricing dimension units
        return qty_dec

    # If unit is per 1,000 (e.g. "USD per 1,000 tokens", "1K tokens")
    if "1,000 tokens" in p_unit or "thousand tokens" in p_unit or "1k tokens" in p_unit:
        if q_unit:
            if "token" in q_unit and not any(k in q_unit for k in ["1,000", "thousand", "1k", "k"]):
                return qty_dec / Decimal("1000")
            if any(k in q_unit for k in ["million", "m"]):
                return qty_dec * Decimal("1000")
            return qty_dec
        return qty_dec

    return qty_dec


def _extract_free_allowance(
    pricing_or_comp: dict[str, Any],
    pricing_unit: str,
    svc_mode: str,
) -> Decimal:
    """Extract and normalize the monthly free allowance quantity as Decimal."""
    if svc_mode in ("consumed", "ineligible", "none"):
        return Decimal("0.0")

    allowance = pricing_or_comp.get("free_allowance")
    if allowance is None:
        return Decimal("0.0")

    if isinstance(allowance, dict):
        raw_qty = allowance.get("quantity", 0.0)
        allow_unit = str(allowance.get("unit", pricing_unit))
    else:
        raw_qty = allowance
        allow_unit = pricing_unit

    try:
        return _normalize_quantity(raw_qty, pricing_unit, allow_unit)
    except ValueError:
        return Decimal("0.0")


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
        Allowances are pooled and shared at the account level across all resources.
      - 'consumed' / 'ineligible': assumes allowance is consumed or ineligible.
      - 'unknown': assumes conservative full on-demand rate with potential savings disclosed.
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

    # Account-level allowance tracking pools for shared free tier dimensions
    # Key: "<service_type>:<dimension_or_component>"
    allowance_pools_low: dict[str, Decimal] = {}
    allowance_pools_high: dict[str, Decimal] = {}

    for s in arch.get("services", []):
        sid = s["id"]
        stype = s["type"]
        svc_meta = cat_services.get(stype, {})
        pricing = svc_meta.get("pricing", {})

        # Service-level free tier mode override if present
        svc_mode = (s.get("free_tier_mode") or global_mode).lower()

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
                    "unrounded_monthly_usd_low": low_cost,
                    "unrounded_monthly_usd_high": high_cost,
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
                c_name = comp.get("name", "component")
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

                    raw_low_q = Decimal(str(comp.get("low_quantity", 1.0)))
                    raw_high_q = Decimal(str(comp.get("high_quantity", 1.0)))

                    # Non-negative quantity validation
                    raw_low_q = max(Decimal("0.0"), raw_low_q)
                    raw_high_q = max(Decimal("0.0"), raw_high_q)
                    if raw_low_q > raw_high_q:
                        raw_low_q, raw_high_q = raw_high_q, raw_low_q

                    c_low_qty = _normalize_quantity(raw_low_q, c_unit)
                    c_high_qty = _normalize_quantity(raw_high_q, c_unit)

                    pool_key = f"{stype}:{c_name}"
                    if pool_key not in allowance_pools_low:
                        initial_allowance = _extract_free_allowance(comp, c_unit, "available")
                        allowance_pools_low[pool_key] = initial_allowance
                        allowance_pools_high[pool_key] = initial_allowance

                    # Calculate potential savings if eligible and available
                    comp_initial_allowance = _extract_free_allowance(comp, c_unit, "available")
                    saved_low_qty = min(c_low_qty, comp_initial_allowance)
                    saved_high_qty = min(c_high_qty, comp_initial_allowance)

                    if svc_mode == "available":
                        avail_low = allowance_pools_low[pool_key]
                        avail_high = allowance_pools_high[pool_key]

                        used_low = min(c_low_qty, avail_low)
                        used_high = min(c_high_qty, avail_high)

                        billable_low = c_low_qty - used_low
                        billable_high = c_high_qty - used_high

                        allowance_pools_low[pool_key] -= used_low
                        allowance_pools_high[pool_key] -= used_high
                    else:
                        # consumed, ineligible, or unknown
                        billable_low = c_low_qty
                        billable_high = c_high_qty

                    comp_low_dec += p_dec * billable_low
                    comp_high_dec += p_dec * billable_high
                    comp_savings_low += p_dec * saved_low_qty
                    comp_savings_high += p_dec * saved_high_qty
                except (TypeError, ValueError, ArithmeticError):
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

            entry: dict[str, Any] = {
                "service": stype,
                "status": "verified",
                "unit_price": unit_price,
                "unit": unit,
                "monthly_usd_low": low_cost,
                "monthly_usd_high": high_cost,
                "unrounded_monthly_usd_low": float(comp_low_dec),
                "unrounded_monthly_usd_high": float(comp_high_dec),
                "usage_assumption": desc,
                "source_url": source_url,
                "components": components,
                "free_tier_mode": svc_mode,
                "potential_free_tier_savings_low": _round_currency(comp_savings_low),
                "potential_free_tier_savings_high": _round_currency(comp_savings_high),
            }
            if svc_mode == "unknown":
                entry["note"] = "Account free-tier availability unknown; modeled at on-demand rates with potential savings disclosed"
            breakdown[sid] = entry
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
            # Handle explicit test or caller inputs on service node
            if "requests" in s:
                raw_lq = Decimal(str(s["requests"]))
                raw_hq = Decimal(str(s["requests"]))
                input_unit = s.get("unit", "requests")
            elif "tokens" in s:
                raw_lq = Decimal(str(s["tokens"]))
                raw_hq = Decimal(str(s["tokens"]))
                input_unit = s.get("unit", "tokens")
            elif "usage_quantity" in s:
                raw_lq = Decimal(str(s["usage_quantity"]))
                raw_hq = Decimal(str(s["usage_quantity"]))
                input_unit = s.get("unit") or s.get("quantity_unit") or (
                    usage_assumptions.get("unit") if isinstance(usage_assumptions, dict) else None
                )
            elif "quantity" in s:
                raw_lq = Decimal(str(s["quantity"]))
                raw_hq = Decimal(str(s["quantity"]))
                input_unit = s.get("unit") or s.get("quantity_unit") or (
                    usage_assumptions.get("unit") if isinstance(usage_assumptions, dict) else None
                )
            else:
                raw_lq = Decimal(
                    str(usage_assumptions.get("low_quantity", 1))
                    if isinstance(usage_assumptions, dict)
                    else "1.0"
                )
                raw_hq = Decimal(
                    str(usage_assumptions.get("high_quantity", 1))
                    if isinstance(usage_assumptions, dict)
                    else "1.0"
                )
                input_unit = (
                    usage_assumptions.get("unit")
                    if isinstance(usage_assumptions, dict)
                    else None
                )

            # Prevent negative input quantities
            raw_lq = max(Decimal("0.0"), raw_lq)
            raw_hq = max(Decimal("0.0"), raw_hq)
            if raw_lq > raw_hq:
                raw_lq, raw_hq = raw_hq, raw_lq

            low_qty = _normalize_quantity(raw_lq, unit, input_unit)
            high_qty = _normalize_quantity(raw_hq, unit, input_unit)

            pool_key = f"{stype}:requests" if "requests" in unit.lower() else f"{stype}:quantity"
            if pool_key not in allowance_pools_low:
                initial_allowance = _extract_free_allowance(pricing, unit, "available")
                allowance_pools_low[pool_key] = initial_allowance
                allowance_pools_high[pool_key] = initial_allowance

            initial_allowance = _extract_free_allowance(pricing, unit, "available")
            saved_low_qty = min(low_qty, initial_allowance)
            saved_high_qty = min(high_qty, initial_allowance)

            if svc_mode == "available":
                avail_low = allowance_pools_low[pool_key]
                avail_high = allowance_pools_high[pool_key]

                used_low = min(low_qty, avail_low)
                used_high = min(high_qty, avail_high)

                billable_low = low_qty - used_low
                billable_high = high_qty - used_high

                allowance_pools_low[pool_key] -= used_low
                allowance_pools_high[pool_key] -= used_high
            else:
                # consumed, ineligible, or unknown
                billable_low = low_qty
                billable_high = high_qty

            if isinstance(unit_price, dict):
                u_low_dec = Decimal(str(unit_price.get("low", 0.0)))
                u_high_dec = Decimal(str(unit_price.get("high", 0.0)))
                low_cost_dec = u_low_dec * billable_low
                high_cost_dec = u_high_dec * billable_high
                savings_low_dec = u_low_dec * saved_low_qty
                savings_high_dec = u_high_dec * saved_high_qty
            else:
                p_dec = Decimal(str(unit_price))
                if p_dec < Decimal("0.0"):
                    raise ValueError("Negative unit price")
                low_cost_dec = p_dec * billable_low
                high_cost_dec = p_dec * billable_high
                savings_low_dec = p_dec * saved_low_qty
                savings_high_dec = p_dec * saved_high_qty

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

            entry = {
                "service": stype,
                "status": "verified",
                "unit_price": unit_price,
                "unit": unit,
                "monthly_usd_low": low_cost,
                "monthly_usd_high": high_cost,
                "unrounded_monthly_usd_low": float(low_cost_dec),
                "unrounded_monthly_usd_high": float(high_cost_dec),
                "usage_assumption": desc,
                "source_url": source_url,
                "free_tier_mode": svc_mode,
                "billable_quantity_low": float(billable_low),
                "billable_quantity_high": float(billable_high),
                "potential_free_tier_savings_low": savings_low,
                "potential_free_tier_savings_high": savings_high,
            }
            if svc_mode == "unknown":
                entry["note"] = "Account free-tier availability unknown; modeled at on-demand rates with potential savings disclosed"
            breakdown[sid] = entry
        except (TypeError, ValueError, ArithmeticError):
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

    if global_mode == "unknown":
        result["free_tier_note"] = "Account-wide free-tier availability unknown; charges calculated at conservative on-demand rates with potential savings disclosed."

    if not is_complete and has_verified_cost:
        result["partial_verified_monthly_usd_low"] = _round_currency(total_low)
        result["partial_verified_monthly_usd_high"] = _round_currency(total_high)

    return result
