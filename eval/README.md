# Evaluation

Owner: Person A. Scenarios live in `eval/scenarios/`, one JSON file per scenario (proposed format; the harness is not written yet).

## Scenario file format
```json
{
  "id": "ecommerce-100k",
  "text": "Free-text requirement given to the system",
  "expected_requirement": { "availability": "high", "traffic_pattern": "spiky" },
  "expected_services": ["CloudFront", "ApplicationLoadBalancer", "RDS_MultiAZ"],
  "forbidden_services": ["Bedrock"]
}
```
`expected_requirement` is a partial Requirement JSON (only the fields being checked). Service names must exist in `catalogue/catalogue.yaml`.

## Metrics (proposed definitions)
- **Parse accuracy:** fraction of fields in `expected_requirement` that match the parser output.
- **Service precision:** |recommended ∩ expected| / |recommended|.
- **Service coverage (recall):** |recommended ∩ expected| / |expected|.
- **Validity rate:** fraction of scenarios whose architecture passes the validator with no errors, without retry.
- **Forbidden-hit rate:** fraction of scenarios recommending any `forbidden_services`.
