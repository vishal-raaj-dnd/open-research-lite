"""Unit tests for the drop-in Researcher / GPTResearcher agent API."""

import os
import sys
import asyncio
import pytest

# Ensure local src takes precedence over any pre-installed packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from open_research_lite import (
    Researcher, 
    GPTResearcher, 
    ExtractionResult, 
    ExtractedFactItem,
    FactExtractionError
)


class StubResearcherExtractor:
    """Deterministic extractor used strictly for unit testing without live API keys."""
    async def extract(
        self, 
        raw_text: str, 
        source_url: str = "", 
        source_title: str = "", 
        existing_facts_summary: str = "", 
        max_chars: int = 60000
    ) -> ExtractionResult:
        facts = []
        if "2.8 TB/s" in raw_text:
            facts.append(ExtractedFactItem(
                subject="HBM4 Memory Stack",
                predicate="peak bandwidth",
                object_val="2.8 TB/s",
                is_numeric=True,
                is_multi_valued=False,
                context_snippet="delivering 2.8 TB/s peak bandwidth"
            ))
        if "26W" in raw_text:
            facts.append(ExtractedFactItem(
                subject="HBM4 Memory Stack",
                predicate="operating power",
                object_val="26W",
                is_numeric=True,
                condition="full saturation",
                context_snippet="measured at 26W under full memory saturation"
            ))
        if "31W" in raw_text:
            facts.append(ExtractedFactItem(
                subject="HBM4 Memory Stack",
                predicate="operating power",
                object_val="31W",
                is_numeric=True,
                condition="continuous load",
                context_snippet="sustained power reaches 31W under continuous load"
            ))
        if "1.6 Tbps" in raw_text:
            facts.append(ExtractedFactItem(
                subject="Silicon Photonics",
                predicate="transmission bandwidth",
                object_val="1.6 Tbps",
                is_numeric=True,
                is_multi_valued=False,
                context_snippet="1.6 Tbps transmission"
            ))
        return ExtractionResult(facts=facts, contradictions=[], redundant_claims_pruned=1)


@pytest.mark.asyncio
async def test_researcher_initialization_and_alias():
    agent1 = Researcher(query="Fault-Tolerant Quantum Error Correction")
    agent2 = GPTResearcher(query="Fault-Tolerant Quantum Error Correction")

    assert agent1.query == "Fault-Tolerant Quantum Error Correction"
    assert isinstance(agent2, Researcher)
    assert agent1.graph is not agent2.graph  # Session isolation test


@pytest.mark.asyncio
async def test_researcher_conduct_research_and_write_report():
    researcher = Researcher(
        query="High-Bandwidth Memory Architecture Trends",
        report_type="research_report",
        extractor=StubResearcherExtractor()
    )

    custom_sources = [
        {
            "url": "https://semiconductor-review.org/hbm4-specs",
            "title": "HBM4 Interface Milestone 2026",
            "content": (
                "Engineers validated an HBM4 memory stack delivering 2.8 TB/s peak bandwidth per stack. "
                "Base operating power consumption is measured at 26W under full memory saturation."
            )
        },
        {
            "url": "https://datacenter-insights.com/memory-audit",
            "title": "HBM4 Memory Power Audit",
            "content": (
                "Testing validates HBM4 memory delivering 2.8 TB/s peak bandwidth per stack. "
                "However, an independent thermal audit reports sustained power reaches 31W under continuous load."
            )
        }
    ]

    # Conduct research with custom sources
    diff_payloads = await researcher.conduct_research(custom_sources=custom_sources)
    assert len(diff_payloads) == 2
    assert len(researcher.sources) == 2

    # Verify knowledge graph captured the facts and detected conflict
    graph = researcher.get_knowledge_graph()
    assert len(graph.facts) > 0

    # Write report
    report = await researcher.write_report()
    assert "# Research Report: High-Bandwidth Memory Architecture Trends" in report
    assert "Key Verified Findings" in report
    assert len(report) > 100

    # Verify telemetry stats
    stats = researcher.get_stats()
    assert stats["sources_count"] == 2
    assert stats["telemetry"]["total_facts_extracted"] > 0


