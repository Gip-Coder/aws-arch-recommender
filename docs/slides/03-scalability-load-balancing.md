# Topic 3: Scalability, Load Balancing, and Auto Scaling

**Presentation Section:** Systems Architecture & Elasticity
**Objective:** Contrast cloud scalability and elasticity patterns, and compare the multi-tier compute model of the sample e-commerce architecture with the event-driven serverless design of the recommender's proposed deployment.

---

## Slide 1: Scalability vs. Elasticity in Cloud Computing

### Key Points
- Scalability: The system's ability to handle increasing workload by adding resources (vertical or horizontal).
- Elasticity: The system's ability to dynamically acquire and release resources in real-time matching demand.
- Horizontal scaling (Scale Out/In) provides higher resilience and cost efficiency than vertical scaling (Scale Up/Down).
- Decoupling tiers prevents localized bottlenecks from degrading overall application performance.

### Speaker Notes
While scalability and elasticity are often used interchangeably, they represent distinct architectural capabilities in AWS. Scalability is the capacity to grow gracefully when load increases, whereas elasticity is the automated, dynamic matching of provisioned capacity to real-time workload fluctuations. Horizontal scaling—adding or removing small identical instances or containers—is preferred over vertical scaling because it avoids single points of failure and eliminates downtime during capacity adjustments.

### Questions an Examiner May Ask
**Q1. Why is horizontal scaling generally preferred over vertical scaling in high-availability systems?**

Answer: Vertical scaling requires resizing or restarting a single virtual server, introducing downtime and reaching hard hardware ceilings. Horizontal scaling adds identical instances across multiple physical locations without interruption, offering virtually unbounded elasticity.

**Q2. How does decoupling state from application logic enable horizontal elasticity?**

Answer: When application instances remain stateless, any instance can process any user request. Session state and persistent data are offloaded to external caches or databases, allowing instances to terminate dynamically during scale-in without dropping active sessions.

---

## Slide 2: Sample E-Commerce Workload (Multi-Tier Elasticity)

### Key Points
- Ingress: Amazon CloudFront absorbs static content demand and terminates client TLS at edge locations.
- Distribution: Application Load Balancer (ALB) balances HTTP/HTTPS traffic across target instance groups.
- Compute Elasticity: EC2 Auto Scaling Group dynamically provisions instances across `ap-south-1a` and `ap-south-1b`.
- Data Tier: Amazon RDS Multi-AZ ensures database durability with automated synchronous failover.

### Speaker Notes
The sample e-commerce architecture demonstrates classic multi-tier elasticity tailored for steady-but-growing commercial web applications. Traffic first encounters Amazon CloudFront edge nodes, which offload static asset requests before traffic reaches the core network. The Application Load Balancer operates at Layer 7, performing health checks and distributing dynamic traffic across EC2 instances managed by an Auto Scaling Group. Spanning instances across two Availability Zones ensures that capacity scales in response to CPU or request metrics while surviving the loss of an entire facility.

### Questions an Examiner May Ask
**Q1. What role do target health checks play in Application Load Balancer routing?**

Answer: The ALB continuously monitors backend targets via HTTP/HTTPS health checks. If an application instance fails successive checks, the ALB immediately stops routing requests to it, while the Auto Scaling Group initiates a replacement instance.

**Q2. How does EC2 Auto Scaling balance instances across multiple Availability Zones?**

Answer: The Auto Scaling Group is configured with multiple subnets across distinct AZs. During scale-out, it distributes new instances evenly across the configured zones; during scale-in, it terminates instances from the zone with the most servers to maintain architectural balance.

---

## Slide 3: Proposed Recommender Deployment (Serverless Scaling)

### Key Points
- Edge Tier: Amazon CloudFront delivers static single-page application (SPA) assets directly from Amazon S3.
- API Routing: Amazon API Gateway HTTP API routes payload submissions with built-in concurrency scaling.
- Event-Driven Compute: AWS Lambda scales automatically per request (up to account concurrency limits).
- Zero Idle Cost: Serverless compute scales to zero during inactivity, incurring zero compute charges when idle.

### Speaker Notes
In contrast to traditional instance-based scaling, our proposed recommender hosting architecture leverages an event-driven serverless model. The frontend is hosted statically on S3 and distributed via CloudFront, eliminating web server provisioning entirely. API Gateway and AWS Lambda scale concurrently and autonomously with incoming request volume: if ten requests arrive simultaneously, AWS initializes ten isolated execution environments. When no requests are active, the compute tier scales to absolute zero, eliminating idle running costs.

### Questions an Examiner May Ask
**Q1. What is a "cold start" in AWS Lambda, and how does it relate to serverless scaling?**

Answer: A cold start occurs when Lambda must initialize a new micro-VM container environment and load the application runtime before executing the handler code. Subsequent requests routed to an existing warm container execute with near-zero initialization latency.

**Q2. What mechanism protects downstream services from being overwhelmed by rapid serverless scaling?**

Answer: AWS Lambda supports Reserved Concurrency and Provisioned Concurrency, which establish upper boundaries on simultaneous executions to prevent downstream databases or APIs from being overwhelmed by unexpected traffic spikes.

---

## Slide 4: Architectural Comparison: Multi-Tier vs. Serverless

### Key Points
- Workload Profile: EC2 Auto Scaling is optimal for long-running, steady traffic; Lambda is optimal for spiky, event-driven traffic.
- Operational Overhead: EC2 requires OS patching, AMI maintenance, and scaling policies; Lambda offloads infrastructure management to AWS.
- Minimum Cost Baseline: EC2 clusters incur ongoing 24/7 baseline instance charges; Lambda bills purely per millisecond of execution.
- Scope Clarity: The recommender uses serverless hosting, but can recommend multi-tier architectures for appropriate customer workloads.

### Speaker Notes
Comparing these two architectures illustrates that cloud design has no universal one-size-fits-all solution; scaling patterns must mirror the specific workload profile. The sample e-commerce application utilizes EC2 Auto Scaling and Multi-AZ RDS because persistent relational workloads with consistent traffic profiles benefit from dedicated compute instances and steady throughput. Conversely, the recommender system itself experiences bursty, on-demand usage, making a serverless API Gateway and Lambda architecture vastly more cost-effective and operationally streamlined.

### Questions an Examiner May Ask
**Q1. Does the AWS Architecture Recommender application run on EC2 Auto Scaling?**

Answer: No. The recommender application's proposed deployment uses serverless components (CloudFront, S3, API Gateway, and Lambda). EC2 Auto Scaling is an architecture pattern that the tool recommends for appropriate customer workloads, such as steady e-commerce sites.

**Q2. When would a team choose EC2 Auto Scaling over AWS Lambda for an application tier?**

Answer: Teams choose EC2 when applications require specialized OS kernels, long-running processes exceeding Lambda's 15-minute execution limit, persistent TCP socket connections, or predictable high-volume traffic where dedicated instances offer a lower cost per transaction.
