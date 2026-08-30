# Cold Email / X DM Template for Aravind Srinivas (CEO of Perplexity)

**Subject**: 88% Token Reduction in Web Search Ingestion (Session Knowledge Graph Engine)

Hi Aravind,

Huge fan of Perplexity’s work on Pro Search and Deep Research.

We recently built **`open-research-lite`** (published on PyPI & GitHub), an open-source ingestion middleware that solves the 80% token bloat problem in multi-page web search loops.

### The Core Insight:
Standard RAG relies on 500-token vector paragraph chunks, which re-read 80% background history across search turns. `open-research-lite` shifts the paradigm to **live Session Knowledge Graph Compilation**:
1. Extracts Subject-Predicate-Object triplets `(Subject ──► Predicate ──► Object)`.
2. 0-ms canonical hash deduplication (`DISCARD` fluff).
3. Emits ~150-word **Concept-Diff Payloads** with explicit numerical variance detection ($110 vs $140/kWh).

### Empirical Benchmark (Live Web Search):
- **Raw Web Words Scraped**: 9,159 words ──► **Diff Payload**: 1,083 words (**88.2% Token Reduction ⚡**)
- **Ingestion Cost**: $0.0298 ──► $0.0035 (**8.5x Cost Reduction**)
- **Report Quality**: 100% technical depth retained.

I thought this concept-diff approach might be relevant to Perplexity's ingestion pipeline. 

- **GitHub**: https://github.com/vishal-raaj-dnd/open-research-lite
- **PyPI**: https://pypi.org/project/open-research-lite/

Best regards,  
Vishal Raaj
