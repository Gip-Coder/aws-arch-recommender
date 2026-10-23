"""Stage 2: Requirement JSON -> draft Architecture JSON (LLM, constrained to the catalogue)."""
import json
from .common import load_catalogue, load_patterns, check_schema
from .llm import call_llm, parse_json_reply

def build_system_prompt() -> str:
    cat = sorted(load_catalogue()["services"])
    pats = json.dumps(load_patterns())
    return (
        "You are an AWS architecture assistant. Choose ONE named pattern and assemble services "
        f"ONLY from this allow-list: {cat}. Patterns: {pats}. Reply with ONLY JSON with keys "
        "pattern, services[{id,type,role,rationale}], connections[{from,to}], security_controls[], "
        "assumptions[]. Give a one-sentence rationale per service."
    )

def recommend(requirements: dict, retries: int = 2) -> dict:
    last = None
    for _ in range(retries + 1):
        try:
            arch = parse_json_reply(call_llm(build_system_prompt(), json.dumps(requirements)))
            check_schema(arch, "architecture")
            return arch
        except Exception as e:
            last = e
    raise ValueError(f"Could not obtain valid architecture JSON: {last}")
