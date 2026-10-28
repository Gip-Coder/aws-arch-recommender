# Topic 1: IAM and Least Privilege

**Presentation Section:** Security & Identity Architecture
**Objective:** Explain how AWS Identity and Access Management (IAM) governs authentication and authorization, how least privilege applies to the proposed serverless recommender deployment, and how credential safety is enforced.

---

## Slide 1: Fundamentals of AWS IAM in Cloud Systems

### Key Points
- Core entities: IAM Users (human operators), Roles (assumed by services/entities), and Policies (JSON permission documents).
- Authentication validates identity; Authorization evaluates IAM policies to grant or deny specific API actions.
- Explicit Deny overrides all Allow statements in IAM policy evaluation logic.
- Least-privilege principle: identities receive only the minimum permissions required for their specific function.

### Speaker Notes
Identity and Access Management is the fundamental security perimeter in AWS, governing every control plane and data plane interaction. In enterprise cloud design, human operators should rarely hold long-term static credentials; instead, applications and serverless components assume scoped IAM roles via the AWS Security Token Service. Permissions are declared through declarative JSON policy documents using the Effect, Action, Resource, and Condition model. Enforcing least privilege at this layer ensures that even if an application tier experiences a vulnerability, the potential blast radius is strictly constrained to authorized actions.

### Questions an Examiner May Ask
**Q1. What is the fundamental difference between an IAM Role and an IAM User?**

Answer: An IAM User is an identity with long-term credentials (password or access keys) intended for a specific person or legacy service. An IAM Role has no permanent credentials and is assumed dynamically by authorized entities or services to obtain temporary, auto-rotating security tokens via AWS STS.

**Q2. How does IAM evaluate permissions when multiple policies are attached?**

Answer: IAM defaults to an implicit deny for all requests. An action is allowed only if an explicit Allow exists and no explicit Deny applies; any explicit Deny statement in any applicable policy immediately overrides all allows.

---

## Slide 2: Least-Privilege Execution in Serverless Architectures

### Key Points
- Serverless compute (AWS Lambda) executes under an assumed IAM Execution Role.
- Baseline deployment role: `aws-arch-recommender-demo-lambda-role` attached exclusively to `AWSLambdaBasicExecutionRole`.
- Permitted actions restricted to CloudWatch Logs: `logs:CreateLogGroup`, `logs:CreateLogStream`, and `logs:PutLogEvents`.
- Avoids anti-patterns: No broad `AdministratorAccess`, `*.*` actions, or unneeded S3/DynamoDB permissions.

### Speaker Notes
In our proposed serverless deployment design, the AWS Lambda execution engine adheres strictly to least-privilege principles. The baseline execution role attaches only the AWS-managed `AWSLambdaBasicExecutionRole`, granting only the permissions needed to write standard execution logs to Amazon CloudWatch. We intentionally avoid the common anti-pattern of assigning administrative access or broad data permissions to a compute component before those features are implemented. This guarantees that the serverless engine can execute its core recommendation pipeline without possessing authority to access unrelated AWS account resources.

### Questions an Examiner May Ask
**Q1. Why should a Lambda execution role omit permissions for services it does not currently call?**

Answer: Following the principle of least privilege, granting unneeded permissions expands the potential blast radius if the function or its dependencies are compromised. Permissions should only be added incrementally as concrete features are implemented.

**Q2. How is the execution role assumed by the Lambda service?**

Answer: The IAM role defines a Trust Policy specifying `lambda.amazonaws.com` as the trusted service principal authorized to perform the `sts:AssumeRole` action.

---

## Slide 3: Credential Safety & Environment Boundaries

### Key Points
- Zero hard-coded credentials in source code, configuration files, or Git history.
- The repository's `AGENTS.md` explicitly mandates environment variables or AWS credential provider chains.
- Stateless execution: The pipeline accepts untrusted user input without storing access keys or sensitive tokens.
- Separation of concerns: Public web clients authenticate via HTTPS without requiring AWS account credentials.

### Speaker Notes
A core architectural requirement of this project is strict credential safety. The project rules in `AGENTS.md` forbid committing API keys, secret keys, or passwords to Git, and automated scanning is integrated into verification workflows. When running locally, the pipeline relies on the standard AWS credential chain or runs completely offline in mock mode. In the proposed cloud deployment, end users interact with the system via public HTTPS endpoints (Amazon CloudFront and API Gateway) without possessing or handling AWS credentials, isolating internal cloud resources from the public internet.

### Questions an Examiner May Ask
**Q1. What is the AWS Default Credential Provider Chain?**

Answer: It is an automated lookup order used by the AWS SDK (Boto3) to locate credentials, searching environment variables (`AWS_ACCESS_KEY_ID`), shared configuration files (`~/.aws/credentials`), and finally instance/container metadata (EC2 metadata or Lambda execution role tokens).

**Q2. How does the architecture prevent prompt injection or untrusted input from escalating privileges?**

Answer: The system treats user input strictly as raw data rather than instructions. Because the downstream pipeline runs as isolated Python logic with fixed capabilities, an input string cannot alter IAM permissions or execute unauthorized AWS API calls.

---

## Slide 4: Scoping Permissions for Optional Integrations

### Key Points
- Proposed integrations (Bedrock live inference, DynamoDB history) require explicit, incremental IAM policy grants.
- Amazon Bedrock access: Scoped strictly to `bedrock:InvokeModel` on the specific foundation model ARN.
- Amazon DynamoDB access: Scoped strictly to `dynamodb:PutItem` and `dynamodb:GetItem` on the history table ARN.
- Status disclosure: These permissions are proposed deployment specifications and are not active in the baseline demo release.

### Speaker Notes
As the recommender system expands from its offline baseline to cloud-native operations, additional IAM permissions must be granted deliberately and conditionally. For live LLM reasoning, the Lambda execution role would require `bedrock:InvokeModel` restricted to the chosen foundation model ARN in `ap-south-1`. For persistent audit logging, `dynamodb:PutItem` would be granted exclusively on the `aws-arch-recommender-demo-history` table ARN. In our presentation, we emphasize that these permissions represent proposed future deployment configurations, ensuring examiners understand that unimplemented features are not falsely claimed as active.

### Questions an Examiner May Ask
**Q1. Why should the Resource field in an IAM policy contain a specific ARN instead of `*`?**

Answer: Restricting the Resource element to specific ARNs (such as a single DynamoDB table or Bedrock model) prevents the identity from accessing or modifying other resources of the same type across the AWS account.

**Q2. Does the current baseline demo release require active DynamoDB or Bedrock IAM permissions?**

Answer: No. The baseline demo executes offline in mock mode using deterministic local validation and example files, requiring zero active AWS IAM permissions or cloud API calls.
