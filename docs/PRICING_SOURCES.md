# AWS Pricing Sources & Cost Estimation Reference

This document records the pricing model, official AWS sources, verification status, and usage assumptions for the AWS Architecture Recommender.

**Target Region:** Asia Pacific (Mumbai) (`ap-south-1`)  
**Pricing Status As Of:** October 2026 (`TODO verify`)  
**Estimate Nature:** Order-of-magnitude planning guide only; **never a guaranteed AWS invoice**.

---

## 1. Principles & Estimation Philosophy

1. **Accuracy Over Completeness:** We never fabricate AWS unit prices, copy unverified numbers from third-party blogs, or guess regional rates.
2. **Unknown is Not Zero:** If an official rate cannot be reliably confirmed for `ap-south-1`, the unit price is recorded as `null` with a `TODO verify` status. The service is reported as `incomplete` and is **never** silently zeroed.
3. **Transparent Partial Totals:** When an architecture contains unverified components, the overall low/high total is reported as `null` (`"status": "incomplete"`). Any verified subset is presented strictly as a separate partial subtotal, never as the total architecture cost.
4. **Range Semantics:**
   - **Low Estimate:** Baseline usage (single instance, minimum storage, baseline request volume).
   - **High Estimate:** Scaled usage (multi-instance, peak load, higher request/storage volumes).

---

## 2. Service Catalogue & Pricing Sources

The table below lists all 17 curated catalogue services for `ap-south-1`.

| Service | Official Source URL | Scope | Billing Unit | Status | Low Usage Assumption | High Usage Assumption |
|---|---|---|---|---|---|---|
| **CloudFront** | [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/) | Global | USD per GB data transfer out | `TODO verify` | 100 GB transfer, 1M requests | 1,000 GB transfer, 10M requests |
| **Route53** | [Route53 Pricing](https://aws.amazon.com/route53/pricing/) | Global | USD per hosted zone / million queries | `TODO verify` | 1 hosted zone, 1M queries | 1 hosted zone, 5M queries |
| **ApplicationLoadBalancer** | [ALB Pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) | `ap-south-1` | USD per ALB-hour / LCU-hour | `TODO verify` | 730 hours, 1 LCU | 730 hours, 3 LCUs |
| **APIGateway** | [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/) | `ap-south-1` | USD per million requests | `TODO verify` | 1 million requests | 10 million requests |
| **EC2AutoScalingGroup** | [EC2 Pricing](https://aws.amazon.com/ec2/pricing/on-demand/) | `ap-south-1` | USD per instance-hour | `TODO verify` | 730 hours (1 instance, e.g. t3.micro) | 1,460 hours (2 instances) |
| **ECSFargate** | [Fargate Pricing](https://aws.amazon.com/fargate/pricing/) | `ap-south-1` | USD per vCPU-hour & GB-hour | `TODO verify` | 0.5 vCPU, 1 GB RAM, 730h (1 task) | 0.5 vCPU, 1 GB RAM, 1,460h (2 tasks) |
| **Lambda** | [Lambda Pricing](https://aws.amazon.com/lambda/pricing/) | `ap-south-1` | USD per million requests & GB-sec | `TODO verify` | 1M invocations @ 128MB / 100ms | 10M invocations @ 128MB / 100ms |
| **RDS** | [RDS MySQL Pricing](https://aws.amazon.com/rds/mysql/pricing/) | `ap-south-1` | USD per instance-hour & GB-month | `TODO verify` | Single-AZ db.t3.micro 730h, 20 GB gp3 | Single-AZ db.t3.micro 730h, 50 GB gp3 |
| **RDS_MultiAZ** | [RDS MySQL Pricing](https://aws.amazon.com/rds/mysql/pricing/) | `ap-south-1` | USD per Multi-AZ instance-hour | `TODO verify` | Multi-AZ db.t3.micro 730h, 20 GB gp3 | Multi-AZ db.t3.micro 730h, 50 GB gp3 |
| **DynamoDB** | [DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/) | `ap-south-1` | USD per million RRU/WRU & GB-month | `TODO verify` | 1M reads/writes, 5 GB storage | 5M reads/writes, 20 GB storage |
| **ElastiCache** | [ElastiCache Pricing](https://aws.amazon.com/elasticache/pricing/) | `ap-south-1` | USD per node-hour | `TODO verify` | cache.t3.micro 730h (1 node) | cache.t3.micro 1,460h (2 nodes) |
| **S3** | [S3 Pricing](https://aws.amazon.com/s3/pricing/) | `ap-south-1` | USD per GB-month & requests | `TODO verify` | 10 GB Standard, 10k PUTs, 100k GETs | 100 GB Standard, 100k PUTs, 1M GETs |
| **SQS** | [SQS Pricing](https://aws.amazon.com/sqs/pricing/) | `ap-south-1` | USD per million requests | `TODO verify` | 1 million requests | 10 million requests |
| **Cognito** | [Cognito Pricing](https://aws.amazon.com/cognito/pricing/) | `ap-south-1` | USD per MAU (Monthly Active User) | `TODO verify` | 1,000 MAUs | 25,000 MAUs |
| **Bedrock** | [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) | `ap-south-1` | USD per 1,000 tokens | `TODO verify` | 100k input / 50k output tokens | 1M input / 500k output tokens |
| **CloudWatch** | [CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/) | `ap-south-1` | USD per GB logs, metrics, alarms | `TODO verify` | 5 GB logs, 3 metrics, 2 alarms | 20 GB logs, 10 metrics, 5 alarms |
| **IAM** | [IAM Documentation](https://aws.amazon.com/iam/) | Global | USD per user/role | `TODO verify` | Core IAM permissions & roles | Core IAM permissions & roles |

---

## 3. Important Exclusions & Limitations

The cost estimation engine calculates core compute, storage, and request costs only. The following categories are explicitly **excluded** from all estimates:

1. **Egress & Data Transfer Out:** Bandwidth charges to the public internet exceeding baseline allowances.
2. **Inter-AZ and Inter-Region Networking:** Cross-AZ traffic (e.g. EC2 to Multi-AZ RDS replication, NAT Gateway data processing).
3. **AWS Support Plans:** Business or Enterprise Support (3% to 10% of monthly bill).
4. **Taxes and Regulatory Fees:** Local goods and services taxes (GST/VAT) and currency conversion fluctuations.
5. **Free Tier Expiration:** Estimates do not assume active first-year 12-month free tier discounts.
