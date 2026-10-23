# Few-shot examples

Owner: Person A. Files are loaded by `parser.py` / `reasoner.py` (the only LLM modules). Both start as `[]`.

## `parser_examples.json`
```json
[
  {
    "input": "free-text requirement (example only, treated as data)",
    "output": { "...": "a Requirement JSON valid against schemas/requirement.schema.json" }
  }
]
```

## `reasoner_examples.json`
```json
[
  {
    "requirements": { "...": "Requirement JSON" },
    "architecture": { "...": "Architecture JSON valid against schemas/architecture.schema.json, services only from catalogue/catalogue.yaml" }
  }
]
```

Rules: every `output`/`architecture` must pass schema + validator; no invented services or prices; no credentials.
