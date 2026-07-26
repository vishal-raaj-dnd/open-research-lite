"""open-research-lite: Token-Efficient Ingestion Middleware & Concept-Diff Engine for Deep Research AI Agents.

Provides high-performance, dual-layer fact extraction and session knowledge graph compilation
to cut agent token bloat by 80-85%.
"""

from open_research_lite.concept_diff import (
    ConceptDiffEngine,
    SessionKnowledgeGraph,
    FactAssertion,
    DualExtractionPipeline,
    UniversalLocalNLPParser,
    ProfessionalLocalExtractor,
    TelemetryTracker,
)

__version__ = "0.1.0"

__all__ = [
    "ConceptDiffEngine",
    "SessionKnowledgeGraph",
    "FactAssertion",
    "DualExtractionPipeline",
    "UniversalLocalNLPParser",
    "ProfessionalLocalExtractor",
    "TelemetryTracker",
]
