# AWS Management Console Deployment Guide: Serverless Recommender Stack

This guide provides a step-by-step, manual walkthrough for deploying the **AWS Architecture Recommender** serverless hosting stack using the AWS Management Console.

> **Scope Note:** This guide covers deploying the recommender application's *own* serverless delivery infrastructure (S3, CloudFront, API Gateway, Lambda, DynamoDB, CloudWatch, and IAM). It does not deploy or modify external architectures recommended by the tool.

---

## 1. Architectural Overview & Resource Inventory

The recommender system deploys as a decoupled serverless application:

```
[Browser / Client]
       │
       ├─────────────────────────────────┐
       ▼ (HTTPS)                         ▼ (HTTPS)
[Amazon CloudFront]             [Amazon API Gateway (HTTP API)]
       │ (Origin Access Control)         │ (Proxy Integration)
       ▼                                 ▼
[Amazon S3 Private Bucket]      [AWS Lambda Function]
(Static Web Assets)             (Python 3.12/3.13 Runtime)
                                         │
                                         ├─ CloudWatch Logs (Execution telemetry)
                                         └─ [Amazon DynamoDB] (History store - future integration)
```

### Shared Resource Naming Convention
To keep resources easily identifiable and prevent accidental deletion of unrelated cloud assets, use the prefix `aws-arch-recommender-demo-`:

| Service | Resource Name / Identifier | Purpose |
|:---|:---|:---|
| **AWS IAM** | `aws-arch-recommender-demo-lambda-role` | Least-privilege Lambda execution role |
| **AWS Lambda** | `aws-arch-recommender-demo-backend` | Recommender execution engine (mock mode) |
| **Amazon S3** | `aws-arch-recommender-demo-frontend-<account-id>` | Private bucket hosting frontend assets |
| **Amazon CloudFront** | `aws-arch-recommender-demo-cdn` | Global CDN with Origin Access Control (OAC) |
| **Amazon API Gateway** | `aws-arch-recommender-demo-api` | HTTP API proxy endpoint |
| **Amazon DynamoDB** | `aws-arch-recommender-demo-history` | On-demand table for recommendation history |
| **Amazon CloudWatch** | `/aws/lambda/aws-arch-recommender-demo-backend` | Dedicated log group |

---

## 2. Pre-Deployment: Cost Controls & Budget Alerts

Before creating any cloud resources, establish spending visibility:

1. **Navigate to:** AWS Console -> **AWS Budgets** (or search "Budgets" in the top search bar).
2. **Create Budget:**
   - Click **Create budget**.
   - Choose **Cost budget (Recommended)**.
   - Set **Budget name:** `aws-arch-recommender-demo-budget`.
   - Set **Budgeted amount:** e.g., `$5.00` USD (Monthly recurring).
   - Configure alert thresholds:
     - Alert 1: 80% of budgeted amount ($4.00) sent to your email.
     - Alert 2: 100% of budgeted amount ($5.00) sent to your email.
3. **Verify:** Check that the budget appears in the AWS Budgets console with status "OK".

> [!IMPORTANT]
> **Budget Alert vs. Spending Cap:** AWS Budget alerts notify you when estimated or actual spending crosses a threshold; **they do NOT stop or shut down active resources**. Monitor resources actively and execute the cleanup steps in Section 8 when finished.

---

## 3. Step-by-Step AWS Console Deployment

### Step 1: Create Least-Privilege IAM Execution Role
- **Where to navigate:** AWS Console -> **IAM** -> **Roles** -> click **Create role**.
- **Trusted entity type:** Select **AWS service**, then choose **Lambda** as the common use case. Click **Next**.
- **Permissions policies:**
  - In the search bar, enter `AWSLambdaBasicExecutionRole`.
  - Check the box next to `AWSLambdaBasicExecutionRole` (grants permission to write logs to CloudWatch).
  - *Do NOT attach AdministratorAccess or DynamoDB policies at this stage.*
