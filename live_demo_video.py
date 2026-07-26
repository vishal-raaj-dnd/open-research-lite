"""Live Interactive Benchmark & Video Recording Demo Script for open-research-lite.

Runs real live internet searches via Tavily & Gemini Flash, showing side-by-side terminal
execution of Baseline Deep Researcher vs open-research-lite Concept-Diff Engine.
"""

import sys
import os
import asyncio
import time

# Ensure UTF-8 output on Windows CMD/PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from tavily import TavilyClient
from open_research_lite import ConceptDiffEngine, TelemetryTracker


async def run_live_video_demo():
    print("\n" + "═"*70)
    print(" 🚀 OPEN-RESEARCH-LITE: LIVE INTERACTIVE BENCHMARK HARNESS")
    print("═"*70)
    
    default_query = "2026 solid state battery Wh/kg energy density commercialization breakthroughs"
    
    print("\n[INPUT PROMPT]")
    try:
        user_input = input(f"Enter research topic (or press Enter for default):\n> ").strip()
    except Exception:
        user_input = ""
        
    query = user_input if user_input else default_query
    print(f"\n⚡ Initiating Real Internet Search for: '{query}'...\n")

    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("❌ Error: TAVILY_API_KEY missing in .env file.")
        return

    # STEP 1: Real Web Search
    print("🌐 [1/3] Querying Tavily Web Search API in real-time...")
    client = TavilyClient(api_key=tavily_key)
    search_response = client.search(query=query, max_results=3, search_depth="advanced", include_raw_content=True)
    results = search_response.get("results", [])
    print(f"   ✓ Retrieved {len(results)} live web pages from the internet.")

    # STEP 2: Baseline Execution (Raw Web Scraping)
    print("\n📊 [2/3] Processing BASELINE Ingestion (Standard Deep Research)...")
    baseline_start = time.time()
    baseline_raw_text = ""
    for item in results:
        raw_body = item.get("raw_content") or item.get("content", "")
        baseline_raw_text += f"# {item.get('title', '')}\nURL: {item.get('url', '')}\n{raw_body}\n\n"
    
    baseline_time = time.time() - baseline_start
    baseline_words = len(baseline_raw_text.split())
    baseline_tokens = int(baseline_words * 1.3)
    baseline_cost = round((baseline_tokens / 1_000_000) * 2.50, 4)
    print(f"   ✓ Baseline Ingested: {baseline_words:,} raw words ({baseline_tokens:,} input tokens | ${baseline_cost})")

    # STEP 3: open-research-lite Execution (Concept-Diff Engine)
    print("\n⚡ [3/3] Processing OPEN-RESEARCH-LITE (Session Knowledge Graph Engine)...")
    engine_start = time.time()
    engine = ConceptDiffEngine()
    
    diff_payloads = []
    for item in results:
        raw_body = item.get("raw_content") or item.get("content", "")
        payload = await engine.process_observation(
            raw_text=raw_body,
            source_url=item.get("url", ""),
            source_title=item.get("title", "")
        )
        diff_payloads.append(payload)

    lite_time = time.time() - engine_start
    combined_payload = "\n\n".join(diff_payloads)
    lite_words = len(combined_payload.split())
    lite_tokens = int(lite_words * 1.3)
    lite_cost = round((lite_tokens / 1_000_000) * 2.50, 4)

    token_savings = round((1 - (lite_words / baseline_words)) * 100, 1) if baseline_words > 0 else 0
    cost_reduction = round(baseline_cost / max(lite_cost, 0.0001), 1)

    # PRINT SIDE-BY-SIDE SCORECARD
    print("\n" + "═"*70)
    print(" 🏆 LIVE SIDE-BY-SIDE BENCHMARK SCORECARD")
    print("═"*70)
    print(f"  Query: \"{query}\"")
    print("─"*70)
    print(f"  Metric                      BASELINE               OPEN-RESEARCH-LITE")
    print("─"*70)
    print(f"  Live Words Ingested  :     {baseline_words:>7,} words          {lite_words:>7,} words")
    print(f"  Input Tokens Passed  :     {baseline_tokens:>7,} tokens         {lite_tokens:>7,} tokens")
    print(f"  Ingestion API Cost   :     ${baseline_cost:>6.4f}                 ${lite_cost:>6.4f}")
    print(f"  Processing Time      :     {baseline_time:>6.2f}s                  {lite_time:>6.2f}s")
    print("─"*70)
    print(f"  🎉 REAL TOKEN REDUCTION :  {token_savings}% Saved ⚡")
    print(f"  💰 REAL COST SAVINGS    :  {cost_reduction}x Cost Reduction")
    print("═"*70)

    # PRINT SAMPLE DIFF PAYLOAD
    print("\n📄 [SAMPLE CONCEPT-DIFF PAYLOAD PASSED TO REASONING MODEL]:")
    print("─"*70)
    print(combined_payload[:600] + "\n...")
    print("─"*70)
    print("✅ Live test completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(run_live_video_demo())
