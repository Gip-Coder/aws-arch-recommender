# AI-Driven AWS Cloud Architecture Design & Recommendation System

Cloud Architecture Design (VIT) course project. Turns a plain-English application description into
an AWS service recommendation, a structured architecture JSON, a diagram, an approximate cost range
and a Well-Architected-style security review. **Recommendation-only: nothing is ever deployed.**

## Pipeline
```
text -> Requirement Parser (LLM) -> Requirement JSON
     -> Reasoning Engine (LLM, constrained to catalogue) -> Architecture JSON
     -> Validation (allow-list, connection rules, orphans)
     -> Diagram | Cost | Security  (deterministic) -> report
```
The LLM is used only for the two language steps; everything downstream is plain code on validated JSON.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py --mock          # no AWS needed: runs the example e-commerce scenario
pytest                        # unit tests
python run.py "Highly available e-commerce site for ~100k users"   # needs Bedrock access
```

### Windows (PowerShell)
If `make` is not installed, run the equivalents directly without activation:
```powershell
python -m venv .venv                                  # venv
.venv\Scripts\pip install -r requirements.txt         # install
.venv\Scripts\pytest -q                               # test
.venv\Scripts\python run.py --mock                    # mock
```

For live mode, copy `.env.example` to `.env`, set `BEDROCK_MODEL_ID` and `AWS_REGION` (see `.env.example`), and configure AWS credentials (`aws configure`) -- never commit credentials. PNG diagrams need Graphviz (`dot`) installed; otherwise a `.dot` file is written.

## Documentation
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Pipeline design, contract schemas, and deterministic stages
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Branching strategy, pull request rules, ownership, and day-by-day plan
- [`docs/TASKS.md`](docs/TASKS.md) - Task split, branch mapping, and deliverable status

## Layout
| Path | Purpose |
|---|---|
| `schemas/` | JSON Schemas for Requirement and Architecture JSON (the contract between stages) |
| `catalogue/` | Curated AWS service allow-list and named reference patterns |
| `src/aws_arch/` | parser, reasoner, validator, diagram, cost, security, pipeline |
| `examples/` | Sample requirement and architecture JSON |
| `tests/` | pytest suite |
| `docs/` | Plan and task split |

## Status
Scaffold with working deterministic stages. TODO: replace placeholder prices, prompts/few-shot
examples, evaluation harness, web UI, deployment (see `docs/TASKS.md`).

## Authors
P. Giphy Bershan (24BCE2201), Sudipta Majumder (24BCE2882) -- guide: Dr. Sunija A P

