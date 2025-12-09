### Extraction prompt (LLM)
```
Extract the following structured information from this contract text. Return a JSON object with these fields:
- parties: array of objects with "name" and "role" (e.g., "Buyer", "Seller", "Licensor", "Licensee")
- effective_date: string date
- term: string describing the contract term/duration
- governing_law: string describing governing law/jurisdiction
- payment_terms: string describing payment terms
- termination: string describing termination conditions
- auto_renewal: boolean indicating if contract auto-renews
- confidentiality: string describing confidentiality obligations
- indemnity: string describing indemnity provisions
- liability_cap: object with "amount" (number) and "currency" (string) if there's a liability cap, null otherwise
- signatories: array of objects with "name" and "title"

Contract text:
{{contract_text_first_8k}}

Return only valid JSON, no markdown formatting.
```

Rationale: Structured fields with strict JSON output enables deterministic parsing. The 8k char window balances coverage and token cost.


