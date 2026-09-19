"""Unit tests for open-research-lite ConceptDiffEngine, Fast LLM Extractor, and Session Knowledge Graph."""

import os
import sys
import asyncio
import concurrent.futures
import pytest

# Ensure local src takes precedence over any pre-installed packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from open_research_lite import (
    SessionKnowledgeGraph,
    FactAssertion,
    ConceptDiffEngine,
    FastLLMExtractor,
    ExtractionResult,
    ExtractedFactItem,
    ContradictionItem,
    TelemetryTracker,
)


@pytest.mark.asyncio
async def test_session_knowledge_graph_deduplication():
    graph = SessionKnowledgeGraph()
    fact1 = FactAssertion(
        subject="Quantum Processor",
        predicate="gate fidelity",
        object_val="99.85%",
        is_numeric=True,
        source_url="https://example.com/source1"
    )
    fact2 = FactAssertion(
        subject="Quantum Processor",
        predicate="gate fidelity",
        object_val="99.85%",
        is_numeric=True,
        source_url="https://example.com/source2"
    )

    # First add should be novel
    assert graph.add_fact(fact1) is True
    # Second identical fact should be exact duplicate
    assert graph.is_exact_duplicate(fact2) is True
    assert graph.add_fact(fact2) is False
    assert len(graph.facts) == 1


@pytest.mark.asyncio
async def test_multi_valued_relations_not_falsely_conflicted():
    """Verifies that multi-valued predicates (features, produces, models) are not flagged as contradictions."""
    graph = SessionKnowledgeGraph()
    fact1 = FactAssertion(
        subject="Anthropic",
        predicate="produces",
        object_val="Claude 3.5 Sonnet",
        is_multi_valued=True,
        is_numeric=False
    )
    fact2 = FactAssertion(
        subject="Anthropic",
        predicate="produces",
        object_val="Claude 3.5 Haiku",
        is_multi_valued=True,
        is_numeric=False
    )

    assert graph.add_fact(fact1) is True
    # Should NOT be flagged as a conflict
    assert graph.find_conflict(fact2) is None
    assert graph.add_fact(fact2) is True
    assert len(graph.facts) == 2


@pytest.mark.asyncio
async def test_conditional_metrics_prevent_false_contradictions():
    """Verifies that differing metrics under distinct conditions (e.g. idle vs peak) do not falsely conflict."""
    graph = SessionKnowledgeGraph()
    fact_idle = FactAssertion(
        subject="Accelerator ASIC",
        predicate="power draw",
        object_val="25W",
        is_numeric=True,
        condition="idle state"
    )
    fact_peak = FactAssertion(
        subject="Accelerator ASIC",
        predicate="power draw",
        object_val="95W",
        is_numeric=True,
        condition="full load"
    )

    graph.add_fact(fact_idle)
    # Distinct operational conditions should NOT conflict
    assert graph.find_conflict(fact_peak) is None
    assert graph.add_fact(fact_peak) is True
    assert len(graph.facts) == 2


@pytest.mark.asyncio
async def test_numeric_conflict_detection():
    """Verifies that differing scalar metrics for the identical entity & condition are flagged as genuine conflicts."""
    graph = SessionKnowledgeGraph()
    fact1 = FactAssertion(
        subject="Cluster Interconnect",
        predicate="target bandwidth",
        object_val="800 Gbps",
        is_numeric=True
    )
    fact2 = FactAssertion(
        subject="Cluster Interconnect",
        predicate="target bandwidth",
        object_val="400 Gbps",
        is_numeric=True
    )

    graph.add_fact(fact1)
    conflict = graph.find_conflict(fact2)
    assert conflict is not None
    assert conflict.object_val == "800 Gbps"


