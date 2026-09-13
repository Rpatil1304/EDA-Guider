# EDA-Guider Project Guide

## 1. Project Purpose

EDA-Guider is a privacy-conscious, rule-based exploratory data analysis assistant. It loads a raw CSV, TSV, XLS, XLSX, or XLSM dataset; profiles it without changing the source; creates an evidence-based preprocessing plan; applies safe transformations to an internal copy; validates the result; generates raw and cleaned profiling reports; and prepares structured evidence for a future LangChain/LLM reporting stage.

The original uploaded file is never overwritten. The cleaned DataFrame is an internal working object and can be exported separately as a processed CSV.

The current implementation is strongest in ingestion, profiling, preprocessing, validation, audit logging, and report generation. LangChain has not yet been connected to an external model. The current agent work prepares a privacy-safe input boundary for that future integration.

## 2. Current End-to-End Flow

```text
User or runner provides a dataset
        |
        v
File type and byte validation
        |
        v
CSV/TSV or Excel ingestion
        |
        v
Raw header and structure validation
        |
        v
Raw profile and YData raw HTML report
        |
        v
Rule-based preprocessing plan
        |
        v
Safe preprocessing on a deep internal copy
        |
        v
Conversion and structural validation
        |
        v
Cleaned profile and YData cleaned HTML report
        |
        v
Before/after summary and downstream handoff
        |
        v
Privacy-safe aggregate evidence for future LangChain use
```

The active pipeline entry point is:

```text
backend/app/preprocessing/pipeline.py
run_preprocessing_pipeline(file_path_or_buffer)
```

## 3. Main Modules

| Responsibility | Implementation |
| --- | --- |
| File loading | `backend/app/ingestion/loader.py` |
| Structure validation | `backend/app/ingestion/structural.py` |
| Shared numeric parsing | `backend/app/profiling/parsing.py` |
| Raw and cleaned profiling | `backend/app/profiling/raw_profiler.py` |
| Rule generation | `backend/app/preprocessing/raw_rule_engine.py` |
| Safe transformations | `backend/app/preprocessing/preprocessor.py` |
| Pipeline orchestration | `backend/app/preprocessing/pipeline.py` |
| Transformation validation | `backend/app/execution/validator.py` |
| Before/after summary and handoff | `backend/app/preprocessing/summary.py` |
| Markdown report | `backend/app/reporting/guide.py` |
| YData HTML reports | `_generate_ydata_profile` in `pipeline.py` |
| Future LLM input preparation | `backend/app/agent/agent.py` |
| Local runner | `backend/run_sample_pipeline.py` |
| Tests | `backend/tests/` |

The active Parts 1 to 6 flow uses `raw_profiler.py` and `raw_rule_engine.py`. Older profiling and rule-engine modules remain in the repository as earlier or alternative implementations but are not the controlling path for the current preprocessing pipeline.

## 4. Pipeline Result

`run_preprocessing_pipeline` returns a structured dictionary containing:

```text
status
ingestion_report
raw_ydata_profile_report
cleaned_ydata_profile_report
structural_report
raw_profile_report
preprocessing_plan
execution_log
preprocessing_summary_report
cleaned_dataframe
pipeline_error
```

`cleaned_dataframe` is retained for internal processing and local export. It should not be sent directly to an external LLM or exposed as the LLM prompt input.

If a stage fails, the pipeline returns structured information from completed stages and places the failing stage, exception type, and message in `pipeline_error`.

## 5. Part 1 - File Type and Ingestion

### 5.1 File extension detection

The loader determines the file type from the filename extension. Supported extensions are:

- `.csv`
- `.tsv`
- `.xls`
- `.xlsx`
- `.xlsm`

Unsupported extensions are rejected with a clear structured error before parsing.

A file-like object uses its `.name` attribute when available. If no extension is available, the loader may use file signatures as a fallback and records a warning that the type was inferred.

### 5.2 Zero-byte validation

The raw bytes are read once and their size is recorded. A zero-byte file is rejected before any CSV or Excel parser is called.

### 5.3 Encoding detection

For text files, the loader:

