"""CLI.  Mock (no AWS):  python run.py --mock
        Live (Bedrock):  python run.py "Highly available e-commerce app for ~100k users"
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from aws_arch.common import ROOT, load_json
from aws_arch.pipeline import run_downstream, run_full

p = argparse.ArgumentParser()
p.add_argument("text", nargs="?")
p.add_argument("--mock", action="store_true", help="use examples/ JSON, skip the LLM")
p.add_argument("--out", default=str(ROOT / "output"))
a = p.parse_args()

if a.mock:
    report = run_downstream(load_json(ROOT / "examples/ecommerce_requirement.json"),
                            load_json(ROOT / "examples/ecommerce_architecture.json"), Path(a.out))
elif a.text:
    report = run_full(a.text, Path(a.out))
else:
    p.error("provide requirement text or --mock")
print(json.dumps(report, indent=2))
