"""Unit tests for open-research-lite ConceptDiffEngine and Session Knowledge Graph."""

import asyncio
import pytest
from open_research_lite import (
    SessionKnowledgeGraph,
    FactAssertion,
    ConceptDiffEngine,
    TelemetryTracker,
    UniversalLocalNLPParser,
)



@pytest.mark.asyncio
async def test_session_knowledge_graph_deduplication():
    graph = SessionKnowledgeGraph()
    fact1 = FactAssertion(
        subject="Solid State Battery",
        predicate="energy density",
        object_val="500 Wh/kg",
        is_numeric=True,
        source_url="https://example.com/source1"
    )
    fact2 = FactAssertion(
        subject="Solid State Battery",
        predicate="energy density",
        object_val="500 Wh/kg",
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
async def test_session_knowledge_graph_conflict_detection():
    graph = SessionKnowledgeGraph()
    fact1 = FactAssertion(
        subject="Battery Cell Cost",
        predicate="target price",
        object_val="$140/kWh",
        is_numeric=True
    )
    fact2 = FactAssertion(
        subject="Battery Cell Cost",
        predicate="target price",
        object_val="$110/kWh",
        is_numeric=True
    )

    graph.add_fact(fact1)
    conflict = graph.find_conflict(fact2)
    assert conflict is not None
    assert conflict.object_val == "$140/kWh"


@pytest.mark.asyncio
async def test_concept_diff_engine_fluff_stripping():
    graph = SessionKnowledgeGraph()
    telemetry = TelemetryTracker()
    engine = ConceptDiffEngine(graph=graph, telemetry=telemetry)

    raw_web_text = (
        "Electric vehicles (EVs) rely on rechargeable batteries to supply power. The history of lithium-ion batteries dates back "
        "to John Goodenough, M. Stanley Whittingham, and Akira Yoshino, who won the Nobel Prize in Chemistry in 2019. "
        "Elon Musk's Tesla has long dominated the EV industry. "
        "In early 2026, researchers demonstrated a solid-state battery cell achieving an energy density of 500 Wh/kg."
    )

    # First observation (Page 1)
    diff_payload_1 = await engine.process_observation(
        raw_text=raw_web_text,
        source_url="https://news.com/battery-2026",
        source_title="2026 Battery News"
    )

    # Second observation with 100% duplicate fluff (Page 2)
    diff_payload_2 = await engine.process_observation(
        raw_text=raw_web_text,
        source_url="https://news.com/battery-2026-duplicate",
        source_title="Duplicate Battery News"
    )

    assert "CONCEPT DIFF PAYLOAD" in diff_payload_1
    assert telemetry.total_input_words > 0
    # Duplicate page should result in discarded redundant facts
    assert telemetry.discards_count > 0




if __name__ == "__main__":
    asyncio.run(test_session_knowledge_graph_deduplication())
    asyncio.run(test_session_knowledge_graph_conflict_detection())
    asyncio.run(test_concept_diff_engine_fluff_stripping())
    print("✅ All ConceptDiffEngine unit tests passed!")
