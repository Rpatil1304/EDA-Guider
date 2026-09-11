# EDA-Guider Project Guide

## 1. Purpose

EDA-Guider is a rule-based assistant for the early stages of exploratory data analysis (EDA). It accepts CSV and Excel files, records how they were loaded, profiles the original values, creates an evidence-based preprocessing plan, applies only safe transformations to an internal copy, validates the result, and generates a readable Markdown report.

The uploaded source file is never overwritten. The processed DataFrame is separate from the original input and can be saved as a new CSV.

The currently connected pipeline implements ingestion through preprocessing summary. Statistical analysis, visualization selection, insight synthesis, and the complete frontend workflow are separate stages and are not yet fully connected to this pipeline.

## 2. Main Pipeline

The active entry point is:

```text
backend/app/preprocessing/pipeline.py
run_preprocessing_pipeline(file_path_or_buffer)
```

The execution order is:

```text
1. Read CSV or Excel input
2. Detect file metadata
3. Build the raw DataFrame
4. Profile the untouched raw values
5. Validate and normalize structure
6. Generate a rule-based preprocessing plan
7. Execute safe plan actions on a deep copy
8. Check row and column preservation
9. Profile the cleaned internal copy
10. Build the before-and-after summary
11. Save or return the processed data and report
```

The structured pipeline result contains:

```text
status
ingestion_report
structural_report
raw_profile_report
preprocessing_plan
execution_log
preprocessing_summary_report
cleaned_dataframe
pipeline_error
```

If a stage fails, the pipeline returns the reports already produced and records the failing stage, exception type, and message in `pipeline_error`.

## 3. Project Modules

| Responsibility | Main implementation |
| --- | --- |
| File loading | `backend/app/ingestion/loader.py` |
| Structure checks | `backend/app/ingestion/structural.py` |
| Raw profiling | `backend/app/profiling/raw_profiler.py` |
| Shared numeric parsing | `backend/app/profiling/parsing.py` |
| Rule generation | `backend/app/preprocessing/raw_rule_engine.py` |
| Preprocessing execution | `backend/app/preprocessing/preprocessor.py` |
| Pipeline orchestration | `backend/app/preprocessing/pipeline.py` |
| Result validation | `backend/app/execution/validator.py` |
| Before-and-after summary | `backend/app/preprocessing/summary.py` |
| Markdown report | `backend/app/reporting/guide.py` |
| Local runner | `backend/run_sample_pipeline.py` |
| Tests | `backend/tests/` |

The active ingestion path uses `raw_profiler.py` and `raw_rule_engine.py`. The older `dataset_profiler.py`, `column_profiler.py`, and `rule_engine.py` modules contain additional or earlier profiling concepts but are not the source of the Parts 1 to 6 report.

## 4. Part 1 - File Ingestion

### 4.1 Input validation

The loader accepts a filesystem path or readable file-like object. Supported formats are `.csv`, `.xlsx`, and `.xls`. Unsupported extensions and unreadable inputs produce a structured ingestion error.

### 4.2 CSV ingestion

For CSV files, the loader:

1. Reads the file bytes once.
2. Detects a UTF-8 byte-order mark when present.
3. Attempts encoding detection with `chardet`.
4. Falls back to `charset-normalizer` when available.
5. Falls back to UTF-8 if no detector is available.
6. Detects comma, semicolon, tab, pipe, or colon delimiters.
7. Chooses the delimiter producing the most consistent row widths.
8. Respects CSV quoting, including values such as `"1,610"`.
9. Detects whether the first row is a header.
10. Loads the data into a Pandas DataFrame.

Encoding, confidence, delimiter, header status, and fallback warnings are recorded.

### 4.3 Excel ingestion

For Excel files:

1. The workbook is loaded through Pandas.
2. The first worksheet is selected.
3. The report records that only the first worksheet was loaded.
4. The worksheet becomes the raw DataFrame.

Excel support requires `openpyxl` for `.xlsx` files and `xlrd` for legacy `.xls` files.

