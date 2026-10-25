"""Deterministic validation: allow-list, connection rules, orphans."""
from .common import load_catalogue

def validate_architecture(arch: dict) -> list[str]:
    cat = load_catalogue()["services"]
    errors = []
    services = arch.get("services")
    if not isinstance(services, list):
        return ["Architecture must contain a list of 'services'"]
    connections = arch.get("connections")
    if not isinstance(connections, list):
        connections = []

    ids = {}
    has_duplicates = False
    for s in services:
        if not isinstance(s, dict) or "id" not in s or "type" not in s:
            errors.append("Invalid service definition in architecture")
            continue
        sid = s["id"]
        if sid in ids:
            has_duplicates = True
        ids[sid] = s["type"]
    if has_duplicates:
        errors.append("Duplicate service ids")

    for s in services:
        if isinstance(s, dict) and "type" in s:
            if s["type"] not in cat:
                errors.append(f"Service '{s['type']}' is not in the curated catalogue")

    for c in connections:
        if not isinstance(c, dict) or "from" not in c or "to" not in c:
            errors.append("Invalid connection definition")
            continue
        if c["from"] not in ids or c["to"] not in ids:
            errors.append(f"Connection {c['from']}->{c['to']} references an unknown service id")
            continue
        src, dst = ids[c["from"]], ids[c["to"]]
        if src in cat and dst not in cat[src]["allowed_targets"]:
            errors.append(f"{src} -> {dst} is not an allowed connection")

    connected = {c["from"] for c in connections if isinstance(c, dict) and "from" in c} | {c["to"] for c in connections if isinstance(c, dict) and "to" in c}
    if len(services) > 1:
        for sid in ids:
            if sid not in connected:
                errors.append(f"Orphaned component: '{sid}'")
    return errors
