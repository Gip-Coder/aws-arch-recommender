import json
from pathlib import Path
from .common import ROOT, load_json, check_schema
from .validator import validate_architecture
from .cost import estimate_cost
from .security import check_security
from .diagram import render

EXAMPLES_DIR = ROOT / "examples"

def list_cached_scenarios() -> list[str]:
    """Return sorted list of scenario names available in examples/."""
    scenarios = set()
    if EXAMPLES_DIR.exists():
        for req_path in EXAMPLES_DIR.glob("*.requirement.json"):
            name = req_path.name.removesuffix(".requirement.json")
            arch_path = EXAMPLES_DIR / f"{name}.architecture.json"
            if arch_path.exists():
                scenarios.add(name)
    return sorted(scenarios)

def load_cached_scenario(name: str) -> tuple[dict, dict]:
    """Load requirement and architecture JSON for a named cached scenario."""
    req_file = EXAMPLES_DIR / f"{name}.requirement.json"
    arch_file = EXAMPLES_DIR / f"{name}.architecture.json"
    if not req_file.exists() or not arch_file.exists():
        available = list_cached_scenarios()
        raise FileNotFoundError(
            f"Scenario '{name}' not found in {EXAMPLES_DIR}. "
            f"Available scenarios: {', '.join(available) if available else 'none'}"
        )
    return load_json(req_file), load_json(arch_file)

def run_downstream(req: dict, arch: dict, out_dir: Path) -> dict:
    check_schema(arch, "architecture")
    errors = validate_architecture(arch)
    if errors:
        return {"valid": False, "errors": errors}
    out_dir.mkdir(parents=True, exist_ok=True)
    files = render(arch, out_dir / "diagram")
    report = {
        "valid": True,
        "services": [{"type": s["type"], "role": s["role"], "why": s.get("rationale", "")} for s in arch["services"]],
        "cost": estimate_cost(arch),
        "security": check_security(arch, req),
        "diagram_files": [str(f) for f in files],
        "assumptions": arch.get("assumptions", []) + req.get("assumptions", []),
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    return report

def run_full(text: str, out_dir: Path) -> dict:
    from .parser import parse_requirements
    from .reasoner import recommend
    req = parse_requirements(text)
    arch = recommend(req)
    return run_downstream(req, arch, out_dir)
