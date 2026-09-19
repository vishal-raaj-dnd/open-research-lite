"""Session Knowledge Graph implementation for open-research-lite.

Thread-safe in-memory graph tracking atomic facts and detecting genuine conflicts
using semantic attributes (multi-valued properties, conditions, numerical metrics)
without fragile hardcoded verb assumptions.
"""

import re
import threading
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class FactAssertion(BaseModel):
    """An atomic factual claim extracted from a web source by the Fast LLM."""
    subject: str = Field(description="Normalized subject/entity name")
    predicate: str = Field(description="Relationship or property verb/name")
    object_val: str = Field(description="Target entity, status, or numerical value")
    is_numeric: bool = Field(default=False, description="Whether object_val contains a numerical stat/metric")
    is_multi_valued: bool = Field(default=False, description="Whether this predicate naturally permits multiple concurrent values")
    condition: Optional[str] = Field(default=None, description="Operational condition or test context (e.g. 'at idle', 'ambient')")
    source_url: str = Field(default="", description="Source URL of origin")
    source_title: str = Field(default="", description="Title of the source web page")
    context_snippet: str = Field(default="", description="Brief original sentence for evidence verification")

    def canonical_key(self) -> str:
        """Returns a normalized string hash key for fast exact matching."""
        s = re.sub(r'\W+', '', self.subject.lower())
        p = re.sub(r'\W+', '', self.predicate.lower())
        o = re.sub(r'\W+', '', self.object_val.lower())
        c = re.sub(r'\W+', '', (self.condition or "").lower())
        return f"{s}:{p}:{o}:{c}"

    def subject_predicate_key(self) -> str:
        """Returns a key representing subject and predicate (for conflict checks)."""
        s = re.sub(r'\W+', '', self.subject.lower())
        p = re.sub(r'\W+', '', self.predicate.lower())
        return f"{s}:{p}"


class SessionKnowledgeGraph:
    """Live in-memory thread-safe state graph tracking verified assertions in a research session."""

    def __init__(self):
        self._lock = threading.RLock()
        self._exact_keys: Set[str] = set()
        self._sp_index: Dict[str, List[FactAssertion]] = {}
        self.facts: List[FactAssertion] = []
        self.entities: Set[str] = set()
        self.contradictions: List[Dict[str, Any]] = []

    def is_exact_duplicate(self, fact: FactAssertion) -> bool:
        with self._lock:
            return fact.canonical_key() in self._exact_keys

    def find_conflict(self, fact: FactAssertion) -> Optional[FactAssertion]:
        """Finds factual conflicts.
        
        Considers:
        - Multi-valued relations (e.g. company produces multiple products) do NOT conflict.
        - Differing operational conditions (e.g. idle power vs peak power) do NOT conflict.
        - Divergent scalar metrics or singular attributes for the identical entity/condition ARE flagged as conflicts.
        """
        with self._lock:
            sp_key = fact.subject_predicate_key()
            if sp_key not in self._sp_index:
                return None

            clean_incoming = fact.object_val.strip().lower()

            for existing in self._sp_index[sp_key]:
                clean_existing = existing.object_val.strip().lower()
                if clean_existing == clean_incoming:
                    continue

                # If either fact is explicitly marked as multi-valued, allow multiple values
                if fact.is_multi_valued or existing.is_multi_valued:
                    continue

                # If both have conditions that differ (e.g. 'idle' vs 'peak'), they describe different scenarios
                if fact.condition and existing.condition:
                    clean_c1 = re.sub(r'\W+', '', fact.condition.lower())
                    clean_c2 = re.sub(r'\W+', '', existing.condition.lower())
                    if clean_c1 != clean_c2:
                        continue

                # If either value is numeric, or predicate is singular, flag genuine conflict
                if fact.is_numeric or existing.is_numeric or not fact.is_multi_valued:
                    return existing

            return None

    def add_fact(self, fact: FactAssertion) -> bool:
        """Adds a fact to the graph if it is not an exact duplicate. Thread-safe."""
        with self._lock:
            key = fact.canonical_key()
            if key in self._exact_keys:
                return False

            self._exact_keys.add(key)
            sp_key = fact.subject_predicate_key()
            if sp_key not in self._sp_index:
                self._sp_index[sp_key] = []
            self._sp_index[sp_key].append(fact)

            self.facts.append(fact)
            self.entities.add(fact.subject)
            # Only add object_val as an entity when it represents a named concept, not a raw metric
            if not fact.is_numeric:
                self.entities.add(fact.object_val)
            return True

    def record_contradiction(
        self,
        subject: str,
        claim_a: str,
        claim_b: str,
        reasoning: str,
        source_url: str = ""
    ) -> None:
        """Records an explicit semantic contradiction identified by the Fast LLM."""
        with self._lock:
            self.contradictions.append({
                "subject": subject,
                "claim_a": claim_a,
                "claim_b": claim_b,
                "reasoning": reasoning,
                "source_url": source_url
            })

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "total_facts": len(self.facts),
                "total_entities": len(self.entities),
                "unique_subject_predicates": len(self._sp_index),
                "total_contradictions": len(self.contradictions)
            }

    def clear(self) -> None:
        """Resets the graph state."""
        with self._lock:
            self._exact_keys.clear()
            self._sp_index.clear()
            self.facts.clear()
            self.entities.clear()
            self.contradictions.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph into a JSON-serializable dictionary."""
        with self._lock:
            return {
                "stats": self.get_stats(),
                "entities": sorted(list(self.entities)),
                "facts": [f.model_dump() for f in self.facts],
                "contradictions": list(self.contradictions)
            }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Loads facts and contradictions from a dictionary into the graph."""
        with self._lock:
            for fact_dict in data.get("facts", []):
                fact = FactAssertion(**fact_dict)
                self.add_fact(fact)
            for c in data.get("contradictions", []):
                self.contradictions.append(c)

    def get_entity_relationships(self, entity_name: str) -> List[FactAssertion]:
        """Returns all facts where entity_name is either subject or object."""
        with self._lock:
            clean = entity_name.strip().lower()
            return [
                f for f in self.facts 
                if f.subject.lower() == clean or f.object_val.lower() == clean
            ]

    def to_mermaid(self, max_edges: Optional[int] = None) -> str:
        """Generates deterministic, sanitized Mermaid graph definition with unified entity nodes."""
        with self._lock:
            lines = ["graph TD"]
            node_ids: Dict[str, str] = {}

            def _get_node_id(entity: str) -> str:
                clean = entity.strip().lower()
                if clean not in node_ids:
                    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', clean)[:24].strip('_')
                    node_ids[clean] = f"n_{sanitized}_{len(node_ids)}"
                return node_ids[clean]

            facts_to_render = self.facts[:max_edges] if max_edges is not None else self.facts
            for fact in facts_to_render:
                sub_id = _get_node_id(fact.subject)
                obj_id = _get_node_id(fact.object_val)
                clean_sub = fact.subject.replace('"', "'").replace("\n", " ").replace("[", "(").replace("]", ")").strip()
                clean_pred = fact.predicate.replace('"', "'").replace("\n", " ").strip()
                clean_obj = fact.object_val.replace('"', "'").replace("\n", " ").replace("[", "(").replace("]", ")").strip()
                lines.append(f'    {sub_id}["{clean_sub}"] -->|"{clean_pred}"| {obj_id}["{clean_obj}"]')
            return "\n".join(lines)

