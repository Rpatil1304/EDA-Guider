# EDA-Guider

**Agentic AI-driven Exploratory Data Analysis system** that guides users through EDA on any tabular dataset (CSV/Excel) - without replacing the analyst.

EDA-Guider inspects a dataset, reasons about what preprocessing it needs, applies that preprocessing internally (never touching the original data), computes real statistics on the cleaned copy, and generates a grounded, evidence-backed report with every decision logged in a transparent audit trail.

---

## Architecture

```
                           EDA-GUIDER
                                │
                         ┌──────▼──────┐
                         │ Data Upload │
                         └──────┬──────┘
                                ↓
                     ┌─────────────────────┐
                     │ Ingestion & Parsing │
                     │ CSV / Excel / Sheets│
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ Semantic Profiling  │
                     │ Type + Data Quality │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │   Rule Engine       │
                     │ Deterministic Rules │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ LangChain + LLM     │
                     │ Decision Reasoning  │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ Confidence Check    │
                     └──────────┬──────────┘
                                ↓
                       ┌────────┴────────┐
                       ↓                 ↓
                      HIGH              LOW
                   confidence        confidence
                       ↓                 ↓
                Internal Apply      User Review
                       └────────┬────────┘
                                ↓
                        Clean Internal Data
                                ↓
                     ┌─────────────────────┐
                     │ Statistical Engine  │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ Visualization Rules │
                     │     100% Rules      │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ Evidence Dictionary │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ LLM Insight Report  │
                     └──────────┬──────────┘
                                ↓
                     ┌─────────────────────┐
                     │ Hallucination Check │
                     └──────────┬──────────┘
                                ↓
                              REPORT
                                │
                 ┌──────────────┼──────────────┐
                 ↓              ↓              ↓
              Dashboard     Audit Trail      Export
                                │
                                ↓
                          Version History
                                │
                                ↓
                           User Feedback
```
---

## Project Roadmap

```text
Phase 0  → Data Structures
              ↓
Phase 1  → Ingestion & Profiling
              ↓
Phase 2  → Custom Rule Engine
              ↓
Phase 3  → LangChain + LLM Agent
              ↓
Phase 4  → Internal Preprocessing
              ↓
Phase 5  → Statistics
              ↓
Phase 6  → Visualization Recommendation
              ↓
Phase 7  → Insight Synthesis
              ↓
Phase 8  → Audit Trail
              ↓
Phase 9  → Orchestration
              ↓
Phase 10 → FastAPI + Next.js
```


---

## How it works

1. **Data Upload** — user provides a CSV, Excel file, or spreadsheet.
2. **Ingestion & Parsing** — file is loaded and normalized into a working format.
3. **Semantic Profiling** — custom type inference per column (not just Pandas dtypes) plus data-quality detection: missing values, whitespace, inconsistent formats, numeric/datetime stored as strings, boolean-like values, potential ID columns, duplicates.
4. **Rule Engine** — deterministic rules convert profiling findings into candidate preprocessing actions.
5. **LangChain + LLM Decision Reasoning** — the LLM reasons over candidate actions, selects and prioritizes them, and explains why.
6. **Confidence Check** — each selected action is scored:
   - **High confidence** → applied automatically to an internal copy of the data.
   - **Low confidence** → flagged for user review instead of auto-applied.
7. **Clean Internal Data** — the original uploaded dataset remains untouched; only an internal copy is modified.
8. **Statistical Engine** — computes descriptive statistics, distributions, outliers, skewness, and correlations on the cleaned data.
9. **Visualization Rules** — a fully rule-based (non-LLM) module recommends visualizations based on actual dataset structure and statistics.
10. **Evidence Dictionary** — all computed facts (stats, quality findings, visualization picks) are collected into a single grounded evidence source.
11. **LLM Insight Report** — the LLM writes a narrative report using only the evidence dictionary.
12. **Hallucination Check** — the generated report is verified against the evidence dictionary before being shown to the user.
13. **Report Delivery** — presented via:
    - **Dashboard** — interactive view
    - **Audit Trail** — action, reasoning, evidence, source, and confidence for every decision
    - **Export** — downloadable report (PDF/HTML)
14. **Version History** — tracks changes across multiple runs on the same dataset.
15. **User Feedback** — users can accept/reject suggested actions, informing future runs.

---

## Design principles

- **Analyst stays in control** — the system guides, it doesn't replace human judgment.
- **Original data is never modified** — all preprocessing happens on an internal copy.
- **Grounded, not generative** — the LLM narrates computed evidence; it doesn't invent statistics.
- **Explainable by default** — every decision is logged with its reasoning, evidence, source, and confidence.
- **Deterministic where it matters** — rule engine and visualization selection are rule-based, not LLM guesses.

---

## Tech Stack

- **Pandas** — data loading and manipulation
- **Custom Rule Engine** — deterministic preprocessing and visualization logic
- **LangChain + LLM** — reasoning, decision explanation, and report generation
