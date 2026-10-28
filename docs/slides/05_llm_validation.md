# Slide 5: LLM Validation, Prompt Injection Defense & Error Repair

## Slide Title
**Reliability & Security Guardrails: Untrusted Input to Verified Output**

## Key Bullet Points
- **Catalogue Allow-List Enforcement**: Services restricted to a curated allow-list in `catalogue/catalogue.yaml`; hallucinated services are rejected before output generation.
- **Prompt Injection Neutralization**: User requirement text is wrapped in `<user_requirement>` delimiters and classified as untrusted data, preventing instruction overrides.
- **Automated Schema Repair**: Automatic 2-step repair-and-retry loop passes the exact JSON Schema validator error back to the LLM to self-correct malformed outputs.
- **Connection Graph Validation**: Deterministic checks verify that all service-to-service links match `allowed_targets` and flag any orphaned components.

## Speaker Notes
In production AI engineering, treating LLM output as authoritative without rigorous checks is unacceptable. We designed a multi-layer defense system. First, all user requirement text is isolated within strict XML-style delimiters and explicitly branded as untrusted data in the system prompt, successfully neutralizing prompt injection attempts like "ignore previous instructions". Second, our reasoning engine is bound to a strict service allow-list and pattern catalogue. If an LLM attempts to hallucinate a non-existent AWS service or connect an ALB directly to S3 without CloudFront, our deterministic validator intercepts and blocks the malformed structure. Finally, schema failures trigger automated repair prompts containing the specific error trace.

## Anticipated Examiner Questions
- **Q1: How do you prevent adversarial prompts from hijacking your system prompt?**
  *Answer:* We decouple the system prompt instructions from user input by encapsulating user text in `<user_requirement>` tags and using a system prompt that explicitly tells the model to treat content within tags strictly as descriptive data, never executable instructions.
- **Q2: What happens if an LLM invents an invalid AWS connection?**
  *Answer:* The deterministic `validator.py` evaluates all edges in `architecture['connections']` against the directed graph rules defined in `catalogue.yaml`. Disallowed connections trigger immediate validation failure.
