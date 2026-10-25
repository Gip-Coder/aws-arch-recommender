# Topic 6: Future Scope

**Presentation Section:** Architectural Evolution & Research Directions
**Objective:** Present realistic future enhancements for the AWS Architecture Recommender, analyze their technical challenges and engineering trade-offs, and explicitly distinguish future directions from completed prototype functionality.

---

## Slide 1: Architectural Evolution Roadmap

### Key Points
- Current Foundation: Deterministic validation, Well-Architected auditing, and cost modeling for core web and serverless patterns.
- Strategic Extension Areas: IoT ingestion, Edge computing, Multi-cloud abstraction, and automated Infrastructure as Code (IaC).
- Engineering Reality: Extensions require rigorous schema evolution, expanded allow-lists, and comprehensive validation rules.
- Scope Clarity: All discussed capabilities represent proposed future research directions; none are implemented in the baseline release.

### Speaker Notes
The existing prototype proves the viability of combining constrained language models with deterministic validation gates for core cloud architectures. As enterprise architectures evolve, the recommendation engine can expand into specialized domains. In this section, we examine four high-impact future directions: IoT telemetry pipelines, edge computing, multi-cloud abstraction, and Infrastructure as Code synthesis. We present each area with engineering rigor, evaluating the specific technical trade-offs and validation requirements necessary to implement them safely.

### Questions an Examiner May Ask
**Q1. Are any IoT, multi-cloud, or Infrastructure as Code features currently implemented in the repository?**

Answer: No. All capabilities discussed in this section represent conceptual future scope. The current baseline implementation focuses strictly on curated AWS web, serverless, and batch architectures.

**Q2. What is the primary architectural challenge when expanding the recommender to new domains?**

Answer: Maintaining deterministic validation. Expanding the service catalogue requires defining precise directional connection rules, schema updates, pricing formulas, and Well-Architected checks to prevent invalid service topologies.

---

## Slide 2: IoT Telemetry & High-Throughput Streaming

### Key Points
- Capability: Recommending event-driven ingestion pipelines using AWS IoT Core, Kinesis Data Streams, and Managed Kafka (MSK).
- Problem Solved: Architecting systems capable of ingesting millions of concurrent MQTT/HTTP device events without dropping packets.
- Technical Challenge: Reconciling rapid device ingestion with downstream persistence throttling and backpressure management.
- Implementation Direction: Introduce specialized "streaming" patterns into `catalogue/patterns.yaml` with queue-depth and partition sizing rules.

### Speaker Notes
Extending the recommender to the Internet of Things would enable automated design for connected devices, industrial telemetry, and smart home platforms. IoT workloads present unique architectural challenges because millions of edge devices submit irregular, high-frequency telemetry. The technical trade-off lies in buffering: systems must ingest bursty payloads via AWS IoT Core and Kinesis while protecting downstream analytics databases from being overwhelmed. Future iterations could incorporate partition-key heuristics and sharding calculations into the reasoning engine.

### Questions an Examiner May Ask
**Q1. How would cost estimation differ for IoT architectures compared to standard web architectures?**

Answer: IoT cost estimation is heavily driven by message payload sizing and API connectivity (such as IoT Core message brokers and Kinesis shard-hours), requiring metering models based on messages per second rather than page views or web requests.

**Q2. What architectural component prevents an IoT pipeline from dropping telemetry during sudden traffic surges?**

Answer: Decoupling the ingestion layer with an elastic streaming buffer (such as Amazon Kinesis or Amazon SQS) absorbs incoming spikes and queues data for asynchronous processing by worker compute tiers.

---

## Slide 3: Edge Computing & Low-Latency Workloads

### Key Points
- Capability: Designing edge architectures utilizing CloudFront Functions, Lambda@Edge, and AWS WAF.
- Problem Solved: Minimizing end-user latency by executing authentication, URL rewrites, and header validation at edge PoPs.
- Technical Challenge: Strict execution boundaries (sub-millisecond runtimes, limited memory, and restricted network calls at edge locations).
- Implementation Direction: Add edge-tier security controls to `security.py` verifying that static assets enforce edge caching policies.

### Speaker Notes
Modern digital experiences demand single-digit millisecond latency across global geographic regions. Incorporating edge computing into the recommender would allow the engine to recommend hybrid edge-origin architectures. For example, simple request rewrites and authorization checks can be delegated to lightweight CloudFront Functions, while heavier processing routes to regional compute tiers. The primary engineering challenge is modeling execution limits: edge runtimes impose strict execution timeouts and restricted networking, requiring the validator to enforce appropriate compute placement.

### Questions an Examiner May Ask
**Q1. What is the operational distinction between CloudFront Functions and Lambda@Edge?**

Answer: CloudFront Functions execute sub-millisecond, lightweight JavaScript operations directly at hundreds of edge points of presence with minimal cost. Lambda@Edge runs full Node.js or Python environments with higher compute power and external network access, but incurs higher execution latency and cost.

**Q2. How would the security module evaluate an edge-first architecture?**

Answer: It would check for edge-level perimeter defense—such as ensuring AWS WAF is attached to the CloudFront distribution and that S3 origin buckets enforce Origin Access Control (OAC) to prevent origin bypass.

---

## Slide 4: Multi-Cloud Abstraction & Infrastructure as Code (IaC)

### Key Points
- Multi-Cloud Capability: Mapping requirements across AWS, Microsoft Azure, and Google Cloud Platform equivalents.
- IaC Synthesis: Automatically emitting deployable Terraform (`.tf`) or AWS Cloud Development Kit (CDK) code from validated reports.
- Technical Challenge: Multi-cloud parity is often superficial; IaC generation introduces severe drift and syntax hallucination risks.
- Implementation Direction: Ground IaC emission in pre-tested, parameterized Terraform module templates rather than raw LLM generation.

### Speaker Notes
The ultimate evolution of the architecture recommender encompasses multi-cloud portability and automated deployment generation. Expanding to Azure or Google Cloud would allow organizations to benchmark architectural patterns and estimated costs across cloud providers. Furthermore, translating the final `report.json` into verified Terraform or AWS CDK code would automate the path from architecture design to code delivery. However, we stress that automated IaC generation must rely on pre-validated, modular code templates rather than unconstrained LLM output to guarantee that generated infrastructure remains secure, syntactically correct, and free from security misconfigurations.

### Questions an Examiner May Ask
**Q1. Why is generating raw Infrastructure as Code directly from an unconstrained LLM risky?**

Answer: Unconstrained LLMs frequently hallucinate invalid resource arguments, omit vital security parameters (such as encryption flags or least-privilege egress rules), and produce non-compilable HCL syntax that fails during automated CI/CD execution.

**Q2. How could the recommender's deterministic pipeline ensure generated Terraform code is safe?**

Answer: By passing the synthesized architecture through a deterministic template engine that populates vetted, pre-audited Terraform modules, followed by automated static analysis using tools like `tfsec` or `checkov` prior to delivery.