- **Role details:**
  - **Role name:** `aws-arch-recommender-demo-lambda-role`
  - **Description:** `Least-privilege role for AWS Architecture Recommender demo Lambda.`
  - Click **Create role**.
- **How to verify:**
  - Search for `aws-arch-recommender-demo-lambda-role` in the IAM Roles list.
  - Open the role and verify under **Permissions** that only `AWSLambdaBasicExecutionRole` is attached.
- **Common failure:** Granting broad full-access policies (e.g. `AmazonS3FullAccess` or `AdministratorAccess`). Stick strictly to basic execution.

---

### Step 2: Create Amazon DynamoDB Table (History Store)
> [!NOTE]
> **Integration Status:** This table is provisioned for architecture history tracking. The current Lambda handler runs in stateless mock mode and does not write to DynamoDB. Provisioning the table demonstrates the target architecture schema; permissions will be added to the IAM role in a future integration phase.

- **Where to navigate:** AWS Console -> **DynamoDB** -> **Tables** -> click **Create table**.
- **Table configuration:**
  - **Table name:** `aws-arch-recommender-demo-history`
  - **Partition key (Primary key):** `id` (Type: **String**)
  - **Sort key:** Leave blank.
  - **Table settings:** Select **Customize settings**.
  - **Capacity mode:** Select **On-demand** (avoids hourly provisioned capacity charges; you only pay for requests executed).
  - **Encryption at rest:** Leave set to default **Owned by Amazon DynamoDB**.
  - Click **Create table**.
- **How to verify:**
  - Verify table status changes from `Creating` to `Active`.
- **Common failure:** Choosing "Provisioned" capacity with high read/write units, which incurs ongoing hourly charges even when idle.

---

### Step 3: Package & Deploy AWS Lambda Backend

#### A. Packaging the Application (Windows PowerShell)
The Lambda deployment package requires the handler, pipeline modules, schemas, catalogue, and third-party dependencies (`PyYAML`, `jsonschema`).

Open **PowerShell** on your Windows machine and run:

```powershell
# 1. Navigate to the repository root
cd "C:\Users\giphy\Cloud Project\aws-arch-recommender"

# 2. Create a clean build staging directory
$BuildDir = "$env:TEMP\lambda_build"
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null

# 3. Copy application files into the staging directory
Copy-Item -Recurse -Path "src" -Destination "$BuildDir\src"
Copy-Item -Recurse -Path "catalogue" -Destination "$BuildDir\catalogue"
Copy-Item -Recurse -Path "schemas" -Destination "$BuildDir\schemas"
Copy-Item -Recurse -Path "examples" -Destination "$BuildDir\examples"
New-Item -ItemType Directory -Path "$BuildDir\deploy" | Out-Null
Copy-Item -Path "deploy\lambda_handler.py" -Destination "$BuildDir\deploy\lambda_handler.py"

# 4. Install dependencies targeting Amazon Linux (Lambda runtime)
# Boto3 is pre-installed in AWS Lambda; install PyYAML and jsonschema
pip install PyYAML jsonschema --target $BuildDir --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12

# 5. Create the deployment zip archive
$ZipFile = "$PWD\lambda_deployment_package.zip"
if (Test-Path $ZipFile) { Remove-Item -Force $ZipFile }
Compress-Archive -Path "$BuildDir\*" -DestinationPath $ZipFile

Write-Host "Deployment package created at: $ZipFile"
```

#### B. Create the Lambda Function in AWS Console
- **Where to navigate:** AWS Console -> **Lambda** -> **Functions** -> click **Create function**.
- **Basic configuration:**
  - Select **Author from scratch**.
  - **Function name:** `aws-arch-recommender-demo-backend`
  - **Runtime:** **Python 3.12** (or **Python 3.13**).
  - **Architecture:** `x86_64`.
  - **Permissions:** Expand *Change default execution role*, select **Use an existing role**, and pick `aws-arch-recommender-demo-lambda-role`.
  - Click **Create function**.
