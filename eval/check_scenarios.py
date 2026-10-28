#!/usr/bin/env python3
"""Validation checker for evaluation scenario definitions in eval/scenarios/*.json.
Ensures:
- Required fields are present: id, input_text, expected_pattern, expected_services
- expected_pattern exists in catalogue/patterns.yaml
- Every expected_services entry exists in catalogue/catalogue.yaml
- IDs are unique across all scenario files
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aws_arch.common import load_json, load_catalogue, load_patterns


def validate_scenarios(scenarios_dir: Path | None = None) -> list[str]:
    if scenarios_dir is None:
        scenarios_dir = ROOT / "eval" / "scenarios"

    errors = []
    if not scenarios_dir.exists():
        return [f"Scenarios directory does not exist: {scenarios_dir}"]

    scenario_files = list(scenarios_dir.glob("*.json"))
    if not scenario_files:
        return [f"No JSON scenario files found in {scenarios_dir}"]

    cat = load_catalogue()["services"]
    patterns = load_patterns()
    seen_ids = set()

    for path in scenario_files:
        try:
            data = load_json(path)
        except Exception as e:
            errors.append(f"[{path.name}] Invalid JSON file: {e}")
            continue

        sid = data.get("id")
        if not sid or not isinstance(sid, str):
            errors.append(f"[{path.name}] Missing or non-string 'id'")
        elif sid in seen_ids:
            errors.append(f"[{path.name}] Duplicate scenario id: '{sid}'")
        else:
            seen_ids.add(sid)

        input_text = data.get("input_text")
        if not input_text or not isinstance(input_text, str):
            errors.append(f"[{path.name}] Missing or non-string 'input_text'")

        pattern = data.get("expected_pattern")
        if not pattern:
            errors.append(f"[{path.name}] Missing 'expected_pattern'")
        elif pattern not in patterns:
            errors.append(f"[{path.name}] 'expected_pattern' '{pattern}' is not defined in catalogue/patterns.yaml")

        services = data.get("expected_services")
        if not isinstance(services, list) or not services:
            errors.append(f"[{path.name}] 'expected_services' must be a non-empty list")
        else:
            for s in services:
                if s not in cat:
                    errors.append(f"[{path.name}] Service '{s}' in expected_services does not exist in catalogue.yaml")

    return errors


def main():
    errors = validate_scenarios()
    if errors:
        print("Scenario validation FAILED with the following errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("All scenarios in eval/scenarios/ passed validation successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
