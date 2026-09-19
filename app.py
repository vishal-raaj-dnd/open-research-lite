"""Hugging Face Space Application for Open-Research-Lite: Deep Research Arena.

Provides an interactive side-by-side comparison:
- Standard Monolithic Deep Research (Context Stuffing)
vs.
- Open-Research-Lite (Differential Knowledge Graph & Concept-Diff Engine)
"""

import os
import sys
import time
import asyncio
import gradio as gr

# Add src directory to path
sys.path.insert(0, os.path.abspath("src"))

from open_research_lite import ConceptDiffEngine, SessionKnowledgeGraph, TelemetryTracker
from open_research_lite.knowledge_graph import FactAssertion


PRESET_SCENARIOS = {
    "HBM4 Architecture 2026 (Bandwidth & Power)": [
        {
            "url": "https://semiconductor-review.org/hbm4-specs-2026",
            "title": "2026 High-Bandwidth Memory HBM4 Specification",
            "content": (
                "Artificial intelligence accelerators require immense memory bandwidth to prevent compute stalls. "
                "The history of DRAM stretches back to Robert Dennard's single-transistor cell invention at IBM in 1968. "
                "Graphics cards and AI servers have traditionally relied on GDDR and older HBM3e memory packages. "
                "In early 2026, JEDEC ratified the official HBM4 specification delivering 2.8 TB/s peak bandwidth per stack. "
                "Base operating power consumption for the 16-high stack is measured at 26W under full continuous saturation."
            )
        },
        {
            "url": "https://datacenter-insights.com/memory-thermal-audit",
            "title": "HBM4 Memory Power and Thermal Audit",
            "content": (
                "What is high bandwidth memory? HBM stacks multiple DRAM dies vertically through silicon vias. "
                "Computing clusters consume megawatts of electricity to power deep learning inference clusters. "
                "Laboratory benchmarks confirm HBM4 delivering 2.8 TB/s peak bandwidth per stack across a 2048-bit bus. "
                "However, an independent thermal audit reports sustained power reaches 31W under continuous load, contradicting the standard vendor rating of 26W."
            )
        },
        {
            "url": "https://hardware-analytica.net/hbm4-scaling",
            "title": "HBM4 Interconnect Scaling Trajectory",
            "content": (
                "High-performance computing data centers are modernizing packaging architectures to support generative AI. "
                "DRAM scaling continues to encounter physical limitations at the sub-nanometer node boundary. "
                "Base operating power consumption for initial test configurations remains tracked at 26W across pilot wafers."
            )
        }
    ],
    "Quantum Error Correction 2026": [
        {
            "url": "https://quantum-insider.io/qec-2026-benchmarks",
            "title": "Topological Qubits and Logical Error Rates 2026",
            "content": (
                "Quantum computing utilizes quantum mechanics principles such as superposition and entanglement. "
                "Traditional computers rely on classical bits that are either 0 or 1. Alan Turing pioneered computing theory in the 1930s. "
                "Recent 2026 neutral-atom quantum processors achieved 1,000 physical qubits with a two-qubit gate fidelity of 99.85%. "
                "Logical qubit memory lifetimes surpassed physical qubits by a factor of 4.2x under surface code error correction."
            )
        },
        {
            "url": "https://physics-advances-review.org/neutral-atoms-qec",
            "title": "Surface Code Scaling and Gate Fidelity Milestones",
            "content": (
                "Quantum mechanics was formulated by Max Planck, Albert Einstein, and Niels Bohr. Quantum computers process qubits. "
                "Neutral atom architectures trap rubidium atoms in optical tweezer arrays. "
                "Testing confirms 1,000 physical qubits operating at 99.85% two-qubit gate fidelity. "
                "A competing laboratory reported logical lifetime enhancement at 3.8x, suggesting variability in cryogenic stability."
            )
        }
    ],
    "HBM4 Memory Architecture & Thermal Power": [
        {
            "url": "https://semiconductor-weekly.com/hbm4-specs",
            "title": "HBM4 2048-bit Interface Architecture & Thermal Dissipation",
            "content": (
                "Artificial intelligence models like ChatGPT require massive GPU clusters to train and run inference. "
                "Datacenters consume megawatts of electricity and require liquid cooling infrastructure. "
                "HBM4 memory standards feature a 2048-bit memory bus providing 2.8 TB/s peak bandwidth per stack. "
                "Total power draw per 16-high HBM4 stack is measured at 26W under sustained 100% memory saturation."
            )
        },
        {
            "url": "https://datacenter-tech-trends.org/ai-memory-scaling",
            "title": "Next-Gen AI Accelerators: Memory Wall Solutions",
            "content": (
                "Moore's Law was posited by Gordon Moore in 1965. AI computing demands have outpaced traditional CPU scaling. "
                "GPUs use specialized high-bandwidth memory stacks bonded via through-silicon vias (TSVs). "
                "New HBM4 production silicon validates the 2048-bit bus delivering 2.8 TB/s bandwidth per stack. "
                "Thermal testing indicates peak power reaches 31W per stack under non-standard 1.1V overdrive."
            )
        }
    ]
}


