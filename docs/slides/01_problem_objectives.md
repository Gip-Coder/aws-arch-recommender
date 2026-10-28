# Slide 1: Problem Statement, Objectives & Motivation

## Slide Title
**AI-Assisted AWS Cloud Architecture Recommendation System**

## Key Bullet Points
- **Cognitive Complexity**: Designing optimal AWS architectures requires balancing hundreds of services, traffic elasticity, availability tiers, and budget limits simultaneously.
- **Novice Pitfalls**: Inexperienced developers and students frequently over-provision compute (e.g. EC2 for idle workloads), choose wrong storage paradigms, or leave critical security holes.
- **Project Objective**: Build an AI-assisted decision-support pipeline translating natural language requirements into structured, explainable AWS recommendations.
- **Recommendation-Only Boundary**: Non-deployment posture guarantees zero unattended AWS costs or risky automated provisioning.

## Speaker Notes
Cloud architecture design is notoriously difficult because decisions are deeply interdependent: choosing Multi-AZ RDS boosts availability but doubles database costs, while switching to serverless changes latency and scaling characteristics. Novices routinely struggle with these multi-objective trade-offs, often defaulting to expensive or insecure monolithic designs. Our system acts as an interactive learning and decision-support aid that takes free-form requirements and produces a fully explainable, validated design proposal. Crucially, we enforce a strict recommendation-only boundary—nothing ever executes or deploys directly to AWS without human architect sign-off.

## Anticipated Examiner Questions
- **Q1: Why not let the system automatically deploy the architecture using Terraform or CDK?**
  *Answer:* Autonomous deployment introduces massive security and financial risks. An LLM mistake could provision expensive GPU clusters or open security groups to 0.0.0.0/0. Human-in-the-loop validation is essential for cloud infrastructure.
- **Q2: Can this replace professional solutions architects?**
  *Answer:* No. It is designed as an educational and drafting accelerator for junior engineers and students. High-level compliance contracts, enterprise governance, and organizational constraints still require senior human judgement.
