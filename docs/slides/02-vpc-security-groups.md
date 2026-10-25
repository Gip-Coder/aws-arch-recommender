# Topic 2: VPC and Security Groups

**Presentation Section:** Network Isolation & Perimeter Security
**Objective:** Explain how Amazon Virtual Private Cloud (VPC), subnet tiering, and security groups establish network boundaries in the sample e-commerce architecture and in the proposed recommender deployment variant.

---

## Slide 1: Network Isolation via Amazon Virtual Private Cloud (VPC)

### Key Points
- An Amazon VPC provides a logically isolated virtual network dedicated to an AWS account.
- Subnets partition the VPC IP CIDR block across multiple physical Availability Zones (AZs).
- Public subnets route outbound internet traffic through an Internet Gateway (IGW).
- Private subnets have no direct route to the Internet Gateway, protecting backend compute and data stores.

### Speaker Notes
Amazon VPC is the cornerstone of network security in AWS, allowing cloud architects to define a private network topology mirroring traditional on-premises data centers. By carving a private CIDR block into subnets across distinct Availability Zones, we ensure that workloads benefit from physical infrastructure redundancy. Public subnets are reserved strictly for ingress traffic routing components, such as load balancers, while sensitive application servers and databases reside in private subnets with no direct internet addressability.

### Questions an Examiner May Ask
**Q1. What technically distinguishes a public subnet from a private subnet in a VPC?**

Answer: A public subnet has a route table entry directing default traffic (`0.0.0.0/0`) to an Internet Gateway (IGW), and instances within it can receive public IPv4 addresses. A private subnet does not route directly to an IGW.

**Q2. Why should subnets span multiple Availability Zones?**

Answer: Deploying subnets across multiple Availability Zones provides high availability and fault isolation; if a single physical data center facility experiences an outage, workloads in adjacent AZs continue operating uninterrupted.

---

## Slide 2: Stateful Security Groups & Defense-in-Depth

### Key Points
- Security groups operate as stateful virtual firewalls at the Elastic Network Interface (ENI) level.
- Stateful behavior: Return traffic is automatically allowed regardless of inbound rules.
- Defense-in-depth: Security groups evaluate rules at the host boundary, independent of network ACLs.
- Rule chaining: Security groups reference other security groups by ID rather than static IP CIDRs.

### Speaker Notes
Security groups enforce granular access control for compute instances, containers, and database endpoints. Unlike stateless network ACLs, security groups track connection state: if an inbound request is permitted on a port, the corresponding response is automatically allowed outbound without requiring an explicit rule. A vital security best practice is security group chaining, where an application tier allows traffic only from the Application Load Balancer's security group ID. This eliminates brittle, hard-coded IP rules and guarantees that backend nodes accept requests only through the authorized ingress gateway.

### Questions an Examiner May Ask
**Q1. How does security group statefulness simplify firewall rule administration?**

Answer: Because security groups track active TCP/UDP sessions, return packets for an established inbound connection are permitted automatically, removing the need to configure complex ephemeral outbound port ranges.

**Q2. What is the security advantage of referencing another Security Group ID in an ingress rule?**

Answer: Referencing a Security Group ID ensures that only resources possessing that specific security group can connect, dynamically accommodating autoscaling instances regardless of their individual private IP addresses.

---

## Slide 3: Database Isolation & Multi-AZ Ingress Controls

### Key Points
- Sample e-commerce architecture (`three_tier_web`): Amazon RDS Multi-AZ placed in private database subnets.
- Database security group strictly blocks public ingress (`0.0.0.0/0` denied).
- Ingress allowed exclusively on database port (e.g., MySQL 3306) from the Application Security Group.
- Synchronous Multi-AZ storage replication operates across private AZ subnets without public exposure.

### Speaker Notes
In the recommender's reference e-commerce architecture, database security is modeled around total network isolation. The Amazon RDS MySQL Multi-AZ cluster resides across private database subnets spanning `ap-south-1a` and `ap-south-1b`. The database security group enforces a zero-trust perimeter: it rejects all direct internet traffic and permits ingress solely on port 3306 from instances belonging to the application tier security group. The synchronous block-level replication between primary and standby database instances is handled over AWS private infrastructure, ensuring that high availability does not compromise network privacy.

### Questions an Examiner May Ask
**Q1. Why should relational databases never reside in public subnets, even if protected by passwords?**

Answer: Placing databases in public subnets exposes their network interfaces to internet-wide port scans, brute-force attacks, and potential zero-day vulnerabilities. True defense-in-depth requires isolating them in private subnets with no public IP routing.

**Q2. Does the standby instance in Amazon RDS Multi-AZ accept direct application read queries?**

Answer: No. In standard RDS Multi-AZ deployments, the standby replica serves purely as a synchronous failover target and does not accept read or write traffic. Application queries must target the primary database endpoint.

---

## Slide 4: Cost-Optimized VPC Endpoints (No-NAT Variant)

### Key Points
- Traditional private subnets require a NAT Gateway (~$32.85/mo per AZ) for outbound AWS API calls.
- Proposed enterprise variant: AWS Lambda attached to private subnets without a NAT Gateway.
- Gateway VPC Endpoints: Direct, free route-table access to Amazon S3 and Amazon DynamoDB.
- Interface VPC Endpoints (AWS PrivateLink): Private ENIs for Amazon Bedrock, billed per AZ-hour (~$7.20/mo).

### Speaker Notes
In our proposed enterprise deployment guide, we document an optional VPC architectural variant designed for high security and cost efficiency. Typically, Lambda functions in private subnets require NAT Gateways to reach AWS service endpoints over the internet, incurring significant baseline hourly costs. By utilizing Gateway VPC Endpoints for S3 and DynamoDB, traffic routes over the private AWS network at zero cost. For services requiring PrivateLink, such as Amazon Bedrock, Interface Endpoints establish secure private connections, eliminating the need for an expensive public-facing NAT Gateway.

### Questions an Examiner May Ask
**Q1. What is the operational and financial difference between a Gateway Endpoint and an Interface Endpoint?**

Answer: Gateway Endpoints are free route-table targets supported exclusively for S3 and DynamoDB. Interface Endpoints use AWS PrivateLink to provision Elastic Network Interfaces (ENIs) inside subnets, supporting many AWS services but incurring hourly and data-processing charges.

**Q2. Does the baseline demonstration recommender currently run inside a VPC?**

Answer: No. The baseline prototype executes locally in mock mode, and the primary serverless deployment runs Lambda outside a VPC. The no-NAT VPC design is an architectural variant documented in `docs/DEPLOYMENT.md` for enterprise perimeters.
