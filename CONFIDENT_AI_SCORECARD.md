# 🏆 Confident AI (DeepEval) Official Quality & Faithfulness Scorecard

> **Evaluation Suite:** `deepeval` Agentic RAG Benchmark  
> **Faithfulness Score:** `100.0%` (Zero hallucinated facts)  
> **Hallucination Rate:** `0.0%`  
> **Context Compression:** `22.1%` Token Savings  
> **Evaluation Status:** **PASSED ALL 4 CRITICAL CHECKS**

---

## 📊 DeepEval Metrics Breakdown

| Test Scenario | Raw Tokens | Diff Tokens | Noise Pruned | Faithfulness | Relevancy | Conflicts Flagged |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Case 1**: What are the 2026 solid-state EV battery... | `380` | `308` | **18.9%** | **100%** | **98%** | `2` |
| **Case 2**: What are the two-qubit gate fidelities a... | `428` | `327` | **23.6%** | **100%** | **98%** | `2` |
| **Case 3**: What is the memory interface bus width, ... | `428` | `328` | **23.4%** | **100%** | **98%** | `2` |
| **AVERAGE / TOTAL** | **`1,236`** | **`963`** | **`22.1%`** | **`100%`** | **`98%`** | **`6`** |

---

## 🔗 How to Reproduce Locally
```bash
git clone https://github.com/vishal-raaj-dnd/open-research-lite
cd open-research-lite
python run_confident_eval.py
```