1. Checks for a UTF-8 byte-order mark.
2. Attempts detection from the raw byte sample using `chardet`.
3. Falls back to `charset-normalizer` when available.
4. Falls back to UTF-8 if detection is unavailable.
5. Records the selected encoding and confidence.
6. Warns when confidence is low.
7. Prefers strict UTF-8 decoding when a low-confidence detector result is valid UTF-8.

### 5.4 CSV and TSV parsing

The loader supports comma, semicolon, tab, and pipe delimiters. It scores candidates by parsed row-width consistency and respects CSV quoting, so a value such as `"1,610"` is not mistaken for an extra column.

If delimiter detection cannot find a useful candidate, the loader defaults to comma and records a possible single-column warning. TSV files use tab as their known delimiter.

Header detection uses the first-row detector and defaults to assuming a header when detection fails. The raw header row is also captured as plain text before Pandas header normalization.

### 5.5 Excel parsing

For XLS, XLSX, and XLSM files:

1. The workbook is opened through Pandas.
2. All worksheet names are collected.
3. Only the first worksheet is loaded into the DataFrame.
4. Remaining worksheets are recorded as skipped.
5. A warning describes the selected worksheet and skipped sheets.

Excel support requires the appropriate packages in `backend/requirements.txt`, including `openpyxl` for modern Excel files and `xlrd` for legacy XLS files.

### 5.6 Structured ingestion report

The ingestion report contains:

- File name
- File type
- File size
- Encoding
- Encoding confidence
- Delimiter
- Header status
- Raw header
- Worksheet names
- Skipped worksheets
- Row and column counts
- Warnings
- Errors

Load failures are returned as structured errors and do not crash the caller.

## 6. Part 2 - Header and Structure Normalization

Structure validation receives the loaded DataFrame and returns a copied, internally normalized DataFrame.

### 6.1 Fatal structure checks

Processing stops when:

- The object is not a Pandas DataFrame.
- The DataFrame has zero columns.
- The DataFrame has zero rows.

### 6.2 Header normalization

Column names are normalized without changing data values:

- Trim surrounding whitespace.
- Convert spacing and special characters to underscores.
- Normalize names to lowercase.
- Assign generic names such as `column_1` to blank or `Unnamed:` headers.
- Make normalized names unique with deterministic suffixes.

For example:

```text
" Customer Name ", "Customer-Name"
```

becomes names such as:

```text
customer_name, customer_name_2
```

The report records original names, normalized names, and renames.

### 6.3 Duplicate columns

Two duplicate concepts are tracked separately:

1. Duplicate header names.
2. Different headers whose complete column values are identical.

Neither is removed automatically. Identical-value columns receive a review action.

### 6.4 Index-like columns

A blank, `Unnamed: 0`, or `index` column containing a zero-based numeric sequence is flagged as an exported index. It is retained and receives `review_index_column`; it is not silently dropped.

### 6.5 Dataset-size warnings

The validator warns about:

- One-row datasets.
- Very small datasets below the configured practical minimum.
- Single-column datasets where correlation and multi-column analysis are limited.

## 7. Part 3 - Raw Profile

The raw profile is generated before preprocessing. It is read-only and describes the original loaded values.

### 7.1 Per-column fields

Each column profile includes:

- Column name
- Raw dtype
- Sample values for local reports
- Actual null count and percentage
- Null-like count and marker breakdown
- Empty-string count
- Whitespace-only count
- Leading/trailing whitespace count
- Mixed Python type count
- Case-variation signal
- Average string length
- Unique count
- Uniqueness ratio
- Numeric parseability percentage
- Datetime parseability percentage
- Boolean parseability percentage
- Identifier signal
- Index signal
- Categorical signal
- Free-text signal
- Semantic type
- Classification confidence
- Format signatures
- Mixed-format warning
- Outlier count and values for local reports
- Skewness
- Quality warnings

### 7.2 Semantic types

The classifier can assign:

- `numeric`
- `datetime`
- `boolean`
- `categorical`
- `identifier`
- `free_text`
- `unresolved`

Every classification has a confidence between `0.0` and `1.0`. Unresolved or low-confidence columns are not guessed into a conversion.

### 7.3 Dataset-level profile

The dataset profile includes:

- Total cells
- Actual null totals
- Null-like totals
- Total missingness
- Empty-string totals
- Whitespace-only totals
- Marker-by-marker null-like totals
- Columns affected by each condition
- Identical-value column pairs
- High-correlation warnings
- High-missingness warnings
- High-cardinality warnings
- Constant-column warnings

