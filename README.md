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
For live mode set a real Bedrock model id in `src/aws_arch/llm.py` and configure AWS credentials
(`aws configure`) -- never commit credentials. PNG diagrams need Graphviz (`dot`) installed;
otherwise a `.dot` file is written.

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
