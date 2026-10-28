# Topic 4: Cost Optimization

**Presentation Section:** Cloud Financial Management & Modeling
**Objective:** Explain how the recommender models infrastructure costs, distinguish architectural estimates from actual AWS billing, and explore architectural cost drivers and operational governance.

---

## Slide 1: Architecture-Driven Cost Modeling

### Key Points
- Cost estimation is integrated directly into the downstream deterministic pipeline (`cost.py`).
- Outputs projected low and high monthly ranges based on standard usage assumptions.
- Calibrated to regional pricing in Asia Pacific (Mumbai) `ap-south-1`.
- Purpose: Early-stage architectural sizing and comparison, not post-deployment financial accounting.

### Speaker Notes
Cost optimization in modern cloud architecture begins at the whiteboard phase, long before infrastructure is provisioned. The AWS Architecture Recommender incorporates a deterministic cost estimator module, `cost.py`, that evaluates recommended services against usage profiles defined in `catalogue/catalogue.yaml`. By generating both a conservative low and high monthly estimate, the tool allows developers to understand the financial implications of architectural choices, such as choosing between serverless components and dedicated multi-tier clusters.

### Questions an Examiner May Ask
**Q1. Why does the recommender produce a low and high cost range rather than a single number?**

Answer: Cloud workloads experience variable demand. A range accommodates fluctuating usage metrics—such as minimal baseline traffic during low hours versus peak load—providing an order-of-magnitude envelope rather than a false illusion of precision.

**Q2. What geographic region is used for the project's pricing calculations?**

Answer: The catalogue and cost calculations are calibrated for the `ap-south-1` (Asia Pacific - Mumbai) region, reflecting local regional pricing and data transfer rates.

---

## Slide 2: Architectural Estimates vs. AWS Billing Reality

### Key Points
- Disclaimer: All generated costs are order-of-magnitude planning estimates, not billing guarantees.
- Baseline mock output on `main`: `$145–$350/month` for the sample e-commerce scenario.
- Actual AWS invoices depend on real-time data transfer, API request volumes, and active resource runtimes.
- AWS Free Tier eligibility varies by account age (12-month free vs. Always Free) and usage history.

### Speaker Notes
It is vital to distinguish architectural estimation from actual AWS billing reality. The numbers produced by the recommender—such as the mock e-commerce baseline estimate of $145 to $350 per month—are planning aids derived from specific sizing assumptions. Real-world AWS bills are driven by metered consumption: outbound internet data transfer, cross-AZ traffic, I/O requests, and operational support tiers. Furthermore, Free Tier allowances depend heavily on account age and prior consumption, meaning developers should never treat architectural estimates as financial guarantees.

### Questions an Examiner May Ask
**Q1. What major cost categories are typically excluded from early-stage architectural estimates?**

Answer: Architectural estimators typically exclude inter-AZ data replication, premium Enterprise/Business support plans, regional taxes, domain registration fees, and edge data transfer exceeding standard baselines.

**Q2. How do 12-Month Free Tier and Always Free Tier differ in AWS?**

Answer: The 12-Month Free Tier grants introductory allowances (such as 750 monthly t2/t3.micro hours) for the first year after account creation. Always Free allowances (such as 1M Lambda requests and 25 GB DynamoDB storage) apply indefinitely to all active accounts.

---

## Slide 3: Major Architectural Cost Drivers in AWS

### Key Points
- NAT Gateways: Single gateway incurs ~$32.85/mo baseline plus data processing fees ($0.045/GB); multi-AZ doubles this.
- Multi-AZ Databases: Synchronous standby instances approximately double relational compute and storage costs.
- Data Transfer Out (DTO): Egress to the public internet is billed per GB; CloudFront edge caching reduces origin egress.
- Managed AI/LLM Inference: Bedrock charges per 1,000 input/output tokens; model selection directly impacts costs.

### Speaker Notes
Architectural decisions frequently introduce hidden cost multipliers that dominate monthly AWS invoices. For example, deploying a NAT Gateway across two private subnets creates a fixed baseline expense of approximately $65 per month before routing any user traffic. Similarly, selecting a Multi-AZ RDS deployment roughly doubles instance and storage costs to achieve automated failover. In AI-assisted pipelines, model selection is a primary cost driver: smaller models (such as Claude Haiku) offer sub-cent inference for routine parsing, whereas frontier models cost significantly more per thousand tokens.

### Questions an Examiner May Ask
**Q1. How does Amazon CloudFront reduce overall infrastructure hosting expenses?**

Answer: CloudFront caches static and semi-dynamic content at edge locations, drastically reducing request volume hitting origin ALB and EC2 servers and substituting higher origin egress fees with lower edge data transfer rates.

**Q2. How does the proposed VPC variant in this project eliminate NAT Gateway expenses?**

Answer: It utilizes Gateway VPC Endpoints for S3 and DynamoDB (which are free) and an Interface Endpoint for Bedrock, allowing private subnet resources to communicate directly over AWS internal networks without an internet-facing NAT Gateway.

---

## Slide 4: Cost Governance & Teardown Discipline

### Key Points
- Proactive Governance: AWS Budgets alert operators before spending exceeds thresholds (e.g., $5.00/mo demo budget).
- Critical distinction: Budget alerts send email/SNS notifications; they do NOT automatically shut down running resources.
- Telemetry Management: Setting CloudWatch log retention (e.g., 7 days) prevents indefinite log storage accumulation.
- Ordered Teardown: Disabling CloudFront, deleting API Gateway/Lambda, emptying S3 buckets, and removing DynamoDB tables prevents orphan charges.

### Speaker Notes
Effective cloud financial management requires operational discipline alongside smart architectural design. In our deployment documentation, we mandate creating an AWS Budget alert with notifications at 80% and 100% of a modest five-dollar threshold before creating resources. Presenters must emphasize that budget alerts are monitoring tools, not spending caps. To prevent unwanted charges following academic demonstrations, we establish an ordered teardown checklist that deletes compute, empties storage, and releases network resources without leaving orphaned cloud assets running.

### Questions an Examiner May Ask
**Q1. What is the difference between an AWS Budget alert and an automated spending cap?**

Answer: An AWS Budget alert only sends a notification when forecasted or actual spend crosses a threshold; it does not stop running resources. An automated cap requires configuring custom Lambda scripts or AWS Service Quotas to actively terminate or shut down workloads.

**Q2. Why must Amazon S3 buckets be emptied before they can be deleted in AWS?**

Answer: Amazon S3 enforces an intentional data-protection safety rule: the AWS API and Console reject bucket deletion requests for non-empty buckets to prevent accidental, irreversible loss of stored objects.
