# AWS Pricing Sources & Cost Estimation Reference

This document records the pricing model, authoritative AWS sources, verification dates, calculation formulas, and usage assumptions for the AWS Architecture Recommender.

**Target Region:** Asia Pacific (Mumbai) (`ap-south-1`)
**Verification Date:** 2026-10-25
**Authoritative Sources:** AWS Price List API (`https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/...`) and official AWS Service Pricing pages.
**Estimate Nature:** Order-of-magnitude architectural planning guide only; **never a guaranteed AWS invoice**.

---

## 1. Principles & Estimation Philosophy

1. **Accuracy Over Completeness:** We never fabricate AWS unit prices, copy unverified numbers from third-party blogs, or guess regional rates. Every verified price is backed by the official AWS Price List API or AWS documentation for `ap-south-1`.
2. **Unknown is Not Zero:** If an official rate cannot be reliably confirmed for `ap-south-1`, the unit price is recorded as `null` with a `TODO verify` status. The service is reported as `incomplete` and is **never** silently zeroed.
3. **Four Distinct Estimation States:**
   - **Complete Estimate (`status: complete`):** All components in the architecture are verified. Total monthly low and high costs are returned as numeric values (`monthly_usd_low <= monthly_usd_high`).
   - **Partial Verified Subtotal (`status: incomplete`):** Some components are verified, but at least one component is unverified. Complete architecture low/high totals are returned as `null` (`None` in Python, serialized to JSON `null`), and verified component costs are reported separately as `partial_verified_monthly_usd_low` and `partial_verified_monthly_usd_high`.
   - **Incomplete Architecture Cost:** Any estimate where unverified services remain. The list of affected components is explicitly exposed in `incomplete_services`.
   - **Fully Unknown Architecture Cost:** All selected components are unverified. Both total low/high estimates are `null` and no partial totals are asserted.
4. **Verified Zero-Cost vs. Free Tier Allowances:**
   - Core IAM permissions, roles, and policies are officially offered by AWS at **no additional charge** ($0.00). This is distinguished from services that incur charges once free-tier thresholds are exceeded.
5. **Reusable Free Allowance Accounting (`free_tier_mode`):**
   - **`available` (default):** Assumes the AWS account qualifies for the applicable monthly free allowance and has not consumed it across other workloads. The allowance is subtracted prior to billing: $\text{billable} = \max(0, \text{usage} - \text{allowance})$.
   - **`consumed` / `ineligible`:** Assumes the allowance has already been exhausted by other applications in the account or the workload does not qualify. Full on-demand unit rates apply to all usage.
   - **`unknown`:** Conservatively calculates full on-demand charges while transparently reporting potential free-tier savings.
6. **Usage Range Semantics:**
   - **Low Estimate:** Baseline production usage (minimum redundancy, baseline storage, light traffic).
   - **High Estimate:** Scaled production usage (multi-instance/multi-task scaling, higher storage retention, elevated request volume).
   - Standard monthly duration is modelled using 730 hours per month as an explicitly documented operational approximation.

---

## 2. Service-by-Service Pricing Verification & Usage Models

### 1. CloudFront
- **Catalogue Key:** `CloudFront`
- **Official Source:** [Amazon CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/) / AWS Price List API (`AmazonCloudFront`, `aws-other` / India Edge)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional Edge (India Edge Locations)
- **Billing Dimensions & Unit Rates:**
  - Data Transfer Out to Internet: **$0.109 per GB** (first 10 TB/month)
  - HTTPS Requests: **$0.0120 per 10,000 requests** ($0.0000012 per request)
- **Usage Assumptions:**
  - *Low:* 100 GB DTO + 1,000,000 HTTPS requests = (100 × $0.109) + (1,000,000 × $0.0000012) = **$12.10/mo**
  - *High:* 1,000 GB DTO + 10,000,000 HTTPS requests = (1,000 × $0.109) + (10,000,000 × $0.0000012) = **$121.00/mo**
