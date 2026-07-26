"""Universal Dual-Layer Fact Extraction Pipeline for open-research-lite."""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from open_research_lite.knowledge_graph import FactAssertion

logger = logging.getLogger("open_research_lite.extractor")


class ExtractedFactItem(BaseModel):
    subject: str = Field(description="Normalized entity or topic name")
    predicate: str = Field(description="Relationship, verb, or property name")
    object_val: str = Field(description="Target entity, value, stat, or status")
    is_numeric: bool = Field(default=False, description="True if value contains numbers, dates, or metrics")
    context_snippet: str = Field(default="", description="Original sentence snippet containing this fact")


class ExtractedFactsPayload(BaseModel):
    facts: List[ExtractedFactItem]


class UniversalLocalNLPParser:
    UNIVERSAL_METRIC_REGEX = re.compile(
        r'('
        r'\b[\$\€\£\¥]\s*\d+(?:\.\d+)?(?:\s*(?:billion|million|trillion|k|M|B|T))?\b'
        r'|\b\d+(?:\.\d+)?\s*(?:Wh/kg|kWh|Wh|MW|GW|TW|GHz|MHz|nm|mm|cm|m|km|miles|kg|lbs|tons|GB|TB|PB|MB/s|GB/s|ms|sec|min|hrs|percent|%)\b'
        r'|\b\d+(?:\.\d+)?\s*(?:x|x-speedup|times|fold|ratio|x-improvement)\b'
        r'|\b(?:Q[1-4]\s*\d{4}|\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b'
        r'|\b\d+(?:\.\d+)?\s*to\s*\d+(?:\.\d+)?\b'
        r')',
        re.IGNORECASE
    )

    BOILERPLATE_PATTERNS = [
        re.compile(r'Accept All Cookies.*', re.IGNORECASE),
        re.compile(r'Privacy Policy|Terms of Service|Terms of Use|All Rights Reserved|Cookie Preferences', re.IGNORECASE),
        re.compile(r'Subscribe to newsletter|Sign up for updates|Follow us on Twitter|Share on Facebook', re.IGNORECASE),
        re.compile(r'Skip to main content|Navigation menu|Toggle navigation', re.IGNORECASE),
        re.compile(r'<script.*?>.*?</script>', re.DOTALL | re.IGNORECASE),
        re.compile(r'<style.*?>.*?</style>', re.DOTALL | re.IGNORECASE),
        re.compile(r'<.*?>', re.DOTALL)
    ]

    UNIVERSAL_VERBS = {
        "achieves", "achieved", "reaches", "reached", "demonstrates", "demonstrated",
        "announces", "announced", "targets", "targeted", "produces", "produced",
        "costs", "cost", "yields", "yielded", "features", "featured", "launches",
        "launched", "develops", "developed", "scales", "scaled", "claims", "claimed",
        "states", "stated", "reports", "reported", "is", "are", "was", "were",
        "exceeds", "exceeded", "begins", "began", "shows", "showed", "proves",
        "proved", "indicates", "indicated", "increases", "increased", "decreases",
        "decreased", "found", "finds", "discovers", "discovered", "publishes", "published"
    }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text
        for pat in self.BOILERPLATE_PATTERNS:
            cleaned = pat.sub(' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def extract_facts(
        self, 
        text: str, 
        source_url: str = "", 
        source_title: str = "",
        max_sentences: int = 35
    ) -> List[FactAssertion]:
        cleaned = self.clean_text(text)
        if len(cleaned) < 20:
            return []

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 15]
        facts: List[FactAssertion] = []
        seen_keys = set()

        for sentence in sentences[:max_sentences]:
            has_metric = bool(self.UNIVERSAL_METRIC_REGEX.search(sentence))
            triplets = self._parse_sentence_triplets(sentence)
            
            for subject, predicate, obj in triplets:
                key = f"{subject.lower()}:{predicate.lower()}:{obj.lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    facts.append(FactAssertion(
                        subject=subject,
                        predicate=predicate,
                        object_val=obj,
                        is_numeric=has_metric,
                        source_url=source_url,
                        source_title=source_title,
                        context_snippet=sentence[:150]
                    ))
        return facts

    def _parse_sentence_triplets(self, sentence: str) -> List[Tuple[str, str, str]]:
        results = []
        clauses = [c.strip() for c in re.split(r'[,;]\s+', sentence) if len(c.strip()) > 15]
        if not clauses:
            clauses = [sentence]

        for clause in clauses:
            words = clause.split()
            if len(words) < 3:
                continue

            found_verb_idx = -1
            found_verb = "states"

            for i, word in enumerate(words):
                clean_word = re.sub(r'\W+', '', word.lower())
                if clean_word in self.UNIVERSAL_VERBS:
                    found_verb_idx = i
                    found_verb = word
                    break

            if found_verb_idx > 0 and found_verb_idx < len(words) - 1:
                subject = " ".join(words[:found_verb_idx])
                obj = " ".join(words[found_verb_idx + 1:])
            else:
                subject = " ".join(words[:min(3, len(words))])
                obj = " ".join(words[min(3, len(words)):])

            subject = re.sub(r'^[^\w]+|[^\w]+$', '', subject).strip()
            obj = re.sub(r'^[^\w]+|[^\w]+$', '', obj).strip()

            if len(subject) >= 2 and len(obj) >= 2:
                results.append((subject[:50], found_verb[:30], obj[:90]))

        return results


class DualExtractionPipeline:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: str = "gemini-2.5-flash",
        provider: str = "google"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.provider = provider
        self.local_extractor = UniversalLocalNLPParser()

    async def extract_facts(
        self, 
        raw_text: str, 
        source_url: str = "", 
        source_title: str = "",
        max_chars: int = 10000
    ) -> List[FactAssertion]:
        text_snippet = raw_text[:max_chars]

        if self.api_key:
            try:
                if "openai" in self.provider.lower() or "gpt" in self.model_name.lower():
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(
                        model=self.model_name,
                        api_key=self.api_key,
                        temperature=0.0
                    ).with_structured_output(ExtractedFactsPayload)
                else:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    llm = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        google_api_key=self.api_key,
                        temperature=0.0
                    ).with_structured_output(ExtractedFactsPayload)

                prompt = (
                    "Extract all unique, high-signal atomic facts, metrics, breakthrough claims, dates, and prices from the text.\n"
                    "Ignore introductory background fluff, company history, navigation text, or basic definitions.\n"
                    "Output a clean array of Subject-Predicate-Object triplets.\n\n"
                    f"SOURCE TITLE: {source_title}\n"
                    f"TEXT:\n{self.local_extractor.clean_text(text_snippet)}\n"
                )

                res: ExtractedFactsPayload = await llm.ainvoke(prompt)
                
                assertions = []
                for item in res.facts:
                    assertions.append(FactAssertion(
                        subject=item.subject.strip(),
                        predicate=item.predicate.strip(),
                        object_val=item.object_val.strip(),
                        is_numeric=item.is_numeric,
                        source_url=source_url,
                        source_title=source_title,
                        context_snippet=item.context_snippet.strip()
                    ))
                return assertions
            except Exception as e:
                logger.warning(f"Layer 1 (LLM) failed: {e}. Falling back to Layer 2.")

        return self.local_extractor.extract_facts(text_snippet, source_url, source_title)