## 8. Missing Values and Text Policy

The system separates actual missing values from text markers such as:

```text
""
"na"
"n/a"
"nan"
"null"
"none"
"missing"
```

The raw report counts each category separately. The current rule-based policy is conservative:

- Report missing and null-like values.
- Preserve them in the internal copy.
- Do not automatically fill them.
- Do not automatically delete them.
- Do not silently convert them into another value.

Whitespace cleanup is different because it is non-destructive normalization. Leading and trailing whitespace is stripped from string columns in the internal copy, while non-string values remain unchanged.

## 9. Numeric, Date, Boolean, and Format Detection

### 9.1 Numeric parser

The shared parser in `profiling/parsing.py` accepts:

- Integers
- Decimal values
- Negative values
- Western grouped values such as `1,610` and `12,345.67`
- Indian grouped values such as `89,17,000`

It rejects inconsistent grouping such as `1,2,3` rather than guessing.

Currency symbols, percentages, units, and measurement conversions are not automatically stripped by the numeric parser.

### 9.2 Datetime detection

String-like values are tested with mixed-format datetime parsing. Numeric and Boolean columns are excluded from date inference to prevent ordinary numbers from becoming timestamps accidentally.

### 9.3 Boolean detection

The parser recognizes `true`, `false`, `yes`, `no`, `y`, `n`, `1`, and `0`, ignoring case and surrounding whitespace.

### 9.4 Mixed-format detection

The profiler records conservative format signatures for:

- ISO dates
- Numeric slash-separated dates
- Named-month dates
- Unit-bearing values
- Currency symbols
- Percentages
- Unitless numeric values

When multiple incompatible signatures appear in one column, the rule engine creates `review_mixed_format` and does not assume a conversion.

## 10. Part 4 - Rule-Based Preprocessing Plan

The rule engine receives the raw DataFrame and raw profile and creates a validated `PreprocessingPlan`. Plan generation does not modify data.

Each action contains:

- Target columns
- Action name
- Confidence
- Reason
- Optional parameters

### 10.1 Main actions

| Action | Meaning | Default behavior |
| --- | --- | --- |
| `strip_whitespace` | Remove outer text whitespace | Execute internally |
| `convert_to_numeric` | Convert high-confidence numeric strings | Execute only if lossless |
| `convert_to_datetime` | Convert high-confidence dates | Execute only if lossless |
| `convert_to_boolean` | Convert recognized Boolean strings | Execute only if lossless |
| `classify_as_categorical` | Record categorical classification | Log without changing values |
| `normalize_case` | Normalize confirmed categories | Execute explicitly |
| `preserve_identifier` | Protect identifier columns | Preserve and log |
| `preserve_free_text` | Protect free text | Preserve and log |
| `review_index_column` | Flag exported index | Needs review |
| `review_duplicate_column` | Flag identical-value columns | Needs review |
| `review_outliers` | Report IQR outliers | Needs review; retain values |
| `review_skewness` | Report heavy skew | Needs review |
| `review_mixed_format` | Flag incompatible formats | Needs review |
| `review_semantic_type` | Flag unresolved type | Needs review |

Missing-value replacement actions are intentionally not generated by the current active rule path because the checklist requires reporting and preservation rather than automatic filling or deletion.

### 10.2 Confidence rules

High-confidence conversions require confidence of at least `0.80`. Lower-confidence conversions receive review treatment. Categorical classification and normalization are also confidence-gated.

## 11. Part 5 - Internal Preprocessing

The executor starts with a deep copy. The source file and raw DataFrame remain unchanged.

### 11.1 Execution order

1. Strip whitespace from string/object columns.
2. Detect duplicate column names.
3. Detect exact duplicate rows.
4. Apply high-confidence numeric conversion.
5. Apply high-confidence datetime conversion.
6. Apply high-confidence Boolean conversion.
7. Record categorical classification.
8. Apply explicit categorical case normalization.
9. Record preservation and review decisions.
10. Return the cleaned copy and complete execution log.

### 11.2 Conversion safety

For every conversion, the executor records null percentage before and after conversion and counts invalid non-null values that would become missing.

A conversion is rejected and the original values are restored when:

