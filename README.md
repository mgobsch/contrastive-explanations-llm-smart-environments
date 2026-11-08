# Contrastive Explanations in the Era of Large Language Models

**Designing for Faithfulness and Accessibility in Smart Environments**

Bachelor thesis, University of Cologne, 2026 · Magdalena Gobsch

This repository contains all code, prompts, test cases, results and the user study of the thesis. It is the reference for every file mentioned in the thesis.

## What the thesis does

SmartEx (Sadeghi et al., 2024) generates contrastive explanations for rule-based smart environments ("Why is the light orange and not green?"). Its template explanations are faithful but hard to read. The thesis tests whether large language models (LLMs) can make them more accessible without losing faithfulness, using four configurations:

| Configuration | Foil selection | Explanation text |
| --- | --- | --- |
| C0 (baseline) | TOPSIS | SmartEx template |
| C1 | TOPSIS | LLM |
| C2 | TOPSIS with weights set by the LLM | LLM |
| C3 | LLM | LLM |

Four LLMs and two prompting strategies (P1 zero-shot, P2 few-shot) were evaluated on three test cases (TC1–TC3). The selected setup (GPT-OSS · P1 · C2) was then compared with the baseline in a user study with 29 participants.

## Repository structure

| Folder | Content | Thesis |
| --- | --- | --- |
| `llm_pipeline/` | `run_tests.py` (generates all explanations), `topsis.py` (TOPSIS for C2) | Ch. 4 |
| `llm_pipeline/data/` | prompts for C1–C3, few-shot examples, test cases (TC1–TC3), few-shot cases (TC4–TC6), rules | Ch. 4 |
| `evaluation/` | `evaluate_faithfulness.py` (faithfulness rubric F1–F5 + hallucination flags), `ground_truth.json` (reference per test case), `foil_reference_table.xlsx` | Section 5.1 |
| `results/selection/` | all 216 generated explanations (`1_generated_explanations.xlsx`), faithfulness scores and hallucination flags (`2_faithfulness_scores.xlsx`, summary in `2_faithfulness_analysis.pdf`), contrastive quality and accessibility ratings (`3_quality_ratings.xlsx`) | Section 5.1 |
| `study/` | the user study web page (`index.html`), the Google Apps Script that saved the answers (`Code.gs`), study documentation (`README.md`) | Section 5.2 |
| `results/user_study/` | anonymised study data (`study_data.xlsx`) and all analyses (`study_analysis.xlsx`) | Section 5.2, Ch. 6 |

## Running the code

Requirements: Python 3.10+ and an API key for [AcademicCloud Chat AI](https://academiccloud.de).

```bash
pip install -r requirements.txt
export ACADEMICCLOUD_API_KEY="your-key"

# 1. Generate the explanations (settings at the top of the script;
#    output: results.xlsx = results/selection/1_generated_explanations.xlsx)
cd llm_pipeline
python run_tests.py

# 2. Rate faithfulness (settings at the top of the script, or see --help)
cd ../evaluation
python evaluate_faithfulness.py --help
```

**Note on the faithfulness ratings.** `evaluate_faithfulness.py` defines the rubric, the reference and the output format. The final scores in `results/selection/2_faithfulness_scores.xlsx` were produced by Claude Opus 5.5 (medium reasoning effort), which applied this script to every explanation; the hallucination flags were then reviewed by the author. The default evaluator model in the script is an AcademicCloud model. Faithfulness and contrastive quality use weighted scores: faithfulness = F1 0.15 + F2 0.30 + F3 0.15 + F4 0.30 + F5 0.10 (column `faithfulness_final_score_weighted`), contrastive quality = Q1 0.15 + Q2 0.40 + Q3 0.10 + Q4 0.35 (column "CQ Score (weighted)" in `3_quality_ratings.xlsx`).

## User study

- Study page: https://mgobsch.github.io/contrastive-explanations-llm-smart-environments/study/
- Preview (nothing is saved): https://mgobsch.github.io/contrastive-explanations-llm-smart-environments/study/?preview=1

The study is closed. The published data contain no LimeSurvey response IDs and no exact start or end times; participants are identified only by a running number (`pid`).

## Not included

The SmartEx engine itself is not part of this repository.

## Citation

> Gobsch, M. (2026). *Contrastive Explanations in the Era of Large Language Models: Designing for Faithfulness and Accessibility in Smart Environments* [Bachelor's thesis, University of Cologne].
