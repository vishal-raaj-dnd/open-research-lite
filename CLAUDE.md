# open research-lite Repository Guide

## Project Description
`open research-lite` is a high-performance, deterministic deep research library and interactive CLI tool. It operates as an alternative to GPT Researcher and SmolAgents, featuring dual-model pipeline execution (Fast LLM for micro-fact diffing and Smart LLM for synthesis), bounded asynchronous concurrency, knowledge graph tracking, and zero hallucination drift.

## Repository Structure

### Root Directory
- `README.md` - Complete project documentation and quickstart guide
- `pyproject.toml` - Python project configuration (v0.3.0)
- `requirements.txt` - Core dependencies
- `cli.py` - Direct CLI launcher (`python cli.py`)
- `open-research.cmd` / `open-research.bat` / `open-research` - Instant custom terminal launchers
- `app.py` - Streamlit research dashboard
- `LICENSE` - MIT License
- `.env.example` - Environment variable template

### Core Package (`src/open_research_lite/`)
- `__init__.py` - Top-level package exports (`Researcher`, `GPTResearcher`, exceptions, models)
- `__main__.py` - Interactive terminal UI with real-time spinners and status panels
- `researcher.py` - Primary `Researcher` class orchestrating parallel ingestion, fact extraction, and report synthesis
- `diff_engine.py` - Micro-fact extraction and novelty/redundancy scoring
- `knowledge_graph.py` - Thread-safe `SessionKnowledgeGraph` for entity-relationship tracking
- `models.py` - Multi-provider LLM factory (Google, OpenAI, Anthropic, Groq, DeepSeek)
- `search.py` - Multi-provider search engine (DuckDuckGo, Tavily, Google, Perplexity)
- `exceptions.py` - Strongly-typed exception hierarchy (`OpenResearchError`, `ConfigurationError`, etc.)
- `telemetry.py` - Thread-safe research metrics, latency, and token cost tracking
- `config.py` - System defaults and settings

### Documentation & Whitepapers (`docs/`)
- `RESEARCH_PAPER.md` - Technical paper on Concept-Diffing vs. ReAct reasoning loops
- `paper.tex` - LaTeX preprint version
- `HUGGINGFACE_LAUNCH_GUIDE.md` - Community deployment guide
- `PR_CONTRIBUTION.md` - Architecture PR templates
- `proposals/` - Community and platform integration proposals

### Benchmarks & Evaluations (`benchmarks/`)
- `benchmark_vs_gpt_researcher.py` - Head-to-head performance benchmarks
- `run_gaia_benchmark.py` - GAIA benchmark runner
- `run_deep_research_benchmark.py` - Deep research benchmark evaluation
- `results/` - Verified benchmark run outputs and scorecards
- `legacy_eval/` - Historical LangGraph evaluation harnesses

### Examples (`examples/`)
- `quickstart_researcher.py` - Library usage example
- `reports/` - Sample research reports across domains

### Tests (`tests/`)
- `test_researcher.py` - Unit tests for Researcher API, dual models, custom search, and exceptions
- `test_concept_diff.py` - Unit tests for ConceptDiffEngine and knowledge graph tracking

## Verification Commands
- `python tests\test_researcher.py` - Run Researcher API test suite
- `python tests\test_concept_diff.py` - Run ConceptDiffEngine test suite
- `python cli.py "query"` - Run headless or interactive CLI