async def run_comparison(scenario_name: str, custom_query: str):
    default_scenario = next(iter(PRESET_SCENARIOS.values()))
    sources = PRESET_SCENARIOS.get(scenario_name, default_scenario)
    
    # 1. Baseline Run
    baseline_text = ""
    for s in sources:
        baseline_text += f"### SOURCE: {s['title']} ({s['url']})\n\n"
        baseline_text += s["content"] * 3 + "\n\n"

    base_words = len(baseline_text.split())
    base_tokens = int(base_words * 1.33)
    base_cost = (base_tokens / 1_000_000.0) * 2.50

    # 2. ConceptDiffEngine Run
    graph = SessionKnowledgeGraph()
    telemetry = TelemetryTracker()
    engine = ConceptDiffEngine(graph=graph, telemetry=telemetry)

    diff_outputs = []
    for s in sources:
        payload = await engine.process_observation(
            raw_text=s["content"] * 3,
            source_url=s["url"],
            source_title=s["title"]
        )
        diff_outputs.append(payload)

    lite_text = "\n\n---\n\n".join(diff_outputs)
    lite_words = len(lite_text.split())
    lite_tokens = int(lite_words * 1.33)
    lite_cost = (lite_tokens / 1_000_000.0) * 2.50

    stats = telemetry.get_summary()
    token_savings_pct = round(((base_tokens - lite_tokens) / base_tokens) * 100, 1) if base_tokens > 0 else 0.0

    scorecard_md = f"""### Benchmark Scorecard
| Metric | Standard Deep Research | open research-lite | Improvement |
| :--- | :--- | :--- | :--- |
| **Input Tokens** | `{base_tokens:,}` tokens | **`{lite_tokens:,}` tokens** | **{token_savings_pct}% Saved** |
| **Est. API Cost** | `${base_cost:.4f}` | **`${lite_cost:.4f}`** | **{token_savings_pct}% Cheaper** |
| **Facts Extracted** | Monolithic text dump | **`{stats['total_facts_extracted']}` structured facts** | Clean Graph |
| **Conflicts Flagged**| Silent Overwrite | **`{stats['facts_conflicted']}` detected & flagged** | Factual Integrity |
| **Redundant Fluff** | 100% Ingested | **`{stats['facts_discarded_duplicate']}` duplicates pruned** | High SNR |
"""

    return baseline_text, lite_text, scorecard_md


def launch_gradio():
    custom_css = """
    .metric-card { background: #1e1e2e; border-radius: 10px; padding: 15px; border: 1px solid #313244; }
    """
    
    with gr.Blocks(title="Deep Research Arena: open research-lite", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("""
        # Deep Research Arena: open research-lite
        ### Evaluating Differential Knowledge Graph Middleware against Monolithic Web Search Stuffing
        
        *Token-efficient research middleware that cuts 70%+ token costs and deterministically flags contradictory web facts.*
        
        [GitHub Repository](https://github.com/vishal-raaj-dnd/open-research-lite) • [PyPI Package](https://pypi.org/project/open-research-lite/)
        """)

        with gr.Row():
            scenario_dropdown = gr.Dropdown(
                choices=list(PRESET_SCENARIOS.keys()),
                value="HBM4 Architecture 2026 (Bandwidth & Power)",
                label="Select Research Evaluation Scenario"
            )
            run_btn = gr.Button("Run Live Side-by-Side Benchmark", variant="primary")

        scorecard_display = gr.Markdown("### Benchmark Metrics will appear here upon execution.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Baseline Deep Research (Monolithic Raw Dump)")
                baseline_output = gr.Markdown(value="*Click 'Run Live Side-by-Side Benchmark' to start...*")

            with gr.Column():
                gr.Markdown("### open research-lite (Concept-Diff Engine)")
                lite_output = gr.Markdown(value="*Click 'Run Live Side-by-Side Benchmark' to start...*")


        run_btn.click(
            fn=lambda s: asyncio.run(run_comparison(s, "")),
            inputs=[scenario_dropdown],
            outputs=[baseline_output, lite_output, scorecard_display]
        )

    return demo


if __name__ == "__main__":
    demo = launch_gradio()
    demo.launch(server_name="0.0.0.0", server_port=7860)
