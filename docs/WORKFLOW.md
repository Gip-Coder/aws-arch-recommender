# Workflow

## Branches
Created by `scripts/setup_branches.sh`. Naming: `a/<topic>` for Person A, `b/<topic>` for Person B, `shared/<topic>` for joint work.
Initial branches: `a/bedrock-live`, `a/prompts`, `a/evaluation`, `b/pricing`, `b/diagram`, `b/security`, `b/ui`, `shared/scenarios`.

## Pull request rules
- One task = one branch = one PR. Small commits. Never push to `main` directly.
- CI (`pytest`) must pass; fill in the PR template.
- Owner of the touched files reviews. Shared files: the other person reviews.
- Nobody edits `schemas/*.json` or `catalogue/catalogue.yaml` without telling the other person first.

## Ownership
| Owner | Paths |
|---|---|
| Person A (AI core) | `src/aws_arch/parser.py`, `reasoner.py`, `llm.py`, `validator.py`, `schemas/`, `catalogue/`, `prompts/`, `eval/` |
| Person B (rendering/analysis/infra) | `src/aws_arch/diagram.py`, `cost.py`, `security.py`, `app/`, `scripts/`, deployment files |
| Shared | `docs/`, `README.md`, `examples/`, `tests/` (each person adds tests for their own modules) |

## Day-by-day plan (draft; presentation window 24 Oct - 2 Nov 2026, adjust to the actual date)
| Day | Person A | Person B |
|---|---|---|
| 1 | Live Bedrock call (`a/bedrock-live`), model id from env | Real pricing with source URLs and date (`b/pricing`) |
| 2 | Parser/reasoner prompts + few-shot (`a/prompts`) | Diagram with `diagrams` icons (`b/diagram`) |
| 3 | Validator/schema tightening | Security rules to 15-25 (`b/security`) |
| 4 | Reference scenarios (`shared/scenarios`) | UI skeleton (`b/ui`) |
| 5 | Evaluation harness (`a/evaluation`) | UI polish + hosting |
| 6 | Run eval, fix failures | Cache 3 demo scenarios |
| 7 | Slides: AI pipeline | Slides: diagram, VPC, security |
| 8 | Dry run | Dry run, `docs/DEMO_CHECKLIST.md` |
