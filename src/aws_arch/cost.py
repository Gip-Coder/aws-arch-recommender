"""Order-of-magnitude cost range from catalogue placeholders. Always labelled as an estimate."""
from .common import load_catalogue

def estimate_cost(arch: dict) -> dict:
    cat = load_catalogue()
    low = high = 0
    for s in arch["services"]:
        lo, hi = cat["services"][s["type"]]["cost"]
        low += lo; high += hi
    return {
        "monthly_usd_low": low, "monthly_usd_high": high,
        "region": cat["region"], "prices_checked_on": cat["prices_checked_on"],
        "note": "Order-of-magnitude estimate; verify against official AWS pricing.",
    }
