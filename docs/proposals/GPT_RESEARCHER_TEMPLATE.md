### Is your feature request related to a problem? Please describe.

When `gpt-researcher` conducts deep research tasks, it scrapes 15 to 20 web sources per task. Raw HTML/markdown ingestion accumulates massive token bloat (often 50,000+ input tokens per run). Up to 85% of these scraped words consist of identical background history and boilerplate text (*"What is an EV battery"*, *"Sony in 1991"*).

This results in:
1. High LLM API token expenses per research task ($1.00 - $2.00+ per run).
2. Latency and rate-limit bottlenecks during scraping loops.
3. LLM attention degradation ("lost-in-the-middle").

---

### Describe the solution you'd like

We would like to introduce an optional ingestion gatekeeper layer using **`open-research-lite`** (available on PyPI via `pip install open-research-lite`):

1. **Session Knowledge Graph**: Maintains a live in-memory state graph of all assertions, metrics, and dates learned during the research session.
2. **Dual-Layer Fact Extraction**: Uses Gemini Flash structured output (or a 0-ms local NLP parser) to extract Subject-Predicate-Object triplets `(Subject ──► Predicate ──► Object)`.
3. **Concept-Diff Classification**:
   - `DISCARD`: Repetitive background fluff deleted immediately ($0 LLM tokens spent).
   - `DIFF_ADD`: Novel assertions added to graph & passed in compact Diff Payload (~150 words).
   - `DIFF_CONFLICT`: Surfaced price or numerical variances explicitly highlighted ($110 vs $140/kWh).

---

### Describe alternatives you've considered

1. **Vector Chunk Reranking**: Still retains 500-word paragraph chunks containing introductory fluff and fails to detect numerical conflicts across different web pages.
2. **Single-Page Summarizers**: Basic summarizers lose fine-grained numerical metrics/dates and cannot deduplicate content against previously scraped web sources.

---

### Additional context

Empirical benchmark tested on live web searches (`2026 solid state battery Wh/kg breakthroughs`):

| Metric | Raw Scraped Web Pages | With `open-research-lite` | Performance Gain |
| :--- | :--- | :--- | :--- |
| **Live Web Words Ingested** | 9,159 words | 1,083 words | **88.2% Token Reduction ⚡** |
| **Input Tokens Passed** | 11,906 tokens | 1,407 tokens | **88.2% Token Savings** |
| **Ingestion API Cost** | $0.0298 | $0.0035 | **8.5x Cost Reduction** |
| **Final Report Quality** | 100% technical depth | 100% technical depth | **Zero Loss of Information** |

**Python 2-Line Integration Example**:
```python
from open_research_lite import ConceptDiffEngine

engine = ConceptDiffEngine()
diff_payload = await engine.process_observation(scraped_web_content, source_url=url, source_title=title)
```

- **PyPI Package**: [https://pypi.org/project/open-research-lite/](https://pypi.org/project/open-research-lite/)
- **GitHub Repo**: [https://github.com/vishal-raaj-dnd/open-research-lite](https://github.com/vishal-raaj-dnd/open-research-lite)

We would love to submit a PR introducing `open-research-lite` as an optional token-reduction middleware for `gpt-researcher`!
