"""Concept-Diff Engine package for open-research-lite.

Provides dynamic Session Knowledge Graph management, universal dual-layer fact extraction
(LLM Mode + Universal Local NLP Mode), and token-dense concept diff payloads.
"""

from open_research_lite.concept_diff.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.concept_diff.extractor import DualExtractionPipeline, UniversalLocalNLPParser
from open_research_lite.concept_diff.diff_engine import ConceptDiffEngine
from open_research_lite.concept_diff.telemetry import TelemetryTracker

# Backward-compatible alias
ProfessionalLocalExtractor = UniversalLocalNLPParser

__version__ = "0.1.0"

__all__ = [
    "SessionKnowledgeGraph",
    "FactAssertion",
    "DualExtractionPipeline",
    "UniversalLocalNLPParser",
    "ProfessionalLocalExtractor",
    "ConceptDiffEngine",
    "TelemetryTracker",
]
