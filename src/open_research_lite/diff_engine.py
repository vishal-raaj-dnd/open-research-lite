"""Concept-Diff Engine implementation for open-research-lite.

Intercepts raw web observations, runs semantic extraction and contradiction detection via the Fast LLM,
diffs assertions against the live Session Knowledge Graph, and constructs token-dense payloads.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple


from open_research_lite.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.extractor import FastLLMExtractor, ExtractionResult
from open_research_lite.telemetry import TelemetryTracker

logger = logging.getLogger("open_research_lite.engine")


class ConceptDiffEngine:
    """Core gatekeeper middleware for distilling raw web observations into verified diff payloads."""

    def __init__(
        self, 
        graph: Optional[SessionKnowledgeGraph] = None,
        telemetry: Optional[TelemetryTracker] = None,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        provider: str = "google",
        extractor: Optional[FastLLMExtractor] = None
    ):
        self.graph = graph or SessionKnowledgeGraph()
        self.telemetry = telemetry or TelemetryTracker()
        self.model_name = model_name
        self.extractor = extractor or FastLLMExtractor(
            api_key=api_key, 
            model_name=model_name,
            provider=provider
        )

    async def process_observation(
        self, 
        raw_text: str, 
        source_url: str = "", 
        source_title: str = ""
    ) -> str:
        """Process raw web page observation, perform concept diffing, and return formatted Diff Payload."""
        if not raw_text or not raw_text.strip():
            return "*No content retrieved from search tool observation.*"

        raw_word_count = len(raw_text.split())
        self.telemetry.record_input_words(raw_word_count)

        # Build comprehensive summary of ALL existing session knowledge for the Fast LLM radar
        existing_summary = ""
        if self.graph.facts:
            summary_lines = []
            for f in self.graph.facts:
                cond_str = f" [condition: {f.condition}]" if f.condition else ""
                summary_lines.append(f"- {f.subject} -> {f.predicate}: {f.object_val}{cond_str}")
            existing_summary = "\n".join(summary_lines)

        # 1. Fast LLM Semantic Extraction & Contradiction Radar (unconstrained context)
        extraction_res: ExtractionResult = await self.extractor.extract(
            raw_text=raw_text,
            source_url=source_url,
            source_title=source_title,
            existing_facts_summary=existing_summary,
            max_chars=None
        )

        discarded_facts: List[FactAssertion] = []
        added_facts: List[FactAssertion] = []
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]] = []

        # 2. Process extracted facts against Session Knowledge Graph
        for item in extraction_res.facts:
            fact = FactAssertion(
                subject=item.subject.strip(),
                predicate=item.predicate.strip(),
                object_val=item.object_val.strip(),
                is_numeric=item.is_numeric,
                is_multi_valued=item.is_multi_valued,
                condition=item.condition,
                source_url=source_url,
                source_title=source_title,
                context_snippet=item.context_snippet.strip()
            )

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

        # 3. Record semantic contradictions detected directly by Fast LLM
        for c in extraction_res.contradictions:
            self.graph.record_contradiction(
                subject=c.subject,
                claim_a=c.existing_claim,
                claim_b=c.conflicting_claim,
                reasoning=c.reasoning,
                source_url=source_url
            )
            self.telemetry.record_conflict()

        # 4. Construct dense Markdown Diff Payload
        payload_text = self._build_diff_payload_markdown(
            source_url=source_url,
            source_title=source_title,
            raw_text=raw_text,
            raw_word_count=raw_word_count,
            added_facts=added_facts,
            conflicting_facts=conflicting_facts,
            llm_contradictions=extraction_res.contradictions,
            discard_count=len(discarded_facts) + extraction_res.redundant_claims_pruned
        )

        payload_word_count = len(payload_text.split())
        self.telemetry.record_output_words(payload_word_count)
        return payload_text

    def _build_diff_payload_markdown(
        self,
        source_url: str,
        source_title: str,
        raw_text: str,
        raw_word_count: int,
        added_facts: List[FactAssertion],
        conflicting_facts: List[Tuple[FactAssertion, FactAssertion]],
        llm_contradictions: List[Any],
        discard_count: int
    ) -> str:
        payload_lines = []
        
        title_str = source_title or source_url or "Web Source"
        payload_lines.append(f"### CONCEPT DIFF PAYLOAD: [{title_str}]")
        if source_url:
            payload_lines.append(f"**URL**: {source_url}")
            
        temp_body = []
        if added_facts:
            temp_body.append("#### NEW FACTS ADDED:")
            for f in added_facts:
                cond_tag = f" ({f.condition})" if f.condition else ""
                metric_tag = " [metric]" if f.is_numeric else ""
                temp_body.append(f"- **{f.subject}** -> *{f.predicate}*: `{f.object_val}`{cond_tag}{metric_tag}")
            temp_body.append("")

        if conflicting_facts:
            temp_body.append("#### METRIC DIVERGENCE DETECTED:")
            for inc, ex in conflicting_facts:
                inc_cond = f" ({inc.condition})" if inc.condition else ""
                ex_cond = f" ({ex.condition})" if ex.condition else ""
                temp_body.append(
                    f"- **{inc.subject} [{inc.predicate}]**: Current claims **'{inc.object_val}'**{inc_cond}, "
                    f"differing from earlier **'{ex.object_val}'**{ex_cond}."
                )
            temp_body.append("")

        if llm_contradictions:
            temp_body.append("#### SEMANTIC CONTRADICTIONS (Fast LLM Radar):")
            for c in llm_contradictions:
                temp_body.append(
                    f"- **{c.subject}**: Opposing claim **'{c.conflicting_claim}'** vs prior **'{c.existing_claim}'**\n"
                    f"  *Reasoning*: {c.reasoning}"
                )
            temp_body.append("")

        if not added_facts and not conflicting_facts and not llm_contradictions:
            clean_snippet = " ".join(raw_text.split()[:40])
            temp_body.append(f"*Context note (background text with no novel assertions)*: \"{clean_snippet}...\"")

        body_str = "\n".join(temp_body)
        body_words = len(body_str.split())

        # Exact token reduction calculation
        reduction_pct = 0
        if raw_word_count > 0:
            reduction_pct = max(0, min(99, int((1.0 - (body_words / max(1, raw_word_count))) * 100)))

        payload_lines.append(
            f"> Summary: Processed {raw_word_count} words | Pruned {discard_count} redundant statements (~{reduction_pct}% token reduction)\n"
        )
        payload_lines.append(body_str)

        return "\n".join(payload_lines)
