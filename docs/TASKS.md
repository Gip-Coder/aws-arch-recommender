# Task split and plan

For branching workflow, PR rules, and the day-by-day schedule, see [Workflow Guide](WORKFLOW.md) (`docs/WORKFLOW.md`).

| Area | Owner | Branch | Status |
|---|---|---|---|
| Live Bedrock integration (env vars, boto3 runtime) | A | `a/bedrock-live` | todo |
| Prompts, parser, reasoner, few-shot examples | A | `a/prompts` | todo |
| Validator rules, JSON Schema tightening | A | `a/prompts` | scaffolded |
| Evaluation harness (accuracy, precision, coverage) | A | `a/evaluation` | todo |
| Cost estimator (real prices, region, date) | B | `b/pricing` | placeholder prices |
| Diagram rendering (swap DOT for `diagrams` + AWS icons) | B | `b/diagram` | DOT scaffolded |
| Security rule set (15-25 rules, pillar-mapped) | B | `b/security` | 5 rules |
| Web UI + deployment (S3/CloudFront/API GW/Lambda) | B | `b/ui` | todo |
| Reference scenarios (10-15 test cases for evaluation) | Shared | `shared/scenarios` | todo |

## Before the presentation (24 Oct - 2 Nov 2026)
- [ ] 3 cached demo scenarios
- [ ] draw.io architecture diagrams (system + sample output)
- [ ] VPC / security-group / scaling slides
- [ ] 10-15 reference scenarios for evaluation (`shared/scenarios`)
