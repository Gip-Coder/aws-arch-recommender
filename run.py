"""CLI.  Mock (no AWS):  python run.py --mock
        Live (Bedrock):  python run.py "Highly available e-commerce app for ~100k users"
"""
import argparse, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from aws_arch.common import ROOT, load_json
from aws_arch.llm import get_token_usage
from aws_arch.pipeline import run_downstream, run_full

p = argparse.ArgumentParser(description="AWS Architecture Recommender CLI")
p.add_argument("text", nargs="?", help="Natural language requirements text")
p.add_argument("--mock", action="store_true", help="use examples/ JSON, skip the LLM")
p.add_argument("--model", default=None, help="override BEDROCK_MODEL_ID")
p.add_argument("--no-cache", action="store_true", help="bypass local response cache")
p.add_argument("--out", default=str(ROOT / "output"), help="output directory")
a = p.parse_args()

if a.model:
    os.environ["BEDROCK_MODEL_ID"] = a.model
if a.no_cache:
    os.environ["AWS_ARCH_NO_CACHE"] = "1"

if a.mock:
    report = run_downstream(load_json(ROOT / "examples/ecommerce_requirement.json"),
                            load_json(ROOT / "examples/ecommerce_architecture.json"), Path(a.out))
elif a.text:
    report = run_full(a.text, Path(a.out))
    usage = get_token_usage()
    if usage["calls"] > 0:
        report["token_usage"] = usage
else:
    p.error("provide requirement text or --mock")
print(json.dumps(report, indent=2))
