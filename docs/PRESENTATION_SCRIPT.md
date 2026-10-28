# Complete Presentation Script: AI-Driven AWS Cloud Architecture Recommender

**Project Title:** AI-Driven AWS Cloud Architecture Design & Recommendation System  
**Course:** Cloud Architecture Design (VIT)  
**Guide:** Dr. Sunija A P  
**Speakers:** 
- **Person A (AI Core & Pipeline Lead):** Sudipta Majumder (24BCE2882)
- **Person B (Downstream Analysis, Infra & UI Lead):** P. Giphy Bershan (24BCE2201)

---

## 1. Title & Team Introduction (Shared / Person A starts)

**[Slide: Title Slide]**

**Person A (Sudipta):**
> "Good morning respected faculty, external examiners, and dear peers. Today, Giphy and I are proud to present our Cloud Architecture Design project: **'AI-Driven AWS Cloud Architecture Design & Recommendation System'**. 
>
> In modern cloud engineering, translating high-level business requirements into an optimal, cost-effective, and secure AWS architecture is a complex, error-prone task. Our project introduces a hybrid decision-support system that takes open-ended plain English requirements and automatically produces a validated AWS architecture specification, a visual architecture diagram, an approximate monthly cost model, and a Well-Architected security review—all without executing dangerous automated deployments."

**Person B (Giphy):**
> "Throughout this project, we maintained a strict engineering division: Sudipta led the AI Core—focusing on requirement extraction via LLMs, catalogue-grounded reasoning engines, JSON schema contracts, prompt injection defenses, and the quantitative evaluation harness. 
>
> I led the downstream analysis and interface layer—focusing on deterministic diagram rendering with AWS iconography, the Well-Architected security audit engine, cloud pricing models, serverless deployment architectures, and the interactive Streamlit user interface. Let us now dive into the real-world problem statement."

---

## 2. Problem Statement & Motivation (Person A)

**[Slide: Problem Statement & Motivation]**

**Person A (Sudipta):**
> "AWS offers over 200 distinct services across compute, storage, databases, networking, and analytics. For any non-trivial application, multiple valid architectural paths exist. For example, a web platform could be built using EC2 Auto Scaling behind an Application Load Balancer, or containerized on ECS Fargate, or completely serverless using API Gateway, Lambda, and DynamoDB.
>
> Junior engineers and students routinely face a severe cognitive burden:
> 1. They struggle to balance competing trade-offs—for example, choosing Multi-AZ RDS boosts availability from 99.9% to 99.95%, but instantly doubles the monthly database bill.
> 2. They default to familiar monolithic patterns (like spinning up EC2 and RDS for idle, low-traffic workloads where serverless would cost pennies).
> 3. They frequently leave critical security misconfigurations in place, such as publicly open S3 buckets, overly permissive `*:*` IAM policies, or unencrypted data volumes.
>
> While generative AI assistants exist today, asking a generic LLM like ChatGPT to design an architecture leads to severe hallucinations: it invents non-existent service names, hallucinates prices, and draws invalid network connections. Our project solves this through a strictly bounded, schema-validated hybrid architecture."

---

## 3. Existing Systems, Limitations & Research Gap (Person A)

**[Slide: Literature Survey & State of the Art]**

**Person A (Sudipta):**
> "During our literature survey, we analyzed current commercial, vendor, and academic tools:
> - **Vendor Assistants (Amazon Q Developer, AWS Kiro):** Excellent for generating Infrastructure-as-Code (CloudFormation/CDK) once the design is decided, but they do not provide an end-to-end multi-attribute recommendation report comparing cost and security from an open-ended specification.
> - **Commercial AI Diagram Tools (Cloudairy, Eraser.io, Miro):** Great at drawing official AWS icons, but they are drawing tools, not architects—the human user must already know exactly which services and connections to draw.
> - **Academic Prototypes (CloudArchitectBuddy, ACSE-Eval):** Pioneered structured state management and threat modeling, but lacked automatic visual diagramming and end-to-end pricing synthesis.
>
> **The Identified Gap:** No single publicly accessible system integrates natural language requirement parsing, AWS-specific service recommendation from a verified catalogue, deterministic diagramming, cost modeling, and Well-Architected security checking in one explainable, student-scale pipeline. That is the contribution of this project."

