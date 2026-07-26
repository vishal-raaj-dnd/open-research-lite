"""Concept-Diff Engine package for DeepResearch-Lite.

Industry-grade ingestion middleware for deep research agents.
Provides dynamic Session Knowledge Graph management, dual-layer fact extraction
(LLM Structured Extraction + Professional Local NLP Mode), and token-dense concept diff payloads.
"""

from open_deep_research.concept_diff.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_deep_research.concept_diff.extractor import DualExtractionPipeline, ProfessionalLocalExtractor
from open_deep_research.concept_diff.diff_engine import ConceptDiffEngine
from open_deep_research.concept_diff.telemetry import TelemetryTracker

__version__ = "0.1.0"

__all__ = [
    "SessionKnowledgeGraph",
    "FactAssertion",
    "DualExtractionPipeline",
    "ProfessionalLocalExtractor",
    "ConceptDiffEngine",
    "TelemetryTracker",
]
