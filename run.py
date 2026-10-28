"""CLI.  Mock (no AWS):  python run.py --mock
        Scenario:        python run.py --scenario serverless_api
        Live (Bedrock):  python run.py "Highly available e-commerce app for ~100k users"
"""
import argparse, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from aws_arch.common import ROOT, load_json
try:
    from aws_arch.llm import get_token_usage
except ImportError:
    get_token_usage = lambda: {"calls": 0}
from aws_arch.pipeline import (
    run_downstream,
    run_full,
    list_cached_scenarios,
    load_cached_scenario,
)

p = argparse.ArgumentParser(description="AWS Architecture Recommender CLI")
p.add_argument("text", nargs="?", help="Natural language requirements text")
p.add_argument("--mock", action="store_true", help="use examples/ ecommerce JSON, skip the LLM")
p.add_argument("--scenario", default=None, help="run deterministic pipeline on a cached scenario from examples/")
p.add_argument("--list-scenarios", action="store_true", help="list available cached scenarios")
p.add_argument("--model", default=None, help="override BEDROCK_MODEL_ID")
p.add_argument("--no-cache", action="store_true", help="bypass local response cache")
p.add_argument("--out", default=None, help="output directory (defaults to output/ or output/<scenario>/)")
a = p.parse_args()

if a.list_scenarios:
    scenarios = list_cached_scenarios()
    print("Available cached scenarios:")
    for s in scenarios:
        print(f"  - {s}")
    sys.exit(0)

if a.model:
    os.environ["BEDROCK_MODEL_ID"] = a.model
if a.no_cache:
    os.environ["AWS_ARCH_NO_CACHE"] = "1"

if a.scenario:
    req, arch = load_cached_scenario(a.scenario)
    out_dir = Path(a.out) if a.out else (ROOT / "output" / a.scenario)
    report = run_downstream(req, arch, out_dir)
elif a.mock:
    out_dir = Path(a.out) if a.out else (ROOT / "output")
    report = run_downstream(load_json(ROOT / "examples/ecommerce_requirement.json"),
                            load_json(ROOT / "examples/ecommerce_architecture.json"), out_dir)
elif a.text:
    out_dir = Path(a.out) if a.out else (ROOT / "output")
    report = run_full(a.text, out_dir)
    usage = get_token_usage()
    if usage["calls"] > 0:
        report["token_usage"] = usage
else:
    p.error("provide requirement text, --scenario <name>, --mock, or --list-scenarios")

print(json.dumps(report, indent=2))
