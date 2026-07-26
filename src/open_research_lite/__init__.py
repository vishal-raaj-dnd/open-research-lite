"""open-research-lite: Token-Efficient Ingestion Middleware & Concept-Diff Engine for Deep Research AI Agents."""

from open_research_lite.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.extractor import DualExtractionPipeline, UniversalLocalNLPParser
from open_research_lite.diff_engine import ConceptDiffEngine
from open_research_lite.telemetry import TelemetryTracker

# Alias for backward compatibility
ProfessionalLocalExtractor = UniversalLocalNLPParser

__version__ = "0.1.1"

__all__ = [
    "ConceptDiffEngine",
    "SessionKnowledgeGraph",
    "FactAssertion",
    "DualExtractionPipeline",
    "UniversalLocalNLPParser",
    "ProfessionalLocalExtractor",
    "TelemetryTracker",
]
