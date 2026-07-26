"""Concept-Diff Engine implementation for open-research-lite."""

import logging
from typing import Dict, List, Optional, Tuple

from open_research_lite.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.extractor import DualExtractionPipeline
from open_research_lite.telemetry import TelemetryTracker

logger = logging.getLogger("open_research_lite.engine")


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
        if not raw_text or not raw_text.strip():
            return "*No content retrieved from search tool observation.*"

        raw_word_count = len(raw_text.split())
        self.telemetry.record_input_words(raw_word_count)

        facts = await self.extractor.extract_facts(
            raw_text=raw_text, 
            source_url=source_url, 
            source_title=source_title
        )

        discarded_facts: List[FactAssertion] = []
        added_facts: List[FactAssertion] = []
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]] = []

        for fact in facts:
            if self.graph.is_exact_duplicate(fact):
                discarded_facts.append(fact)
                self.telemetry.record_discard()
                continue
            
            existing_conflict = self.graph.find_conflict(fact)
            if existing_conflict:
                conflicting_facts.append((fact, existing_conflict))
                self.graph.add_fact(fact)
                self.telemetry.record_conflict()
                continue

            self.graph.add_fact(fact)
            added_facts.append(fact)
            self.telemetry.record_add()

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
        payload_lines = []
        
        title_str = source_title or source_url or "Web Source"
        payload_lines.append(f"### 🌐 CONCEPT DIFF PAYLOAD: [{title_str}]")
        if source_url:
            payload_lines.append(f"**URL**: {source_url}")
            
        reduction_pct = 0
        output_est = min(len(added_facts), 12) * 8 + len(conflicting_facts) * 20 + 20
        if raw_word_count > 0:
            reduction_pct = max(0, int((1 - (output_est / raw_word_count)) * 100))

        payload_lines.append(f"> ⚡ **Gatekeeper Summary**: Processed {raw_word_count} words | Discarded {discard_count} redundant facts (~{reduction_pct}% fluff removed)\n")

        if added_facts:
            payload_lines.append("#### 🟢 NEW FACTS ADDED:")
            # Prioritize numeric metrics first, then cap at 12 top facts per source
            sorted_facts = sorted(added_facts, key=lambda f: f.is_numeric, reverse=True)[:12]
            for f in sorted_facts:
                metric_tag = " 📊" if f.is_numeric else ""
                payload_lines.append(f"- **{f.subject}** → *{f.predicate}*: `{f.object_val}`{metric_tag}")
            payload_lines.append("")

        if conflicting_facts:
            payload_lines.append("#### ⚠️ CONFLICTS DETECTED:")
            for inc, ex in conflicting_facts[:5]:
                payload_lines.append(
                    f"- **{inc.subject} [{inc.predicate}]**: Current claims **'{inc.object_val}'**, "
                    f"contradicting prior **'{ex.object_val}'**."
                )
            payload_lines.append("")

        if not added_facts and not conflicting_facts:
            payload_lines.append("*No novel claims or metrics found in this source. Entire page was redundant background fluff.*")

        return "\n".join(payload_lines)