- **Upload Code:**
  - In the **Code source** tab, click **Upload from** -> **.zip file**.
  - Select `lambda_deployment_package.zip` generated above and click **Save**.
- **Configure Runtime Settings:**
  - Scroll down to **Runtime settings** and click **Edit**.
  - Set **Handler** to: `deploy.lambda_handler.lambda_handler`
  - Click **Save**.
- **Configure General Settings:**
  - Open the **Configuration** tab -> **General configuration** -> click **Edit**.
  - **Memory:** `256 MB`
  - **Timeout:** `15 seconds` (allows deterministic schema validation and Graphviz dot parsing).
  - Click **Save**.
- **Configure Environment Variables:**
  - In the **Configuration** tab -> **Environment variables** -> click **Edit**.
  - Ensure `USE_BEDROCK` is **NOT** set (or set to `0`). Mock mode is the default.
  - Click **Save**.
- **How to verify (Test Event):**
  - Open the **Test** tab in the Lambda console.
  - Name the event: `TestEcommerce`
  - Enter JSON event payload:
    ```json
    {
      "text": "Build a scalable e-commerce application with relational database"
    }
    ```
  - Click **Test**.
  - Verify **Execution result:** shows **Status: Succeeded (HTTP 200)**.
  - Expand details to confirm JSON body contains `valid: true`, `mock_mode: true`, and the breakdown of services (`CloudFront`, `ApplicationLoadBalancer`, `EC2AutoScalingGroup`, `RDS_MultiAZ`).
- **Common failures:**
  - `Runtime.ImportModuleError: No module named 'deploy'`: The ZIP archive was created from the parent folder rather than the contents of the staging folder, or handler path is misspelled. Ensure handler is `deploy.lambda_handler.lambda_handler`.
  - `Task timed out after 3.00 seconds`: Lambda default timeout of 3s was not raised to 15s.

---

### Step 4: Create Amazon API Gateway (HTTP API)
- **Where to navigate:** AWS Console -> **API Gateway** -> click **Create API**.
- **Choose API Type:** Under **HTTP API**, click **Build**.
- **Step 1 - Create an API:**
  - Click **Add integration**.
  - Select **Lambda**.
  - Lambda function: Select `aws-arch-recommender-demo-backend`.
  - **API name:** `aws-arch-recommender-demo-api`.
  - Click **Next**.
- **Step 2 - Configure routes:**
  - **Method:** `POST`
  - **Resource path:** `/recommend`
  - **Integration target:** `aws-arch-recommender-demo-backend`
  - Click **Next**.
- **Step 3 - Define stages:**
  - Stage name: `$default` (keep **Auto-deploy** enabled).
  - Click **Next**, then click **Create**.
- **Configure CORS (Cross-Origin Resource Sharing):**
  - In the left sidebar, click **CORS**.
  - Click **Configure**.
  - **Access-Control-Allow-Origins:** `*` (or your CloudFront domain once created).
  - **Access-Control-Allow-Methods:** `POST, OPTIONS`.
  - **Access-Control-Allow-Headers:** `content-type`.
  - Click **Save**.
- **How to verify:**
  - Copy the **Invoke URL** from the API details (e.g., `https://abcdef123.execute-api.ap-south-1.amazonaws.com`).
  - Open Windows PowerShell and run:
    ```powershell
    $apiUrl = "https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/recommend"
    Invoke-RestMethod -Uri $apiUrl -Method Post -ContentType "application/json" -Body '{"text": "Build a scalable e-commerce app"}'
    ```
  - Verify that the response returns HTTP 200 with the full architecture JSON report.
- **Common failure:** Calling the base Invoke URL without the `/recommend` path suffix, resulting in a `{"message":"Not Found"}` (HTTP 404).

---