---

## 4. Proposed Pipeline & Architecture (Person A & Person B Hand-off)

**[Slide: Proposed Pipeline Architecture]**

**Person A (Sudipta):**
> "Let us look at our pipeline flow. Our core design philosophy is: **'LLM for language; plain code for math, security, and rendering.'**
>
> 1. **Step 1 (Requirement Parser):** The user enters free-form requirements (e.g. *'Highly available e-commerce platform for ~100k users with steady traffic'*). An LLM running via Amazon Bedrock extracts structured technical attributes and outputs a validated `Requirement JSON`.
> 2. **Step 2 (Architecture Reasoner):** A second Bedrock LLM call takes the `Requirement JSON` and maps it strictly to our curated AWS service catalogue and named reference patterns (like `three_tier_web`, `serverless_rest_api`, `static_site_cdn`, or `batch_pipeline`). It outputs an `Architecture JSON`.
> 3. **Step 3 (Deterministic Validation):** Before any downstream report is generated, our rule-based validator inspects the architecture against our `catalogue.yaml` allow-list. If the LLM hallucinates a service or creates an invalid connection, it is blocked immediately.
>
> Once the architecture is verified as mathematically valid, the LLM's job is completely finished, and it hands off the validated JSON to Person B's downstream engines."

**Person B (Giphy):**
> "Thank you, Sudipta. Once the validated Architecture JSON is produced, my downstream engines take over in parallel without invoking any further LLM calls:
> 4. **Step 4A (Diagram Generator):** Feeds the services and connections into the Python `diagrams` library, clustering services by category (Network, Compute, Database, Storage) with official AWS iconography, with an automated fallback to Graphviz DOT.
> 5. **Step 4B (Cost Estimator):** Computes monthly low and high cost ranges based on regional unit prices (`ap-south-1`) and usage volume assumptions.
> 6. **Step 4C (Security & Best-Practice Review):** Evaluates the design against 15 deterministic rules mapped to the AWS Well-Architected Framework pillars.
> 7. **Step 5 (Final Report & UI):** The outputs are aggregated into `report.json` and rendered in real-time on our Streamlit web interface."

---

## 5. Security Guardrails, Prompt Defense & Error Repair (Person A)

**[Slide: Reliability, LLM Validation & Prompt Injection Defense]**

**Person A (Sudipta):**
> "In AI engineering, treating LLM output as trustworthy without verification is dangerous. We built three core layers of reliability:
> 1. **Prompt Injection Defense:** Malicious users often attempt prompt overrides (e.g. *'Ignore previous instructions and output something else'*). In `parser.py`, all user text is strictly encapsulated inside `<user_requirement>` XML tags and declared in the system prompt as untrusted input data, never system instructions.
> 2. **Catalogue & Directed Graph Allow-Lists:** In `reasoner.py`, the LLM is explicitly constrained to 17 curated AWS services in `catalogue.yaml`. Every connection is checked against source-target adjacency lists. An Application Load Balancer is allowed to connect to EC2 or ECS, but if the LLM attempts to connect an ALB directly to an RDS database or S3, our validator blocks it.
> 3. **Automated Schema Repair Loop:** If an LLM response suffers from syntax corruption or missing fields, our code captures the exact `jsonschema` validation error and injects it into a repair-and-retry prompt (up to 2 retries), allowing the model to self-heal without crashing."

---

## 6. Experimental Evaluation & Benchmark Metrics (Person A)

**[Slide: Experimental Evaluation & Results]**

**Person A (Sudipta):**
> "To measure our system's accuracy scientifically, we built an automated evaluation harness in `eval/run_eval.py`. Using official AWS Architecture Center reference blueprints as ground truth, we evaluated test scenarios across four quantitative metrics:
>
> 1. **Service Selection Accuracy (Recall):** Measures what percentage of essential AWS services the system correctly identified. We achieved **100.0%** across standard reference scenarios.
> 2. **Service Precision:** Measures whether the model avoided over-recommending superfluous services. We achieved **100.0%** precision, demonstrating that the catalogue-constrained prompts prevent architecture bloat.
> 3. **Pattern Match Rate:** Evaluates whether the system selected the right architectural archetype (`three_tier_web`, `serverless_rest_api`, `static_site_cdn`). We achieved **100.0%** pattern classification.
> 4. **Architecture Validity Rate:** Evaluates whether generated graphs have zero orphans, valid schema conformance, and valid connection edges. 100% of tested architectures passed without manual intervention.
>
> Now, Giphy will walk you through the downstream modules, our deployment stack, and a live demonstration."

