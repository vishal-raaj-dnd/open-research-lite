"""Session Knowledge Graph implementation for open-research-lite.

Maintains live, in-memory graph state of accumulated factual assertions,
metrics, entity relationships, and source citations for a research session.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class FactAssertion(BaseModel):
    """An atomic factual claim extracted from a web source."""
    subject: str = Field(description="Normalized subject/entity name")
    predicate: str = Field(description="Relationship or property verb/name")
    object_val: str = Field(description="Target entity, status, or numerical value")
    is_numeric: bool = Field(default=False, description="Whether object_val contains a numerical stat/metric")
    source_url: str = Field(default="", description="Source URL of origin")
    source_title: str = Field(default="", description="Title of the source web page")
    context_snippet: str = Field(default="", description="Brief original sentence for evidence verification")

    def canonical_key(self) -> str:
        """Returns a normalized string hash key for fast exact matching."""
        s = re.sub(r'\W+', '', self.subject.lower())
        p = re.sub(r'\W+', '', self.predicate.lower())
        o = re.sub(r'\W+', '', self.object_val.lower())
        return f"{s}:{p}:{o}"

    def subject_predicate_key(self) -> str:
        """Returns a key representing subject and predicate (useful for numeric conflict checks)."""
        s = re.sub(r'\W+', '', self.subject.lower())
        p = re.sub(r'\W+', '', self.predicate.lower())
        return f"{s}:{p}"


class SessionKnowledgeGraph:
    """Live in-memory state graph tracking all facts learned in a research session."""

    def __init__(self):
        # Canonical hash set for 0-ms exact match lookups
        self._exact_keys: Set[str] = set()
        
        # Subject+Predicate -> List[FactAssertion] for conflict checking
        self._sp_index: Dict[str, List[FactAssertion]] = {}
        
        # All stored unique facts
        self.facts: List[FactAssertion] = []
        
        # Unique entities
        self.entities: Set[str] = set()

    def is_exact_duplicate(self, fact: FactAssertion) -> bool:
        """Check if exact fact is already in the knowledge graph (0 ms cost)."""
        return fact.canonical_key() in self._exact_keys

    def find_conflict(self, fact: FactAssertion) -> Optional[FactAssertion]:
        """Detect if incoming fact contradicts an existing fact for the same subject & predicate."""
        sp_key = fact.subject_predicate_key()
        if sp_key not in self._sp_index:
            return None
        
        for existing in self._sp_index[sp_key]:
            if existing.object_val.strip().lower() != fact.object_val.strip().lower():
                return existing
        return None

    def add_fact(self, fact: FactAssertion) -> bool:
        """Add a new fact to the knowledge graph. Returns True if novel, False if already present."""
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
        self.entities.add(fact.object_val)
        return True

    def get_stats(self) -> Dict[str, int]:
        """Return graph node & edge counts."""
        return {
            "total_facts": len(self.facts),
            "total_entities": len(self.entities),
            "unique_subject_predicates": len(self._sp_index)
        }

    def to_mermaid(self) -> str:
        """Generate a Mermaid diagram string representing the knowledge graph."""
        lines = ["graph TD"]
        for i, fact in enumerate(self.facts[:30]):
            sub_id = f"sub_{hash(fact.subject) % 10000}"
            obj_id = f"obj_{hash(fact.object_val) % 10000}"
            clean_sub = fact.subject.replace('"', "'")
            clean_pred = fact.predicate.replace('"', "'")
            clean_obj = fact.object_val.replace('"', "'")
            lines.append(f'    {sub_id}["{clean_sub}"] -->|"{clean_pred}"| {obj_id}["{clean_obj}"]')
        return "\n".join(lines)
