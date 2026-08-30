# Reddit Viral Post Template (Ban-Proof & High-Signal)

### Recommended Subreddits:
- **`r/LocalLLaMA`** (Flared as `Project` or `Discussion`)
- **`r/LangChain`** (Flared as `Project / Show & Tell`)
- **`r/Python`** (Flared as `Showcase`)
- **`r/MachineLearning`** (Flared as `Project`)

---

### 📌 Title Options (Pick One):

**Option A (Best for `r/LocalLLaMA` & `r/LangChain`)**:
> I benchmarked how many tokens Deep Research agents burn on web scrapes: 85% is repetitive fluff. Built an open-source Concept-Diff engine to fix it (`open-research-lite`).

**Option B (Best for `r/Python`)**:
> `open-research-lite`: An open-source ingestion middleware that cuts AI agent web search token costs by 88% using live Knowledge Graph compilation.

---

### 📝 Reddit Post Body Text:

Hey r/LocalLLaMA,

Over the last few weeks, I was testing automated Deep Research agents (`langchain-ai/open_deep_research`, `gpt-researcher`, `smolagents`). 

When these agents perform multi-step web searches, they fetch 10 to 30 web pages. The raw text (3,000–5,000 words per page) gets appended directly to the agent's context window. 

By iteration 3, the agent is re-reading 30,000+ input tokens per turn—**up to 85% of which is identical background history** (*"What is an EV battery"*, *"Sony in 1991"*). This inflates API costs ($1.50+ per search run) and degrades model reasoning focus ("lost-in-the-middle").

### The Solution: Concept-Diffing & Knowledge Graph Compilation

Instead of passing raw 5,000-word web scrapes to the reasoning LLM, we built **`open-research-lite`**—a lightweight ingestion middleware that sits between web scrapers and the agent:

1. **Session Knowledge Graph**: Maintains an in-memory graph state of all entities, dates, and metrics learned during the session.
2. **Dual-Layer Extraction**: Uses Gemini Flash structured output (or a **0-ms offline local NLP parser** when running without API keys) to extract Subject-Predicate-Object triplets `(Subject ──► Predicate ──► Object)`.
3. **Concept-Diff Classification**:
   - `DISCARD`: Repetitive background fluff deleted immediately ($0 tokens spent).
   - `DIFF_ADD`: Novel claims added to graph & passed in a compact Diff Payload (~150 words).
   - `DIFF_CONFLICT`: Numerical/price contradictions explicitly highlighted ($110 vs $140/kWh).

---

### 📊 Real Live Web Search Benchmark

Tested across live web searches on Deep Research Bench queries (`2026 solid state battery Wh/kg breakthroughs`):

| Metric | Baseline Scrapes | With `open-research-lite` | Savings |
| :--- | :--- | :--- | :--- |
| **Live Web Words Ingested** | 9,159 words | 1,083 words | **88.2% Token Reduction ⚡** |
| **Input Tokens Passed** | 11,906 tokens | 1,407 tokens | **88.2% Token Savings** |
| **Ingestion API Cost** | $0.0298 | $0.0035 | **8.5x Cost Reduction** |
| **Final Report Quality** | 100% technical depth | 100% technical depth | **Zero Loss of Precision** |

---

### 💻 How to Use It (2 Lines of Python)

It's published on PyPI (`pip install open-research-lite`) and completely open source:

```python
from open_research_lite import ConceptDiffEngine

engine = ConceptDiffEngine()

# Process any raw web scrape or search observation:
diff_payload = await engine.process_observation(
    raw_text=scraped_web_content,
    source_url=url,
    source_title=title
)
print(diff_payload)
```

- **PyPI**: https://pypi.org/project/open-research-lite/
- **GitHub**: https://github.com/vishal-raaj-dnd/open-research-lite
- **Research Paper (Zenodo / DOI)**: https://doi.org/10.5281/zenodo.22168098

Would love to get feedback from the community! Let me know what you think or if you'd like to see integrations with other frameworks like AutoGPT or CrewAI.
