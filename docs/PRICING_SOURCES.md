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
5. **Account-Level Free Allowance Pooling (`free_tier_mode`):**
   - AWS Free Tier allowances (e.g. SQS 1M requests, DynamoDB 25 GB storage, Cognito 50k MAUs) are granted **per AWS account**, never per queue, table, or resource.
   - **`available` (default):** Assumes an eligible AWS account with unused monthly allowance. When multiple resources in the architecture share the same service dimension, allowance is pooled and shared (e.g. two SQS queues sharing 1M free requests total, not 1M per queue).
   - **`consumed` / `ineligible`:** Assumes the allowance is already exhausted by other workloads or the account does not qualify. Full on-demand unit rates apply to all usage.
   - **`unknown`:** Conservatively calculates full on-demand charges while disclosing potential savings and adding an explicit transparency note (`free_tier_note`).
6. **Financial Currency Precision & Line-Item Reconciliation:**
   - Calculations use `decimal.Decimal` with financial `ROUND_HALF_UP` quantization.
   - Displayed line items are rounded to 2 decimal places, while internal unrounded costs (`unrounded_monthly_usd_low/high`) are preserved to prevent premature loss of small charges (e.g. 1,000,001 requests displays as $0.00 while internal cost remains positive at $0.0000004).
   - The total architecture cost exactly reconciles with the sum of displayed line items.
7. **Unit-Driven Normalization:**
   - Usage quantities are converted strictly via explicit units (e.g. `"requests"` vs `"million requests"`, `"tokens"` vs `"1,000 tokens"`) or catalogue-defined metadata, avoiding ambiguous magnitude thresholds.
8. **Usage Range Semantics:**
   - **Low Estimate:** Baseline production usage (minimum redundancy, baseline storage, light traffic).
   - **High Estimate:** Scaled production usage (multi-instance/multi-task scaling, higher storage retention, elevated request volume).
   - Standard monthly duration is modelled using 730 hours per month as an explicitly documented operational approximation.
9. **Separation of Standard Rates from Promotional Free-Tier Allowances:**
   - Per official AWS guidance ([Finding prices in service price list files](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/finding-prices-in-service-price-list-files.html)), bulk Price List API files provide authoritative On-Demand and Savings Plan rates but are not an exhaustive catalog of promotional allowances.
   - We verify standard On-Demand unit prices against regional Price List API records, while Free Tier terms (AWS Always Free vs 12-Month introductory offers) are independently verified from official AWS Free Tier service documentation and published pricing schedules.

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
- **Usage Assumptions & Engine Modeling:**
  - *Modeled Scope:* Both hosted zones ($0.50/zone-month) and standard DNS queries ($0.40/M) are actively modeled in `catalogue/catalogue.yaml` and computed by `src/aws_arch/cost.py`.
  - *Low:* 1 hosted zone + 1,000,000 standard queries = $0.50 + $0.40 = **$0.90/mo**
  - *High:* 1 hosted zone + 10,000,000 standard queries = $0.50 + $4.00 = **$4.50/mo**
- **Architectural Scope & Exclusions:**
  - *Architectural Scope:* Route 53 charges are calculated **only** when the architecture contains a `Route53` node. General web or compute architectures omitting Route 53 are never charged for Route 53.
  - *Exclusions:* Optional Route 53 add-ons such as Traffic Flow routing policies ($50.00/policy-month), Route 53 Resolver endpoints ($0.125/hr per ENI), DNSSEC signing, and domain name registration fees ($12.00–$50.00+/year) are excluded from the core service model.

