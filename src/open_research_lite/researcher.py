"""High-level autonomous research agent for open-research-lite.

Provides a drop-in API similar to GPT-Researcher, powered by differential
knowledge-state tracking and concept-diff ingestion to eliminate token bloat.
"""

import asyncio
import logging
import os
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from open_research_lite.diff_engine import ConceptDiffEngine
from open_research_lite.knowledge_graph import SessionKnowledgeGraph, FactAssertion
from open_research_lite.telemetry import TelemetryTracker
from open_research_lite.exceptions import (
    OpenResearchError,
    SearchProviderError,
    ReportSynthesisError,
    ConfigurationError
)

logger = logging.getLogger("open_research_lite.researcher")


class Researcher:
    """Production research agent with differential knowledge-graph middleware."""

    def __init__(
        self,
        query: str,
        report_type: str = "research_report",
        search_api: str = "auto",
        max_results: int = 5,
        max_concurrency: int = 4,
        search_func: Optional[Callable[[str, int], Awaitable[List[Dict[str, str]]]]] = None,
        model_name: Optional[str] = None,
        writer_model: Optional[str] = None,
        extractor_model: Optional[str] = None,
        fast_llm: Optional[str] = None,
        fast_llm_model: Optional[str] = None,
        smart_llm: Optional[str] = None,
        smart_llm_model: Optional[str] = None,
        api_key: Optional[str] = None,
        writer_api_key: Optional[str] = None,
        extractor_api_key: Optional[str] = None,
        extractor: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
    ):
        self.query = query.strip()
        self.report_type = report_type
        self.search_api = search_api.lower()
        self.max_results = max_results
        self.max_concurrency = max(1, max_concurrency)
        self.search_func = search_func
        self.max_tokens = max_tokens
        
        # Dual-Model Architecture:
        # Resolve models dynamically based on available API keys if not explicitly provided
        from open_research_lite.models import resolve_api_key, get_default_models
        default_ext, default_writer = get_default_models()

        self.extractor_model = extractor_model or fast_llm or fast_llm_model or default_ext
        self.writer_model = writer_model or smart_llm or smart_llm_model or model_name or default_writer
        self.fast_llm = self.extractor_model
        self.smart_llm = self.writer_model
        self.model_name = self.writer_model

        self.writer_api_key = writer_api_key or resolve_api_key(self.writer_model) or api_key
        self.extractor_api_key = extractor_api_key or resolve_api_key(self.extractor_model) or api_key
        self.api_key = self.writer_api_key
        self.verbose = verbose

        # Isolated per-session components (no global singleton leakage)
        self.graph = SessionKnowledgeGraph()
        self.telemetry = TelemetryTracker()
        self.engine = ConceptDiffEngine(
            graph=self.graph,
            telemetry=self.telemetry,
            api_key=self.extractor_api_key,
            model_name=self.extractor_model,
            extractor=extractor
        )

        self.sources: List[Dict[str, str]] = []
        self.diff_payloads: List[str] = []
        self.report: str = ""
        self._has_researched: bool = False

    async def conduct_research(
        self, 
        custom_sources: Optional[List[Dict[str, str]]] = None
    ) -> List[str]:
        """Runs the search loop and processes raw observations through the ConceptDiffEngine concurrently."""
        if custom_sources is not None:
            self.sources = custom_sources
        else:
            self.sources = await self._fetch_sources()

        self.diff_payloads.clear()
        self._has_researched = True

        # Concurrent bounded ingestion prevents worker thread bottleneck
        sem = asyncio.Semaphore(self.max_concurrency)

        async def _ingest_source(source: Dict[str, str]) -> Optional[str]:
            title = source.get("title", "Web Source")
            url = source.get("url", "")
            raw_content = source.get("content", "") or source.get("raw_content", "")

            if not raw_content:
                return None

            async with sem:
                diff_payload = await self.engine.process_observation(
                    raw_text=raw_content,
                    source_url=url,
                    source_title=title
                )
                if self.verbose:
                    logger.info(f"Ingested '{title}' -> {len(diff_payload.split())} diff words.")
                return diff_payload

        tasks = [_ingest_source(s) for s in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, r in enumerate(results):
            if isinstance(r, BaseException):
                src_title = self.sources[i].get("title", self.sources[i].get("url", f"source[{i}]"))
                logger.error(f"Failed to process source '{src_title}': {r}")
            elif r is not None:
                self.diff_payloads.append(r)

        return self.diff_payloads

    async def write_report(self, custom_prompt: Optional[str] = None) -> str:
        """Synthesizes a structured research report from the knowledge graph and diff payloads."""
        if not self._has_researched:
            await self.conduct_research()

        context_data = self.get_research_context()


        # 1. If LLM API key is present, generate report via writer model
        if self.writer_api_key:
            try:
                self.report = await self._generate_report_llm(context_data, custom_prompt)
                return self.report
            except Exception as e:
                logger.error(f"Remote LLM report synthesis failed: {e}")
                raise ReportSynthesisError(f"Smart LLM synthesis failed using {self.writer_model}: {e}") from e

        # 2. Local deterministic report synthesis from knowledge graph facts & diffs
        self.report = self._generate_report_deterministic(custom_prompt)
        return self.report

    async def _fetch_sources(self) -> List[Dict[str, str]]:
        """Executes search based on configured backend with zero silent fallbacks."""
        # 0. Custom search callable (Enterprise / Custom Vector DB)
        if self.search_func:
            try:
                custom_results = await self.search_func(self.query, self.max_results)
                if isinstance(custom_results, list) and len(custom_results) > 0:
                    return custom_results
            except Exception as e:
                logger.error(f"Custom search provider failed: {e}")
                raise SearchProviderError(f"Custom search provider execution failed: {e}") from e

        # Resolve provider
        chosen_provider = self.search_api
        if chosen_provider == "auto":
            chosen_provider = "tavily" if os.getenv("TAVILY_API_KEY") else "duckduckgo"

        # 1. Tavily Search (Strict, no silent degradation)
        if chosen_provider == "tavily":
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key:
                raise ConfigurationError(
                    "Tavily search provider selected but TAVILY_API_KEY is not set. "
                    "Set TAVILY_API_KEY in environment or use search_api='duckduckgo'."
                )
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=tavily_key)
                response = client.search(
                    query=self.query,
                    max_results=self.max_results,
                    search_depth="advanced",
                    include_raw_content=True
                )
                results = []
                for item in response.get("results", []):
                    results.append({
                        "title": item.get("title", "Web Result"),
                        "url": item.get("url", ""),
                        "content": item.get("raw_content") or item.get("content", "")
                    })
                if results:
                    return results
                raise SearchProviderError(f"Tavily returned 0 search results for query: '{self.query}'.")
            except Exception as e:
                if isinstance(e, (ConfigurationError, SearchProviderError)):
                    raise
                logger.error(f"Tavily search failed: {e}")
                raise SearchProviderError(f"Tavily search failed: {e}") from e

        # 2. DuckDuckGo Search (Multi-tier resilient search: ddgs -> duckduckgo_search -> langchain -> direct HTML)
        elif chosen_provider == "duckduckgo":
            # Tier 1: Direct ddgs / duckduckgo_search library
            try:
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS  # type: ignore

                with DDGS() as ddgs_client:
                    raw_items = list(ddgs_client.text(self.query, max_results=self.max_results))
                if raw_items:
                    results = []
                    for item in raw_items:
                        results.append({
                            "title": item.get("title", f"Web result for {self.query}"),
                            "url": item.get("href", item.get("link", "https://duckduckgo.com")),
                            "content": item.get("body", item.get("snippet", ""))
                        })
                    if results:
                        return results
            except Exception as ddgs_err:
                logger.debug(f"Direct DDGS search failed, attempting langchain wrapper: {ddgs_err}")

            # Tier 2: LangChain DuckDuckGoSearchResults wrapper
            try:
                from langchain_community.tools import DuckDuckGoSearchResults
                ddg = DuckDuckGoSearchResults(max_results=self.max_results, output_format="list")
                raw_res = ddg.run(self.query)
                if isinstance(raw_res, list) and len(raw_res) > 0:
                    results = []
                    for item in raw_res:
                        if isinstance(item, dict):
                            results.append({
                                "title": item.get("title", f"Web result for {self.query}"),
                                "url": item.get("link", "https://duckduckgo.com"),
                                "content": item.get("snippet", "")
                            })
                    if results:
                        return results
                elif isinstance(raw_res, str) and raw_res.strip():
                    return [{
                        "title": f"Web results for {self.query}",
                        "url": "https://duckduckgo.com",
                        "content": raw_res
                    }]
            except Exception as lc_err:
                logger.debug(f"LangChain DDG search failed, attempting HTML fallback: {lc_err}")

            # Tier 3: Native direct HTTP HTML scraping via requests & BeautifulSoup
            try:
                import requests
                from bs4 import BeautifulSoup
                resp = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": self.query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = []
                    for item in soup.find_all("div", class_="result__body")[:self.max_results]:
                        title_elem = item.find("a", class_="result__url") or item.find("h2")
                        snippet_elem = item.find("a", class_="result__snippet")
                        url_elem = item.find("a", class_="result__url")
                        if title_elem:
                            raw_link = url_elem.get("href", "") if url_elem else "https://duckduckgo.com"
                            results.append({
                                "title": title_elem.get_text(strip=True),
                                "url": raw_link,
                                "content": snippet_elem.get_text(strip=True) if snippet_elem else ""
                            })
                    if results:
                        return results
            except Exception as html_err:
                logger.debug(f"Direct HTML fallback failed: {html_err}")

            raise SearchProviderError(
                f"DuckDuckGo search failed across all mechanisms for query: '{self.query}'. "
                "Please verify your network connection or install ddgs: `pip install -U ddgs`."
            )

        else:
            raise ConfigurationError(
                f"Unsupported search provider '{self.search_api}'. Must be 'tavily', 'duckduckgo', or 'auto'."
            )


    async def _generate_report_llm(self, context_data: str, custom_prompt: Optional[str]) -> str:
        prompt = custom_prompt or (
            f"You are an elite principal research scientist and technical intelligence director.\n"
            f"Synthesize an unconstrained, deeply rigorous, publication-grade comprehensive research dossier on the topic: '{self.query}'.\n\n"
            f"QUALITY & DEPTH DIRECTIVE:\n"
            f"- Do not summarize superficially, truncate, or abbreviate. Provide exhaustive, granular technical explanations, quantitative precision, and systematic analysis.\n"
            f"- Ground every assertion, data point, and architectural claim directly in the verified empirical facts and concept-diff observations provided below.\n"
            f"- Structure the dossier into the following authoritative sections with clear, hierarchical markdown headers:\n\n"
            f"# Executive Summary & Strategic Brief\n"
            f"- Core thesis, key architectural breakthroughs, and high-impact executive takeaways.\n\n"
            f"# Technical Architecture & Foundational Mechanics\n"
            f"- Deep, step-by-step exposition of system mechanics, physical constraints, material/software interfaces, and design novelties.\n\n"
            f"# Quantitative Benchmark & Metrics Matrix\n"
            f"- Provide an exhaustive Markdown comparison table comparing all verified metrics:\n"
            f"| Entity / Subsystem | Metric / Parameter | Value / Measurement | Operating Condition / Context | Source Citation |\n\n"
            f"# Engineering Trade-Offs, Thermals, Scalability & Failure Modes\n"
            f"- Exhaustive breakdown of trade-offs (e.g. throughput vs. latency, thermal dissipation vs. power density, packaging complexity vs. yield rate).\n"
            f"- Known failure modes, bottlenecks, and boundary vulnerabilities.\n\n"
            f"# Contradiction, Divergence & Consensus Analysis\n"
            f"- Detailed examination of conflicting measurements or competing industry narratives identified across the sources, detailing technical explanations for divergence.\n\n"
            f"# Strategic Outlook & Industry Roadmap\n"
            f"- Commercialization timelines, standards standardization, economic feasibility, and future technological milestones.\n\n"
            f"# Verified Bibliographic References\n"
            f"- Complete list of all investigated sources with hyperlinked titles and URLs.\n\n"
            f"VERIFIED RESEARCH CONTEXT:\n{context_data}\n"
        )

        from open_research_lite.models import get_chat_model, with_retry
        llm = get_chat_model(self.writer_model, self.writer_api_key, max_tokens=self.max_tokens)

        res = await with_retry(lambda: llm.ainvoke(prompt))
        report_text = str(res.content).strip()
        attribution = f"\n\n---\n*Synthesized by: {self.writer_model} (Fact-filtered via: {self.extractor_model}) via open research-lite*"
        return report_text + attribution

    def _generate_report_deterministic(self, custom_prompt: Optional[str]) -> str:
        """Synthesizes a structured report directly from verified knowledge graph facts."""
        lines = [
            f"# Research Report: {self.query}",
            f"> *Synthesized by: Local Deterministic Engine via open research-lite*",
            "",
            "## 1. Executive Summary",
            f"This report synthesizes verified factual assertions regarding **{self.query}** "
            f"across {len(self.sources)} investigated sources.",
            "",
            "## 2. Key Verified Findings & Technical Metrics",
        ]

        metric_facts = [f for f in self.graph.facts if f.is_numeric]
        general_facts = [f for f in self.graph.facts if not f.is_numeric]

        if metric_facts:
            lines.append("### Key Metrics:")
            for f in metric_facts:
                cond = f" *(under: {f.condition})*" if f.condition else ""
                lines.append(f"- **{f.subject}** [{f.predicate}]: `{f.object_val}`{cond}")
            lines.append("")

        if general_facts:
            lines.append("### Key Assertions:")
            for f in general_facts:
                lines.append(f"- **{f.subject}** {f.predicate} {f.object_val}.")
            lines.append("")

        if not self.graph.facts:
            lines.append("*No discrete atomic assertions were isolated.*")

        if self.graph.contradictions:
            lines.extend([
                "## 3. Key Controversies & Conflicting Claims",
            ])
            for c in self.graph.contradictions:
                lines.append(f"- **{c.get('subject', 'Entity')}**: Claim 1: `{c.get('claim_a', '')}` vs Claim 2: `{c.get('claim_b', '')}`. *Reasoning*: {c.get('reasoning', '')}")
            lines.append("")

        lines.extend([
            "## 4. Knowledge Graph Overview",
            f"- **Total Distinct Entities**: {len(self.graph.entities)}",
            f"- **Total Verified Facts**: {len(self.graph.facts)}",
            "",
            "## 5. Source Citations & References",
        ])

        for s in self.sources:
            title = s.get("title", "Web Source")
            url = s.get("url", "")
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")

        return "\n".join(lines)

    def get_research_context(self) -> str:
        """Returns concatenated markdown diff payloads representing high-SNR research context."""
        return "\n\n---\n\n".join(self.diff_payloads)

    def get_knowledge_graph(self) -> SessionKnowledgeGraph:
        """Returns the active session knowledge graph."""
        return self.graph

    def get_stats(self) -> Dict[str, Any]:
        """Returns telemetry and graph statistics."""
        return {
            "telemetry": self.telemetry.get_summary(),
            "graph": self.graph.get_stats(),
            "sources_count": len(self.sources)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Returns the full research session state as a structured dictionary."""
        return {
            "query": self.query,
            "report_type": self.report_type,
            "fast_llm": self.extractor_model,
            "smart_llm": self.writer_model,
            "search_api": self.search_api,
            "sources": self.sources,
            "report": self.report,
            "diff_payloads": self.diff_payloads,
            "knowledge_graph": self.graph.to_dict(),
            "telemetry": self.telemetry.get_summary(),
        }

    def export_json(self, filepath: str = "research_report.json") -> str:
        """Saves the complete research mission as structured JSON."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return filepath

    def export_markdown(self, filepath: str = "research_report.md") -> str:
        """Saves report to a clean Markdown file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.report)
        return filepath

    def export_html(self, filepath: str = "research_report.html") -> str:
        """Exports a standalone interactive HTML dossier with embedded visual knowledge graph."""
        tel = self.telemetry.get_summary()
        stats = self.graph.get_stats()
        mermaid_code = self.graph.to_mermaid()

        # Convert inline markdown tokens to HTML elements
        def _format_inline(txt: str) -> str:
            # Code
            txt = re.sub(r'`([^`]+)`', r'<code>\1</code>', txt)
            # Bold
            txt = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', txt)
            # Italic
            txt = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', txt)
            # Links
            txt = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', txt)
            return txt

        body_html = []
        for line in self.report.split("\n"):
            line = line.strip()
            if not line:
                body_html.append("<br/>")
            elif line.startswith("# "):
                body_html.append(f"<h1 class='report-h1'>{_format_inline(line[2:])}</h1>")
            elif line.startswith("## "):
                body_html.append(f"<h2 class='report-h2'>{_format_inline(line[3:])}</h2>")
            elif line.startswith("### "):
                body_html.append(f"<h3 class='report-h3'>{_format_inline(line[4:])}</h3>")
            elif line.startswith("- "):
                body_html.append(f"<li class='report-li'>{_format_inline(line[2:])}</li>")
            else:
                body_html.append(f"<p class='report-p'>{_format_inline(line)}</p>")

        content_html = "\n".join(body_html)


        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Dossier: {self.query}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111726;
            --surface-border: #1e293b;
            --accent: #ef4444;
            --accent-glow: rgba(239, 68, 68, 0.18);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.6;
            padding: 30px 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        .badge {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.3);
            margin-bottom: 12px;
        }}
        h1.title {{ font-size: 28px; font-weight: 800; color: #fff; margin-bottom: 8px; }}
        p.subtitle {{ color: var(--text-muted); font-size: 14px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 20px;
        }}
        .card-val {{ font-size: 26px; font-weight: 800; color: var(--accent); font-family: 'JetBrains Mono', monospace; }}
        .card-lbl {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}

        .section-box {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section-title {{ font-size: 18px; font-weight: 700; margin-bottom: 16px; color: #fff; display: flex; align-items: center; gap: 8px; }}
        .mermaid {{ display: flex; justify-content: center; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; overflow-x: auto; }}

        .report-content {{ padding: 10px 0; }}
        .report-h1 {{ font-size: 22px; margin: 20px 0 10px; color: var(--accent); }}
        .report-h2 {{ font-size: 18px; margin: 18px 0 8px; color: #fff; border-bottom: 1px solid var(--surface-border); padding-bottom: 6px; }}
        .report-h3 {{ font-size: 15px; margin: 14px 0 6px; color: var(--text-muted); }}
        .report-p {{ margin-bottom: 10px; color: #cbd5e1; font-size: 14px; }}
        .report-li {{ margin-left: 20px; margin-bottom: 6px; color: #cbd5e1; font-size: 14px; }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Differential Knowledge Graph Dossier</span>
            <h1 class="title">{self.query}</h1>
            <p class="subtitle">Generated autonomously via <strong>open research-lite</strong> with <strong>{self.model_name}</strong> | Evaluated across {len(self.sources)} sources</p>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-val">{tel['token_reduction_pct']}%</div>
                <div class="card-lbl">Token Bloat Pruned</div>
            </div>
            <div class="card">
                <div class="card-val">{stats['total_facts']}</div>
                <div class="card-lbl">Verified Fact Triplets</div>
            </div>
            <div class="card">
                <div class="card-val">{stats['total_entities']}</div>
                <div class="card-lbl">Unique Entities Mapped</div>
            </div>
            <div class="card">
                <div class="card-val" style="color: {'var(--warning)' if tel['facts_conflicted'] > 0 else 'var(--success)'};">{tel['facts_conflicted']}</div>
                <div class="card-lbl">Contradictions Flagged</div>
            </div>
        </div>

        <div class="section-box">
            <div class="section-title">Interactive Session Knowledge Graph</div>
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>

        <div class="section-box">
            <div class="section-title">Synthesized Executive Report</div>
            <div class="report-content">
{content_html}
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_template)
        return filepath


# Drop-in alias for GPT-Researcher compatibility
GPTResearcher = Researcher
