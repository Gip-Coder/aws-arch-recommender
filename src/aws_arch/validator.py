"""Deterministic validation: allow-list, connection rules, orphans."""
from .common import load_catalogue

def validate_architecture(arch: dict) -> list[str]:
    cat = load_catalogue()["services"]
    errors = []
    ids = {s["id"]: s["type"] for s in arch["services"]}
    if len(ids) != len(arch["services"]):
        errors.append("Duplicate service ids")
    for s in arch["services"]:
        if s["type"] not in cat:
            errors.append(f"Service '{s['type']}' is not in the curated catalogue")
    for c in arch["connections"]:
        if c["from"] not in ids or c["to"] not in ids:
            errors.append(f"Connection {c['from']}->{c['to']} references an unknown service id")
            continue
        src, dst = ids[c["from"]], ids[c["to"]]
        if src in cat and dst not in cat[src]["allowed_targets"]:
            errors.append(f"{src} -> {dst} is not an allowed connection")
    connected = {c["from"] for c in arch["connections"]} | {c["to"] for c in arch["connections"]}
    if len(arch["services"]) > 1:
        for sid in ids:
            if sid not in connected:
                errors.append(f"Orphaned component: '{sid}'")
    return errors