def test_thread_safety_concurrent_mutation():
    """Verifies thread-safety under concurrent additions from multiple threads."""
    graph = SessionKnowledgeGraph()

    def add_batch(thread_idx: int):
        for i in range(50):
            fact = FactAssertion(
                subject=f"Entity_{thread_idx}",
                predicate="measures",
                object_val=f"val_{thread_idx}_{i}",
                is_numeric=True  # numeric values are NOT added to entities set
            )
            graph.add_fact(fact)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(add_batch, t) for t in range(5)]
        concurrent.futures.wait(futures)

    assert len(graph.facts) == 250
    # Numeric object_vals are excluded from entity set — only subjects are tracked
    assert len(graph.entities) == 5


class StubTestExtractor:
    """Deterministic extractor used for offline pipeline testing without network calls."""
    async def extract(
        self,
        raw_text: str,
        source_url: str = "",
        source_title: str = "",
        existing_facts_summary: str = "",
        max_chars: int = 60000
    ) -> ExtractionResult:
        return ExtractionResult(
            facts=[
                ExtractedFactItem(
                    subject="Linear Attention Accelerator",
                    predicate="achieves context",
                    object_val="128k context",
                    is_numeric=True,
                    is_multi_valued=False,
                    context_snippet="linear attention accelerator achieving 128k context"
                ),
                ExtractedFactItem(
                    subject="Linear Attention Accelerator",
                    predicate="latency speedup",
                    object_val="4.2x",
                    is_numeric=True,
                    is_multi_valued=False,
                    context_snippet="4.2x latency speedup"
                )
            ],
            contradictions=[],
            redundant_claims_pruned=3
        )


@pytest.mark.asyncio
async def test_concept_diff_engine_fluff_stripping():
    graph = SessionKnowledgeGraph()
    telemetry = TelemetryTracker()
    engine = ConceptDiffEngine(graph=graph, telemetry=telemetry, extractor=StubTestExtractor())

    raw_web_text = (
        "Transformer architectures rely on attention mechanisms to process sequential language tokens. "
        "The history of attention models dates back to fundamental papers in 2017 by Vaswani and colleagues. "
        "Silicon computing clusters consume high electrical wattage across modern datacenters. "
        "In 2026, researchers demonstrated a linear attention accelerator achieving 128k context with 4.2x latency speedup."
    )

    # First observation (Page 1)
    diff_payload_1 = await engine.process_observation(
        raw_text=raw_web_text,
        source_url="https://tech-news.com/attention-2026",
        source_title="2026 Attention Benchmark"
    )

    # Second observation with 100% duplicate fluff (Page 2)
    diff_payload_2 = await engine.process_observation(
        raw_text=raw_web_text,
        source_url="https://tech-news.com/attention-2026-duplicate",
        source_title="Duplicate Attention Benchmark"
    )

    assert "CONCEPT DIFF PAYLOAD" in diff_payload_1
    assert telemetry.total_input_words > 0
    # Duplicate page should result in discarded redundant facts
    assert telemetry.discards_count > 0


@pytest.mark.asyncio
async def test_fast_llm_extractor_raises_on_missing_key():
    """Verifies that FastLLMExtractor strictly enforces API key requirement and does not silently fall back."""
    from open_research_lite.exceptions import FactExtractionError
    extractor = FastLLMExtractor(api_key=None, model_name="unknown-model")
    extractor.api_key = None  # Ensure no key
    try:
        await extractor.extract("Some sample text to process")
        assert False, "Expected FactExtractionError was not raised"
    except FactExtractionError as e:
        assert "No API key" in str(e)


if __name__ == "__main__":
    asyncio.run(test_session_knowledge_graph_deduplication())
    asyncio.run(test_multi_valued_relations_not_falsely_conflicted())
    asyncio.run(test_conditional_metrics_prevent_false_contradictions())
    asyncio.run(test_numeric_conflict_detection())
    test_thread_safety_concurrent_mutation()
    asyncio.run(test_concept_diff_engine_fluff_stripping())
    asyncio.run(test_fast_llm_extractor_raises_on_missing_key())
    print("[OK] All ConceptDiffEngine unit tests passed!")
