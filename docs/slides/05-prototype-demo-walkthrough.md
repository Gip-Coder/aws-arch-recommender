# Topic 5: Prototype and Demo Walkthrough

**Presentation Section:** Implementation & Demonstration
**Objective:** Provide a presenter-ready walkthrough of the AWS Architecture Recommender prototype, explain the verified offline mock execution workflow, and review generated architectural artifacts.

---

## Slide 1: Problem Statement & Recommender Pipeline Architecture

### Key Points
- Challenge: Designing cloud architectures manually is error-prone, requiring deep knowledge of 200+ AWS services and Well-Architected guidelines.
- Solution: An AI-assisted recommendation engine that transforms plain-English requirements into validated, costed, and security-reviewed architectures.
- Hybrid Pipeline: LLMs handle language tasks (parsing and pattern selection); deterministic Python modules handle validation, costing, and security.
- Scope Boundary: Recommendation-only system; no cloud resources are provisioned or altered during execution.

### Speaker Notes
The fundamental motivation behind this project is to bridge the gap between business requirements and AWS technical architecture. Manually designing systems often results in over-provisioned compute, unsegmented networks, or security misconfigurations. Our tool implements a disciplined hybrid pipeline: natural language is parsed and reasoned by Foundation Models, but all downstream structural validation, cost calculations, and security evaluations are executed by deterministic code adhering to strict schemas.

### Questions an Examiner May Ask
**Q1. Why not let the Large Language Model generate the entire architecture and cost breakdown directly?**

Answer: LLMs are prone to hallucinations, fabricating non-existent services, unsupported connections, and inaccurate pricing arithmetic. Confining the LLM to requirement extraction and pattern selection while using deterministic Python modules for validation and costing guarantees mathematical and structural accuracy.

**Q2. Does this prototype deploy or provision active infrastructure in an AWS account?**

Answer: No. The recommender is strictly an architecture planning and analysis tool; it emits structured reports and visual diagrams without provisioning or altering active cloud infrastructure.

---

## Slide 2: Ingestion & Deterministic Validation Gate

### Key Points
- Ingestion: Extracts structured attributes (app type, user count, availability, storage, budget sensitivity) into `requirement.json`.
- Reasoning: Selects reference patterns from `catalogue/patterns.yaml` bounded by the 17-service allow-list in `catalogue/catalogue.yaml`.
- Schema Verification: Both intermediate JSON documents are strictly validated against formal draft JSON Schemas.
- Graph Topology Validation: `validator.py` checks allowed connection targets and flags disconnected or orphan components.

### Speaker Notes
The integrity of the recommendation engine relies on its validation gates. When user requirements enter the pipeline, they are mapped into a structured requirement schema. During the reasoning stage, the LLM is constrained by system prompts to pick services exclusively from our curated catalogue of 17 AWS services. Before any downstream analysis occurs, `validator.py` inspects the candidate topology to ensure that connection rules—such as an ALB connecting to an EC2 Auto Scaling Group—are respected, and that no orphaned or disconnected nodes exist.

### Questions an Examiner May Ask
**Q1. What happens if the reasoning engine attempts to recommend an unapproved or hallucinated service?**

Answer: The validator compares all service IDs against the allow-list in `catalogue/catalogue.yaml`. If an unknown service (e.g. "AWS MagicBox") appears, `validator.py` catches it, rejects the architecture, and returns an error report without running downstream analyses.

**Q2. How are circular or invalid connections caught during validation?**

Answer: The validator inspects the directional `from` and `to` connection pairs against the `allowed_targets` defined in `catalogue.yaml` for each service type, rejecting illegal connections (such as a database connecting directly to an Application Load Balancer).

---

## Slide 3: Downstream Synthesis (Diagram, Cost & Security Review)

### Key Points
- Graphviz Generation: `diagram.py` converts architecture JSON into `output/diagram.dot` and optional `output/diagram.png`.
- Cost Range Modeling: `cost.py` calculates conservative low and high monthly USD estimates based on sizing assumptions.
- Well-Architected Security Audit: `security.py` runs rule-based checks for IAM roles, encryption at rest, TLS in transit, S3 protection, and Multi-AZ DBs.
- Consolidated Artifact: `pipeline.py` synthesizes findings into `output/report.json`.

