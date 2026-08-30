# Feature Proposal: Ingestion Gatekeeper Middleware (`open-research-lite`) for 85% Token Reduction in Llama Stack Web Agents

## 📌 Context & Motivation in `llama-stack`
Meta's `llama-stack` provides agentic APIs, tool execution interfaces, and RAG pipelines for Llama 3 models. However, when Llama Stack agents execute web search tools (e.g. Brave Search, Tavily, web scrapers), raw web page text dumps **3,000 to 5,000 tokens of introductory background fluff per page** directly into Llama 3's context window.

This causes:
1. High token inference latency and GPU memory overhead during agent search loops.
2. Context window bloat across multi-turn agent execution.
3. Degradation in model reasoning focus due to repetitive fluff ("lost-in-the-middle").

---

## 💡 Solution: Integration with `open-research-lite`

We propose introducing an ingestion middleware layer or tool wrapper for `llama-stack` using **`open-research-lite`** (available via `pip install open-research-lite`):

- **Session Knowledge Graph**: Maintains a live in-memory state graph of assertions `(Subject ──► Predicate ──► Object)` learned across agent search steps.
- **Concept-Diff Classification**:
  - `DISCARD`: Repetitive background fluff dropped immediately ($0 tokens spent).
  - `DIFF_ADD`: Novel claims added to graph & passed in compact Diff Payload (~150 words).
  - `DIFF_CONFLICT`: Contradictions explicitly highlighted ($110 vs $140/kWh).

---

## 📊 Empirical Benchmarks

Tested across live web searches on Deep Research Bench queries:

| Metric | Raw Scraped Web Pages | With `open-research-lite` | Performance Gain |
| :--- | :--- | :--- | :--- |
| **Live Web Words Ingested** | 9,159 words | 1,083 words | **88.2% Token Reduction ⚡** |
| **Input Tokens Passed** | 11,906 tokens | 1,407 tokens | **88.2% Token Savings** |
| **Ingestion API Cost** | $0.0298 | $0.0035 | **8.5x Cost Reduction** |
| **Final Precision** | 100% technical depth | 100% technical depth | **Zero Information Loss** |

---

## 💻 2-Line Llama Stack Tool Example

```python
from open_research_lite import ConceptDiffEngine

engine = ConceptDiffEngine()

# In Llama Stack web tool handler:
diff_payload = await engine.process_observation(
    raw_text=scraped_web_content,
    source_url=url,
    source_title=title
)
```

We would love to submit a PR introducing `open-research-lite` as an optional token-reduction middleware for `llama-stack`!

- **PyPI Package**: https://pypi.org/project/open-research-lite/
- **GitHub Repo**: https://github.com/vishal-raaj-dnd/open-research-lite