### Step 5: Create Private Amazon S3 Bucket (Frontend Host)
- **Where to navigate:** AWS Console -> **Amazon S3** -> click **Create bucket**.
- **Bucket configuration:**
  - **Bucket name:** `aws-arch-recommender-demo-frontend-<your-aws-account-id>` (must be globally unique).
  - **AWS Region:** Same region as Lambda (e.g. `ap-south-1`).
  - **Object Ownership:** Select **ACLs disabled (recommended)**.
  - **Block Public Access settings:** Keep **Block all public access** strictly **CHECKED**.
  - **Bucket Versioning:** Disabled.
  - **Default encryption:** Server-side encryption with Amazon S3-managed keys (SSE-S3).
  - Click **Create bucket**.
- **Upload Placeholder Frontend Asset:**
  - Click on the newly created bucket.
  - Click **Upload** -> upload a basic `index.html` file (e.g., `<!DOCTYPE html><html><body><h1>AWS Arch Recommender Frontend</h1></body></html>`).
  - Click **Upload**.
- **How to verify:**
  - Check the bucket properties. Confirm **Public access:** displays `Bucket and objects not public`.
- **Common failure:** Unchecking "Block all public access" to try to make it work. S3 must remain completely private; CloudFront will access it securely via OAC.

---

### Step 6: Create Amazon CloudFront Distribution with Origin Access Control (OAC)
- **Where to navigate:** AWS Console -> **CloudFront** -> click **Create distribution**.
- **Origin configuration:**
  - **Origin domain:** Click the text box and select your S3 bucket: `aws-arch-recommender-demo-frontend-<account-id>.s3.ap-south-1.amazonaws.com`.
  - **Origin access:** Select **Origin access control settings (recommended)**.
  - Click **Create control setting**:
    - Name: `aws-arch-recommender-demo-oac`
    - Origin type: **S3**
    - Signing behavior: **Sign requests (recommended)**
    - Click **Create**.
- **Default cache behavior:**
  - **Viewer protocol policy:** Select **Redirect HTTP to HTTPS**.
  - **Allowed HTTP methods:** `GET, HEAD`.
  - **Cache key and origin requests:** Select **Cache policy: CachingOptimized**.
- **Settings:**
  - **Default root object:** Enter `index.html`.
  - **Price class:** `Use only North America and Europe` or `Use all edge locations` (Mumbai is in all locations).
  - Click **Create distribution**.
