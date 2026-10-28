# Slide 6: Experimental Evaluation & Benchmark Metrics

## Slide Title
**Empirical Evaluation Harness: Accuracy, Precision & Compliance**

## Key Bullet Points
- **Automated Evaluation Harness (`eval/run_eval.py`)**: Runs reproducible tests over hand-curated reference architecture scenarios.
- **Quantitative Metrics**:
  - **Service Selection Accuracy (Recall)**: $\frac{|\text{Expected} \cap \text{Recommended}|}{|\text{Expected}|}$
  - **Service Precision**: $\frac{|\text{Expected} \cap \text{Recommended}|}{|\text{Recommended}|}$
  - **Pattern Match %**: Exact classification against reference patterns (`three_tier_web`, `serverless_rest_api`, etc.)
  - **Architecture Validity Rate**: Percentage of generated graphs passing all graph connection & allow-list rules without orphans.
  - **Well-Architected Security Compliance**: Percentage of deterministic security and reliability baseline checks passed.
- **Reporting**: Automated generation of `output/eval_results.csv` and Markdown evaluation tables.

## Speaker Notes
To evaluate our architecture recommendations rigorously, we constructed an automated benchmarking harness. Using hand-curated reference architectures derived from official AWS Whitepapers as our ground truth, we test across diverse archetypes including three-tier web applications, serverless REST APIs, and static global CDNs. We track both Service Selection Recall (did it recommend all required core services?) and Precision (did it avoid recommending unnecessary services?). Furthermore, our harness validates graph connectivity and security compliance rates, recording timing and token metrics into CSV and Markdown tables to demonstrate continuous pipeline quality.

## Anticipated Examiner Questions
- **Q1: How do you establish your ground truth for evaluation?**
  *Answer:* Ground truth scenarios are authored directly from published AWS Well-Architected Reference Architectures and AWS Architecture Center blueprints, which specify official recommended services for standard application patterns.
- **Q2: What is the difference between service accuracy and service precision in your metrics?**
  *Answer:* Accuracy (Recall) measures whether the system identified all the necessary services for the workload. Precision measures whether the system kept the recommendation clean without cluttering it with irrelevant or bloated services.