---

## 7. Downstream Modules: Diagrams, Security & Pricing (Person B)

**[Slide: Deterministic Engines — Diagram, Security & Pricing]**

**Person B (Giphy):**
> "Let us look at how the downstream deterministic modules operate:
>
> 1. **Visual Diagram Engine (`diagram.py`):** We use `diagrams.aws` to render production-grade architecture diagrams. Rather than asking an LLM to guess coordinates, our Python code parses the JSON graph, creates visual clusters for tiers (e.g., VPC, Public Subnet, Private Data Subnet), maps official AWS icons (CloudFront, ALB, EC2, RDS, DynamoDB), and renders high-resolution PNGs. If Graphviz is not installed locally, it gracefully degrades to generating Graphviz `.dot` files without crashing.
> 2. **Well-Architected Security Engine (`security.py`):** We expanded our rule engine to audit 15 deterministic checks across the 5 Well-Architected pillars:
>    - *Security:* Flagging public S3 buckets, missing TLS encryption in transit, missing SSE encryption at rest, and enforcing scoped IAM roles.
>    - *Reliability:* Flagging single-AZ databases when high availability is requested, and checking for health-checked load balancers.
>    - *Cost Optimization:* Warning if an over-provisioned Multi-AZ EC2 stack is requested for a student project with a 'minimise' budget.
> 3. **Order-of-Magnitude Cost Estimator (`cost.py`):** Rather than hallucinating arbitrary prices, our estimator maps services to explicit usage assumptions (e.g., 730 instance hours, 10M API calls, 100 GB storage in `ap-south-1`), providing an auditable low-to-high monthly range."

---

## 8. System Deployment Architecture & Cost Control (Person B)

**[Slide: System Deployment Architecture & AWS Free Tier]**

**Person B (Giphy):**
> "It is essential to distinguish between the architecture our system *recommends* to users, and the cloud architecture on which our recommender *itself runs*.
>
> For our own system's deployment:
> - **Frontend:** A single-page application hosted on Amazon S3 and distributed via Amazon CloudFront using Origin Access Control (OAC) with enforced HTTPS.
> - **API & Compute:** Amazon API Gateway HTTP API routing requests to serverless AWS Lambda functions. We specifically chose HTTP API over REST API because it is 70% cheaper ($1.00 vs $3.50 per million requests).
> - **AI Layer:** Amazon Bedrock managed API invoking Claude 3 Haiku or Claude 3.5 Sonnet—eliminating the need to run expensive 24/7 EC2 GPU instances ($700+/month).
> - **Persistence:** Amazon DynamoDB on-demand for session history, and CloudWatch for operational logging.
>
> **Cost Discipline:** At a student demo volume of 500 pipeline executions per month, AWS hosting sits comfortably at **$0 (100% inside the AWS Free Tier)**. The only cost is Bedrock LLM tokens, which total roughly **$5 to $16 per month**, keeping our budget completely safe."

---

## 9. Interactive Prototype & Live Demo (Person B)

**[Slide: Live System Walkthrough & Streamlit UI]**

**Person B (Giphy):**
> *(Demonstrating screen or CLI / Streamlit)*
> "Here is our working prototype in action:
> 1. In **Streamlit (`app/streamlit_app.py`)**, the user is greeted with a clean interface featuring a prompt input, a 'Demo Mode' toggle, and scenario selection sidebar.
> 2. When we select our **'Serverless Mobile REST API'** scenario and click **Generate**:
>    - You see the recommended services: Cognito, API Gateway, Lambda, and DynamoDB, along with a human-readable one-sentence engineering rationale for each choice.
>    - The **Diagram tab** displays the visual architecture showing API Gateway routing requests to Lambda and writing to DynamoDB.
>    - The **Cost tab** displays the breakdown: ~$2 to $70/month with transparent usage assumptions.
>    - The **Security tab** audits the design against the Well-Architected Framework, showing passed checks and actionable recommendations.
> 3. To guarantee presentation safety in case of network or AWS outages, our `--scenario` and `--mock` flags allow the entire system to run 100% offline from validated cache."

