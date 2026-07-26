"""Live Internet Test Comparison Script for DeepResearch-Lite.

Fetches REAL live web search results from the internet via Tavily API
and processes them live through the ConceptDiffEngine using Gemini Flash.
"""

import asyncio
import os
import sys

# Reconfigure stdout to utf-8 for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("src"))

from open_deep_research.concept_diff import (
    ConceptDiffEngine,
    SessionKnowledgeGraph,
    TelemetryTracker
)
from open_deep_research.utils import tavily_search_async
from langchain_core.runnables import RunnableConfig


async def run_live_test(search_query: str = "2026 solid state battery Wh/kg energy density breakthroughs"):
    tavily_key = os.getenv("TAVILY_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    print("\n" + "="*75)
    print("🌐 REAL LIVE INTERNET TEST COMPARISON")
    print("="*75)
    print(f"Query: '{search_query}'")
    print(f"Tavily API Key : {'✅ Configured' if tavily_key else '❌ Missing (Set TAVILY_API_KEY in .env)'}")
    print(f"Gemini API Key : {'✅ Configured' if gemini_key else '⚠️ Missing (Will use fast local parser)'}")
    print("="*75 + "\n")

    if not tavily_key:
        print("💡 TIP: To fetch real live web pages from Tavily, add your TAVILY_API_KEY to your .env file:")
        print("   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx")
        print("\nExecuting live search test...\n")

    # Initialize live engine
    graph = SessionKnowledgeGraph()
    telemetry = TelemetryTracker()
    engine = ConceptDiffEngine(graph=graph, telemetry=telemetry, api_key=gemini_key)

    try:
        # 1. Fetch REAL live web search results from Tavily
        print(f"📡 Fetching live search results for query: '{search_query}'...")
        results = await tavily_search_async(
            search_queries=[search_query],
            max_results=4,
            include_raw_content=True
        )

        raw_pages = []
        for response in results:
            for item in response.get('results', []):
                raw_pages.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "raw_content": item.get("raw_content") or item.get("content", "")
                })

        print(f"✅ Fetched {len(raw_pages)} live web pages from the internet.\n")

        # 2. Process real live web pages through ConceptDiffEngine
        diff_payloads = []
        baseline_total_words = 0

        for i, page in enumerate(raw_pages, 1):
            url = page['url']
            title = page['title']
            raw_text = page['raw_content']
            word_count = len(raw_text.split())
            baseline_total_words += word_count

            print(f" Processing Page {i}/{len(raw_pages)}: [{title[:45]}...] ({word_count:,} raw words)...")
            
            payload = await engine.process_observation(
                raw_text=raw_text,
                source_url=url,
                source_title=title
            )
            diff_payloads.append(payload)

        combined_payload = "\n\n".join(diff_payloads)
        lite_total_words = len(combined_payload.split())

        baseline_tokens = int(baseline_total_words * 1.3)
        lite_tokens = int(lite_total_words * 1.3)
        saved_pct = round(max(0.0, (1 - (lite_tokens / baseline_tokens)) * 100), 1) if baseline_tokens > 0 else 0.0

        # 3. Print Live Results Scorecard
        print("\n" + "="*75)
        print("🏆 REAL LIVE TEST SCORECARD")
        print("="*75)
        print(f"{'METRIC':<30} | {'RAW LIVE SCRAPE':<18} | {'DEEPRESEARCH-LITE':<18}")
        print("-" * 75)
        print(f"{'Live Words Fetched':<30} | {baseline_total_words:<18,} | {lite_total_words:<18,}")
        print(f"{'Estimated Input Tokens':<30} | {baseline_tokens:<18,} | {lite_tokens:<18,}")
        print(f"{'Estimated API Cost per Run':<30} | ${((baseline_tokens/1e6)*2.5):<17.4f} | ${((lite_tokens/1e6)*2.5):<17.4f}")
        print(f"{'Token Savings':<30} | {'0% (Full Bloat)':<18} | {f'{saved_pct}% SAVED ⚡':<18}")
        print(f"{'Facts Added (DIFF_ADD)':<30} | {'-':<18} | {telemetry.adds_count:<18}")
        print(f"{'Facts Discarded (DISCARD)':<30} | {'-':<18} | {telemetry.discards_count:<18}")
        print(f"{'Conflicts Flagged':<30} | {'-':<18} | {telemetry.conflicts_count:<18}")
        print("="*75 + "\n")

        print("📄 LIVE COMBINED DIFF PAYLOAD FOR LLM:")
        print("-------------------------------------------------------------")
        print(combined_payload[:2000] + ("\n... [truncated for display]" if len(combined_payload) > 2000 else ""))
        print("-------------------------------------------------------------\n")

    except Exception as e:
        print(f"❌ Error running live search: {e}")
        print("Ensure TAVILY_API_KEY is configured in your .env file.")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "2026 solid state battery Wh/kg energy density breakthroughs"
    asyncio.run(run_live_test(query))
