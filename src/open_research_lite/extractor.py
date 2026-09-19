"""Universal Fast LLM Fact & Contradiction Extraction Pipeline.

Replaces brittle keyword heuristics and regex guessing with full Fast LLM semantic reasoning
(e.g., Gemini 2.5 Flash, GPT-4o-Mini, Claude 3.5 Haiku, Llama 3.1 8B).
Extracts atomic subject-predicate-object assertions, quantitative metrics, operational conditions,
and detects genuine factual contradictions against existing session knowledge.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from open_research_lite.knowledge_graph import FactAssertion
from open_research_lite.exceptions import ConfigurationError, FactExtractionError

logger = logging.getLogger("open_research_lite.extractor")


class ExtractedFactItem(BaseModel):
    """An atomic fact isolated from source text by the Fast LLM."""
    subject: str = Field(description="Normalized entity, system, or concept name")
    predicate: str = Field(description="Relationship, verb, or property name (e.g. bandwidth, operates_at, founded_in)")
    object_val: str = Field(description="Target entity, status, numerical metric, or specific value")
    is_numeric: bool = Field(default=False, description="True if value contains numbers, dates, units, or currencies")
    is_multi_valued: bool = Field(default=False, description="True if this relation naturally allows multiple concurrent values (e.g. products, partners)")
    condition: Optional[str] = Field(default=None, description="Operational scenario or test condition (e.g., 'at idle', 'ambient temp', 'v2 architecture')")
    context_snippet: str = Field(default="", description="Original sentence snippet from the source supporting this assertion")


class ContradictionItem(BaseModel):
    """A genuine factual or metric contradiction detected against prior knowledge."""
    subject: str = Field(description="Entity or topic with conflicting claims")
    existing_claim: str = Field(description="Prior claim or established consensus")
    conflicting_claim: str = Field(description="The contradictory claim presented in this source")
    reasoning: str = Field(description="Semantic explanation of why this is a direct contradiction rather than a different variant or condition")


class ExtractionResult(BaseModel):
    """Complete structured output returned by the Fast LLM."""
    facts: List[ExtractedFactItem] = Field(default_factory=list, description="List of unique factual assertions and metrics")
    contradictions: List[ContradictionItem] = Field(default_factory=list, description="Contradictions detected against existing session knowledge")
    redundant_claims_pruned: int = Field(default=0, description="Approximate count of repetitive fluff, introductory boilerplate, or navigation statements discarded")


class FastLLMExtractor:
    """Production-grade semantic extractor powered by high-speed, cost-efficient Fast LLMs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        provider: str = "google"
    ):
        from open_research_lite.models import resolve_api_key
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key or resolve_api_key(model_name)

    async def extract(
        self,
        raw_text: str,
        source_url: str = "",
        source_title: str = "",
        existing_facts_summary: str = "",
        max_chars: Optional[int] = None
    ) -> ExtractionResult:
        """Extracts facts and analyzes contradictions using the Fast LLM."""
        if not raw_text or not raw_text.strip():
            return ExtractionResult()

        if max_chars is not None and max_chars > 0:
            text_snippet = raw_text[:max_chars].strip()
        else:
            text_snippet = raw_text.strip()

        # Fast LLM extraction requires a valid API key
        if not self.api_key:
            raise FactExtractionError(
                f"No API key provided or resolved for Fast LLM extractor model '{self.model_name}'. "
                "FastLLMExtractor requires a valid provider API key (e.g. GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY) "
                "to perform high-signal semantic fact extraction."
            )

        return await self._extract_with_llm(
            text_snippet=text_snippet,
            source_url=source_url,
            source_title=source_title,
            existing_facts_summary=existing_facts_summary
        )

    async def extract_facts(
        self,
        raw_text: str,
        source_url: str = "",
        source_title: str = "",
        max_chars: Optional[int] = None
    ) -> List[FactAssertion]:
        """Convenience method returning FactAssertion objects for backward compatibility."""
        res = await self.extract(raw_text, source_url, source_title, max_chars=max_chars)
        assertions: List[FactAssertion] = []
        for item in res.facts:
            assertions.append(FactAssertion(
                subject=item.subject.strip(),
                predicate=item.predicate.strip(),
                object_val=item.object_val.strip(),
                is_numeric=item.is_numeric,
                is_multi_valued=item.is_multi_valued,
                condition=item.condition,
                source_url=source_url,
                source_title=source_title,
                context_snippet=item.context_snippet.strip()
            ))
        return assertions

    async def _extract_with_llm(
        self,
        text_snippet: str,
        source_url: str,
        source_title: str,
        existing_facts_summary: str
    ) -> ExtractionResult:
        from open_research_lite.models import get_chat_model

        base_llm = get_chat_model(self.model_name, self.api_key)
        llm = base_llm.with_structured_output(ExtractionResult)

        prompt = (
            "You are the Fast LLM fact extraction and contradiction engine for open-research-lite.\n"
            "Analyze the text and extract high-signal atomic factual claims, quantitative metrics, "
            "and architectural/scientific properties.\n\n"
            "Guidelines:\n"
            "1. Isolate Subject-Predicate-Object triplets.\n"
            "2. Distinguish singular properties from multi-valued properties (is_multi_valued=True for products, partners, features).\n"
            "3. If a metric applies under a specific operational context (e.g., 'at idle', 'ambient temperature', 'peak load'), "
            "record it in 'condition' so it is not mistaken for a contradiction.\n"
            "4. If existing verified knowledge is provided below, check if the current source directly CONTRADICTS "
            "any existing claim for the same entity and condition. If so, populate the 'contradictions' list with explicit reasoning.\n"
            "5. Ignore navigation text, cookie banners, introductory background fluff, and repetitive SEO prose.\n\n"
            f"SOURCE TITLE: {source_title}\n"
            f"SOURCE URL: {source_url}\n"
        )

        if existing_facts_summary:
            prompt += f"\nEXISTING SESSION KNOWLEDGE:\n{existing_facts_summary}\n"

        prompt += f"\nSOURCE TEXT TO ANALYZE:\n{text_snippet}\n"

        try:
            result: ExtractionResult = await llm.ainvoke(prompt)
            return result
        except Exception as e:
            logger.error(f"Fast LLM extraction call failed ({self.model_name}): {e}")
            raise FactExtractionError(f"Fast LLM extraction failed ({self.model_name}): {e}") from e


# Backward-compatible alias
DualExtractionPipeline = FastLLMExtractor
