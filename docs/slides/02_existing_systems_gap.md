# Slide 2: Existing Systems, Limitations & Research Gap

## Slide Title
**Landscape Analysis: Vendor, Commercial & Academic Tools**

## Key Bullet Points
- **Vendor Tools (Amazon Q / AWS Kiro)**: Strong for IaC generation and IDE tasks, but lack integrated, all-in-one recommendation reports covering diagram, cost, and security from natural text.
- **Commercial Diagram Tools (Cloudairy, Eraser.io, Miro)**: Excellent visual drawing engines, but require users to already know exactly which services and configurations to draw.
- **Academic Systems (CloudArchitectBuddy, ACSE-Eval)**: Pioneered structured state tracking and threat modeling, but lack automated visual diagramming or end-to-end pricing synthesis.
- **Identified Research Gap**: Absence of an integrated, explainable pipeline coupling natural-language requirement interpretation with deterministic AWS validation, cost estimation, and diagramming in a single workflow.

## Speaker Notes
When surveying existing tools, we noticed a clear fragmentation across the software lifecycle. Vendor assistants like Amazon Q Developer generate CloudFormation snippets, but do not provide an end-to-end explainable architecture review from scratch. AI diagramming tools like Cloudairy or Eraser can render beautiful icons, but they expect the engineer to already know their architecture. Meanwhile, academic prototypes like CloudArchitectBuddy introduced structured state management but omitted automatic visual diagrams and cost models. Our work bridges this exact gap by unifying requirement parsing, catalogue-constrained reasoning, diagram generation, cost projection, and security auditing into a unified pipeline.

## Anticipated Examiner Questions
- **Q1: How does your tool compare to AWS Well-Architected Tool in the AWS console?**
  *Answer:* The official AWS tool is a manual, questionnaire-driven audit for already existing or drafted workloads. Our system is generative and proactive: it generates the initial architecture and automatically evaluates it against Well-Architected baseline rules.
- **Q2: Why not just use general ChatGPT or Claude chat interfaces?**
  *Answer:* General conversational LLMs hallucinate non-existent service connections, invent pricing, and produce inconsistent free-text answers. Our pipeline guarantees schema conformance and strictly validates every output against our curated AWS catalogue.