### 4.4 Ingestion report

The ingestion report records file name, file type, encoding, encoding confidence, delimiter, header status, row count, column count, warnings, and errors. A failed load stops the pipeline with a structured error rather than an uncontrolled crash.

## 5. Part 2 - Structure Validation

Structure validation runs before the preprocessing plan is generated.

### 5.1 Fatal checks

The dataset cannot continue when the loaded object is not a DataFrame, the DataFrame has zero columns, or the DataFrame has zero rows.

### 5.2 Duplicate columns

Duplicate column names are detected and made unique internally. The original names remain available in the raw profile. For example:

```text
value, value, city
```

becomes:

```text
value, value_2, city
```

No user data is deleted.

### 5.3 Index-like columns

A likely exported row-index column is detected when its name is blank, `Unnamed: 0`, or `index`, its values are numeric, and its values form a zero-based sequence from `0` to `row_count - 1`.

The column is retained, not silently dropped. The rule engine creates `review_index_column` so the user can decide whether it should be removed later.

### 5.4 Duplicate rows

Duplicate rows are detected during execution and recorded. They are retained by default because automatic deletion could remove legitimate repeated observations.

### 5.5 Structural report

The structural report includes validation status, fatal status, row count, column count, duplicate columns, renamed columns, index-like columns, warnings, and errors.

## 6. Part 3 - Raw Data Profiling

The raw profile is generated from the loaded DataFrame before any cleaning action. Profiling is read-only and does not alter values, dtypes, headers, or row order.

### 6.1 Per-column observations

For every column, the profiler records:

- Column name and raw Pandas dtype.
- Sample values and unique-value count.
- Actual null count and percentage.
- Null-like count and marker breakdown.
- Whitespace count and empty-string count.
- Mixed Python type count and mixed-type status.
- Case-variation status.
- Numeric-like, datetime-like, and Boolean-like percentages.
- Identifier, index-like, categorical, and free-text signals.
- Column warnings.

### 6.2 Dataset-level observations

The profile also records total cells, actual nulls, null-like values, total missing values, missing percentages, columns containing missing values, and high-correlation warnings for numeric columns.

### 6.3 Warning types

The active profiler can report high missingness at 50 percent or more, high cardinality at 90 percent or more unique values, constant or entirely null columns, and high absolute Pearson correlation of at least `0.95`.

These are observations, not automatic deletion instructions.

## 7. Missing-Value and Text Quality Rules

### 7.1 Actual missing values

Actual missing values include `None`, `NaN`, and other values recognized by Pandas as missing.

### 7.2 Null-like text

The following markers are recognized case-insensitively after trimming:

```text
""
"na"
"n/a"
"nan"
"null"
"none"
"missing"
```

### 7.3 Planned missing-value actions

When evidence is present, the rule engine creates `replace_null_like` and `replace_empty_strings`. These actions convert matching text in the internal copy to Pandas missing values. They do not modify the uploaded source file. Actual missing values are not filled or imputed automatically.

### 7.4 Whitespace

Leading and trailing whitespace is measured for string values. Execution strips it from string/object columns. Non-string values are preserved.

## 8. Numeric, Datetime, and Boolean Profiling

### 8.1 Safe numeric parser

`backend/app/profiling/parsing.py` accepts plain integers, decimals, negative values, Western grouped values such as `1,610` and `12,345.67`, and Indian grouped values such as `89,17,000` and `1,15,44,000`.

It rejects inconsistent values such as `1,2,3` instead of guessing their meaning. Currency symbols, units, and percentage symbols are not removed by this parser because those require separate semantic rules.

### 8.2 Numeric profiling

The profiler calculates the percentage of semantic non-null values that can be parsed safely. A high percentage in a string-like column can produce `convert_to_numeric`.

### 8.3 Datetime profiling

String-like values are checked with mixed-format datetime parsing. Numeric and Boolean columns are excluded so ordinary numbers are not misinterpreted as timestamps.

