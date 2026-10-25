# AWS Architecture Recommender — Presentation Slide Content

This directory contains presentation-ready slide outlines, speaker notes, and technical examiner defense questions for the **AWS Architecture Recommender** academic project.

---

## 1. Project Presentation Overview

The presentation explains the architecture, security governance, scalability models, cost estimation mechanics, and operational prototype of the AWS Architecture Recommender. The content is structured into six focused topic decks formatted for direct translation into presentation slides.

Each section adheres to a consistent structure:
- **Slide Title & Key Points:** 3 to 5 concise, presentation-ready bullet points.
- **Speaker Notes:** 3 to 5 comprehensive sentences expanding on the architectural rationale and technical depth.
- **Questions an Examiner May Ask:** 2 to 4 rigorous technical questions with concise, technically sound answers grounded in AWS best practices and repository reality.

---

## 2. Presentation Sections

The presentation content is divided into six sequential modules:

1. [**Topic 1: IAM and Least Privilege**](01-iam-least-privilege.md)
   *Covers AWS IAM fundamentals, least-privilege execution roles for serverless compute, credential safety, and permission scoping for optional cloud integrations.*

2. [**Topic 2: VPC and Security Groups**](02-vpc-security-groups.md)
   *Covers network isolation, public vs. private subnets, stateful security group firewalls, database perimeter protection, and cost-optimized VPC endpoints.*

3. [**Topic 3: Scalability, Load Balancing, and Auto Scaling**](03-scalability-load-balancing.md)
   *Covers cloud scalability vs. elasticity, multi-tier EC2 Auto Scaling across Availability Zones, serverless scaling with API Gateway/Lambda, and a direct architectural comparison.*

4. [**Topic 4: Cost Optimization**](04-cost-optimization.md)
   *Covers architecture-driven cost modeling in Mumbai (`ap-south-1`), architectural estimates vs. billing reality, major cost drivers (NAT Gateways, Multi-AZ, egress), and budget governance.*

5. [**Topic 5: Prototype and Demo Walkthrough**](05-prototype-demo-walkthrough.md)
   *Covers project problem statement, pipeline ingestion/validation/synthesis stages, verified offline mock execution (`python run.py --mock`), and feature branch deliverables.*

6. [**Topic 6: Future Scope**](06-future-scope.md)
   *Covers architectural evolution into IoT telemetry streaming, edge computing with CloudFront Functions, multi-cloud abstraction, and automated Infrastructure as Code (Terraform/CDK) synthesis.*

---

## 3. Suggested Presentation Narrative Flow

The six topics are designed to follow a logical academic defense narrative:
1. **Foundation & Perimeter (Topics 1 & 2):** Begin with fundamental cloud governance—how identity (IAM) and network isolation (VPC & Security Groups) establish a zero-trust perimeter.
2. **Workload Behavior & Economics (Topics 3 & 4):** Transition into operational realities—contrasting multi-tier instance scaling with serverless concurrency, followed by transparent cloud financial modeling and cost drivers.
3. **Working Prototype Demonstration (Topic 5):** Walk through the implemented system—explaining the hybrid AI/deterministic pipeline, showing the verified offline mock execution workflow, and inspecting the generated architecture, diagrams, cost ranges, and Well-Architected review.
4. **Strategic Evolution (Topic 6):** Conclude with future engineering directions—evaluating IoT, edge computing, and Infrastructure as Code synthesis with an objective analysis of technical trade-offs.

---

## 4. Source and Accuracy Notes

- **Baseline Fidelity:** The prototype walkthrough and pipeline descriptions reflect the verified implementation on the repository's `main` branch.
- **Distinguishing Implemented vs. Proposed Infrastructure:** Implemented capabilities (such as deterministic validation, offline mock execution, rule-based security, and Graphviz generation) are explicitly distinguished from proposed deployment architectures (such as the S3/CloudFront OAC and API Gateway hosting design documented in `docs/DEPLOYMENT.md`).
- **Feature Branch Clarity:** Advanced user interfaces (Streamlit UI on branch `b/ui`) and serverless deployment handlers (`deploy/` on branch `b/deploy-guide`) represent modular feature branch deliverables in the project roadmap.
- **Future Scope Boundaries:** All topics in Section 6 represent conceptual extensions; no IoT, edge, multi-cloud, or IaC generation code is present in the current baseline release.
- **Cost Disclaimer:** All presented cost figures represent order-of-magnitude planning envelopes derived from sizing assumptions in `ap-south-1`; they are not guarantees of actual AWS invoices.
