"""open-research-lite: Production-Grade Differential Knowledge-State Ingestion & Autonomous Research Agent."""

from open_research_lite.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.extractor import (
    FastLLMExtractor,
    ExtractionResult,
    ExtractedFactItem,
    ContradictionItem,
    DualExtractionPipeline,
)
from open_research_lite.diff_engine import ConceptDiffEngine
from open_research_lite.telemetry import TelemetryTracker
from open_research_lite.researcher import Researcher, GPTResearcher
from open_research_lite.models import with_retry
from open_research_lite.exceptions import (
    OpenResearchError,
    ConfigurationError,
    SearchProviderError,
    FactExtractionError,
    ReportSynthesisError,
    KnowledgeGraphError,
)

__version__ = "0.3.1"

__all__ = [
    "Researcher",
    "GPTResearcher",
    "ConceptDiffEngine",
    "SessionKnowledgeGraph",
    "FactAssertion",
    "FastLLMExtractor",
    "ExtractionResult",
    "ExtractedFactItem",
    "ContradictionItem",
    "DualExtractionPipeline",
    "TelemetryTracker",
    "with_retry",
    "OpenResearchError",
    "ConfigurationError",
    "SearchProviderError",
    "FactExtractionError",
    "ReportSynthesisError",
    "KnowledgeGraphError",
]
