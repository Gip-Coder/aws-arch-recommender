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
### Live Mode with Amazon Bedrock
1. **Request Model Access**: In the AWS Console, switch to your target region (e.g. `ap-south-1` Asia Pacific - Mumbai), navigate to **Amazon Bedrock -> Model access**, and enable access to your desired model (e.g. `Anthropic Claude 3 Haiku` or `Claude 3.5 Sonnet`).
2. **Configure Local Credentials**: Configure your AWS credentials via `aws configure` (or IAM Identity Center `aws configure sso`). Never commit credentials or paste keys in files.
3. **Set Environment Variables**: Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Set `BEDROCK_MODEL_ID` (e.g. `anthropic.claude-3-haiku-20240307-v1:0`) and `AWS_REGION` (default `ap-south-1`).
4. **Run Live Recommendations**:
   ```bash
   python run.py "Highly available e-commerce site for ~100k users"
   ```
   Optional flags:
   - `--model <id>`: Override the Bedrock model ID for a single run.
   - `--no-cache`: Bypass the disk cache in `.cache/` to force a fresh Bedrock call.
   - `--out <dir>`: Custom destination directory for report and diagram (default: `output/`).

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