- Any non-null value would be lost.
- The configured data-loss threshold would be exceeded.
- The conversion confidence is below the execution threshold.
- The column is entirely null.

Unknown Boolean values such as `maybe` cause rejection rather than silently becoming false or missing.

### 11.3 Action statuses

Every action has one of these statuses:

- `executed`: transformation or detection completed.
- `skipped`: deliberately not applicable or entirely null.
- `rejected`: conversion would lose data and was rolled back.
- `needs_review`: deliberate human-review decision.
- `unsupported`: no executor exists for an unknown action, which is a system issue.

## 12. Outliers and Skewness

Every numeric column is checked using an IQR-based method. The report records:

- Outlier count
- Outlier values in local reports
- Skewness
- Heavy-skew warning when absolute skewness reaches the configured threshold

Outliers are not automatically removed or corrected. The rule engine creates review actions so downstream statistics and visualization logic can decide how to handle them.

## 13. Part 6 - Validation and Immutability

After preprocessing, validation checks:

- Row count preservation.
- Column name and order preservation.
- Non-empty cleaned DataFrame.
- Original raw DataFrame equality with its first deep snapshot.

The pipeline returns a structured validation error if preprocessing changes row or column structure unexpectedly.

## 14. Part 7 - Cleaned Profile and Before/After Summary

The cleaned internal DataFrame is re-profiled using the same profiler as the raw data.

The summary contains:

- Raw profile
- Cleaned profile
- Raw and cleaned shape
- Column-by-column positional diff
- Dtype before and after
- Null percentage before and after
- Unique count before and after
- Related actions per column
- Original null summary
- Execution log
- Action-status totals
- Changed-column count
- Unresolved columns
- Needs-review columns
- Excluded columns and reasons
- Downstream handoff metadata

## 15. YData Profiling Reports

The pipeline generates two separate YData Profiling HTML reports using the same `_generate_ydata_profile` function in `pipeline.py`.

### 15.1 Raw report

Generated immediately after ingestion and before preprocessing:

```text
<dataset>_raw_profiling_report.html
```

This report describes the loaded raw DataFrame.

### 15.2 Cleaned report

Generated after preprocessing and structural validation:

```text
<dataset>_cleaned_profiling_report.html
```

This report describes the cleaned internal DataFrame.

YData Profiling uses minimal mode for compatibility and performance. If the package is not installed, the pipeline records an `unavailable` status instead of crashing the preprocessing process.

The HTML reports are local artifacts. They may contain sample values, so they must not be sent directly to an external LLM.

## 16. Markdown Preprocessing Report

`backend/app/reporting/guide.py` generates the user-readable Markdown report. It reads the structured pipeline result and does not rerun or modify the dataset.

The Markdown report includes:

- Ingestion metadata
- Structure validation
- Duplicate and index warnings
- Raw missingness breakdown
- Semantic type and confidence table
- Parseability percentages
- Outlier and skewness fields
- Preprocessing plan
- Execution log
- Status totals
- Raw/cleaned shape comparison
- Cleaned missingness
- Snapshot validation
- Unresolved and needs-review columns
- Exclusion reasons
- Downstream eligible columns
- Sampling metadata
- Future statistics and visualization stages

## 17. Privacy-Safe LangChain Input Preparation

The agent module now contains:

```python
build_llm_evidence_input(pipeline_result)
```

This function prepares the future LangChain input from existing structured reports. It does not call an LLM yet.

### 17.1 Included evidence

The evidence payload includes:

- Dataset name and pipeline status
- Ingestion metadata
- Structural findings
- Aggregate raw profile metrics
- Semantic classifications and confidence
- Missingness totals and percentages
- Parseability percentages
- Outlier and skewness metadata
- Preprocessing plan
- Execution actions and measurements
- Cleaned profile metadata
- Before/after summary
- Excluded and needs-review columns
- Downstream eligible columns
- Raw and cleaned YData report status

### 17.2 Excluded content

The LLM evidence payload deliberately excludes:

- The raw DataFrame
- The cleaned DataFrame
- Raw sample values
- Outlier values
- YData HTML content
- Direct row-level dataset values

Privacy metadata records that these fields were removed. This allows a future LLM to explain computed evidence without receiving the actual dataset.

### 17.3 Intended future LangChain flow