### Speaker Notes
Once an architecture passes structural validation, the downstream synthesis stage executes three deterministic analysis engines. The diagram generator builds a clean Graphviz DOT topology and attempts PNG compilation. Simultaneously, the cost estimator calculates monthly low and high financial envelopes based on standard regional usage baselines. Concurrently, the security auditor checks Well-Architected controls, flagging missing IAM roles or single-AZ database risks. All findings are aggregated into a single, machine-readable `report.json` artifact.

### Questions an Examiner May Ask
**Q1. How does the security engine evaluate encryption and high-availability compliance?**

Answer: It performs declarative inspection: it verifies that "encryption at rest" and "encryption in transit" are declared in the architecture's security controls, and if requirements demand high availability, it verifies that `RDS_MultiAZ` is selected instead of standalone `RDS`.

**Q2. What happens if Graphviz is not installed on the host machine?**

Answer: The diagram module catches the absence of the `dot` binary gracefully: it always writes the valid `output/diagram.dot` source file to disk and skips PNG compilation without raising an unhandled exception or breaking the pipeline.

---

## Slide 4: Executing the Verified Offline Mock Workflow

### Key Points
- Verified Baseline Command: Executed from PowerShell via `python run.py --mock`.
- 100% Offline: Loads verified reference scenarios from `examples/` without requiring AWS credentials or internet access.
- Execution Output: Exits 0, outputs serialized report JSON to stdout, and writes `report.json` to the `output/` directory.
- Test Reproducibility: Validated locally by `pytest -q` (all baseline unit tests passing).

### Speaker Notes
To ensure flawless demonstration reliability in academic and testing settings, the repository includes a fully offline mock mode. Executing `python run.py --mock` bypasses external API calls by loading curated requirement and architecture files from the `examples/` directory directly into the deterministic downstream pipeline. The execution completes in under a quarter of a second, outputting the complete JSON report, Graphviz DOT diagram, and cost estimates. This command serves as our verified automated baseline on branch `main`.

### Questions an Examiner May Ask
**Q1. What does the mock workflow prove if it does not invoke an active LLM?**

Answer: It proves the end-to-end correctness of the deterministic downstream pipeline: schema validation, Graphviz rendering, cost arithmetic, security auditing, and report serialization execute cleanly without external dependencies.

**Q2. Where are the generated output files stored during a mock run?**

Answer: The pipeline writes artifacts to the `output/` directory in the repository root, creating `report.json`, `diagram.dot`, and `diagram.png` (if `dot` is installed).

---

## Slide 5: Demonstration Roadmap & Live Mode Prerequisites

### Key Points
- Baseline Scope: Command-line pipeline execution via `run.py --mock` on branch `main`.
- Web Interface Deliverable: Interactive Streamlit UI dashboard implemented on branch `b/ui` (`streamlit run app/streamlit_app.py`).
- Serverless Deployment Deliverable: Console deployment guide and Lambda handler implemented on branch `b/deploy-guide`.
- Live Mode Prerequisites: Requires AWS credentials (`aws configure`) in `ap-south-1` and a valid Bedrock model ID in `src/aws_arch/llm.py`.

### Speaker Notes
To provide examiners with clear visibility into project engineering, we distinguish baseline repository capabilities from our modular feature branch deliverables. On our core `main` branch, the command-line pipeline provides complete deterministic analysis. The interactive Streamlit web dashboard—featuring offline scenario exploration and visual tabs—was developed on feature branch `b/ui`. For live Bedrock inference, the system requires active AWS credentials in Mumbai and a configured Foundation Model ID, ensuring transparent operational boundaries.

### Questions an Examiner May Ask
**Q1. Why are the Streamlit UI and serverless Lambda handler maintained on separate branches?**

Answer: The project follows a modular Git feature-branch strategy where individual components (pricing engine, diagrams, UI, deployment) are developed, tested, and audited in isolation before sequential integration into `main`.

**Q2. What error occurs if live mode is triggered without configuring AWS Bedrock credentials?**

Answer: The pipeline's Boto3 client raises a client authentication error. The Streamlit UI catches this failure gracefully and displays an informative guidance message explaining how to configure credentials or re-enable Demo mode.