### 3. Application Load Balancer (ALB)
- **Catalogue Key:** `ApplicationLoadBalancer`
- **Official Source:** [Elastic Load Balancing Pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) / AWS Price List API (`AWSELB`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - ALB Instance Hours SKU `WJ2MHASNP2ZNKFXX`: `APS3-LoadBalancerUsage` (**$0.0239000000 per ALB-hour**)
  - LCU Capacity Units SKU `HFFD75W4GFXQPHZR`: `APS3-LCUUsage` (**$0.0080000000 per LCU-hour**)
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
- **Price List API Verification & SKUs:**
  - HTTP API SKU `S2BWD3VP3K4M5Q9P`: `APS3-ApiGatewayHttpRequest` ($0.0000010500 per request = **$1.05 per million requests**)
  - REST API SKU `AEUDCPQMKMJHSZGF`: `APS3-ApiGatewayRequest` ($0.0000035000 per request = **$3.50 per million requests**)
- **Billing Dimensions & Unit Rates:**
  - HTTP API: **$1.05 per million requests** (first 300 million)
  - REST API: **$3.50 per million requests** (first 333 million)
- **Usage Assumptions:**
  - *Low:* 5,000,000 HTTP API requests = 5 × $1.05 = **$5.25/mo**
  - *High:* 25,000,000 HTTP API requests = 25 × $1.05 = **$26.25/mo**
- **Important Conditions & Exclusions:** Payload units are metered in 512 KB increments. Dedicated API Gateway caching and REST API private endpoints are excluded.

### 5. EC2 Auto Scaling Group
- **Catalogue Key:** `EC2AutoScalingGroup`
- **Official Source:** [Amazon EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/) / AWS Price List API (`AmazonEC2`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - `t3.micro` Linux Shared SKU `9NX7BP9ZGC9GB8AX`: `APS3-BoxUsage:t3.micro` (**$0.0112000000 per instance-hour**)
- **Billing Dimensions & Unit Rates:**
  - Instance Type: `t3.micro` Linux / Shared Tenancy: **$0.0112 per instance-hour**
- **Usage Assumptions (730 hours/month):**
  - *Low:* 1 instance continuous = 730 hours × $0.0112 = **$8.18/mo**
  - *High:* 2 instances continuous (auto-scaled) = 1,460 hours × $0.0112 = **$16.35/mo**
- **Important Conditions & Exclusions:** Attached EBS root volumes (gp3 @ $0.096/GB-mo) and cross-AZ traffic are billed separately. 12-Month Free Tier (750h/mo) is not modeled for production estimates.

### 6. Amazon ECS on AWS Fargate
- **Catalogue Key:** `ECSFargate`
- **Official Source:** [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/) / AWS Price List API (`AmazonEC2`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - Fargate vCPU Rate: `APS3-Fargate-vCPU-Hours:perCPU` (**$0.0425600000 per vCPU-hour**)
  - Fargate Memory Rate: `APS3-Fargate-GB-Hours` (**$0.0046550000 per GB-hour**)
  - Ephemeral Storage Rate: `APS3-Fargate-EphemeralStorage-GB-Hours` ($0.0001110000 per GB-hour after first 20 GB)
- **Billing Dimensions & Unit Rates:**
  - vCPU: **$0.04256 per vCPU-hour** (Linux/x86 On-Demand in `ap-south-1`)
  - Memory: **$0.004655 per GB-hour** (Linux/x86 On-Demand in `ap-south-1`)
  - Ephemeral Storage: First 20 GB included free per task; $0.000111/GB-hour thereafter
  - *Regional Rate Distinction:* Note that $0.04656/vCPU-hr and $0.00511/GB-hr apply to `us-west-1` (N. California) and `sa-east-1` (Sao Paulo). The correct verified rates for Asia Pacific (Mumbai) (`ap-south-1`) are strictly $0.04256/vCPU-hr and $0.004655/GB-hr.
- **Usage Assumptions (730 hours/month):**
  - *Low:* 1 task (0.5 vCPU, 1 GB RAM, 730h) = (365 × $0.04256) + (730 × $0.004655) = $15.53 + $3.40 = **$18.93/mo**
  - *High:* 2 tasks (1.0 vCPU, 2 GB RAM, 730h each = 1,460 task-hours) = (1,460 × $0.04256) + (2,920 × $0.004655) = $62.14 + $13.59 = **$75.73/mo**
- **Important Conditions & Exclusions:** Additional ephemeral storage beyond 20 GB and Windows container OS licenses are excluded.

### 7. AWS Lambda
- **Catalogue Key:** `Lambda`
- **Official Source:** [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/) / AWS Price List API (`AWSLambda`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - Invocations SKU `VPGUBFQ4KNZKMKGJ`: `APS3-Request` (**$0.0000002000 per request** = $0.20 per million requests)
  - Free Tier Requests SKU `ZQVCC2M69R4S79XS`: `Global-Request` (First 1,000,000 requests free per month)
  - Compute Duration SKU `PHDF9YNAFR3HDSR8`: `APS3-Lambda-GB-Second` (**$0.0000166667 per GB-second**, Tier 1)
  - Free Tier Duration SKU `4VCGJ7EG8PJVZG7S`: `Global-Lambda-GB-Second` (First 400,000 GB-seconds free per month)
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
- **Price List API Verification & SKUs:**
  - Single-AZ Instance SKU `TDP2T3MABGFDWYMQ`: `db.t3.micro Single-AZ instance hour running MySQL` (**$0.0250000000 per hour**)
  - Single-AZ gp3 Storage Rate: `APS3-RDS:GP3-Storage` (**$0.1310000000 per GB-month**)
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
- **Price List API Verification & SKUs:**
  - Multi-AZ Instance SKU `XY6F6U9686MYMXAN`: `db.t3.micro Multi-AZ instance hour running MySQL` (**$0.0490000000 per hour**)
  - Multi-AZ Storage Rate: `APS3-RDS:Multi-AZ-GP3-Storage`: `GB-month of provisioned GP3 storage for Multi-AZ deployments running MySQL` (**$0.2620000000 per GB-month**)
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
- **Price List API Verification & SKUs:**
  - Storage SKU `8Q6HK3ASV67MN388`: `APS3-TimedStorage-ByteHrs` (0–25 GB: **$0.00** free tier; >25 GB: **$0.2850000000 per GB-month**)
  - Write Request Units SKU `A5DP2X4YSZ84WEJA`: `APS3-WriteRequestUnits` (**$0.71 per million WRU** = $0.0000007100/unit)
  - Read Request Units SKU `HQZY4ZFUTRDPV7ZE`: `APS3-ReadRequestUnits` (**$0.1425 per million RRU** = $0.0000001425/unit)
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
- **Price List API Verification & SKUs:**
  - `cache.t3.micro` Redis SKU `XZTCQWH2CTD9RTXE`: `APS3-NodeUsage:cache.t3.micro` (**$0.0210000000 per node-hour**)
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
- **Price List API Verification & SKUs:**
  - Standard Storage SKU `USGUTP2JY23N9GH2`: `APS3-TimedStorage-ByteHrs` (0–50 TB: **$0.0250000000 per GB-month**)
  - Tier 1 Requests SKU `UJ844B8DVMQUFJQP`: `APS3-Requests-Tier1` (**$0.0050000000 per 1,000 PUT, COPY, POST, LIST**)
  - Tier 2 Requests SKU `SF3QQQMZGA3PPF33`: `APS3-Requests-Tier2` (**$0.0004000000 per 1,000 GET and all other**)
- **Billing Dimensions & Unit Rates:**
  - Standard Storage: **$0.025 per GB-month** (first 50 TB)
  - Tier 1 Requests (PUT, COPY, POST, LIST): **$0.005 per 1,000 requests** ($0.000005/req)
  - Tier 2 Requests (GET and all other): **$0.0004 per 1,000 requests** ($0.0000004/req)
- **Usage Assumptions:**
  - *Low:* 50 GB storage + 20,000 PUTs + 200,000 GETs = (50 × $0.025) + (20 × $0.005) + (200 × $0.0004) = $1.25 + $0.10 + $0.08 = **$1.43/mo**
  - *High:* 500 GB storage + 100,000 PUTs + 1,000,000 GETs = (500 × $0.025) + (100 × $0.005) + (1,000 × $0.0004) = $12.50 + $0.50 + $0.40 = **$13.40/mo**
- **Important Conditions & Exclusions:** Data transfer out to the internet and lifecycle transitions to Glacier are excluded. 12-Month Free Tier (5 GB) is not modeled for production estimates.

### 13. Amazon SQS
- **Catalogue Key:** `SQS`
- **Official Source:** [Amazon SQS Pricing](https://aws.amazon.com/sqs/pricing/) / AWS Price List API (`AWSQueueService`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - Standard Requests SKU `Y6JJ7JBXQG364CH7`: `APS3-Requests-Tier1` Standard (**$0.40 per million requests** = $0.0000004000/req, Tier 1 up to 100 billion reqs/mo)
  - Monthly Free Allowance SKU `MNCJEPJRCSC9RFY2`: `Global-Requests` Any (**First 1,000,000 requests free per month** = $0.0000000000)
  - FIFO Requests SKU `WXF9K2K46U6ZR9US`: `APS3-Requests-FIFO-Tier1` FIFO (**$0.50 per million requests** = $0.0000005000/req)
  - Fair Queue SKU `2M2GBHBUZDGCE7CK`: `APS3-Requests-Fair-Tier1` Fair (**$0.10 per million requests** = $0.0000001000/req)
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
  - *Multi-Queue Account Pooling:*
    - When multiple queues exist in an architecture, the 1M allowance is shared across queues. Line-item breakdown assigns the allowance sequentially in order of appearance as an estimation convention; the overall architecture total is invariant to resource ordering.
- **Important Conditions & Exclusions:** Standard queue requests are metered in 64 KB chunks (payloads from 64 KB to 256 KB count as 2 to 4 billable requests). FIFO queues ($0.50/M) and cross-region queue data transfer are excluded from standard baseline.

### 14. Amazon Cognito
- **Catalogue Key:** `Cognito`
- **Official Source:** [Amazon Cognito Pricing](https://aws.amazon.com/cognito/pricing/) / AWS Price List API (`AmazonCognito`, `ap-south-1`)
- **Verification Date:** 2026-10-25
- **Region Scope:** Regional (`ap-south-1`)
- **Price List API Verification & SKUs:**
  - User Pools MAU SKU `SJDJQB52YRYNVHRN`: `APS3-CognitoUserPoolsMAU` (0–50k MAU: **$0.00** free tier; 50k–100k MAU: **$0.0055000000 per MAU**)
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
- **Price List API Verification & SKUs:**
  - Titan Text Express Input SKU `6UNCKSWRDBPA548S`: `APS3-TitanTextG1-Express-input-tokens` (**$0.0010000000 per 1,000 tokens** = $1.00/M tokens)
  - Titan Text Express Output SKU `NHZ5ECAKWBFG3N8H`: `APS3-TitanTextG1-Express-output-tokens` (**$0.0019000000 per 1,000 tokens** = $1.90/M tokens)
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
- **Price List API Verification & SKUs:**
  - Custom Metrics SKU `WJAN9NR7AQ8KWB2U`: `APS3-CW:MetricMonitorUsage` (0–10,000 metrics: **$0.3000000000 per metric-month**)
  - Standard Alarms SKU `MBFPHE42AKJWSCZH`: `APS3-CW:AlarmMonitorUsage` (**$0.1000000000 per alarm-month**)
  - Log Ingestion SKU `JBQP6QEETS2BK5DQ`: `APS3-DataProcessing-Bytes` (**$0.6700000000 per GB custom log data ingested in Standard log class**)
  - Log Storage SKU `M9PG5USRE2QBB6FU`: `APS3-TimedStorage-ByteHrs` (**$0.0300000000 per GB-month**)
  - Free Tier Custom Metrics SKU `3ZJZSGX8K87XPW4R`: `Global-CW:MetricMonitorUsage` (First 10 metrics free per month)
  - Free Tier Alarms SKU `FCH8WPMWVXA4B6VM`: `Global-CW:AlarmMonitorUsage` (First 10 alarms free per month)
  - Free Tier Log Ingestion SKU `SSNSJENVU973ECHE`: `Global-DataProcessing-Bytes` (First 5 GB free per month)
  - Free Tier Log Storage SKU `6XTVPDAM3VF25UTA`: `Global-TimedStorage-ByteHrs` (First 5 GB free per month)
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