```text
Pipeline result
    |
    v
build_llm_evidence_input
    |
    v
Privacy-safe aggregate JSON
    |
    v
LangChain prompt/model
    |
    v
Structured overall report
    |
    v
Evidence validation
```

The LLM should interpret and explain locally computed facts. It should not be responsible for calculating statistics from raw rows or inventing unsupported findings.

## 18. Downstream Handoff

The preprocessing summary contains a `downstream_handoff` object with:

- `eligible_columns`
- `excluded_columns`
- Exclusion reasons
- Sampling metadata
- Original row count
- Analysis row count
- Maximum analysis sample size
- Confirmation that the cleaned dataset was not changed by sampling

Identifiers, free text, unresolved columns, and review-flagged columns are excluded from downstream analysis metadata. The cleaned DataFrame itself is not sampled or altered at this stage.

## 19. Running a New Dataset

Configure the path in:

```text
backend/run_sample_pipeline.py
```

Run from the project root with an environment containing the backend dependencies:

```powershell
.\.myvenv\Scripts\python.exe backend\run_sample_pipeline.py
```

The runner prints:

- Pipeline status
- Raw YData report status
- Cleaned YData report status
- Ingestion and structure details
- Raw profile
- Preprocessing plan
- Execution log
- Summary
- Cleaned-data preview

For a path input, it writes:

```text
<dataset>_processed.csv
<dataset>_eda_report.md
<dataset>_raw_profiling_report.html
<dataset>_cleaned_profiling_report.html
```

The input dataset is not overwritten.

## 20. Europe Dataset Example

For `europe.csv`:

- The dataset loads successfully with 36 rows and 11 columns.
- The blank first column is identified as an exported index and retained for review.
- Grouped numeric values such as `"1,610"` are converted safely to `1610.0`.
- Numeric conversion introduces no nulls.
- Raw and cleaned YData reports are generated in the supported environment.
- The raw snapshot remains unchanged.
- Outliers and skewness are reported for review rather than automatically corrected.

## 21. Testing

Run the backend tests:

```powershell
cd backend
python -m pytest -q
```

The test suite covers:

- File extensions and zero-byte inputs
- CSV, TSV, and Excel ingestion
- Encoding and delimiter behavior
- Header and duplicate-column handling
- Index-like and identical-value columns
- Raw profiling immutability
- Missingness rollups
- Numeric, datetime, and Boolean parseability
- Grouped numeric parsing
- Semantic classification and confidence
- Mixed date and unit formats
- Outliers and skewness
- Safe conversion and rollback
- Unknown versus review actions
- Categorical normalization
- Identifier and free-text preservation
- Unresolved-column review
- Snapshot validation
- Cleaned re-profiling
- Before/after summary
- Downstream handoff
- Privacy-safe LLM evidence extraction
- Markdown report generation

The Excel test requires `openpyxl` in the selected environment. YData HTML generation requires a compatible Python environment with `ydata-profiling` installed.

## 22. Dependencies

Backend dependencies are declared in `backend/requirements.txt`.

Important packages include:

- Pandas for DataFrames and ingestion.
- `chardet` and `charset-normalizer` for encoding detection.
- `openpyxl` and `xlrd` for Excel support.
- Pydantic for structured action schemas.
- YData Profiling for local HTML reports.
- Pytest for regression testing.
- NumPy, scikit-learn, and Plotly for future analysis stages.

LangChain and an LLM provider are not yet connected. The privacy-safe evidence boundary is implemented first so that a future model integration receives aggregate evidence rather than raw data.

## 23. Current Status

### Implemented

- Multi-format ingestion and structured errors.
- Raw header and structure handling.
- Raw profiling and missingness reporting.
- Semantic type classification and confidence.
- Numeric, datetime, and Boolean parseability.
- Safe conversions with rollback.
- Categorical normalization.
- Identifier/free-text preservation.
- Unresolved and mixed-format review.
- Duplicate and index review.
- Outlier and skewness reporting.
- Complete execution logging.
- Raw snapshot verification.
- Cleaned re-profiling.
- Before/after summary.
- Downstream handoff metadata.
- Raw and cleaned YData HTML reports.
- Detailed Markdown preprocessing report.
- Privacy-safe aggregate evidence preparation for LangChain.

### Not yet connected

