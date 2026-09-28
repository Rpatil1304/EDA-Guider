# EDA-Guider

**Agentic AI-driven Exploratory Data Analysis system** that acts as a generalized EDA decision-support tool for arbitrary tabular datasets (CSV/Excel).

EDA-Guider analyzes the structure and quality of an uploaded dataset, recommends dataset-specific preprocessing actions, performs safe preprocessing on an internal copy, computes statistical information, recommends useful visualizations, and generates a grounded final EDA report.

The system is designed to **assist the analyst rather than replace the analyst**. The original uploaded dataset is never modified, and raw dataset records are not passed to the LLM models.

---

## Architecture

```text
                              EDA-GUIDER
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   Data Upload    │
                         │    CSV / Excel   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Ingestion     │
                         │   & Validation   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Data Profiling & │
                         │ Custom Type      │
                         │    Inference     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Preprocessing   │
                         │   Rule Engine    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Safe Internal    │
                         │ Preprocessing    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Cleaned Internal │
                         │      Data        │
                         └────────┬─────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
             ┌──────────────────┐     ┌──────────────────┐
             │ Statistical      │     │ Visualization    │
             │ Engine           │     │ Rule Engine      │
             └────────┬─────────┘     └────────┬─────────┘
                      │                        │
                      └───────────┬────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Structured       │
                         │ Evidence         │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Model 1      │
                         │ Visualization    │
                         │    Selection     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Selected         │
                         │ Visualizations   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Model 2      │
                         │  Final EDA       │
                         │     Report       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Final Structured │
                         │    EDA Report    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Dashboard     │
                         │   + Audit Trail  │
                         └──────────────────┘
```

---

## Core Workflow

### 1. Data Upload & Ingestion

The user uploads a tabular dataset in CSV or Excel format. The ingestion layer validates the input and loads it into a working DataFrame without modifying the uploaded source.

### 2. Data Profiling

EDA-Guider performs custom dataset profiling instead of blindly relying on Pandas data types.

The profiling stage analyzes:

- Raw data type and inferred semantic type
- Missing-value count and percentage
- Unique-value count and cardinality
- Whitespace, empty strings, and null-like values
- Numeric, datetime, and boolean parseability
- Mixed data types
- Potential identifier and constant columns
- Duplicate values and outlier-related characteristics

It handles cases such as numbers or dates stored as strings, percentages containing `%`, extra whitespace, inconsistent capitalization, and null-like strings such as `NA`, `N/A`, `NULL`, or `None`.

### 3. Custom Preprocessing Rule Engine

A deterministic preprocessing rule engine analyzes profiling evidence and creates dataset-specific preprocessing actions.

Supported actions include:

- Replacing null-like values
- Replacing empty strings
- Removing unnecessary whitespace
- Numeric conversion
- Datetime conversion
- Boolean conversion
- Case normalization
- Categorical classification
- Identifier preservation
- Free-text preservation
- Review-required situations

The decisions depend on the characteristics of the dataset rather than a fixed preprocessing template.

### 4. Safe Internal Preprocessing

Preprocessing is performed on a **private deep copy** of the uploaded DataFrame. The original dataset is never modified.

High-confidence actions are applied internally, while lower-confidence or unsupported actions can be recorded for review.

For type conversions:

- Valid values are converted to the target type.
- Invalid non-null values are converted to missing values.
- Existing missing values are tracked separately.
- Conversion outcomes and confidence information are recorded.

### 5. Preprocessing Audit Trail

Every preprocessing decision is recorded in an execution log containing information such as:

- Column affected
- Action performed
- Execution status
- Reason for the action
- Confidence
- Values changed
- Missing-value percentage before and after conversion
- Existing missing-value count before conversion
- Invalid non-null value count
- Conversion-related data-quality information

### 6. Statistical Analysis

After preprocessing, EDA-Guider computes statistical information from the cleaned internal dataset.

**Numeric analysis:** count, mean, median, standard deviation, minimum, maximum, quartiles, IQR, skewness, kurtosis, outlier bounds, outlier count, and outlier percentage.

**Categorical analysis:** count, unique values, top category, frequency, percentages, and top categories.

**Datetime analysis:** minimum date, maximum date, unique dates, and duration.

**Boolean analysis:** true/false counts and percentages.