- **Configure S3 Bucket Policy for CloudFront OAC:**
  - A prominent yellow banner appears in CloudFront: *"The S3 bucket policy needs to be updated..."*
  - Click **Copy policy**.
  - Navigate to **Amazon S3** -> your bucket -> **Permissions** tab -> **Bucket policy** -> click **Edit**.
  - Paste the policy generated by CloudFront. It resembles:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": {
        "Sid": "AllowCloudFrontServicePrincipalReadOnly",
        "Effect": "Allow",
        "Principal": {
          "Service": "cloudfront.amazonaws.com"
        },
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::aws-arch-recommender-demo-frontend-<account-id>/*",
        "Condition": {
          "StringEquals": {
            "AWS:SourceArn": "arn:aws:cloudfront::<account-id>:distribution/<distribution-id>"
          }
        }
      }
    }
    ```
  - Click **Save changes**.
- **How to verify:**
  - Wait for the CloudFront distribution status to show **Enabled** (Last modified timestamp updates).
  - Copy the **Distribution domain name** (e.g., `https://d12345abcdef.cloudfront.net`).
  - Open the URL in a browser. Confirm that the `index.html` page renders securely over HTTPS.
- **Common failure:** Forgetting to update the S3 bucket policy after creating the CloudFront distribution, resulting in an `AccessDenied` (HTTP 403) error when browsing to the CloudFront URL.

---

### Step 7: Configure CloudWatch Monitoring & Troubleshooting
- **Where to navigate:** AWS Console -> **CloudWatch** -> **Log groups**.
- **Locate Log Group:** Find `/aws/lambda/aws-arch-recommender-demo-backend`.
- **Set Retention Policy:**
  - Select the log group -> click **Actions** -> **Edit retention setting**.
  - Change retention from *Never expire* to **7 days** (prevents ongoing storage costs for demo logs).
  - Click **Save**.
- **Troubleshooting Verification:**
  - **Successful invocation:** Open the latest log stream. You should see `START RequestId...`, memory usage, and `REPORT RequestId... Duration: ~100 ms Billed Duration: ~100 ms`.
  - **Simulated failure check:** Trigger a test event in Lambda with empty text: `{"text": ""}`.
  - Verify that the log stream records an HTTP 400 rejection: `Field 'text' cannot be empty or whitespace` without an unhandled stack trace or crash.

---

## 4. Pipeline Integration & Mock Mode Behavior

### Actual Imports & Module Resolution
The Lambda handler imports directly from the existing repository modules:
- `aws_arch.common.load_json`, `aws_arch.common.ROOT`
- `aws_arch.pipeline.run_downstream`

When packaged, the ZIP file preserves the relative directory structure expected by `common.py`:
- `schemas/*.schema.json`
- `catalogue/*.yaml`
- `examples/*.json`

### Writable Storage in Lambda
In AWS Lambda, only the `/tmp` directory is writable. The handler creates an isolated temporary directory via Python's `tempfile.TemporaryDirectory()` inside `/tmp` for `run_downstream` to write `report.json` and `diagram.dot`, ensuring full execution compatibility without modifying read-only root files.

### Mock Mode vs. Dynamic Parsing
- **Default Mock Mode:** Returns the validated canonical e-commerce reference architecture. The input prompt is validated for presence and string type, but arbitrary natural language requirements are not parsed by an LLM in mock mode.
- **Bedrock Integration Status:** In this serverless release, `USE_BEDROCK=1` returns **HTTP 501 Not Implemented**. Upstream `src/aws_arch/llm.py` contains hardcoded model IDs (`REPLACE_WITH_BEDROCK_MODEL_ID`) and attempts to write to a cache directory at the package root (`/var/task/.cache`), which is read-only in Lambda. Enabling live Bedrock invocation requires future upstream refactoring to support dynamic model configuration and redirecting cache storage to `/tmp`.

---

## 5. Cost Transparency & Teardown Guide

### Potential Incurred Charges
Even when running a lightweight demo, charges can accumulate across services:
- **CloudFront:** First 1 TB DTO is Free Tier eligible; regional edge requests after free tier incur standard request rates.
- **Amazon S3:** Storage is charged per GB-month; GET/PUT requests incur standard API fees once Free Tier expires.
- **API Gateway:** HTTP APIs charge \$1.00 per million requests after the initial 12-month Free Tier (1M requests/mo).
- **AWS Lambda:** 1M free requests and 3.2M seconds of compute time per month on the AWS Free Tier.
- **DynamoDB:** 25 GB of storage and 25 write/read capacity units are free under Always Free tier.
- **CloudWatch:** 5 GB log ingestion and 5 GB archival are free; excess log volume is billed per GB.

> [!NOTE]
> **Estimator Disclaimer:** Estimates generated by the AWS Architecture Recommender are conservative, order-of-magnitude architectural projections based on Mumbai regional pricing. They are **not** billing guarantees or credit agreements. Always review official AWS Pricing pages before deploying production workloads.

---

### Ordered Teardown Sequence (Prevent Orphaned Costs)
To completely remove all demo resources and ensure zero residual charges, execute this cleanup checklist in the exact order specified:

```
1. Disable & Delete CloudFront Distribution
   └─ Reason: Deleting the CDN first prevents new incoming web requests.
      Action: CloudFront -> Select 'aws-arch-recommender-demo-cdn' -> Disable -> Wait for disabled status -> Delete.

2. Delete API Gateway HTTP API
   └─ Reason: Stops backend request routing.
      Action: API Gateway -> Select 'aws-arch-recommender-demo-api' -> Actions -> Delete.

3. Delete AWS Lambda Function
   └─ Reason: Stops execution compute.
      Action: Lambda -> Select 'aws-arch-recommender-demo-backend' -> Actions -> Delete.

4. Empty and Delete S3 Frontend Bucket
   └─ Reason: S3 buckets cannot be deleted until completely empty.
      Action: S3 -> Select bucket -> Click 'Empty' -> Confirm -> Click 'Delete' -> Confirm.

5. Delete DynamoDB History Table
   └─ Reason: Removes demo database storage.
      Action: DynamoDB -> Select 'aws-arch-recommender-demo-history' -> Delete table.

6. Delete CloudWatch Log Group
   └─ Reason: Removes archived execution logs.
      Action: CloudWatch -> Log groups -> Select '/aws/lambda/aws-arch-recommender-demo-backend' -> Delete log group.

7. Delete IAM Execution Role
   └─ Reason: Removes demo access credentials.
      Action: IAM -> Roles -> Select 'aws-arch-recommender-demo-lambda-role' -> Delete.

8. Delete AWS Budget Alert (Optional)
   └─ Action: AWS Budgets -> Select 'aws-arch-recommender-demo-budget' -> Delete.
```

#### Final Teardown Verification Check
Run the following PowerShell check using AWS CLI (if installed) or inspect the console to confirm that zero demo resources remain:
- **CloudFront:** Distribution list contains no distributions with comment `aws-arch-recommender-demo`.
- **Lambda:** `Get-LMFunction -FunctionName aws-arch-recommender-demo-backend` returns `ResourceNotFoundException`.
- **S3:** Bucket list contains no bucket matching `aws-arch-recommender-demo-frontend-*`.
- **DynamoDB:** Table list contains no table named `aws-arch-recommender-demo-history`.

---

## 6. Optional VPC Architectural Variant (Enterprise Design)

For enterprise environments requiring isolated network perimeters, the backend Lambda can be deployed within an **Amazon VPC** without a costly NAT Gateway.

### Architecture Layout
```
[Private Subnet A] ──┐
                     ├─> [Lambda: Recommender] ──> [Security Group: Lambda-Egress]
[Private Subnet B] ──┘                                   │
                                                         ├─> Gateway VPC Endpoint ──> Amazon S3
                                                         ├─> Gateway VPC Endpoint ──> Amazon DynamoDB
                                                         └─> Interface VPC Endpoint ──> AWS Bedrock
```

### Key Considerations & VPC Endpoints
1. **Private Subnets:** Lambda is associated with private subnets across at least two Availability Zones (AZs) for high availability.
2. **Security Groups:**
   - Lambda Security Group: Allow outbound HTTPS (TCP 443) to the VPC CIDR or specific Endpoint Security Groups. No inbound rules required.
3. **Gateway VPC Endpoints (S3 & DynamoDB):**
   - **Cost:** **Free** (no hourly charge, no data processing fees).
   - **Configuration:** Attached directly to private route tables via prefix lists.
   - S3 endpoint allows fetching pipeline schemas and templates; DynamoDB endpoint allows saving recommendations.
4. **Interface VPC Endpoints (AWS PrivateLink for Bedrock):**
   - **Cost:** **Billed hourly** (~$0.01/AZ-hour, roughly ~$7.20/month per AZ) plus data processing charges.
   - **Configuration:** Required if private Lambda needs to call the Amazon Bedrock API without public internet routing.
5. **Why No NAT Gateway?**
   - A single NAT Gateway costs ~$32.85/month in `ap-south-1` plus data processing fees, and high availability across two AZs doubles that cost to ~$65.70/month.
   - Using VPC Endpoints eliminates NAT Gateway costs while maintaining a 100% private network perimeter.
6. **Critical Trade-Off:**
   - Without a NAT Gateway, the Lambda function has **no access to the public internet**. Any external service, package repository, or API that lacks a VPC Endpoint in your VPC cannot be reached.