### 8.4 Boolean profiling

Boolean-like values include `true`, `false`, `yes`, `no`, `y`, `n`, `1`, and `0`, checked case-insensitively after trimming.

## 9. Part 4 - Rule-Based Preprocessing Plan

The rule engine receives the raw DataFrame and raw profile. It produces a `PreprocessingPlan` without modifying data.

Each action contains target columns, an action name, confidence from `0.0` to `1.0`, a reason, and optional parameters.

### 9.1 Active actions

| Action | Purpose | Default behavior |
| --- | --- | --- |
| `strip_whitespace` | Remove outer whitespace | Execute internally |
| `replace_null_like` | Convert known missing markers | Execute internally |
| `replace_empty_strings` | Convert empty strings | Execute internally |
| `convert_to_numeric` | Convert high-confidence numeric strings | Execute only when safe |
| `convert_to_datetime` | Convert high-confidence datetime strings | Execute only when safe |
| `convert_to_boolean` | Convert high-confidence Boolean strings | Execute only when safe |
| `classify_as_categorical` | Identify low-cardinality data | May trigger case normalization |
| `normalize_case` | Normalize confirmed categorical text | Execute for confirmed categorical data |
| `preserve_identifier` | Protect likely IDs | Skip transformation |
| `preserve_free_text` | Protect high-cardinality text | Skip transformation |
| `review_index_column` | Flag exported index columns | Skip; manual review required |

### 9.2 Confidence policy

Conversion confidence must be at least `0.80`. Lower-confidence conversions are skipped and logged for review. Categorical normalization also requires confidence of at least `0.80`.

### 9.3 Identifier and free-text protection

High-cardinality columns with names containing signals such as `id`, `uuid`, `identifier`, or `code` can be preserved as identifiers. High-cardinality variable-length strings can be preserved as free text because automatic conversion or normalization could destroy meaning.

## 10. Part 5 - Safe Internal Preprocessing

The executor creates `df.copy(deep=True)` before applying any transformation. The source DataFrame and uploaded file remain unchanged.

### 10.1 Fixed execution order

1. Apply planned null-like replacement.
2. Apply planned empty-string replacement.
3. Strip leading and trailing whitespace from all string/object columns.
4. Detect duplicate columns and retain them for review.
5. Detect duplicate rows and retain them for review.
6. Apply high-confidence numeric, datetime, and Boolean conversions.
7. Apply case normalization for confirmed categorical columns.
8. Record preservation and review-only actions as skipped.
9. Return the cleaned internal DataFrame and execution log.

### 10.2 Conversion protection

Before accepting a numeric, datetime, or Boolean conversion, the executor compares null percentage before and after, counts non-null values that became missing, and checks the configured data-loss threshold.

If any non-null value becomes missing, or loss exceeds the threshold, the original column is restored and the action receives status `rejected`. This prevents invalid values such as `bad` from silently becoming `NaN`.

Grouped numeric values such as `"1,610"` are parsed through the shared parser and become `1610`, not missing.

### 10.3 Review-only actions

`review_index_column`, `preserve_identifier`, `preserve_free_text`, and actions beginning with `review_` are recorded but not automatically applied.

### 10.4 Execution log

Each entry records columns, action, status, reason, confidence when relevant, values changed when relevant, duplicate counts when relevant, null percentages before and after conversion, data-loss percentage, and invalid non-null count.

Possible statuses are `executed`, `skipped`, and `rejected`.

## 11. Part 6 - Post-Processing Validation

After execution, `Validator.compare` checks the raw and cleaned DataFrames.

The validation requires the same row count, the same column names and order, and a non-empty cleaned DataFrame. Values and dtypes may change, but preprocessing cannot silently add or remove rows or columns. A failure is returned as a structured `preprocessing_validation` error.

## 12. Part 7 - Before-and-After Summary