**Relationship analysis:** numeric correlation matrix.

### 7. Rule-Based Visualization Recommendation Engine

EDA-Guider contains a deterministic visualization recommendation engine. It does **not generate charts**; it recommends visualizations based on the actual dataset structure and statistical evidence.

Supported recommendation types include:

- Histogram
- Box plot
- Bar chart
- Pie chart
- Scatter plot
- Line chart
- Grouped bar chart
- Stacked bar chart
- 100% stacked bar chart
- Correlation heatmap
- Missingness bar chart
- Missingness heatmap
- Violin plot
- QQ plot
- Pair plot

Each recommendation contains a rule ID, chart type, relevant columns, reason, confidence, and priority. The rule engine produces **candidates**, not the final visualization list.

### 8. Model 1 — Visualization Selection

Model 1 receives structured, privacy-safe evidence containing:

- Raw dataset information
- Preprocessing information
- Cleaned dataset information
- Statistical information
- Rule-based visualization candidates

Its responsibility is to select a small set of useful, complementary, and non-redundant visualizations.

It avoids redundant combinations such as multiple distribution charts for the same variable, bar and pie charts for the same category, excessive scatter plots, and multiple charts describing the same missingness pattern.

### 9. Model 2 — Final EDA Report Generation

Model 2 receives:

- Raw dataset information
- Preprocessing information
- Cleaned dataset information
- Statistical information
- Rule-based visualization candidates
- Visualizations selected by Model 1

Model 2 does not access original dataset rows. Its role is to synthesize the supplied evidence into one concise, human-readable EDA report.

The final report contains exactly five sections:

1. **Raw Data Information**
2. **Preprocessing Done**
3. **Cleaned Data Information**
4. **Statistical Information**
5. **Visualization Information**

The report explains important findings without exposing raw records or mechanically reproducing every internal preprocessing step, statistic, or visualization candidate.

### 10. Privacy-Safe Evidence Passing

The LLM models receive structured aggregate evidence rather than individual dataset records. The evidence can contain dataset dimensions, column metadata, data-quality information, preprocessing decisions, aggregate statistics, correlations, visualization candidates, and selected visualizations.

### 11. LangChain Architecture

LangChain is used to orchestrate the model stages with modern Runnable-based workflows.

The project uses:

- `ChatPromptTemplate`
- `RunnableLambda`
- `RunnableParallel`
- `PydanticOutputParser`

The LLM flow is:

```text
Structured Evidence
       │
       ▼
RunnableParallel
       │
       ▼
Prompt Template
       │
       ▼
LLM Model
       │
       ▼
Pydantic Output Parser
       │
       ▼
Structured Result
```

### 12. Structured Output

Pydantic schemas enforce structured outputs for visualization selection and final EDA report generation. This makes model responses predictable and easier for the application to consume.

### 13. Auditability

EDA-Guider maintains an audit trail for preprocessing and analytical decisions, providing visibility into what action was considered, which column was affected, why the action was performed, whether it was executed or skipped, confidence associated with the decision, and the data-quality effects of conversions.

---

## Design Principles

- **Analyst stays in control** — the system provides recommendations and explanations rather than replacing human judgment.
- **Original data is never modified** — preprocessing is performed on an internal copy.
- **Dataset-adaptive** — preprocessing and visualization recommendations depend on the actual dataset.
- **Deterministic where reliability matters** — profiling, preprocessing rules, statistics, and visualization candidate generation use deterministic logic.
- **Model-based reasoning and synthesis** — Model 1 selects useful visualizations and Model 2 produces the final human-readable report.
- **Evidence-grounded** — models receive structured evidence rather than raw dataset records.
- **Explainable by default** — preprocessing decisions and their reasoning are recorded in the audit trail.
- **No chart generation** — the system recommends suitable visualizations but does not render the charts itself.

---

## Tech Stack

- **Python** — core application and pipeline development
- **Pandas** — data loading, manipulation, profiling, preprocessing, and statistical analysis
- **Custom Rule Engine** — deterministic profiling, preprocessing decisions, and visualization recommendation logic
- **LangChain** — LLM orchestration using Runnable-based workflows
- **Google Gemini** — Model 1 for visualization selection and Model 2 for final EDA report generation
- **Pydantic** — structured validation and LLM output schemas
- **Streamlit** — interactive application interface