- LangChain model invocation.
- Provider/API configuration and secret management.
- LLM-generated overall narrative report.
- Evidence-grounded hallucination checking.
- Rule-based statistical profiling module in the main pipeline.
- Rule-based visualization recommendation output in the main pipeline.
- Final chart/report/dashboard delivery workflow.

## 24. Recommended Next Stage

The next implementation stage should add LangChain around the existing evidence boundary:

1. Choose a model/provider or local model.
2. Configure secrets outside source control.
3. Convert the evidence dictionary to a validated JSON prompt input.
4. Ask for structured report sections and visualization recommendations.
5. Validate the model response against the `EDAReport` schema.
6. Check every claim against the evidence dictionary.
7. Reject unsupported claims.
8. Keep the raw and cleaned datasets local.

```text
Local ingestion and preprocessing
        |
        v
Local raw/cleaned profiles
        |
        v
Privacy-safe aggregate evidence
        |
        v
LangChain structured generation
        |
        v
Evidence validation
        |
        v
Final report and visualization recommendations
```

## 25. Remaining Implementation Roadmap

The preprocessing and privacy-safe evidence stages are implemented. The following work remains before EDA-Guider can generate a complete statistics, visualization, and LLM-written insight report.

### 25.1 Stage A - Complete local statistical profiling

**Current status:** Not connected. `backend/app/statistics/statistical_profiler.py` is currently empty, although statistical Pydantic schemas already exist in `backend/app/schemas/statistics.py`.

**Implementation steps:**

1. Accept the cleaned DataFrame and `downstream_handoff` metadata.
2. Use only eligible columns from the handoff.
3. Exclude identifiers, free text, unresolved columns, and review-excluded columns.
4. Compute numeric statistics:
        - Count
        - Missing count and percentage
        - Mean, median, standard deviation
        - Minimum and maximum
        - Quartiles
        - Skewness and kurtosis
        - IQR bounds
        - Outlier count and percentage
5. Compute categorical statistics:
        - Count
        - Unique count
        - Most frequent category
        - Top-category frequencies and percentages
6. Compute datetime statistics:
        - Minimum date
        - Maximum date
        - Unique count
        - Duration in days
7. Compute Boolean statistics:
        - True count and percentage
        - False count and percentage
8. Compute correlations only for eligible numeric columns.
9. Return a validated `StatisticalProfile` object.
10. Add tests for numeric, categorical, datetime, Boolean, missing, excluded, and constant columns.

**Important rule:** statistics must be calculated locally. The LLM should receive the aggregate statistical result, not the DataFrame.

### 25.2 Stage B - Implement deterministic visualization recommendations

**Current status:** The repository contains visualization modules and schemas, but the complete recommendation flow is not connected to the active preprocessing pipeline. Plot rendering is also only a stub in `backend/app/visualization/plotly_renderer.py` if that module is used.

**Implementation steps:**

1. Accept `StatisticalProfile` and the downstream handoff.
2. Recommend charts from deterministic rules, for example:
        - Numeric distribution: histogram
        - Numeric outlier review: box plot
        - Skewed numeric column: histogram with log-scale suggestion
        - Two numeric columns with meaningful correlation: scatter plot
        - Categorical column: bar chart
        - Datetime column: time-series line chart
        - Boolean column: count bar chart
        - Numeric by category: grouped bar or box plot
3. Never recommend charts using excluded columns.
4. Include chart type, columns, title, reason, and supporting evidence IDs.
5. Validate that every recommended column exists and is eligible.
6. Add tests for each chart rule and excluded-column behavior.

**Important rule:** chart selection should remain deterministic and rule-based. LangChain may explain a recommendation, but it should not invent chart specifications.

### 25.3 Stage C - Build a stable evidence package

**Current status:** Partially implemented. `build_llm_evidence_input()` in `backend/app/agent/agent.py` already removes raw samples, outlier values, DataFrames, and YData HTML.

**Implementation steps:**

1. Add the local `StatisticalProfile` to the evidence package.
2. Add deterministic visualization recommendations.
3. Assign stable evidence IDs to every statistic, warning, decision, and recommendation.
4. Store the source field, column, metric, and value for each evidence item.
5. Remove direct identifiers and sensitive column names when required by the privacy policy.
6. Validate that no DataFrame, HTML, sample, row value, or outlier value enters the final payload.
7. Serialize the package as validated JSON.
8. Add a privacy test that scans serialized JSON for prohibited fields and values.

