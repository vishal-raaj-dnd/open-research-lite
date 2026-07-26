"""Concept-Diff Engine implementation for DeepResearch-Lite.

Intercepts raw web search/scrape observations, performs dual-layer fact extraction,
diffs assertions against the live Session Knowledge Graph, and builds token-dense payloads.
"""

import logging
from typing import Dict, List, Optional, Tuple

from open_deep_research.concept_diff.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_deep_research.concept_diff.extractor import DualExtractionPipeline
from open_deep_research.concept_diff.telemetry import TelemetryTracker

logger = logging.getLogger("concept_diff.engine")


class ConceptDiffEngine:
    """Core gatekeeper middleware for filtering search results into clean diff payloads."""

    def __init__(
        self, 
        graph: Optional[SessionKnowledgeGraph] = None,
        telemetry: Optional[TelemetryTracker] = None,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.graph = graph or SessionKnowledgeGraph()
        self.telemetry = telemetry or TelemetryTracker()
        self.extractor = DualExtractionPipeline(api_key=api_key, model_name=model_name)

    async def process_observation(
        self, 
        raw_text: str, 
        source_url: str = "", 
        source_title: str = ""
    ) -> str:
        """Process raw web page observation, perform concept diffing, and return formatted Diff Payload.
        
        Args:
            raw_text: Raw scraped text or web search output string
            source_url: Source URL of origin
            source_title: Page title
            
        Returns:
            Condensed, fluff-free Diff Payload string formatted in Markdown
        """
        if not raw_text or not raw_text.strip():
            return "*No content retrieved from search tool observation.*"

        raw_word_count = len(raw_text.split())
        self.telemetry.record_input_words(raw_word_count)

        # 1. Dual-Layer Extraction (LLM or Local NLP)
        facts = await self.extractor.extract_facts(
            raw_text=raw_text, 
            source_url=source_url, 
            source_title=source_title
        )

        discarded_facts: List[FactAssertion] = []
        added_facts: List[FactAssertion] = []
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]] = []

        # 2. Diff incoming facts against Session Knowledge Graph
        for fact in facts:
            # Check exact match -> DISCARD
            if self.graph.is_exact_duplicate(fact):
                discarded_facts.append(fact)
                self.telemetry.record_discard()
                continue
            
            # Check conflict -> DIFF_CONFLICT
            existing_conflict = self.graph.find_conflict(fact)
            if existing_conflict:
                conflicting_facts.append((fact, existing_conflict))
                self.graph.add_fact(fact) # store to track history
                self.telemetry.record_conflict()
                continue

            # Novel fact -> DIFF_ADD
            self.graph.add_fact(fact)
            added_facts.append(fact)
            self.telemetry.record_add()

        # 3. Construct dense Markdown Diff Payload
        payload_text = self._build_diff_payload_markdown(
            source_url=source_url,
            source_title=source_title,
            raw_word_count=raw_word_count,
            added_facts=added_facts,
            conflicting_facts=conflicting_facts,
            discard_count=len(discarded_facts)
        )

        payload_word_count = len(payload_text.split())
        self.telemetry.record_output_words(payload_word_count)
        
        logger.info(
            f"Processed '{source_title or source_url}': {raw_word_count} raw words ──► {payload_word_count} diff words "
            f"({len(added_facts)} ADD, {len(discarded_facts)} DISCARD, {len(conflicting_facts)} CONFLICT)"
        )
        
        return payload_text

    def _build_diff_payload_markdown(
        self,
        source_url: str,
        source_title: str,
        raw_word_count: int,
        added_facts: List[FactAssertion],
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]],
        discard_count: int
    ) -> str:
        """Format facts into a clean, token-efficient Markdown payload."""
        payload_lines = []
        
        title_str = source_title or source_url or "Web Source"
        payload_lines.append(f"### 🌐 CONCEPT DIFF PAYLOAD: [{title_str}]")
        if source_url:
            payload_lines.append(f"**URL**: {source_url}")
            
        reduction_pct = 0
        if raw_word_count > 0:
            output_est = len(added_facts) * 15 + len(conflicting_facts) * 25 + 30
            reduction_pct = max(0, int((1 - (output_est / raw_word_count)) * 100))

        payload_lines.append(f"> ⚡ **Gatekeeper Summary**: Processed {raw_word_count} words | Discarded {discard_count} redundant facts (~{reduction_pct}% fluff removed)\n")

        # 🟢 NEW FACTS (DIFF_ADD)
        if added_facts:
            payload_lines.append("#### 🟢 NEW FACTS ADDED:")
            for f in added_facts:
                metric_tag = " 📊" if f.is_numeric else ""
                payload_lines.append(f"- **{f.subject}** ──({f.predicate})──► **{f.object_val}**{metric_tag}")
            payload_lines.append("")

        # ⚠️ CONFLICTS (DIFF_CONFLICT)
        if conflicting_facts:
            payload_lines.append("#### ⚠️ CONFLICTS DETECTED:")
            for inc, ex in conflicting_facts:
                payload_lines.append(
                    f"- **{inc.subject} [{inc.predicate}]**: Current source claims **'{inc.object_val}'**, "
                    f"contradicting prior record **'{ex.object_val}'** (from {ex.source_url or 'prior source'})."
                )
            payload_lines.append("")

        if not added_facts and not conflicting_facts:
            payload_lines.append("*No novel claims or metrics found in this source. Entire page was redundant background fluff.*")

        return "\n".join(payload_lines)
