---
title: open research-lite
colorFrom: red
colorTo: crimson
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Autonomous Deep Research Agent with Differential Knowledge Graphs and Dual-Model Architecture
tags:
  - deep-research
  - llm-agents
  - gpt-researcher
  - knowledge-graph
  - agentic-rag
  - token-optimization
  - dual-model
  - paper:10.5281/zenodo.22168098
---

# open research-lite

> **Autonomous Deep Research Agent with Differential Knowledge Graphs and Dual-Model Pipeline**  
> *Slashes 70–85% token bloat, extracts atomic fact assertions, catches metric contradictions deterministically, and synthesizes executive research dossiers.*

[![PyPI version](https://img.shields.io/pypi/v/open-research-lite.svg)](https://pypi.org/project/open-research-lite/)
[![Tests](https://img.shields.io/badge/tests-16%2F16%20passing-brightgreen.svg)](#testing--verification)
[![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-red.svg)](https://www.python.org/downloads/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22168098.svg)](https://doi.org/10.5281/zenodo.22168098)
[![Token Savings](https://img.shields.io/badge/Token_Reduction-70%25+-red.svg)](#why-open-research-lite-over-gpt-researcher)

---

## Why open research-lite over GPT-Researcher?

In conventional research agents (such as GPT-Researcher), over **70% to 85% of prompt tokens** are consumed ingesting repetitive introductory fluff, boilerplate history, and SEO prose across multi-page web search streams. Furthermore, GPT-Researcher's "Fast LLM" is only used for generating search sub-queries, while raw scraped web pages (50,000+ tokens) are dumped directly into the expensive "Smart LLM". When two sources present divergent metrics (for example, `26W` vs `31W` peak package power), conventional agents silently average or hallucinate.

`open research-lite` introduces an architectural layer add-on with **Session Knowledge-State Tracking ($G_t = G_{t-1} \cup \Delta G_t$)** that supercharges the Fast LLM & Smart LLM pipeline:

1. **Fast LLM (`fast_llm` / `extractor_model`)**: A fast, cost-efficient model (e.g., `gemini-2.5-flash`, `gpt-4o-mini`, `claude-3-5-haiku`, `llama-3.1-8b`) acts as an intelligent gatekeeper. It sifts raw web scrapes, isolates Subject-Predicate-Object triplets and quantitative metrics, prunes 70%+ redundant text, and detects metric contradictions.
2. **Smart LLM (`smart_llm` / `writer_model`)**: A flagship reasoning model (e.g., `claude-3-5-sonnet`, `gpt-4o`, `gemini-2.5-pro`, `o1`, `deepseek-r1`) receives only the high-signal, distilled differential graph assertions (~1,200 tokens instead of 50,000+ raw tokens) and writes a comprehensive, structured research dossier.

| Capability | GPT-Researcher | open research-lite | Why It Matters |
| :--- | :---: | :---: | :--- |
| **Ingestion Pipeline** | Raw document stuffing (50k+ tokens) | **Dual-Model Differential Graph** | **70%+ Cheaper API costs and sub-second synthesis** |
| **Fast LLM Role** | Search sub-query generator only | **Fact Extractor & Contradiction Radar** | Converts raw scrapes into verified fact graph |
| **Contradiction Detection** | None (silently averages) | **Deterministic Contradiction Radar** | Flags real metric disputes across sources |
| **Visual Knowledge Graph** | None | **Interactive HTML / Mermaid Dossier** | Visual entity relationship mapping |
| **Interactive Terminal UI** | Basic stdout | **Crimson Terminal Dashboard (Claude Code-inspired)** | Full model dropdowns, live progress, metric scorecards |
| **Multi-Tenancy & Isolation** | Varies | **Thread-Safe Session Isolation** | Zero state leakage between concurrent runs |
| **Drop-in Compatibility** | `GPTResearcher` | **`from open_research_lite import GPTResearcher`** | 1-line seamless replacement |

---

## Quickstart

### 1. Installation

```bash
pip install open-research-lite
```

### 2. Custom Terminal Commands (No `python -m` Required)

Launch deep autonomous research straight from your terminal using custom executable commands:

```bash
# Windows
.\open-research "High-Bandwidth Memory HBM4 Architecture and Interconnect Scaling"

# Or run the interactive crimson TUI wizard
.\open-research
```

```bash
# macOS / Linux
./open-research "Fault-Tolerant Quantum Computing and Surface Code Thresholds"
```

*Automatically generates both a clean Markdown dossier (`research_report.md`) and a standalone visual HTML report (`research_report.html`) with embedded interactive Mermaid knowledge graphs!*

---

### 3. Supported Production Models

`open research-lite` supports 18+ production models selectable directly from interactive dropdowns:

- **Google**: Gemini 2.5 Flash, Gemini 2.5 Pro
- **OpenAI**: GPT-4o, GPT-4o Mini, GPT-4.1, o1, o3-mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
- **DeepSeek**: DeepSeek-R1, DeepSeek-V3
- **Meta / Groq**: Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B
- **Mistral**: Mistral Large, Mistral Small

---

### 4. Python API (Drop-in GPT-Researcher Replacement)

Use `open research-lite` as a drop-in replacement for GPT-Researcher with identical `fast_llm` and `smart_llm` parameters:

```python
import asyncio
from open_research_lite import GPTResearcher, Researcher

async def main():
    # 1. Initialize Researcher with Fast LLM and Smart LLM
    researcher = GPTResearcher(
        query="High-Bandwidth Memory HBM4 Architecture Trends",
        report_type="research_report",
        fast_llm="gpt-4o-mini",               # Fast LLM for fact extraction & graph building
        smart_llm="claude-3-5-sonnet-latest", # Smart LLM for analytical dossier writing
        search_api="tavily",                  # Or "duckduckgo" for free search
        max_results=5
    )

    # 2. Conduct research (extracts facts and updates session graph)
    await researcher.conduct_research()

    # 3. Synthesize structured report
    report = await researcher.write_report()
    print(report)

    # 4. Export visual HTML dossier and Markdown
    researcher.export_markdown("hbm4_report.md")
    researcher.export_html("hbm4_dossier.html")

    # 5. Inspect telemetry & graph stats
    stats = researcher.get_stats()
    print(f"Token reduction: {stats['telemetry']['token_reduction_pct']}%")
    print(f"Verified assertions: {stats['graph']['total_facts']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 5. Standalone Middleware Usage (for LangGraph, CrewAI, AutoGPT)

You can use the core `ConceptDiffEngine` as gatekeeper middleware for existing agent architectures:

```python
import asyncio
from open_research_lite import ConceptDiffEngine

async def main():
    engine = ConceptDiffEngine(model_name="gemini-2.5-flash")

    raw_scrape = """
    High-Bandwidth Memory (HBM) stacks integrate multiple DRAM dies via TSVs.
    In 2026, engineers validated an HBM4 memory stack delivering 2.8 TB/s peak bandwidth per stack.
    Operating power consumption is measured at 26W under full saturation.
    """

    # Intercept raw scrape and convert into dense diff payload
    diff_payload = await engine.process_observation(
        raw_text=raw_scrape,
        source_url="https://semiconductor-audit.org/hbm4-2026",
        source_title="HBM4 Interface Milestone"
    )

    print(diff_payload)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Interactive Visual HTML Dossier

Every research mission exports an interactive dark-mode HTML dossier containing:
1. **Mermaid.js Knowledge Graph**: Pan, zoom, and inspect verified entity links and relationships.
2. **Contradiction Radar**: Callout cards highlighting conflicting claims between sources.
3. **Efficiency Scorecard**: Raw input tokens, pruned redundant tokens, and unique mapped entities.
4. **Structured Executive Dossier**: Executive summary, key metrics, and linked source citations.

---

## Repository Structure

```text
open-research-lite/
├── src/
│   └── open_research_lite/         # Production package (v0.3.1)
│       ├── __init__.py             # Top-level exports (Researcher, GPTResearcher, exceptions)
│       ├── __main__.py             # Interactive crimson TUI wizard
│       ├── researcher.py           # Core orchestrator with bounded async concurrency
│       ├── diff_engine.py          # Differential fact extraction & contradiction engine
│       ├── knowledge_graph.py      # Thread-safe SessionKnowledgeGraph (RLock)
│       ├── models.py               # Multi-provider LLM factory (Google, OpenAI, Anthropic, etc.)
│       ├── exceptions.py           # Typed exception hierarchy
│       └── telemetry.py            # Token cost and latency metrics
├── docs/                           # Whitepapers, technical specifications & proposals
│   ├── RESEARCH_PAPER.md           # Formal paper on Concept-Diffing architecture
│   ├── paper.tex                   # LaTeX preprint
│   └── proposals/                  # Platform integration proposals
├── benchmarks/                     # GAIA & deep research benchmarks and verified results
│   ├── results/                    # Benchmark scorecards and evaluation outputs
│   └── legacy_eval/                # Historical benchmark harnesses
├── examples/                       # Developer guides & quickstart scripts
│   ├── quickstart_researcher.py    # Complete Python API walkthrough
│   └── reports/                    # Domain-specific sample reports
├── tests/                          # Production unit & integration test suites (16/16 passing)
│   ├── test_researcher.py          # Researcher API, dual models, custom search tests
│   └── test_concept_diff.py        # Fact diffing and knowledge graph tests
├── cli.py                          # Direct launcher
├── open-research.cmd               # Custom Windows terminal command
└── pyproject.toml                  # Package configuration (v0.3.1)
```

---

## Enterprise Production Features (v0.3.1)

- **Zero Silent Fallback**: Web search failures and credential gaps explicitly raise typed `ConfigurationError` or `SearchProviderError` rather than silently degrading.
- **Structured Search Ingestion**: DuckDuckGo and Tavily ingest discrete per-source records with real URLs, page titles, and snippets instead of single monolithic text blobs.
- **Native Model Output Ceilings**: Dynamic resolution sets exact physical output limits (64k for Claude 3.7, 8,192 for Claude 3.5 Sonnet/Haiku, 4,096 for Opus), preventing HTTP 400 Bad Request errors.
- **Automatic Provider Resolution**: `get_default_models()` auto-detects configured environment keys (Gemini $\to$ OpenAI $\to$ Anthropic $\to$ Groq $\to$ DeepSeek $\to$ Mistral) for true zero-config operation.
- **Bounded Asynchronous Concurrency**: Parallel source processing via `asyncio.Semaphore(max_concurrency)` prevents API rate limits and thread starvation during web crawls.
- **Custom Search Provider Injection**: Supply your own search callback (`search_func`) to query internal enterprise databases, vector indices, or proprietary APIs seamlessly.
- **Structured JSON Export**: Call `export_json("output.json")` or `to_dict()` to ingest research graph nodes, facts, contradiction warnings, and telemetry directly into microservice pipelines.
- **Strongly-Typed Exceptions**: Catch granular errors (`ConfigurationError`, `SearchProviderError`, `FactExtractionError`, `ReportSynthesisError`) without unhandled crashes or silent mock fallbacks.
- **Thread-Safe Multi-Tenancy**: `SessionKnowledgeGraph` and `TelemetryTracker` employ reentrant locking (`threading.RLock`) to guarantee complete thread safety across parallel worker threads.

---

## Testing & Verification

```bash
# Run the complete test suite (16 tests)
pytest tests/ -v

# Or run individual test scripts
python tests/test_concept_diff.py
python tests/test_researcher.py

# Run quickstart demo
python examples/quickstart_researcher.py
```

---

## Citation

```bibtex
@article{openresearchlite2026,
  title={Differential Knowledge-State Tracking for Token-Efficient Autonomous Deep Research Agents},
  author={open research-lite Team},
  year={2026},
  doi={10.5281/zenodo.22168098}
}
```

## License
MIT License. Open source and production ready.

