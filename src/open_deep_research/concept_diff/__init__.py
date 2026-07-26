"""Concept-Diff Engine package for open_deep_research.

Re-exports core classes from open_research_lite for single-source-of-truth consistency.
"""

from open_research_lite import (
    ConceptDiffEngine,
    SessionKnowledgeGraph,
    FactAssertion,
    DualExtractionPipeline,
    UniversalLocalNLPParser,
    ProfessionalLocalExtractor,
    TelemetryTracker,
)

__version__ = "0.1.1"

__all__ = [
    "SessionKnowledgeGraph",
    "FactAssertion",
    "DualExtractionPipeline",
    "UniversalLocalNLPParser",
    "ProfessionalLocalExtractor",
    "ConceptDiffEngine",
    "TelemetryTracker",
]
