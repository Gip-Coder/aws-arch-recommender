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

## Web UI (Streamlit)

A Streamlit web dashboard is available for interactive architecture exploration, visual topology inspection, and Well-Architected reviews.

### 1. Installation & Launch (Windows PowerShell)

Activate the virtual environment and install dependencies:
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (includes Streamlit)
pip install -r requirements.txt

# Launch the Streamlit web dashboard
streamlit run app/streamlit_app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

### 2. Using Demo Mode (Offline)
- **Demo mode is enabled by default** via the sidebar checkbox.
- In Demo mode, the application runs 100% offline using verified scenarios in the `examples/` directory. No AWS account, credentials, or internet connection are required.
- **Selecting Scenarios:** Use the sidebar dropdown ("Select Cached Scenario") to switch between available reference architectures. The input requirements and resulting service topology, diagrams, cost projections, and security findings will update automatically.
- Clicking **Generate** in Demo mode re-runs the deterministic downstream pipeline locally for the selected scenario.

### 3. Switching to Live Mode
- To analyze arbitrary natural-language requirements dynamically, uncheck **Demo mode** in the sidebar.
- Enter your application requirements in the text box and click **Generate**.
- **Prerequisites for Live Mode:**
  1. Configure AWS credentials with permissions for Amazon Bedrock in `ap-south-1`:
     ```powershell
     aws configure
     ```
  2. Configure a valid Foundation Model ID in `src/aws_arch/llm.py` (e.g. `anthropic.claude-3-sonnet-20240229-v1:0` or similar Bedrock model).

### 4. Common Troubleshooting
- **Graphviz Diagram Rendering:** If Graphviz (`dot`) is installed and on the system `PATH`, high-resolution PNG diagrams are generated. If `dot` is not installed, the UI automatically falls back to rendering the topology directly in your browser using Graphviz DOT and provides the raw DOT source code.
- **Port Conflicts:** If port 8501 is busy, specify an alternate port:
  ```powershell
  streamlit run app/streamlit_app.py --server.port 8502
  ```
- **PowerShell Execution Policy:** If running `Activate.ps1` produces a script execution restriction, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```

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
