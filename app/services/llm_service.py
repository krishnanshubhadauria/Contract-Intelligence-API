import os
from typing import Dict, List, Any, Optional, AsyncIterator
from openai import OpenAI, AsyncOpenAI
from app.core.config import settings

class LLMService:
    def __init__(self):
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
            self.async_client = None
    
    def _get_model(self) -> str:
        """Get the LLM model to use"""
        return "gpt-4-turbo-preview" if self.client else "gpt-3.5-turbo"
    
    async def extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract structured fields from contract text"""
        if not self.client:
            # Fallback to basic extraction
            return self._basic_extraction(text)
        
        prompt = f"""Extract the following structured information from this contract text. Return a JSON object with these fields:
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
{text[:8000]}

Return only valid JSON, no markdown formatting."""

        try:
            response = self.client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": "You are a contract analysis expert. Extract structured information from contracts and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return self._basic_extraction(text)
    
    def _basic_extraction(self, text: str) -> Dict[str, Any]:
        """Basic rule-based extraction fallback"""
        result = {
            "parties": [],
            "effective_date": None,
            "term": None,
            "governing_law": None,
            "payment_terms": None,
            "termination": None,
            "auto_renewal": None,
            "confidentiality": None,
            "indemnity": None,
            "liability_cap": None,
            "signatories": []
        }
        
        # Simple keyword-based extraction
        text_lower = text.lower()
        if "auto" in text_lower and "renew" in text_lower:
            result["auto_renewal"] = True
        
        return result
    
    async def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on context"""
        if not self.client:
            return "LLM service not configured. Please set OPENAI_API_KEY."
        
        prompt = f"""Answer the following question based only on the provided contract context. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": "You are a contract analysis assistant. Answer questions based only on the provided contract text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    async def answer_question_stream(self, question: str, context: str) -> AsyncIterator[str]:
        """Stream answer tokens"""
        if not self.async_client:
            yield "LLM service not configured. Please set OPENAI_API_KEY."
            return
        
        prompt = f"""Answer the following question based only on the provided contract context. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        try:
            stream = await self.async_client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": "You are a contract analysis assistant. Answer questions based only on the provided contract text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def audit_contract(self, text: str, extracted_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Audit contract for risky clauses"""
        findings = []
        
        # Check auto-renewal with short notice
        if extracted_fields.get("auto_renewal"):
            text_lower = text.lower()
            # Look for notice periods
            if "30" in text and "day" in text_lower:
                # Check if it's less than 30 days
                import re
                notice_pattern = r'(\d+)\s*(?:day|days|d)'
                matches = re.findall(notice_pattern, text_lower)
                for match in matches:
                    if int(match) < 30:
                        findings.append({
                            "severity": "high",
                            "category": "auto_renewal",
                            "description": f"Auto-renewal with only {match} days notice",
                            "evidence": self._find_evidence(text, "auto", "renew"),
                            "char_range": None,
                            "page": None
                        })
                        break
        
        # Check for unlimited liability
        text_lower = text.lower()
        if "unlimited" in text_lower and "liability" in text_lower:
            findings.append({
                "severity": "high",
                "category": "liability",
                "description": "Unlimited liability clause detected",
                "evidence": self._find_evidence(text, "unlimited", "liability"),
                "char_range": None,
                "page": None
            })
        
        # Check liability cap
        liability_cap = extracted_fields.get("liability_cap")
        if liability_cap and isinstance(liability_cap, dict):
            amount = liability_cap.get("amount", 0)
            if amount == 0 or amount is None:
                findings.append({
                    "severity": "medium",
                    "category": "liability",
                    "description": "No liability cap specified",
                    "evidence": "Liability cap field is null or zero",
                    "char_range": None,
                    "page": None
                })
        
        # Check broad indemnity
        indemnity = extracted_fields.get("indemnity", "")
        if indemnity and isinstance(indemnity, str):
            indemnity_lower = indemnity.lower()
            if any(word in indemnity_lower for word in ["all", "any", "every", "unlimited"]):
                findings.append({
                    "severity": "high",
                    "category": "indemnity",
                    "description": "Broad indemnity clause detected",
                    "evidence": indemnity[:200],
                    "char_range": None,
                    "page": None
                })
        
        # Use LLM for more sophisticated checks
        if self.client:
            llm_findings = await self._llm_audit(text, extracted_fields)
            findings.extend(llm_findings)
        
        return findings
    
    async def _llm_audit(self, text: str, extracted_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM for additional audit checks"""
        prompt = f"""Analyze this contract for risky clauses. Check for:
1. Auto-renewal with less than 30 days notice
2. Unlimited liability
3. Broad indemnity clauses
4. Unfavorable termination terms
5. Missing confidentiality protections

Contract text (first 8000 chars):
{text[:8000]}

Extracted fields:
{extracted_fields}

Return a JSON array of findings, each with:
- severity: "high", "medium", or "low"
- category: string describing the category
- description: string describing the issue
- evidence: string with relevant text excerpt

Return only valid JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": "You are a contract risk analyst. Identify risky clauses and return JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            findings = result.get("findings", [])
            return findings
        except Exception as e:
            print(f"LLM audit error: {e}")
            return []
    
    def _find_evidence(self, text: str, *keywords: str) -> str:
        """Find evidence text containing keywords"""
        text_lower = text.lower()
        for i, line in enumerate(text.split('\n')):
            line_lower = line.lower()
            if all(kw in line_lower for kw in keywords):
                # Return context around the line
                lines = text.split('\n')
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                return '\n'.join(lines[start:end])
        return "Evidence not found in text"