The package should have this conceptual structure:

```text
dataset_metadata
ingestion_evidence
structure_evidence
profiling_evidence
preprocessing_evidence
statistical_evidence
visualization_evidence
validation_evidence
privacy_metadata
```

### 25.4 Stage D - Connect LangChain

**Current status:** Not implemented. The current `Agent` class is a placeholder and does not call a model.

**Implementation steps:**

1. Choose the LLM provider or local model.
2. Add LangChain and the provider package to `backend/requirements.txt`.
3. Configure the API key or local model outside source control.
4. Add environment-variable validation and a clear missing-configuration error.
5. Define a prompt that explains:
        - The input is aggregate evidence only.
        - Raw data was not provided.
        - Every claim must reference supplied evidence IDs.
        - Unsupported claims must be omitted or marked uncertain.
6. Use structured output matching `EDAReport` in `backend/app/schemas/report.py`.
7. Send only the validated evidence JSON to LangChain.
8. Parse and validate the model response with Pydantic.
9. Reject malformed output and retry only under a bounded policy.
10. Record model name, prompt version, evidence version, and response validation status.

LangChain should explain local facts. It should not calculate unknown statistics, inspect raw files, or receive the original DataFrame.

### 25.5 Stage E - Add evidence and hallucination validation

**Current status:** Not implemented.

**Implementation steps:**

1. Require each generated insight to include evidence IDs.
2. Check that every evidence ID exists in the local evidence package.
3. Check that mentioned columns exist in the profile.
4. Check that mentioned values and percentages match computed values within an allowed rounding tolerance.
5. Reject claims that have no supporting evidence.
6. Mark unsupported or uncertain statements instead of silently accepting them.
7. Set `hallucination_checked=True` only after validation succeeds.
8. Store rejected claims in the audit trail.

### 25.6 Stage F - Assemble the final report

**Current status:** The preprocessing Markdown report is implemented. The final statistics/insights report is not assembled.

**Implementation steps:**

1. Combine ingestion details, preprocessing findings, statistics, charts, and validated LLM insights.
2. Populate `EDAReport` with:
        - Dataset name
        - Overall summary
        - Evidence-backed insights
        - Visualization recommendations
        - Preprocessing summary
        - Statistics summary
        - Hallucination-check status
3. Preserve raw and cleaned YData report links as local artifacts.
4. Add Markdown and JSON export.
5. Add an optional HTML/PDF presentation layer after the content is validated.

### 25.7 Stage G - Connect API and frontend

**Current status:** The frontend exists, but the upload-to-final-report workflow is not fully connected. The API analysis endpoint is incomplete.

**Implementation steps:**

1. Accept an uploaded file through the API instead of accepting an unvalidated path only.
2. Store the upload in a controlled temporary location.
3. Run the local pipeline.
4. Return report metadata and local artifact references without returning raw data.
5. Add a separate endpoint for validated final report generation.
6. Stream progress states for ingestion, profiling, preprocessing, statistics, visualization, and LLM reporting.
7. Display review-required actions before any user-approved destructive operation.
8. Keep API responses free of raw samples and DataFrames.

### 25.8 Stage H - Security and production hardening

Before external LLM use, implement:

- Secret management through environment variables or a secret manager.
- No API keys in source control.
- Request and response size limits.
- File-size and row-count limits.
- Temporary-file cleanup.
- Prompt-injection handling for text fields.
- PII and sensitive-column detection.
- Column-name and report-content redaction policy.
- Model timeout and retry limits.
- Audit logging without raw values.
- Explicit user consent before external transmission.

## 26. Recommended Implementation Order

The safest implementation order is:

```text
1. Complete local statistical profiler
2. Add deterministic visualization recommender
3. Extend privacy-safe evidence package
4. Add evidence IDs and validation
5. Connect LangChain with structured output
6. Add hallucination/evidence checks
7. Assemble final report
8. Connect API and frontend
9. Add production security controls
```

Each stage should be implemented with focused tests before the next stage is started. The raw dataset should remain local throughout all stages unless the user explicitly enables an approved external data-sharing policy.
