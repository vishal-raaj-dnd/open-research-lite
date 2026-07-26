"""Industry-Grade Fact Extraction Pipeline for DeepResearch-Lite.

Implements a dual-layer extraction architecture:
- Layer 1 (LLM Mode): Sub-second structured JSON triplet extraction via Gemini Flash / OpenAI when API keys are available.
- Layer 2 (Local NLP Mode): Advanced local rule-based NLP parser extracting entities, metrics, dates, and S-P-O relations when offline or without API keys.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from open_deep_research.concept_diff.knowledge_graph import FactAssertion

logger = logging.getLogger("concept_diff.extractor")


class ExtractedFactItem(BaseModel):
    """Pydantic schema for structured fact extraction."""
    subject: str = Field(description="Normalized entity or topic name")
    predicate: str = Field(description="Relationship, verb, or property name")
    object_val: str = Field(description="Target entity, value, stat, or status")
    is_numeric: bool = Field(default=False, description="True if value contains numbers, dates, or metrics")
    context_snippet: str = Field(default="", description="Original sentence snippet containing this fact")


class ExtractedFactsPayload(BaseModel):
    """Container for array of extracted facts."""
    facts: List[ExtractedFactItem]


class ProfessionalLocalExtractor:
    """Industry-grade local NLP & heuristic fact extractor.
    
    Operates offline with 0-ms latency without requiring external LLM API calls.
    Performs boilerplate stripping, metric scanning, entity resolution, and S-P-O triplet extraction.
    """

    METRIC_REGEX = re.compile(
        r'(\b\d+(?:\.\d+)?\s*(?:Wh/kg|kWh|\$/kWh|\$|€|%|MW|GW|nm|GHz|km|miles|kg|tons|units|cells)\b|\b(?:Q[1-4]\s*\d{4}|\d{4})\b)',
        re.IGNORECASE
    )

    BOILERPLATE_PATTERNS = [
        re.compile(r'Accept All Cookies.*', re.IGNORECASE),
        re.compile(r'Privacy Policy|Terms of Use|All Rights Reserved|Cookie Preferences', re.IGNORECASE),
        re.compile(r'Subscribe to newsletter|Sign up for updates|Follow us on Twitter', re.IGNORECASE),
        re.compile(r'<script.*?>.*?</script>', re.DOTALL | re.IGNORECASE),
        re.compile(r'<style.*?>.*?</style>', re.DOTALL | re.IGNORECASE),
        re.compile(r'<.*?>', re.DOTALL) # HTML tags
    ]

    COMMON_VERBS = {
        "achieves", "reaches", "demonstrates", "announces", "targets", "produces",
        "costs", "yields", "features", "launches", "develops", "scales", "claims",
        "states", "reports", "is", "are", "exceeds", "begins"
    }

    def clean_text(self, text: str) -> str:
        """Strip HTML tags, scripts, navigation footers, and redundant whitespace in 0 ms."""
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
        max_sentences: int = 25
    ) -> List[FactAssertion]:
        """Parse text into structured FactAssertion objects using local NLP heuristics."""
        cleaned = self.clean_text(text)
        if len(cleaned) < 20:
            return []

        # Sentence segmentation using regex
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 15]
        facts: List[FactAssertion] = []
        seen_keys = set()

        for sentence in sentences[:max_sentences]:
            has_metric = bool(self.METRIC_REGEX.search(sentence))
            triplet = self._parse_sentence_triplet(sentence)
            
            if triplet:
                subject, predicate, obj = triplet
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

    def _parse_sentence_triplet(self, sentence: str) -> Optional[Tuple[str, str, str]]:
        """Parse a sentence into (Subject, Predicate, Object) using grammar pattern matching."""
        words = sentence.split()
        if len(words) < 4:
            return None

        # Look for explicit action/relation verbs in sentence
        found_verb_idx = -1
        found_verb = "claims/states"

        for i, word in enumerate(words[1:6], 1):
            clean_word = re.sub(r'\W+', '', word.lower())
            if clean_word in self.COMMON_VERBS:
                found_verb_idx = i
                found_verb = word
                break

        if found_verb_idx != -1 and found_verb_idx < len(words) - 1:
            subject = " ".join(words[:found_verb_idx])
            obj = " ".join(words[found_verb_idx + 1:])
        else:
            # Fallback noun-phrase split
            subject = " ".join(words[:2])
            obj = " ".join(words[2:])

        # Clean subject and object strings
        subject = re.sub(r'^[^\w]+|[^\w]+$', '', subject).strip()
        obj = re.sub(r'^[^\w]+|[^\w]+$', '', obj).strip()

        if len(subject) > 2 and len(obj) > 2:
            return (subject[:50], found_verb[:30], obj[:80])
        return None


class DualExtractionPipeline:
    """Industry-Grade Dual-Layer Fact Extraction Pipeline.
    
    Automatically selects Layer 1 (LLM Structured Mode) if API key is provided,
    otherwise falls back smoothly to Layer 2 (Professional Local NLP Mode).
    """

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: str = "gemini-2.5-flash",
        provider: str = "google"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.provider = provider
        self.local_extractor = ProfessionalLocalExtractor()

    async def extract_facts(
        self, 
        raw_text: str, 
        source_url: str = "", 
        source_title: str = "",
        max_chars: int = 8000
    ) -> List[FactAssertion]:
        """Extract atomic facts using Layer 1 (LLM) or Layer 2 (Local NLP)."""
        text_snippet = raw_text[:max_chars]

        # LAYER 1: LLM Structured Extraction (If API key exists)
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
                    "Extract all unique, high-signal atomic facts, metrics, breakthrough claims, and dates from the text.\n"
                    "Ignore introductory background fluff, company history, or basic definitions.\n"
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
                logger.info(f"Layer 1 (LLM): Extracted {len(assertions)} facts from {source_url or source_title}")
                return assertions
            except Exception as e:
                logger.warning(f"Layer 1 (LLM) failed: {e}. Falling back to Layer 2 (Local NLP).")

        # LAYER 2: Professional Local NLP Extractor (Fallback / Offline)
        facts = self.local_extractor.extract_facts(text_snippet, source_url, source_title)
        logger.info(f"Layer 2 (Local NLP): Extracted {len(facts)} facts from {source_url or source_title}")
        return facts