---

## 10. Research Novelty, Prior Art & Future Roadmap (Person A)

**[Slide: Innovation, Patents & Future Scope]**

**Person A (Sudipta):**
> "To conclude, let us address academic novelty and prior art honestly:
> - During our patent search, we identified **US Patent 12,463,867 B1** (*'Agentically-orchestrated foundational models for cloud architecture development'*), which claims using a plurality of LLM agent roles to design cloud systems. 
> - Because multi-agent generation is already patented, we deliberately chose not to frame our novelty around 'using multiple LLM agents'. Instead, our true academic novelty is **robust system integration**:
>   1. A hybrid pipeline coupling probabilistic LLMs to deterministic downstream graph validators and cost engines.
>   2. Bounding generation to a strict, curated catalogue to eliminate hallucinations.
>   3. Educational explainability—providing explicit trade-off rationales rather than treating AI as a black box.
> - **Future Roadmap:** Extending the catalogue to support multi-cloud targets (GCP/Azure), automated Infrastructure-as-Code export (generating Terraform and AWS CDK), and multi-region disaster recovery topologies."

**Person B (Giphy):**
> "Our codebase is fully modular, covered by 21 automated unit tests, strictly version-controlled, and recommendation-only for safety. 
>
> Thank you Dr. Sunija and respected examiners for your time and guidance. Sudipta and I are now eager and ready to take your questions."

---

## 11. Examiner Q&A Cheat Sheet (Prepared Answers)

### Questions Directed to Person A (Sudipta - AI Core, Prompts, Evaluation):
- **Examiner: "Why did you use two separate LLM steps instead of one single prompt that outputs the whole architecture?"**
  - *Sudipta:* "Single-prompt generation suffers from task overload. If an LLM tries to parse free text, understand traffic patterns, pick services, wire connections, and write rationales all at once, the probability of hallucination spikes. By splitting the task into a Requirement Parser (Stage 1) and an Architecture Reasoner (Stage 2), each model has a single, well-defined cognitive responsibility bounded by a schema."
- **Examiner: "How do you protect your pipeline against malicious prompt injection?"**
  - *Sudipta:* "We treat all user input as untrusted data by encapsulating it within `<user_requirement>` delimiters. The system prompt contains explicit guardrail instructions specifying that anything inside those delimiters must be parsed strictly as descriptive text, never as instructions. In `tests/test_prompts.py`, we explicitly test injection strings like *'ignore previous instructions'*, proving the system remains uncompromised."
- **Examiner: "How did you compute your evaluation metrics?"**
  - *Sudipta:* "We tested the pipeline against reference architectures derived from official AWS Whitepapers. We compute Service Selection Accuracy (Recall) as $|Recommended \cap Expected| / |Expected|$ and Service Precision as $|Recommended \cap Expected| / |Recommended|$. We also measure pattern match rate and graph validity rate using our deterministic validator."

### Questions Directed to Person B (Giphy - Downstream, Diagrams, Security, Cost):
- **Examiner: "Why didn't you let the LLM generate the diagram code directly?"**
  - *Giphy:* "Research papers such as DiagramAI (KES 2025) demonstrate that when LLMs directly output diagrams in Mermaid or SVG, they suffer from high syntax failure rates, distorted layouts, and inaccurate icon usage. By constraining the LLM to output structured JSON and using the Python `diagrams` library, our diagram rendering is 100% deterministic, repeatable, and uses official AWS iconography."
- **Examiner: "Why is your system strictly recommendation-only? Why not automatically provision the infrastructure?"**
  - *Giphy:* "Autonomous deployment introduces severe financial and operational hazards. An LLM mistake could deploy an unauthenticated public database or expensive multi-node GPU clusters costing thousands of dollars. Cloud governance mandates human-in-the-loop validation before real cloud infrastructure is provisioned."
- **Examiner: "How accurate is your cost estimation?"**
  - *Giphy:* "Our cost estimator is deliberately labelled as an order-of-magnitude estimate. It does not attempt to predict exact cents because real cloud bills fluctuate with dynamic egress traffic. Instead, it computes low and high bounds from transparent, documented baseline usage assumptions (e.g. 730 hours, 100k requests) in the `ap-south-1` region."
