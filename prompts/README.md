# Few-shot Prompt Examples

Owner: Person A (`prompts/`). Loaded by `src/aws_arch/parser.py` and `src/aws_arch/reasoner.py`.

## Content & Coverage
Both `parser_examples.json` and `reasoner_examples.json` contain 4 canonical AWS architectural patterns:
1. **Three-Tier Web Application** (`three_tier_web`): CloudFront -> ALB -> EC2AutoScalingGroup -> RDS_MultiAZ
2. **Serverless REST API** (`serverless_rest_api`): APIGateway -> Lambda -> DynamoDB (+ Cognito)
3. **Static Content Site** (`static_site_cdn`): CloudFront -> S3 (with OAC)
4. **Batch / Asynchronous Pipeline** (`batch_pipeline`): S3, SQS -> Lambda -> DynamoDB

## Validation Rules
- Every service referenced in `reasoner_examples.json` is strictly allow-listed in `catalogue/catalogue.yaml`.
- Every connection between services is valid per the source service's `allowed_targets` in `catalogue/catalogue.yaml`.
- All examples conform to `schemas/requirement.schema.json` and `schemas/architecture.schema.json`.
- Enforced by unit tests in `tests/test_prompts.py`.
