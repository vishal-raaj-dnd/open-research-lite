# open-research-lite ⚡

![open-research-lite Banner](assets/banner.png)

> **Token-Efficient Ingestion Middleware & Concept-Diff Engine for Deep Research AI Agents**

[![PyPI version](https://img.shields.io/pypi/v/open-research-lite.svg)](https://pypi.org/project/open-research-lite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Token Savings](https://img.shields.io/badge/Token_Savings-85%25-green.svg)](#benchmark--scorecard)

`open-research-lite` is an intelligent, high-performance gatekeeper layer designed for AI Research Agents (such as `langchain-ai/open_deep_research`, `gpt-researcher`, `smolagents`, `AutoGPT`, `CrewAI`, or custom LangGraph workflows). 

It solves the **Extreme Token Bloat & Repetitive Fluff** flaw in existing deep research systems by shifting the paradigm from *"Read raw 5,000-word scraped web pages"* to **"Compile knowledge incrementally into a live Session Knowledge Graph."**

---

## 🚀 Key Features

* **Dual-Layer Extraction Architecture**:
  - **Layer 1 (LLM Mode)**: Sub-second structured JSON triplet extraction `(Subject ──► Predicate ──► Object)` via **Gemini 2.5 Flash** or **OpenAI Mini** when an API key is available.
  - **Layer 2 (Professional Local NLP Mode)**: 0-ms offline local NLP parser (regex metric extraction, grammar triplet matching, entity resolution) when running without API keys.
* **Session Knowledge Graph**: Maintains an in-memory graph state of all entities, metrics, and claims learned during a research session.
* **Concept-Diff Engine**: Classifies scraped facts into 3 categories:
  - `DISCARD`: Repetitive background fluff deleted immediately ($0 LLM tokens spent).
  - `DIFF_ADD`: Novel assertions added to graph & passed in Diff Payload.
  - `DIFF_CONFLICT`: Contradictory statements (e.g. $110 vs $140/kWh) explicitly flagged.
* **80%+ Token & Cost Reduction**: Delivers a ~150-word **Diff Payload** to the main reasoning model instead of 5,000 words of background history.

---

## ⚡ Quickstart

### 1. Installation

```bash
pip install -e .
```

### 2. Basic Usage (Python API)

```python
import asyncio
from open_deep_research.concept_diff import ConceptDiffEngine

async def main():
    # Automatically uses GEMINI_API_KEY if present, otherwise uses Professional Local NLP
    engine = ConceptDiffEngine()

    raw_scraped_text = """
    Electric vehicles have become popular over the last decade... 
    Lithium-ion batteries were invented by John Goodenough...
    In 2026, researchers demonstrated a solid-state cell achieving 500 Wh/kg energy density.
    Target production cell cost is $110/kWh.
    """

    # Process raw scrape into a condensed Diff Payload
    diff_payload = await engine.process_observation(
        raw_text=raw_scraped_text,
        source_url="https://tech-news.com/ev-batteries",
        source_title="EV Battery 2026 Report"
    )

    print(diff_payload)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Benchmark & Scorecard

Running `DeepResearch-Lite` on real web searches (`2026 solid state battery Wh/kg breakthroughs`):

```
===========================================================================
🏆 DEEPRESEARCH-LITE HACKATHON SCORECARD
===========================================================================
METRIC                         | BASELINE AGENT     | DEEPRESEARCH-LITE 
---------------------------------------------------------------------------
Live Web Words Fetched         | 9,159 words        | 1,083 words       
Input Tokens Passed to LLM     | 11,906 tokens      | 1,407 tokens      
Estimated Cost per Search Run  | $0.0298            | $0.0035           
Token Reduction                | 0% (Full Bloat)    | 88.2% SAVED ⚡     
Fact-to-Fluff Signal Ratio     | ~15% High Signal   | ~95% High Signal ⚡
===========================================================================
```

---

## 🛠️ Framework Integration

### LangGraph / open_deep_research Integration
`DeepResearch-Lite` integrates seamlessly into `open_deep_research/deep_researcher.py` at the `researcher_tools()` node:

```python
from open_deep_research.concept_diff import ConceptDiffEngine

diff_engine = ConceptDiffEngine()

# In researcher_tools():
processed_observations = []
for obs, tool_call in zip(observations, tool_calls):
    if len(obs) > 100:
        diff_payload = await diff_engine.process_observation(obs, source_title=tool_call['name'])
        processed_observations.append(diff_payload)
```

---

## 🧪 Testing & Demonstration Scripts

- **Run Unit Tests**:
  ```bash
  python -m pytest tests/test_concept_diff.py
  ```

- **Run Side-by-Side Hackathon Benchmark**:
  ```bash
  python demo_comparison.py
  ```

- **Run Live Internet Search Comparison**:
  ```bash
  python run_live_test.py "your custom research prompt"
  ```

---

## 📄 License
MIT License. Free for open-source and commercial use.
