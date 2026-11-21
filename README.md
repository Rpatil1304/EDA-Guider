# EDA-Guider 📊

**AI-Driven Exploratory Data Analysis & Intelligent Decision-Support System**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.1%20Flash%20%7C%203.8%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**EDA-Guider** is a privacy-conscious, enterprise-grade decision-support platform designed to generalize exploratory data analysis for arbitrary tabular datasets (`CSV`, `TSV`, `XLS`, `XLSX`, `XLSM`).

The system offers a **dual-mode workflow**:
1. **📁 RAW Dataset Mode:** Automated profiling, custom semantic type inference, deterministic rule-based preprocessing on an isolated copy, statistical modeling, candidate visualization generation, and two-stage Google Gemini orchestration for non-redundant chart pruning and executive EDA report generation.
2. **🧹 Clean Dataset Mode:** Conversational AI data analyst and interactive visualizer. Ask questions in natural language; EDA-Guider generates executable Pandas and Plotly code, validates it against a strict AST security sandbox, auto-corrects runtime errors, and returns direct answers with interactive charts.

> **Privacy Guarantee:** The user's original data is **never modified**. Raw data rows are **never passed to external LLMs**. Only privacy-safe, structured aggregate metadata and statistical summaries cross the LLM boundary.

---

## 📑 Table of Contents

