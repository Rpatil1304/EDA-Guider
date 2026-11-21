# EDA-Guider

AI-Driven Exploratory Data Analysis and Decision-Support System

EDA-Guider is an exploratory data analysis (EDA) platform for tabular datasets (CSV, TSV, XLS, XLSX, XLSM). It combines deterministic data profiling and transformation rules with Google Gemini to generate structured analysis reports and provide interactive natural language querying.

Original raw data is never modified. Raw data rows are not sent to external LLMs; only aggregate metadata, schema details, and summary statistics are processed for report and query generation.

---

## Modes of Operation

### 1. RAW Dataset Mode (Automated EDA)
Designed for uncleaned datasets.
- **Profiling:** Detects data types, corrupt headers, null-like tokens (`NA`, `NULL`, `None`, empty strings), formatted numbers, dates, and outliers.
- **Rule-Based Preprocessing:** Deterministically normalizes missing tokens and data types on an isolated internal copy. Source data remains untouched.
- **Audit Logging:** Records every transformation step with confidence scores and before-and-after missing rates.
- **Statistical Analysis:** Computes summary metrics, distributions, IQR outlier thresholds, skewness, kurtosis, and correlation matrices.
- **Two-Stage Gemini Reporting:**
  - Prunes candidate charts to remove redundant visualizations.
  - Generates a structured executive EDA report covering raw data summary, preprocessing steps, cleaned data profile, statistics, and visualization insights.

### 2. Clean Dataset Mode (Interactive Q&A and Visualizer)
Designed for clean, ready-to-analyze datasets.
- **Natural Language Queries:** Query the dataset in plain English.
- **Sandboxed Code Generation:** Generates Pandas and Plotly code to compute answers and interactive charts.
- **AST Security Sandbox:** Validates generated code using Python Abstract Syntax Trees (AST) against an approved module list (`pandas`, `numpy`, `plotly`, `math`, `datetime`, `re`) and blocks hazardous built-ins (`open`, `eval`, `exec`).
- **Self-Healing Execution:** Captures execution errors and tracebacks, automatically retrying code generation up to two times.

---

## System Architecture

```text
                           User Dataset
                 (CSV / TSV / XLS / XLSX / XLSM)
                                |
        +-----------------------+-----------------------+
        |                                               |
        v                                               v
[ RAW Dataset Mode ]                           [ Clean Dataset Mode ]
Ingestion & Type Inference                     Metadata & Schema Extraction
        |                                               |
Deterministic Preprocessing (Deep Copy)         Natural Language User Query
        |                                               |
Audit Trail & Statistical Analysis              LLM Code Generation (Pandas/Plotly)
        |                                               |
Candidate Visualization Engine                  AST Code Validation & Security Check
        |                                               |
Two-Stage Gemini Pipeline                       Sandboxed Execution & Auto-Retry
  1. Chart Pruning                                      |
  2. Executive Report Generation                Synthesized Response & Plotly Chart
        |                                               |
        +-----------------------+-----------------------+
                                |
                                v
                        Streamlit Frontend
```

---

## Project Structure

```text
EDA-Guider/
├── backend/
│   ├── app/
│   │   ├── clean_query/      # Clean dataset Q&A and visualization engine
│   │   ├── execution/        # Safe transformation execution
│   │   ├── ingestion/        # File validation and loaders
│   │   ├── langchain/        # Two-stage Gemini LLM pipelines and prompts
│   │   ├── orchestration/    # End-to-end pipeline coordination
│   │   ├── preprocessing/    # Transformation rules
│   │   ├── profiling/        # Type inference and data profiling
│   │   ├── statistics/       # Descriptive and bivariate statistics
│   │   ├── visualization/    # Chart recommendation engine
│   │   ├── config.py         # App configuration
│   │   ├── llm_client.py     # Gemini client interface
│   │   └── main.py           # FastAPI entry point
│   └── requirements.txt      # Backend dependencies
├── frontend/
│   ├── components/           # Streamlit view components
│   ├── api.py                # Backend API client
│   ├── app.py                # Streamlit application entry point
│   └── config.py             # Frontend configuration
├── docker-compose.yml        # Docker composition file
├── Dockerfile                # Backend container definition
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/EDA-Guider.git
cd EDA-Guider
```

### 2. Backend Setup
1. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables in `backend/.env`:
   ```ini
   GOOGLE_API_KEY="your-google-gemini-api-key"
   GEMINI_MODEL="gemini-3.1-flash-lite-preview"
   DEBUG=False
   ```

4. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   API documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
1. Open a separate terminal, activate the virtual environment, and navigate to `frontend`:
   ```bash
   cd frontend
   streamlit run app.py
   ```
2. The user interface will open in your browser at `http://localhost:8501`.

### 4. Running with Docker
```bash
docker-compose up --build
```
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## Security and Privacy

- **Data Privacy:** Raw data records are never passed to external LLM APIs. Only metadata schemas and computed aggregate statistics are shared.
- **Immutability:** Operations run on deep copies of the data, leaving user input files untouched.
- **Code Sandboxing:** All dynamically generated code passes through an AST parser before execution to prevent arbitrary code execution and restrict imports to an allowlist.

---

## License

This project is licensed under the MIT License.
