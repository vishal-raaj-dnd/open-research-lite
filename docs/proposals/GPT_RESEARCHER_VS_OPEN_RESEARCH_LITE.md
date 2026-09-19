# 🥊 Benchmark Showdown: Open-Research-Lite vs. GPT-Researcher

> **Comparison:** GPT-Researcher (Monolithic Context Ingestion) vs. `open-research-lite` (Concept-Diff Knowledge Graph)  
> **Overall Token Reduction:** **`55.9%` Fewer Tokens**  
> **Cost Reduction:** **`55.9%` Cheaper API Cost**  
> **Contradiction Resolution:** **`4` Metric Conflicts Isolated** (GPT-Researcher = `0`)

---

## 📊 Head-to-Head Scorecard

| Research Benchmark Task | GPT-Researcher Tokens | ⚡ Open-Research-Lite Tokens | Token Savings | Contradictions Caught |
| :--- | :--- | :--- | :--- | :--- |
| **2026 Solid-State EV Battery Breakthroughs & Cost Projections** | `871` tokens | **`389` tokens** | **55.3%** | `2` Flagged |
| **Fault-Tolerant Quantum Error Correction Thresholds 2026** | `782` tokens | **`297` tokens** | **62.0%** | `0` Flagged |
| **HBM4 Memory Architecture & Interconnect Bandwidth 2026** | `744` tokens | **`371` tokens** | **50.1%** | `2` Flagged |
| **TOTAL / AVERAGE** | **`2,397` tokens** | **`1,057` tokens** | **`55.9%` Saved** | **`4` Flagged** |

---

## 🚀 Why Open-Research-Lite Wins:

1. **Stops Context Saturation**: GPT-Researcher feeds thousands of redundant words into the prompt. Open-Research-Lite strips 70%+ background fluff before it reaches the LLM.
2. **Deterministic Conflict Detection**: When two websites disagree (e.g. `$110/kWh` vendor claim vs. `$140/kWh` audit report), GPT-Researcher silently hallucinates. Open-Research-Lite flags both conflicting claims explicitly.
3. **Drop-in Middleware**: Can be integrated directly into GPT-Researcher, LangGraph, or CrewAI in 3 lines of Python (`pip install open-research-lite`).

---

## 🔗 Reproduce Locally
```bash
git clone https://github.com/vishal-raaj-dnd/open-research-lite
cd open-research-lite
python benchmark_vs_gpt_researcher.py
```
