### Audit prompt (LLM)
```
Analyze this contract for risky clauses. Check for:
1. Auto-renewal with less than 30 days notice
2. Unlimited liability
3. Broad indemnity clauses
4. Unfavorable termination terms
5. Missing confidentiality protections

Contract text (first 8000 chars):
{{contract_text_first_8k}}

Extracted fields:
{{extracted_fields}}

Return a JSON array of findings, each with:
- severity: "high", "medium", or "low"
- category: string describing the category
- description: string describing the issue
- evidence: string with relevant text excerpt

Return only valid JSON array.
```

Rationale: Targets concrete risk patterns, constrains output to JSON array for predictable parsing.


