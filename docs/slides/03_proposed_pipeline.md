# Slide 3: Proposed Pipeline & Deterministic Workflow

## Slide Title
**Hybrid Architecture: LLM Reasoning Coupled to Deterministic Engines**

## Key Bullet Points
- **Two-Stage LLM Core**: Stage 1 Requirement Parser (extracts structured JSON) &rarr; Stage 2 Architecture Reasoner (maps to catalogue patterns).
- **Strict Data Contracts**: Communication bounded entirely by JSON Schemas (`requirement.schema.json` and `architecture.schema.json`).
- **Deterministic Downstream Execution**: Validation, diagram generation, cost computation, and security auditing run via plain Python code (zero LLM calls).
- **Predictable & Auditable**: Decoupling language reasoning from downstream analysis ensures mathematical accuracy, zero cost hallucinations, and repeatable testing.

## Speaker Notes
The fundamental architectural decision of our system is separating probabilistic language understanding from deterministic downstream computation. We use Amazon Bedrock LLMs exclusively in two places: understanding the user's natural language requirements, and choosing the appropriate architecture pattern. Once the model outputs an Architecture JSON, the LLM is completely done. Downstream steps—checking connection validity, rendering the diagram, calculating cost ranges, and running security rules—are executed by deterministic Python algorithms. This avoids costly downstream LLM token usage, guarantees repeatability, and prevents mathematical hallucinations in cost estimation.

## Anticipated Examiner Questions
- **Q1: Why not let the LLM draw the diagram directly in SVG or Mermaid?**
  *Answer:* Academic benchmarks like DiagramAI (KES 2025) proved that LLMs make frequent syntax errors when generating visual diagrams directly from free text. Generating a structured JSON intermediate representation and rendering deterministically produces far higher syntax validity and layout consistency.
- **Q2: What happens if the LLM output fails schema validation?**
  *Answer:* We implemented an automated repair-and-retry loop (up to 2 retries) that feeds the exact schema validation error back into the model prompt to fix the output without crashing.
