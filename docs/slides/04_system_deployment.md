# Slide 4: System's Own Cloud Architecture & Service Selection

## Slide Title
**Serverless Cloud Infrastructure for the Recommender System**

## Key Bullet Points
- **Frontend Layer**: Static SPA hosted on Amazon S3 and distributed globally via Amazon CloudFront (Origin Access Control, TLS 1.3).
- **API & Compute**: Amazon API Gateway (HTTP API for low cost) routing requests to AWS Lambda functions running pipeline micro-stages.
- **AI Core**: Amazon Bedrock managed API invocation (Claude 3 Haiku / Claude 3.5 Sonnet) avoiding custom GPU infrastructure costs.
- **Persistence & Observability**: Amazon DynamoDB for generation session history, second S3 bucket for diagram artifacts, and Amazon CloudWatch for structured execution logs.
- **Cost Discipline**: Serverless architecture has zero idle cost, staying comfortably within the AWS Free Tier during normal student testing.

## Speaker Notes
It is vital to distinguish between the architecture our system recommends to end users, and the architecture on which our system itself runs. For our own deployment, we designed a lean, cloud-native serverless architecture. Amazon CloudFront serves the static frontend from S3 with Origin Access Control. API Gateway routes requests to Lambda functions that invoke Amazon Bedrock. DynamoDB handles session persistence, while CloudWatch captures runtime logs. Because everything is serverless and pay-per-request, idle operational expenses are literally zero dollars, keeping our operational footprint within the AWS Free Tier.

## Anticipated Examiner Questions
- **Q1: Why choose API Gateway HTTP API over REST API?**
  *Answer:* HTTP API is roughly 70% cheaper ($1.00 per million requests vs $3.50 for REST API), provides lower latency, and natively supports modern OIDC/JWT authorization needed for student demos.
- **Q2: Why not run a self-hosted open-source model on an EC2 GPU instance?**
  *Answer:* Running a dedicated GPU instance like `g5.xlarge` costs over $700 per month 24/7. Serverless Bedrock API calls cost fractions of a cent per prompt (roughly $5–$16 for 500 complete pipeline runs), making it dramatically more economical for educational workloads.