@pytest.mark.asyncio
async def test_dual_model_configuration():
    agent = Researcher(
        query="Neuromorphic Computing Architectures",
        fast_llm="gpt-4o-mini",
        smart_llm="claude-3-5-sonnet-latest",
        extractor_api_key="mock-sub-key",
        writer_api_key="mock-main-key"
    )
    assert agent.extractor_model == "gpt-4o-mini"
    assert agent.fast_llm == "gpt-4o-mini"
    assert agent.writer_model == "claude-3-5-sonnet-latest"
    assert agent.smart_llm == "claude-3-5-sonnet-latest"
    assert agent.extractor_api_key == "mock-sub-key"
    assert agent.writer_api_key == "mock-main-key"
    # Ensure engine received extractor configuration
    assert agent.engine.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_custom_search_provider_and_json_export():
    async def mock_enterprise_search(query: str, max_results: int):
        return [
            {
                "url": "https://internal-docs.corp/optics",
                "title": "Silicon Photonics Transceiver Scaling",
                "content": "Optical interconnects achieve 1.6 Tbps transmission with 3.2 pJ/bit energy efficiency."
            }
        ]

    agent = Researcher(
        query="Silicon Photonics Interconnects",
        search_func=mock_enterprise_search,
        max_results=1,
        extractor=StubResearcherExtractor()
    )

    diffs = await agent.conduct_research()
    assert len(diffs) == 1
    assert "Silicon Photonics" in diffs[0]

    report = await agent.write_report()
    assert len(report) > 50

    # Test export_json and to_dict
    state = agent.to_dict()
    assert state["query"] == "Silicon Photonics Interconnects"
    assert "telemetry" in state
    assert "knowledge_graph" in state

    json_path = agent.export_json("test_report.json")
    assert os.path.exists(json_path)
    os.remove(json_path)

    # Test Graph Serialization & Query
    graph = agent.get_knowledge_graph()
    g_dict = graph.to_dict()
    assert g_dict["stats"]["total_facts"] > 0
    rels = graph.get_entity_relationships(list(graph.entities)[0])
    assert len(rels) > 0


@pytest.mark.asyncio
async def test_researcher_fails_without_credentials():
    """Verifies that Researcher raises FactExtractionError when called without API keys or injected extractor."""
    agent = Researcher(query="Test Missing Credentials", model_name="unknown-model")
    agent.extractor_api_key = None
    agent.engine.extractor.api_key = None
    try:
        await agent.conduct_research(custom_sources=[{
            "url": "https://test.com", "title": "Test", "content": "Some test content"
        }])
        assert False, "Expected FactExtractionError was not raised"
    except FactExtractionError as e:
        assert "No API key" in str(e)


@pytest.mark.asyncio
async def test_exceptions_hierarchy():
    from open_research_lite import (
        OpenResearchError,
        ConfigurationError,
        SearchProviderError,
        FactExtractionError,
        ReportSynthesisError,
        KnowledgeGraphError,
    )

    err = SearchProviderError("Search failed", details={"provider": "custom"})
    assert isinstance(err, OpenResearchError)
    assert "provider" in str(err)


if __name__ == "__main__":
    print("Running test_researcher_initialization_and_alias...", flush=True)
    asyncio.run(test_researcher_initialization_and_alias())
    print("Running test_researcher_conduct_research_and_write_report...", flush=True)
    asyncio.run(test_researcher_conduct_research_and_write_report())
    print("Running test_dual_model_configuration...", flush=True)
    asyncio.run(test_dual_model_configuration())
    print("Running test_custom_search_provider_and_json_export...", flush=True)
    asyncio.run(test_custom_search_provider_and_json_export())
    print("Running test_researcher_fails_without_credentials...", flush=True)
    asyncio.run(test_researcher_fails_without_credentials())
    print("Running test_exceptions_hierarchy...", flush=True)
    asyncio.run(test_exceptions_hierarchy())
    print("[OK] All Researcher API tests passed!", flush=True)
