#!/usr/bin/env python3
"""Evaluation harness for AWS Architecture Recommender.
Usage:
    python eval/run_eval.py --mock-llm
    python eval/run_eval.py --live
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aws_arch.common import load_json, check_schema
from aws_arch.validator import validate_architecture
from aws_arch.security import check_security


def compute_metrics(expected: dict, actual_arch: dict, actual_req: dict | None = None, response_time_sec: float = 0.0) -> dict:
    """Compute evaluation metrics for a single scenario."""
    expected_services = set(expected.get("expected_services", []))
    recommended_services = {s["type"] for s in actual_arch.get("services", [])}

    # Accuracy / Coverage: fraction of expected services that were found
    if not expected_services:
        accuracy = 1.0 if not recommended_services else 0.0
    else:
        accuracy = len(expected_services & recommended_services) / len(expected_services)

    # Precision: fraction of recommended services that were expected
    if not recommended_services:
        precision = 1.0 if not expected_services else 0.0
    else:
        precision = len(expected_services & recommended_services) / len(recommended_services)

    # Pattern match
    pattern_match = 1.0 if actual_arch.get("pattern") == expected.get("expected_pattern") else 0.0

    # Architecture validity
    val_errors = validate_architecture(actual_arch)
    validity = 1.0 if not val_errors else 0.0

    # Security check pass rate
    sec_checks = check_security(actual_arch, actual_req)
    if sec_checks:
        passed_count = sum(1 for c in sec_checks if c.get("passed", False))
        sec_rate = passed_count / len(sec_checks)
    else:
        sec_rate = 1.0

    return {
        "id": expected["id"],
        "expected_pattern": expected.get("expected_pattern", "unknown"),
        "actual_pattern": actual_arch.get("pattern", "unknown"),
        "pattern_match": pattern_match,
        "service_accuracy": accuracy,
        "service_precision": precision,
        "architecture_valid": validity,
        "security_pass_rate": sec_rate,
        "response_time_sec": round(response_time_sec, 3),
        "validation_errors": val_errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate architecture recommender against scenarios")
    parser.add_argument("--mock-llm", action="store_true", default=True, help="use canned outputs in eval/canned/")
    parser.add_argument("--live", action="store_true", help="run against live pipeline (needs Bedrock)")
    parser.add_argument("--scenarios-dir", default=str(ROOT / "eval" / "scenarios"))
    parser.add_argument("--canned-dir", default=str(ROOT / "eval" / "canned"))
    parser.add_argument("--out-dir", default=str(ROOT / "output"))
    args = parser.parse_args()

    use_live = args.live
    scenarios_dir = Path(args.scenarios_dir)
    canned_dir = Path(args.canned_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scenario_files = sorted(scenarios_dir.glob("*.json"))
    if not scenario_files:
        print(f"No scenarios found in {scenarios_dir}")
        sys.exit(1)

    results = []

    for s_file in scenario_files:
        scenario = load_json(s_file)
        sid = scenario["id"]
        start_t = time.time()

        if use_live:
            from aws_arch.parser import parse_requirements
            from aws_arch.reasoner import recommend
            req = parse_requirements(scenario["input_text"])
            arch = recommend(req)
            elapsed = time.time() - start_t
        else:
            canned_file = canned_dir / f"{sid}.json"
            if not canned_file.exists():
                print(f"Warning: Missing canned file for {sid} at {canned_file}")
                continue
            canned = load_json(canned_file)
            req = canned.get("requirement", {})
            arch = canned.get("architecture", {})
            elapsed = 0.05

        metrics = compute_metrics(scenario, arch, req, elapsed)
        results.append(metrics)

    # Average metrics
    n = len(results)
    avg_acc = sum(r["service_accuracy"] for r in results) / n if n else 0.0
    avg_prec = sum(r["service_precision"] for r in results) / n if n else 0.0
    avg_pat = sum(r["pattern_match"] for r in results) / n if n else 0.0
    avg_val = sum(r["architecture_valid"] for r in results) / n if n else 0.0
    avg_sec = sum(r["security_pass_rate"] for r in results) / n if n else 0.0
    avg_time = sum(r["response_time_sec"] for r in results) / n if n else 0.0

    # Write CSV
    csv_path = out_dir / "eval_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "expected_pattern",
                "actual_pattern",
                "pattern_match",
                "service_accuracy",
                "service_precision",
                "architecture_valid",
                "security_pass_rate",
                "response_time_sec",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Write Markdown
    md_lines = [
        "# Evaluation Results\n",
        f"**Mode:** {'Live Pipeline (Bedrock)' if use_live else 'Mock LLM (Canned Outputs)'}\n",
        f"**Scenarios Evaluated:** {n}\n",
        "| Scenario ID | Pattern Match | Service Accuracy | Service Precision | Valid Arch | Security Pass % | Time (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        md_lines.append(
            f"| `{r['id']}` | {'Yes' if r['pattern_match'] else 'No'} | "
            f"{r['service_accuracy']*100:.1f}% | {r['service_precision']*100:.1f}% | "
            f"{'Pass' if r['architecture_valid'] else 'Fail'} | {r['security_pass_rate']*100:.1f}% | "
            f"{r['response_time_sec']}s |"
        )
    md_lines.append(
        f"| **AVERAGE** | **{avg_pat*100:.1f}%** | **{avg_acc*100:.1f}%** | "
        f"**{avg_prec*100:.1f}%** | **{avg_val*100:.1f}%** | **{avg_sec*100:.1f}%** | **{avg_time:.2f}s** |"
    )

    md_content = "\n".join(md_lines) + "\n"
    (out_dir / "eval_results.md").write_text(md_content, encoding="utf-8")

    # Print to console
    print(md_content)
    print(f"Results written to {csv_path} and {out_dir / 'eval_results.md'}")


if __name__ == "__main__":
    main()