The cleaned internal copy is profiled again. The summary compares raw and cleaned profiles positionally and reports raw and cleaned row counts, column counts, changed-column count, execution-log count, column-level actions, before-and-after dtypes, null percentages, unique counts, and null summaries.

The changed-column count includes columns with a profile difference or a related execution action. It is not limited to columns whose displayed values visibly changed.

## 13. Generated Markdown Report

`backend/app/reporting/guide.py` converts the structured result into Markdown without rerunning the pipeline or modifying data.

The report contains:

1. File ingestion metadata.
2. Structure validation results.
3. Index-like column warnings.
4. Raw profile metrics.
5. Missing-value and null-like summaries.
6. Per-column profile table.
7. Rule-based preprocessing plan.
8. Internal execution log.
9. Raw-versus-cleaned summary.
10. Planned future EDA steps.

## 14. Running a New Dataset

Edit `CSV_PATH` in `backend/run_sample_pipeline.py`, then run:

```powershell
cd backend
python run_sample_pipeline.py
```

The runner checks the path, calls the pipeline, prints stage output, saves `<input-name>_processed.csv`, saves `<input-name>_eda_report.md`, and prints a cleaned-data preview. The original file is not overwritten.

## 15. Europe Dataset Example

For `europe.csv`, the pipeline identifies the blank-header first column as an exported index and creates a review action. It recognizes grouped numeric values in the source data.

The value:

```text
population_per_sq_km = "1,610"
```

is safely converted to:

```text
population_per_sq_km = 1610.0
```

No conversion-created null is introduced. The index-like column is retained because dropping it automatically could be destructive; the report tells the user to review it.

## 16. Testing

Run the backend tests from the backend directory:

```powershell
cd backend
python -m pytest -q
```

The tests cover CSV and Excel loading, delimiter behavior, duplicate columns, invalid structures, raw profiling, null-like and empty-string rules, grouped numeric parsing, malformed numeric values, exported index detection, whitespace cleanup, Boolean and categorical handling, duplicate-row reporting, lossy conversion rejection, row and column preservation, pipeline result structure, and Markdown report generation.

The Excel test requires the dependencies in `backend/requirements.txt`. If `openpyxl` is unavailable, CSV and preprocessing tests can still run, but Excel test setup will fail.

## 17. Dependencies

Dependencies are listed in `backend/requirements.txt`.

Important packages include Pandas, `chardet`, `charset-normalizer`, `openpyxl`, `xlrd`, Pydantic, Pytest, NumPy, scikit-learn, and Plotly.

## 18. Current Status and Boundaries

### Implemented and connected

- CSV and Excel ingestion.
- Encoding, delimiter, and header detection.
- Empty-data validation.
- Duplicate-column detection and internal renaming.
- Exported-index detection.
- Duplicate-row detection.
- Raw null, null-like, whitespace, empty-string, mixed-type, case, numeric, datetime, and Boolean profiling.
- Grouped-number parsing.
- Rule-based preprocessing planning.
- Safe internal transformations.
- Lossless conversion protection.
- Post-processing structural validation.
- Before-and-after summary.
- Markdown report generation.
- Processed CSV output.

### Not yet fully connected to the main pipeline

- Full descriptive-statistics report.
- Automatic visualization recommendations.
- Evidence-based insight synthesis.
- Complete API upload-to-report workflow.
- Complete frontend dashboard workflow.
- Final combined report with charts and insights.

Review-only behavior is intentional. Index removal, duplicate-row removal, outlier removal, imputation, currency conversion, percentage conversion, and free-text transformations should become explicit evidence-backed actions before being made automatic.

## 19. Future End-to-End Flow

```text
Upload dataset
    |
    v
Ingest and validate
    |
    v
Profile raw data
    |
    v
Generate preprocessing plan
    |
    v
Execute safe internal actions
    |
    v
Validate and summarize changes
    |
    v
Generate descriptive statistics
    |
    v
Recommend visualizations
    |
    v
Generate evidence-based insights
    |
    v
Present final report and dashboard
```