- [Key Capabilities](#-key-capabilities)
- [Dual-Mode Architecture](#-dual-mode-architecture)
  - [1. RAW Dataset Workflow (Automated EDA)](#1-raw-dataset-workflow-automated-eda)
  - [2. Clean Dataset Workflow (AI Q&A & Visualizer)](#2-clean-dataset-workflow-ai-qa--visualizer)
- [Core System Components](#-core-system-components)
  - [Custom Profiling & Semantic Type Inference](#custom-profiling--semantic-type-inference)
  - [Rule-Based Preprocessing & Audit Trail](#rule-based-preprocessing--audit-trail)
  - [Statistical Analytics Engine](#statistical-analytics-engine)
  - [Deterministic Visualization Recommendation](#deterministic-visualization-recommendation)
  - [Two-Stage LangChain & Gemini Pipeline](#two-stage-langchain--gemini-pipeline)
  - [AST Sandboxed Code Execution & Self-Correction](#ast-sandboxed-code-execution--self-correction)
- [Project Directory Structure](#-project-directory-structure)
- [API Reference](#-api-reference)
- [Quickstart & Installation](#-quickstart--installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Docker Setup](#docker-setup)
- [Security & Sandbox Policies](#-security--sandbox-policies)
- [Tech Stack](#-tech-stack)
- [Design Principles](#-design-principles)

---

## 🚀 Key Capabilities

- **Automated RAW Data Audit:** Detects corrupted headers, inconsistent data encodings, missing values, empty strings, null-like tokens (`NA`, `N/A`, `NULL`, `None`), percentages, dates stored as strings, mixed types, and outliers.
- **Safe Preprocessing on Internal Deep Copy:** Generates deterministic transformation rules. Applies high-confidence conversions to an internal copy while keeping the source dataset read-only.
- **Granular Audit Trail:** Every single transformation (conversions, replaced nulls, cleaned whitespace) is recorded with confidence scores, reasonings, and before-and-after missing rate metrics.
- **Two-Stage Gemini LLM Synthesis:**
  - *Stage 1 (Model 1):* Prunes and validates rule-recommended visualizations, eliminating redundancy (e.g., duplicate distributions or overlapping categorical plots).
  - *Stage 2 (Model 2):* Synthesizes findings into a structured 5-section executive report without leaking raw data.
- **Natural Language Data Assistant (Clean Datasets):** Query clean datasets using plain English (e.g., *"What is the average profit by region?"*, *"Plot a scatter of birth rate vs death rate"*).
- **Self-Healing AST-Sandboxed Python Execution:** Executes LLM-generated code in a sandboxed AST environment with strict module allowlists. Automatically catches execution errors, feeds tracebacks back to the LLM, and self-corrects up to 2 retry attempts.
- **Interactive Visualizations:** Generates dynamic Plotly figures, data tables, and formatted metric KPIs directly in the Streamlit frontend.

---

## 🏛 Dual-Mode Architecture

```text
                                   USER DATASET
                       (CSV / TSV / XLS / XLSX / XLSM)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
       [ 📁 RAW DATASET MODE ]                         [ 🧹 CLEAN DATASET MODE ]
     Automated Profiling & EDA                       Interactive AI Q&A & Visualizer
                 │                                               │
                 ▼                                               ▼
       Ingestion & Validation                         Metadata & Schema Extraction
                 │                                    (Dimensions, Types, Statistics)
                 ▼                                               │
     Semantic Profiling Engine                                   ▼
   (Types, Null-tokens, Outliers)                     Natural Language Query from User
                 │                                               │
                 ▼                                               ▼
     Preprocessing Rule Engine                       LLM Code Generation (Pandas + Plotly)
                 │                                               │
                 ▼                                               ▼
     Safe Internal Preprocessing                      AST Code Validation & Security
      (Private Deep-Copy Only)                        (Strict Whitelist, Block Builtins)
                 │                                               │
                 ▼                                               ▼
    Preprocessing Audit Logging                      Sandboxed Execution & Self-Correction
                 │                                    (Auto-retries on runtime exceptions)
                 ▼                                               │
     Statistical Analysis Engine                                 ▼
   (IQR, Skewness, Kurtosis, Corr)                    Multi-Modal Response Generation
                 │                                    ├─ Synthesized Text Explanation
                 ▼                                    ├─ Interactive Plotly Chart
   Visualization Candidate Engine                     ├─ Formatted Table (DataFrame/Series)
       (Deterministic Rules)                          └─ Code Transparency & Logs
                 │
                 ▼
  Privacy-Safe Structured Evidence
                 │
                 ▼
   Stage 1: Model 1 (Gemini)
  (Visualization Pruning & Choice)
                 │
                 ▼
   Stage 2: Model 2 (Gemini)
    (Final Structured EDA Report)
                 │
                 ▼
     Streamlit Executive UI
```

---

### 1. RAW Dataset Workflow (Automated EDA)

Designed for uncleaned datasets straight from exports or databases.

1. **Ingestion & Integrity Check:** Validates file encoding (`UTF-8`, `ISO-8859-1`, etc.), format extensions, structural headers, and empty files.
2. **Semantic Type Profiling:** Identifies the true semantic type of every column (e.g. numeric columns formatted with `$`, commas, or `%`, ISO-8601 or free-format datetimes, boolean indicators, categorical dimensions, identifier columns, and text).
3. **Deterministic Preprocessing:** Produces a concrete transformation plan (standardizing null-like representations, trimming padding whitespace, coercing verified types, and flagging low-confidence fields for human review).
4. **Execution on Private Deep-Copy:** Applies transformations to an internal copy. Invalid non-null tokens are safely converted to nulls and tracked.
5. **Statistical Profiling:** Computes univariate and bivariate statistics: mean, median, standard deviation, quartiles, interquartile range (IQR), skewness, kurtosis, outlier counts, category frequency distributions, datetime durations, and Pearson correlation matrices.
6. **Deterministic Visualization Rules:** Generates mathematically grounded visualization candidates with explicit priority, confidence, and target columns.
7. **Two-Stage Gemini Reasoning:**
   - **Model 1 (Selection):** Evaluates visualization candidates against dataset metrics, eliminating duplicate perspectives (e.g. choosing between a Histogram or Box Plot; preventing multiple correlation charts).
   - **Model 2 (Executive Report):** Synthesizes the structured evidence into an executive 5-section report:
     - 1. *Raw Data Information*
     - 2. *Preprocessing Done*
     - 3. *Cleaned Data Information*
     - 4. *Statistical Information*
     - 5. *Visualization Information*

---

### 2. Clean Dataset Workflow (AI Q&A & Visualizer)

Designed for pre-cleaned, curated datasets where users want immediate insights, ad-hoc aggregations, and charts on demand.

1. **Zero-Leakage Metadata Profiling:** Extracts dataset dimensions, data types, distinct category samples, numeric ranges, and the first 2-3 sample records. Raw rows are never transmitted.
2. **Natural Language Translation:** Translates user questions into executable Pandas data-manipulation code and Plotly figure generation.
3. **AST Security Validation:** Abstract Syntax Tree (AST) scanning ensures the code only imports allowlisted packages (`pandas`, `numpy`, `plotly`, `math`, `datetime`, `re`) and blocks hazardous built-ins (`open`, `eval`, `exec`, `__import__`).
4. **Self-Healing Execution:** Runs the code on a DataFrame copy. If a `KeyError`, `TypeError`, or syntax error occurs, the execution engine feeds the exact error traceback back to Gemini to self-heal and re-execute (up to 2 retries).
5. **Interactive Results:**
   - Plain-English analytical answer synthesized from computed results.
   - Live, responsive Plotly charts rendered in Streamlit.
   - Sliced DataFrames or Series displayed in interactive data tables.
   - Full code transparency expander revealing the executed Python code.

---

## 🔍 Core System Components

### Custom Profiling & Semantic Type Inference
Unlike standard `df.dtypes` which often flags dirty numbers or dates as generic `object`, EDA-Guider executes custom multi-pass profiling:
- Detects string-encoded numbers: `"1,200.50"`, `"-45%"`, `"$99.99"`.
- Detects dates across international formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YYYY HH:MM:SS`.
- Unmasks disguised missing values: `"N/A"`, `"nan"`, `"null"`, `"None"`, `"?"`, `"-"`, `""` (whitespace-only).
- Distinguishes high-cardinality identifiers (UUIDs, auto-increment IDs) from genuine categorical features.

### Rule-Based Preprocessing & Audit Trail
Transformations are deterministic, reproducible, and fully auditable:
- **Null Standardization:** Normalizes disparate missing tokens into uniform `NaN`.
- **Safe Type Coercion:** Preserves valid values; captures invalid entries without crashing.
- **Audit Log Metrics:** For every transformed column, logs:
  - Transformation action & execution status
  - Reason & confidence score
  - Value count modified
  - Missing percentage before vs. after
  - Count of invalid entries converted to null

### Statistical Analytics Engine
Computes comprehensive statistical metrics on the cleaned internal copy:
- **Numeric:** Mean, median, standard deviation, variance, min, max, Q1, Q3, IQR, IQR-based lower/upper outlier thresholds, outlier count, skewness, kurtosis.
- **Categorical:** Total count, unique count, mode, mode frequency, percentage distribution, and top-k frequency tables.
- **Datetime:** Earliest date, latest date, span/duration in days, and unique date count.
- **Correlation:** Computes pairwise numeric correlation matrix.

### Deterministic Visualization Recommendation
Recommends chart candidates based on structural evidence:
- **Histograms & Box Plots:** Continuous numeric distributions & skewness analysis.
- **Bar Charts & Grouped Bars:** Categorical comparisons and multi-category aggregations.
- **Scatter Plots & Line Charts:** Bivariate numeric relationships and datetime trends.
- **Heatmaps & Pair Plots:** Multi-feature correlations and feature interactions.
- **Missingness Visualizations:** Missing data distribution matrices and bars.

### Two-Stage LangChain & Gemini Pipeline
Orchestrated via LangChain's Runnable ecosystem (`ChatPromptTemplate`, `RunnableParallel`, `PydanticOutputParser`):
- **Model 1 (`LLMVisualizationValidation`):** Receives rule candidates and filters out redundancies, returning an accepted/adjusted visualization suite.
- **Model 2 (`LLMFinalEDAReport`):** Generates structured markdown summaries across all 5 standard EDA sections.
- **Fallback Resilience:** If API quotas are exceeded or network drops occur, the system automatically falls back to deterministic rule outputs so workflows never halt.

### AST Sandboxed Code Execution & Self-Correction
Built for secure conversational analysis on clean datasets:
- **Allowlisted Libraries:** Only `pandas`, `numpy`, `plotly`, `math`, `datetime`, and `re`.
- **AST Parsing:** Traverses the syntax tree before execution to intercept forbidden tokens (`open`, `os`, `sys`, `subprocess`, `__import__`).
- **Automated Feedback Loop:**
  ```text
  User Query ──> LLM Code Gen ──> AST Check ──> Execute Code
                                                    │
                                              ┌─────┴─────┐
                                           Success      Error
                                              │           │
                                              ▼           ▼
                                          Synthesize   Feed Traceback
                                            Answer     Back to LLM
                                                      (Auto-Retry)
  ```

---

## 📂 Project Directory Structure

```text
EDA-Guider/
├── backend/
│   ├── app/
│   │   ├── agent/                 # Agent orchestration schemas & evidence preparation
│   │   ├── audit/                 # Preprocessing audit trail loggers
│   │   ├── clean_query/           # Mode 2: Clean Dataset Q&A & Visualizer Engine
│   │   │   ├── answer_generator.py    # Natural language synthesis from execution
│   │   │   ├── code_generator.py      # Query-to-Python/Plotly code generation
│   │   │   ├── dataset_loader.py      # Clean dataset ingestion & parsing
│   │   │   ├── executor.py            # AST security validation & self-healing sandbox
│   │   │   ├── metadata_extractor.py  # Zero-leakage metadata profiler
│   │   │   ├── router.py              # FastAPI endpoints for Clean mode
│   │   │   └── service.py             # Clean query execution pipeline
│   │   ├── execution/             # Transformation execution & validation
│   │   ├── ingestion/             # File validation & CSV/Excel loaders
│   │   ├── langchain/             # Mode 1: Two-Stage Gemini LLM pipelines
│   │   │   ├── model.py               # Gemini chat model setup & parsers
│   │   │   └── prompt_template.py     # Stage 1 & Stage 2 system prompts
│   │   ├── orchestration/         # Main end-to-end pipeline coordination
│   │   │   └── pipeline.py            # run_preprocessing_pipeline entry point
│   │   ├── preprocessing/         # Rule engine & safe transformations
│   │   ├── profiling/             # Custom semantic profiler & parsers
│   │   ├── reporting/             # Report formatters
│   │   ├── schemas/               # Pydantic data schemas
│   │   ├── statistics/            # Descriptive & bivariate statistical engine
│   │   ├── visualization/         # Deterministic chart recommendation engine
│   │   ├── config.py              # Backend configuration & environment loader
│   │   ├── llm_client.py          # Unified Google Gemini client interface
│   │   └── main.py                # FastAPI entry application & route definitions
│   ├── requirements.txt           # Backend Python dependencies
│   └── run_sample_pipeline.py     # CLI test runner for sample pipelines
├── frontend/
│   ├── components/
│   │   ├── clean_section.py       # Streamlit UI for Clean Dataset Q&A & Charts
│   │   └── report.py              # Streamlit UI for RAW Dataset Automated EDA Report
│   ├── api.py                     # Backend API client bridge
│   ├── app.py                     # Streamlit Dual-Mode application entry
│   └── config.py                  # Frontend service endpoints
├── docker-compose.yml             # Container orchestration
├── Dockerfile                     # Backend container definition
└── README.md                      # Project documentation
```

---

## 📡 API Reference

The FastAPI backend exposes the following REST endpoints:

### 1. `GET /health`
Returns the operational status of the service.
- **Response:** `{"status": "ok"}`

### 2. `POST /analyze`
Analyzes an uploaded raw tabular dataset (CSV, TSV, XLS, XLSX, XLSM), runs the complete automated EDA pipeline, and returns the comprehensive report.
- **Request:** `multipart/form-data` with `file: UploadFile`
- **Response:**
  ```json
  {
    "status": "success",
    "raw_profile": { ... },
    "preprocessing_plan": [ ... ],
    "execution_log": [ ... ],
    "cleaned_profile": { ... },
    "statistics": { ... },
    "candidate_visualizations": [ ... ],
    "llm_validations": [ ... ],
    "final_eda_report": {
      "raw_data_information": "...",
      "preprocessing_done": "...",
      "cleaned_data_information": "...",
      "statistical_information": "...",
      "visualization_information": "..."
    }
  }
  ```

### 3. `POST /clean/metadata`
Extracts privacy-safe schema and statistical metadata for a clean dataset without retaining raw data.
- **Request:** `multipart/form-data` with `file: UploadFile`
- **Response:**
  ```json
  {
    "status": "success",
    "filename": "sales_clean.csv",
    "metadata": {
      "summary": {
        "total_rows": 1000,
        "total_columns": 8,
        "missing_cell_percentage": 0.0,
        "duplicate_rows": 0
      },
      "columns": { ... },
      "column_groups": {
        "numeric": [ ... ],
        "categorical": [ ... ],
        "datetime": [ ... ]
      },
      "sample_records": [ ... ]
    }
  }
  ```

### 4. `POST /clean/query`
Processes a natural language query against a clean dataset. Generates code, executes it in an AST sandbox, handles self-corrections, and returns natural language explanations with optional Plotly figures or tabular data.
- **Request:** `multipart/form-data` with:
  - `file`: Dataset file
  - `query`: User's natural language question
  - `metadata_json` *(optional)*: Cached metadata JSON string
- **Response:**
  ```json
  {
    "status": "success",
    "query": "What is the average revenue by region?",
    "answer": "The region with the highest average revenue is North America at $42,500...",
    "code": "result_df = df.groupby('region')['revenue'].mean().reset_index()",
    "has_figure": true,
    "figure": { "data": [ ... ], "layout": { ... } },
    "result_data": {
      "type": "dataframe",
      "data": [ ... ]
    },
    "attempts_count": 1
  }
  ```

---

## ⚡ Quickstart & Installation

### Prerequisites
- **Python 3.11+** installed
- **Git** installed
- A **Google Gemini API Key** ([Get your key here](https://aistudio.google.com/))

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/EDA-Guider.git
   cd EDA-Guider
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the `backend/` directory:
   ```ini
   # backend/.env
   GOOGLE_API_KEY="your-google-gemini-api-key-here"
   GEMINI_MODEL="gemini-3.1-flash-lite-preview"
   DEBUG=False
   ```

5. **Start the FastAPI backend:**
   ```bash
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *The backend documentation will be live at `http://127.0.0.1:8000/docs`.*

### Frontend Setup

1. **Open a new terminal window** (activate the same virtual environment).

2. **Run the Streamlit application:**
   ```bash
   cd frontend
   streamlit run app.py
   ```
   *The dashboard will automatically open at `http://localhost:8501`.*

---

### Docker Setup

To deploy EDA-Guider using Docker:

```bash
# Ensure GOOGLE_API_KEY is configured in backend/.env
docker-compose up --build
```
- **Backend:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`

---

## 🛡 Security & Sandbox Policies

EDA-Guider is built with a defense-in-depth approach for data privacy and code execution:

| Security Vector | Implementation Detail |
| :--- | :--- |
| **Data Privacy** | Raw dataset rows are **never** provided to external LLM prompts. Only aggregate metadata (counts, column names, statistical summaries) is shared. |
| **Dataset Immutability** | All transformations are performed on an isolated deep copy (`df.copy(deep=True)`). The source dataset is strictly read-only. |
| **AST Code Validation** | Every generated Python script is parsed via Python's `ast` module before execution. Unapproved imports trigger an immediate `CodeSecurityError`. |
| **Module Allowlist** | Only verified analysis packages are permitted: `pandas`, `numpy`, `plotly`, `math`, `datetime`, `re`. |
| **Blocked Builtins** | Explicitly prohibits dangerous functions including `open`, `eval`, `exec`, `compile`, `__import__`, `breakpoint`, `input`. |
| **Execution Sandboxing** | Code runs with isolated variable namespaces, capturing `stdout` streams and preventing host environment modification. |

---

## 🛠 Tech Stack

| Domain | Technology / Library |
| :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/) |
| **Frontend Framework** | [Streamlit](https://streamlit.io/) |
| **Data Processing & Analytics** | [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [Scikit-learn](https://scikit-learn.org/) |
| **Excel & File Ingestion** | [OpenPyXL](https://openpyxl.readthedocs.io/), [XLRD](https://xlrd.readthedocs.io/), [Chardet](https://github.com/chardet/chardet) |
| **Interactive Visualizations** | [Plotly Express & Graph Objects](https://plotly.com/python/) |
| **LLM & Agent Orchestration** | [LangChain](https://www.langchain.com/), [LangChain Google GenAI](https://github.com/langchain-ai/langchain-google) |
| **Large Language Models** | [Google Gemini 3.1 Flash-Lite / Gemini 3.8 Flash](https://ai.google.dev/) |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) |
| **Automated Testing** | [Pytest](https://docs.pytest.org/) |

---

## 🎯 Design Principles

1. **Analyst in the Driver's Seat:** The system recommends and synthesizes; it never assumes authority over domain-specific business logic.
2. **Deterministic Where Precision Matters:** Profiling, preprocessing rule generation, outlier identification, and statistical calculations use deterministic mathematical algorithms rather than probabilistic LLMs.
3. **LLMs for High-Value Synthesis:** Google Gemini is leveraged where it excels: deduplicating visualization candidates, contextual reasoning, natural-language query comprehension, and report drafting.
4. **Resilience by Default:** If LLM access is interrupted, the deterministic fallback pipeline guarantees that reports, statistics, and candidate visualizations are still delivered without interruption.
5. **Transparency & Auditability:** Every recommendation and transformation is grounded in explicit mathematical evidence recorded in the audit log.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
