import json
from pathlib import Path
from .common import check_schema
from .validator import validate_architecture
from .cost import estimate_cost
from .security import check_security
from .diagram import render

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
