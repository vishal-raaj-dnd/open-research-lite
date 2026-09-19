"""Quickstart Example: Using open research-lite as an Autonomous Research Agent."""

import os
import sys
import asyncio

# Ensure local src takes precedence
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from open_research_lite import GPTResearcher, Researcher


async def main():
    print("=" * 70)
    print(" [open research-lite] Autonomous Research Agent Demo")
    print("=" * 70)

    # 1. Initialize Researcher
    researcher = GPTResearcher(
        query="High-Bandwidth Memory HBM4 Architecture and Interconnect Scaling",
        report_type="research_report",
        verbose=True
    )

    # 2. Sample multi-source scraped content
    sample_scrapes = [
        {
            "url": "https://semiconductor-weekly.com/hbm4-specs",
            "title": "HBM4 2048-bit Architecture Milestone",
            "content": (
                "Artificial intelligence accelerators require high-density memory interfaces. "
                "In 2026, memory manufacturers validated an HBM4 2048-bit bus delivering 2.8 TB/s peak bandwidth. "
                "Base operating power consumption per 16-high stack is measured at 26W under sustained memory saturation."
            )
        },
        {
            "url": "https://datacenter-trends.org/memory-power-audit",
            "title": "HBM4 Thermal and Power Dissipation Report",
            "content": (
                "Silicon interposers bond memory stacks to host processors. "
                "Benchmarking validates HBM4 achieving 2.8 TB/s peak bandwidth. "
                "However, an independent thermal audit claims sustained power reaches 31W under overdrive conditions, "
                "differing from initial baseline claims of 26W."
            )
        }
    ]

    print("\n[1] Ingesting sources into Differential Knowledge Graph...")
    diff_payloads = await researcher.conduct_research(custom_sources=sample_scrapes)

    print(f" -> Processed {len(diff_payloads)} sources.")
    stats = researcher.get_stats()
    tel = stats["telemetry"]
    print(f" -> Facts extracted: {tel['total_facts_extracted']}")
    print(f" -> Redundant fluff pruned: {tel['facts_discarded_duplicate']}")
    print(f" -> Metric contradictions caught: {tel['facts_conflicted']}")

    print("\n[2] Synthesizing Final Report...")
    report = await researcher.write_report()

    print("\n" + "-" * 70)
    print(report)
    print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
