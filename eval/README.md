# Evaluation Harness

Owner: Person A (`eval/`). Measures recommender accuracy, precision, validity, and compliance against ground-truth scenarios.

## Execution
```bash
# Mock mode (using canned outputs, no AWS required):
python eval/run_eval.py --mock-llm

# Live mode (running against real Bedrock pipeline):
python eval/run_eval.py --live
```

## Metric Formulas
1. **Service Selection Accuracy (Recall):**
   $$\text{Accuracy} = \frac{|\text{Expected Services} \cap \text{Recommended Services}|}{|\text{Expected Services}|}$$
   Measures what percentage of essential reference architecture components were correctly identified.
2. **Service Precision:**
   $$\text{Precision} = \frac{|\text{Expected Services} \cap \text{Recommended Services}|}{|\text{Recommended Services}|}$$
   Measures whether the model avoids over-recommending irrelevant or superfluous services.
3. **Pattern Match:**
   $$1 \text{ if } \text{actual\_pattern} == \text{expected\_pattern} \text{ else } 0$$
   Checks if the selected high-level architectural pattern strictly matches the reference design.
4. **Architecture Validity Rate:**
   $$1 \text{ if } \text{validate\_architecture(arch)} == [] \text{ else } 0$$
   Evaluates strict compliance with allow-lists, connection targets, and absence of orphaned components.
5. **Security Check Pass Rate:**
   $$\text{Pass Rate} = \frac{\text{Number of Passed Security Checks}}{\text{Total Security Checks Evaluated}}$$
   Percentage of Well-Architected baseline security checks satisfied by the recommendation.

## Outputs
- `output/eval_results.csv`: Machine-readable per-scenario evaluation metrics.
- `output/eval_results.md`: Markdown summary table suitable for presentation slides and project reports.