- **Important Conditions & Exclusions:** AWS Free Tier includes 1 TB DTO and 10M requests free per month globally. The model computes on-demand rates without assuming persistent free-tier discounts. Dedicated IP SSL and Origin Shield are excluded.

### 2. Route 53
- **Catalogue Key:** `Route53`
- **Official Source:** [Amazon Route 53 Pricing](https://aws.amazon.com/route53/pricing/) / AWS Price List API (`AmazonRoute53`, `aws-other`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Global
- **Billing Dimensions & Unit Rates:**
  - Hosted Zone: **$0.50 per hosted zone / month** (first 25 zones)
  - Standard DNS Queries: **$0.40 per 1,000,000 queries** ($0.0000004 per query)
  - Queries to Alias records: **$0.00** (Free of charge)
- **Usage Assumptions:**
  - *Low:* 1 hosted zone + 1,000,000 standard queries = $0.50 + $0.40 = **$0.90/mo**
  - *High:* 1 hosted zone + 10,000,000 standard queries = $0.50 + $4.00 = **$4.50/mo**
- **Important Conditions & Exclusions:** Traffic Flow policies ($50/mo) and DNS Firewall endpoints are excluded.

### 3. Application Load Balancer (ALB)
- **Catalogue Key:** `ApplicationLoadBalancer`
- **Official Source:** [Elastic Load Balancing Pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) / AWS Price List API (`AWSELB`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - ALB Instance Hours: **$0.0239 per ALB-hour**
  - Load Balancer Capacity Units (LCU): **$0.008 per LCU-hour**
- **Usage Assumptions (730 hours/month):**
  - *Low:* 730 ALB-hours + 730 LCU-hours (1 average LCU) = (730 × $0.0239) + (730 × $0.008) = $17.45 + $5.84 = **$23.29/mo**
  - *High:* 730 ALB-hours + 2,190 LCU-hours (3 average LCUs) = (730 × $0.0239) + (2,190 × $0.008) = $17.45 + $17.52 = **$34.97/mo**
- **Important Conditions & Exclusions:** Cross-zone load balancing data transfer charges are excluded.

### 4. Amazon API Gateway
- **Catalogue Key:** `APIGateway`
- **Official Source:** [Amazon API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/) / AWS Price List API (`AmazonApiGateway`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - HTTP API: **$1.05 per million requests** (first 300 million)
  - REST API: **$3.50 per million requests** (first 333 million)
- **Usage Assumptions:**
  - *Low:* 5,000,000 HTTP API requests = 5 × $1.05 = **$5.25/mo**
  - *High:* 25,000,000 HTTP API requests = 25 × $1.05 = **$26.25/mo**
- **Important Conditions & Exclusions:** API Gateway dedicated caching and REST API private endpoints are excluded.

### 5. EC2 Auto Scaling Group
- **Catalogue Key:** `EC2AutoScalingGroup`
- **Official Source:** [Amazon EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/) / AWS Price List API (`AmazonEC2`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Instance Type: `t3.micro` Linux / Shared Tenancy: **$0.0112 per instance-hour**
- **Usage Assumptions (730 hours/month):**
  - *Low:* 1 instance continuous = 730 hours × $0.0112 = **$8.18/mo**
  - *High:* 2 instances continuous (auto-scaled) = 1,460 hours × $0.0112 = **$16.35/mo**
- **Important Conditions & Exclusions:** Attached EBS root volumes (gp3 @ $0.096/GB-mo) and cross-AZ traffic are billed separately.

### 6. Amazon ECS on AWS Fargate
- **Catalogue Key:** `ECSFargate`
- **Official Source:** [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/) / AWS Price List API (`AmazonEC2`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - vCPU: **$0.04256 per vCPU-hour** (Linux/x86)
  - Memory: **$0.004655 per GB-hour**
  - Ephemeral Storage: First 20 GB included free per task
- **Usage Assumptions (730 hours/month):**
  - *Low:* 1 task (0.5 vCPU, 1 GB RAM, 730h) = (365 × $0.04256) + (730 × $0.004655) = $15.53 + $3.40 = **$18.93/mo**
  - *High:* 2 tasks (1.0 vCPU, 2 GB RAM, 730h each = 1,460 task-hours) = (1,460 × $0.04256) + (2,920 × $0.004655) = $62.14 + $13.59 = **$75.73/mo**
- **Important Conditions & Exclusions:** Additional ephemeral storage beyond 20 GB is excluded.

### 7. AWS Lambda
- **Catalogue Key:** `Lambda`
- **Official Source:** [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/) / AWS Price List API (`AWSLambda`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Requests: **$0.20 per million requests** ($0.0000002 per request)
  - Compute: **$0.0000166667 per GB-second** (x86 architecture)
- **Usage Assumptions:**
  - *Low:* 2,000,000 requests @ 128 MB (0.125 GB) and 200 ms (0.2s) duration = 50,000 GB-s compute = (2M × $0.0000002) + (50,000 × $0.0000166667) = $0.40 + $0.83 = **$1.23/mo**
  - *High:* 10,000,000 requests @ 256 MB (0.25 GB) and 300 ms (0.3s) duration = 750,000 GB-s compute = (10M × $0.0000002) + (750,000 × $0.0000166667) = $2.00 + $12.50 = **$14.50/mo**
- **Important Conditions & Exclusions:** Provisioned concurrency and Lambda@Edge execution are excluded.

### 8. Amazon RDS (Single-AZ MySQL)
- **Catalogue Key:** `RDS`
- **Official Source:** [Amazon RDS for MySQL Pricing](https://aws.amazon.com/rds/mysql/pricing/) / AWS Price List API (`AmazonRDS`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Instance: `db.t3.micro` Single-AZ MySQL: **$0.025 per hour**
  - Storage: General Purpose SSD (`gp3`) Single-AZ: **$0.131 per GB-month**
- **Usage Assumptions (730 hours/month):**
  - *Low:* 730h db.t3.micro + 20 GB gp3 storage = (730 × $0.025) + (20 × $0.131) = $18.25 + $2.62 = **$20.87/mo**
  - *High:* 730h db.t3.micro + 100 GB gp3 storage = (730 × $0.025) + (100 × $0.131) = $18.25 + $13.10 = **$31.35/mo**
- **Important Conditions & Exclusions:** Backup storage exceeding database size and provisioned IOPS above 3,000 baseline are excluded.

### 9. Amazon RDS Multi-AZ (MySQL)
- **Catalogue Key:** `RDS_MultiAZ`
- **Official Source:** [Amazon RDS for MySQL Pricing](https://aws.amazon.com/rds/mysql/pricing/) / AWS Price List API (`AmazonRDS`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Instance: `db.t3.micro` Multi-AZ MySQL: **$0.049 per hour**
  - Storage: General Purpose SSD (`gp3`) Multi-AZ: **$0.262 per GB-month** (2x Single-AZ replication)
- **Usage Assumptions (730 hours/month):**
  - *Low:* 730h Multi-AZ db.t3.micro + 20 GB gp3 Multi-AZ storage = (730 × $0.049) + (20 × $0.262) = $35.77 + $5.24 = **$41.01/mo**
  - *High:* 730h Multi-AZ db.t3.micro + 100 GB gp3 Multi-AZ storage = (730 × $0.049) + (100 × $0.262) = $35.77 + $26.20 = **$61.97/mo**
- **Important Conditions & Exclusions:** Cross-AZ replication data transfer within Multi-AZ cluster is included in the Multi-AZ instance and storage price.

### 10. Amazon DynamoDB
- **Catalogue Key:** `DynamoDB`
- **Official Source:** [Amazon DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/) / AWS Price List API (`AmazonDynamoDB`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates (On-Demand):**
  - Standard Storage: **$0.285 per GB-month** (First 25 GB free)
  - Read Request Units (RRU): **$0.1425 per million RRU** ($0.0000001425 per unit)
  - Write Request Units (WRU): **$0.71 per million WRU** ($0.00000071 per unit)
- **Usage Assumptions:**
  - *Low:* 10 GB storage (within free tier = $0.00) + 5M RRU + 1M WRU = $0.00 + (5 × $0.1425) + (1 × $0.71) = **$1.42/mo**
  - *High:* 50 GB storage (25 GB billed @ $0.285 = $7.13) + 25M RRU + 5M WRU = $7.13 + (25 × $0.1425) + (5 × $0.71) = $7.13 + $3.56 + $3.55 = **$14.24/mo**
- **Important Conditions & Exclusions:** Point-in-time recovery (PITR) and global tables replication are excluded.

### 11. Amazon ElastiCache
- **Catalogue Key:** `ElastiCache`
- **Official Source:** [Amazon ElastiCache Pricing](https://aws.amazon.com/elasticache/pricing/) / AWS Price List API (`AmazonElastiCache`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Node Type: `cache.t3.micro` Redis: **$0.021 per node-hour**
- **Usage Assumptions (730 hours/month):**
  - *Low:* 1 node × 730 hours = 730 × $0.021 = **$15.33/mo**
  - *High:* 2 nodes (primary + replica) × 730 hours = 1,460 × $0.021 = **$30.66/mo**
- **Important Conditions & Exclusions:** Backup snapshot storage and cross-AZ data transfer are excluded.

### 12. Amazon S3
- **Catalogue Key:** `S3`
- **Official Source:** [Amazon S3 Pricing](https://aws.amazon.com/s3/pricing/) / AWS Price List API (`AmazonS3`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Standard Storage: **$0.025 per GB-month** (first 50 TB)
  - Tier 1 Requests (PUT, COPY, POST, LIST): **$0.005 per 1,000 requests** ($0.000005/req)
  - Tier 2 Requests (GET and all other): **$0.0004 per 1,000 requests** ($0.0000004/req)
- **Usage Assumptions:**
  - *Low:* 50 GB storage + 20,000 PUTs + 200,000 GETs = (50 × $0.025) + (20 × $0.005) + (200 × $0.0004) = $1.25 + $0.10 + $0.08 = **$1.43/mo**
  - *High:* 500 GB storage + 100,000 PUTs + 1,000,000 GETs = (500 × $0.025) + (100 × $0.005) + (1,000 × $0.0004) = $12.50 + $0.50 + $0.40 = **$13.40/mo**
- **Important Conditions & Exclusions:** Data transfer out to the internet and lifecycle transitions to Glacier are excluded.

### 13. Amazon SQS
- **Catalogue Key:** `SQS`
- **Official Source:** [Amazon SQS Pricing](https://aws.amazon.com/sqs/pricing/) / AWS Price List API (`AWSQueueService`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Free Allowance: First 1,000,000 requests free each month under AWS Always Free tier
  - Standard Queue: **$0.40 per million requests** ($0.0000004 per request)
- **Usage Assumptions & Calculations:**
  - *Full Allowance Available (`free_tier_mode: available`):*
    - Low (1,000,000 requests): $\max(0, 1.0 - 1.0) \times \$0.40 = \mathbf{\$0.00/\text{mo}}$ (potential free-tier savings: $0.40)
    - 2,000,000 requests: $\max(0, 2.0 - 1.0) \times \$0.40 = 1.0 \times \$0.40 = \mathbf{\$0.40/\text{mo}}$
    - High (10,000,000 requests): $\max(0, 10.0 - 1.0) \times \$0.40 = 9.0 \times \$0.40 = \mathbf{\$3.60/\text{mo}}$ (potential free-tier savings: $0.40)
  - *Allowance Consumed / Ineligible (`free_tier_mode: consumed`):*
    - 1,000,000 requests: $1.0 \times \$0.40 = \mathbf{\$0.40/\text{mo}}$
    - 2,000,000 requests: $2.0 \times \$0.40 = \mathbf{\$0.80/\text{mo}}$
    - 10,000,000 requests: $10.0 \times \$0.40 = \mathbf{\$4.00/\text{mo}}$
- **Important Conditions & Exclusions:** FIFO queue rate ($0.50/M) and payloads over 64 KB (which are billed as multiple 64 KB billable requests) are excluded.

### 14. Amazon Cognito
- **Catalogue Key:** `Cognito`
- **Official Source:** [Amazon Cognito Pricing](https://aws.amazon.com/cognito/pricing/) / AWS Price List API (`AmazonCognito`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Free Tier: First 50,000 Monthly Active Users (MAUs) free each month
  - Tier 1 (50,001 to 100,000 MAUs): **$0.0055 per MAU**
- **Usage Assumptions:**
  - *Low:* 10,000 MAUs (within 50,000 free tier) = **$0.00/mo**
  - *High:* 60,000 MAUs = 50,000 free + 10,000 billed @ $0.0055 = **$55.00/mo**
- **Important Conditions & Exclusions:** Advanced Security Features (Cognito Plus / SES SMS messaging charges) are excluded.

### 15. Amazon Bedrock
- **Catalogue Key:** `Bedrock`
- **Official Source:** [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) / AWS Price List API (`AmazonBedrock`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates (Amazon Titan Text Express):**
  - Input Tokens: **$0.001 per 1,000 tokens** ($1.00 per 1M tokens)
  - Output Tokens: **$0.0019 per 1,000 tokens** ($1.90 per 1M tokens)
- **Usage Assumptions:**
  - *Low:* 5,000,000 in / 1,000,000 out tokens = (5,000 × $0.001) + (1,000 × $0.0019) = $5.00 + $1.90 = **$6.90/mo**
  - *High:* 25,000,000 in / 5,000,000 out tokens = (25,000 × $0.001) + (5,000 × $0.0019) = $25.00 + $9.50 = **$34.50/mo**
- **Important Conditions & Exclusions:** Provisioned throughput model units and third-party foundation models (e.g. Claude 3.5 Sonnet) are excluded.

### 16. Amazon CloudWatch
- **Catalogue Key:** `CloudWatch`
- **Official Source:** [Amazon CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/) / AWS Price List API (`AmazonCloudWatch`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Billing Dimensions & Unit Rates:**
  - Custom Metrics: **$0.30 per metric-month** (first 10,000)
  - Standard Alarms: **$0.10 per alarm-month**
  - Log Ingestion: **$0.67 per GB** (Standard log class)
  - Log Storage: **$0.03 per GB-month**
- **Usage Assumptions:**
  - *Low:* 5 metrics ($1.50) + 2 alarms ($0.20) + 5 GB logs ($3.35) + 5 GB storage ($0.15) = **$5.20/mo**
  - *High:* 20 metrics ($6.00) + 5 alarms ($0.50) + 25 GB logs ($16.75) + 25 GB storage ($0.75) = **$24.00/mo**
- **Important Conditions & Exclusions:** Contributor Insights and high-resolution metrics are excluded.

### 17. AWS Identity and Access Management (IAM)
- **Catalogue Key:** `IAM`
- **Official Source:** [AWS IAM Pricing](https://aws.amazon.com/iam/pricing/) & AWS Documentation
- **Verification Date:** 2026-10-25
- **Region Scope:** Global
- **Billing Dimensions & Unit Rates:**
  - Core IAM Service: **$0.00** ("AWS Identity and Access Management is a feature of your AWS account offered at no additional charge.")
- **Usage Assumptions:**
  - *Low:* Standard IAM roles, policies, and instance profiles = **$0.00/mo**
  - *High:* Standard IAM roles, policies, and instance profiles = **$0.00/mo**
- **Important Conditions & Exclusions:** Advanced integrations such as IAM Roles Anywhere external CA anchors or AWS KMS keys used with IAM policies are billed under their respective services.

---

## 3. Reference Summary Table

| Service Identifier | Category | Region Scope | Status | Low Cost ($/mo) | High Cost ($/mo) | Primary Billing Driver |
|---|---|---|---|---|---|---|
| `CloudFront` | network | Regional Edge | `verified` | $12.10 | $121.00 | Data Transfer Out ($0.109/GB) + HTTPS Requests |
| `Route53` | network | Global | `verified` | $0.90 | $4.50 | Hosted Zone ($0.50/mo) + Queries ($0.40/M) |
| `ApplicationLoadBalancer`| network | `ap-south-1` | `verified` | $23.29 | $34.97 | ALB-Hours ($0.0239/hr) + LCUs ($0.008/LCU-hr) |
| `APIGateway` | network | `ap-south-1` | `verified` | $5.25 | $26.25 | HTTP API Requests ($1.05/M) |
| `EC2AutoScalingGroup` | compute | `ap-south-1` | `verified` | $8.18 | $16.35 | `t3.micro` Linux Instance-Hours ($0.0112/hr) |
| `ECSFargate` | compute | `ap-south-1` | `verified` | $18.93 | $75.73 | vCPU ($0.04256/hr) + RAM ($0.004655/GB-hr) |
| `Lambda` | compute | `ap-south-1` | `verified` | $1.23 | $14.50 | Invocations ($0.20/M) + Compute ($0.0000167/GB-s) |
| `RDS` | database | `ap-south-1` | `verified` | $20.87 | $31.35 | Single-AZ `db.t3.micro` ($0.025/hr) + gp3 ($0.131/GB) |
| `RDS_MultiAZ` | database | `ap-south-1` | `verified` | $41.01 | $61.97 | Multi-AZ `db.t3.micro` ($0.049/hr) + gp3 ($0.262/GB) |
| `DynamoDB` | database | `ap-south-1` | `verified` | $1.42 | $14.24 | On-Demand RRU ($0.1425/M) + WRU ($0.71/M) + Storage |
| `ElastiCache` | database | `ap-south-1` | `verified` | $15.33 | $30.66 | `cache.t3.micro` Redis Node-Hours ($0.021/hr) |
| `S3` | storage | `ap-south-1` | `verified` | $1.43 | $13.40 | Standard Storage ($0.025/GB) + Request Tiers |
| `SQS` | integration | `ap-south-1` | `verified` | $0.00 | $3.60 | Standard Queue Requests ($0.40/M, 1M free allowance) |
| `Cognito` | security | `ap-south-1` | `verified` | $0.00 | $55.00 | User Pools MAUs (first 50k free, then $0.0055/MAU) |
| `Bedrock` | ai | `ap-south-1` | `verified` | $6.90 | $34.50 | Titan Text Express Tokens ($0.001/1k in, $0.0019/1k out) |
| `CloudWatch` | ops | `ap-south-1` | `verified` | $5.20 | $24.00 | Log Ingestion ($0.67/GB) + Metrics ($0.30) + Alarms |
| `IAM` | security | Global | `verified` | $0.00 | $0.00 | Core IAM features included at no charge ($0.00) |

---

## 4. Explicit Charges Excluded From Cost Engine

The cost estimation engine explicitly excludes the following material infrastructure charges:
1. **NAT Gateway:** Hourly ($0.045/hr) + Data Processing ($0.045/GB) across AZs.
2. **Inter-AZ Network Traffic:** VPC cross-AZ peering or traffic between compute and database across AZs ($0.01/GB).
3. **Data Transfer Out (Internet Egress):** General EC2 internet egress beyond the baseline CloudFront traffic.
4. **AWS Enterprise / Business Support:** Pro-rated monthly support contracts (3%–10% of monthly AWS spend).
5. **Government Taxes & Currency Fluctuation:** Applicable Indian Goods and Services Tax (GST: 18%) or banking foreign exchange spreads.
