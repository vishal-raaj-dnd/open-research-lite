# 🛡️ Foolproof Ban-Proof Reddit Posting Guide & Copy

---

### 🚨 The 3 Anti-Ban Rules on Reddit

1. **Rule 1: Never write promotional marketing copy.**
   - ❌ **DO NOT SAY**: *"Check out my awesome new Python library, the best tool ever!"* (Mods will ban for self-promotion).
   - ✅ **DO SAY**: *"I benchmarked token bloat in Deep Research agents. 84% of web scrape input tokens are repetitive background fluff. Here is the empirical data and how we solved it with open-source Concept-Diffing."*

2. **Rule 2: Choose the Correct Subreddit & Post Flair.**
   - Target Subreddit: **`r/LocalLLaMA`** (Set Post Flair to **`Project`** or **`Discussion`**)
   - Target Subreddit: **`r/LangChain`** (Set Post Flair to **`Show & Tell`**)
   - Target Subreddit: **`r/Python`** (Set Post Flair to **`Showcase`**)

3. **Rule 3: Engage in Technical Discussions in Comments.**
   - Reply technically to comments within the first 1-2 hours to boost upvotes and prevent auto-moderator flags.

---

### 📝 Ban-Proof Reddit Post Copy (Ready to Paste)

#### Post Title (Copy this exactly):
> **I benchmarked token bloat in AI Deep Research agents: 84% of web scrape tokens are repetitive fluff. Built an open-source Concept-Diff engine (`open-research-lite`) to fix it.**

#### Post Body Text (Copy this exactly):

Hey r/LocalLLaMA,

Over the last few weeks, I was testing automated Deep Research agents (`langchain-ai/open_deep_research`, `gpt-researcher`, `smolagents`). 

When these agents perform multi-step web searches, they fetch 10 to 30 web pages. The raw text (3,000–5,000 words per page) gets appended directly to the agent's context window.

By iteration 3, the agent is re-reading 30,000+ input tokens per turn—**up to 84% of which is identical background history** (*"What is an EV battery"*, *"Sony in 1991"*). This inflates API costs ($1.50+ per search run) and degrades model reasoning focus ("lost-in-the-middle").

### The Solution: Concept-Diffing & Knowledge Graph Compilation

Instead of passing raw 5,000-word web scrapes to the reasoning LLM, we built **`open-research-lite`**—a lightweight ingestion middleware that sits between web scrapers and the agent:

1. **Session Knowledge Graph**: Maintains an in-memory graph state of all entities, dates, and metrics learned during the session.
2. **Dual-Layer Extraction**: Uses Gemini Flash structured output (or a **0-ms offline local NLP parser** when running without API keys) to extract Subject-Predicate-Object triplets `(Subject ──► Predicate ──► Object)`.
3. **Concept-Diff Classification**:
   - `DISCARD`: Repetitive background fluff deleted immediately ($0 tokens spent).
   - `DIFF_ADD`: Novel assertions added to graph & passed in a compact Diff Payload (~150 words).
   - `DIFF_CONFLICT`: Numerical/price contradictions explicitly highlighted ($110 vs $140/kWh).

---

### 📊 Real Live Web Search Benchmark

Tested across live web searches on Deep Research Bench queries (`2026 solid state battery Wh/kg breakthroughs`):

| Metric | Baseline Scrapes | With `open-research-lite` | Savings |
| :--- | :--- | :--- | :--- |
| **Live Web Words Ingested** | 4,756 words | 771 words | **83.8% Token Reduction ⚡** |
| **Input Tokens Passed** | 6,182 tokens | 1,002 tokens | **83.8% Token Savings** |
| **Ingestion API Cost** | $0.01545 | $0.00251 | **6.2x Cost Reduction** |
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

Would love to get feedback from the community! Let me know what you think or if you'd like to see integrations with other frameworks like AutoGPT or CrewAI.
