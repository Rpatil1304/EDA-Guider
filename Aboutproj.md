# EDA-Guider Project Guide

## 1. Project Purpose

EDA-Guider is an exploratory data analysis assistant for CSV and Excel datasets.

The project is designed to guide the user through the early EDA workflow:

1. Load the dataset safely.
2. Validate its structure.
3. Understand the raw data.
4. Identify possible preprocessing actions.
5. Apply safe actions to an internal copy.
6. Explain what changed.
7. Prepare the dataset for future statistics, visualizations, and insights.

The original uploaded file is never modified.

## 2. Overall Execution Flow

```text
Input CSV or Excel file
        |
        v
Part 1: File ingestion
        |
        v
Part 2: Structure validation
        |
        v
Part 3: Raw data profiling
        |
        v
Part 4: Preprocessing plan
        |
        v
Part 5: Internal preprocessing execution
        |
        v
Part 6: Before-and-after summary
        |
        v
Part 7: Future statistical, visualization, and insight analysis
```

The current implemented pipeline runs through Parts 1 to 6. Part 7 is represented in the report as the next planned stage.

## 3. Part 1 - File Ingestion

The process begins when the user provides a CSV or Excel file.

### CSV ingestion

For CSV files, the system:

- Reads the file safely.
- Detects the file encoding.
- Detects the delimiter, such as comma, semicolon, tab, or pipe.
- Detects whether the first row is a header.
- Loads the data into a Pandas DataFrame.
- Preserves the original file.

### Excel ingestion

For Excel files, the system:

- Reads the workbook.
- Loads the first worksheet.
- Records that only the first worksheet was used.
- Loads the worksheet into a Pandas DataFrame.

### Ingestion result

The ingestion report records information such as:

- File name
- File type
- Encoding
- Encoding confidence
- Delimiter
- Header status
- Row count
- Column count
- Warnings
- Errors

If the file cannot be loaded, the pipeline stops and returns a structured error instead of crashing.

## 4. Part 2 - Structure Validation

After loading the file, the dataset structure is checked before detailed analysis begins.

The system checks:

- Whether the DataFrame is empty.
- Whether the dataset contains columns.
- Whether the dataset has a usable structure.
- Whether duplicate column names exist.
- Whether structural warnings or errors should be reported.

Duplicate column names are preserved in the raw profile but are made unique internally. For example:

```text
value, value, city
```

can become:

```text
value, value_2, city
```

The structural report contains:

- Validation status
- Row count
- Column count
- Duplicate columns
- Warnings
- Errors
- Fatal status when the dataset cannot continue

## 5. Part 3 - Raw Data Profiling

The raw profile is created before any preprocessing is applied.

This is important because it gives the user an honest description of the original dataset.

For every column, the profiler records:

- Column name
- Original data type
- Number of unique values
- Sample values
- Actual null count
- Actual null percentage
- Null-like text count
- Breakdown of null-like markers
- Empty-string count
- Whitespace count
- Numeric-like percentage
- Datetime-like percentage
- Boolean-like percentage
- Whether the column may be an identifier
- Whether the column may be categorical
- Whether the column may contain free text
- Quality warnings

The raw profile does not modify the DataFrame.

### Raw data warnings

The profiler can identify warnings such as:

- High missingness
- High cardinality
- Constant or entirely null columns
- Strong correlation between numeric columns

## 6. Null and Missing-Value Policy

A major project decision was made for null values:

> Null values should be explained to the user instead of automatically being solved.

Nulls do not automatically block visualization or insight generation.

The system separates missing values into different categories:

### Actual null values

These are values recognized by Pandas as missing, such as `None` or `NaN`.

### Null-like text values

These are text values that commonly represent missing data, such as:

- Empty strings
- `NA`
- `N/A`
- `nan`
- `null`
- `none`
- `missing`

### Null report

The dataset-level null summary contains:

- Total number of cells
- Actual null count
- Actual null percentage
- Null-like value count
- Null-like percentage
- Total missing count
- Total missing percentage
- Columns containing actual nulls
- Columns containing null-like values

Each column also contains its own null count, percentage, and null-like breakdown.

Null and null-like values are reported but are not automatically filled, removed, or replaced.

## 7. Part 4 - Preprocessing Plan

The rule engine uses the raw profile to create a preprocessing plan.

The plan does not immediately change the dataset. It describes possible actions based on evidence found during profiling.

Possible plan actions include:

- Strip leading and trailing whitespace.
- Convert numeric-looking strings to numeric values.
- Convert datetime-looking strings to datetime values.
- Convert boolean-like values to Boolean values.
- Classify low-cardinality columns as categorical.
- Preserve likely identifier columns.
- Preserve likely free-text columns.
- Record duplicate rows and duplicate columns for review.

Each plan action contains:

- Target column or columns
- Action name
- Confidence score
- Reason for the action
- Optional parameters

### Null-related change

The preprocessing plan no longer creates actions such as:

```text
replace_null_like
replace_empty_strings
```

Null and null-like values remain available for reporting and later analysis decisions.

## 8. Part 5 - Internal Preprocessing Execution

The system creates a deep copy of the input DataFrame before applying safe preprocessing actions.

The original DataFrame and original uploaded file remain unchanged.

The executor can apply high-confidence transformations such as:

- Whitespace cleanup
- Numeric conversion
- Datetime conversion
- Boolean conversion
- Case normalization for confirmed categorical columns

Conversions are protected by a data-loss threshold. If a conversion would create too many missing values, it is rejected and the original values are restored.

The executor also reports duplicate rows and duplicate columns without removing them automatically.

Every action is recorded in an execution log with:

- Columns affected
- Action name
- Status
- Reason
- Confidence when applicable
- Values changed when applicable
- Null percentage before and after conversions
- Data-loss information when applicable

Possible statuses include:

- `executed`
- `skipped`
- `rejected`

Null-like text values such as `NA` and empty strings are preserved.

## 9. Part 6 - Before-and-After Summary

After internal preprocessing, the cleaned DataFrame is profiled again.

The summary compares:

```text
Raw profile
versus
Cleaned profile
```

The summary reports:

- Raw row count
- Cleaned row count
- Raw column count
- Cleaned column count
- Changed column count
- Execution log count
- Column-level changes
- Actions related to each column
- Before-and-after data types
- Before-and-after null percentages
- Before-and-after unique counts
- Original null summary

This gives the user a clear explanation of what the system did internally.

The cleaned DataFrame is used internally and can also be saved as a processed CSV by the sample runner.

## 10. Part 7 - Planned Future EDA Analysis

Part 7 is the next major stage of the project.

The current report documents Part 7 as planned work. It will later use the prepared internal data and evidence collected in Parts 1 to 6.

Planned Part 7 capabilities are:

1. Statistical profiling.
2. Descriptive statistics.
3. Distribution analysis.
4. Outlier analysis.
5. Correlation analysis.
6. Rule-based visualization recommendations.
7. Evidence-based insight generation.
8. A final report combining statistics, charts, and insights.

The project already contains early modules and schemas for visualization and insight handling, but these stages are not yet fully connected to the main preprocessing pipeline.

## 11. Standalone User Report

The pipeline now generates a separate Markdown report for the user.

When the sample runner is executed:

```powershell
cd backend
python run_sample_pipeline.py
```

it creates a report beside the input dataset:

```text
03_Calfus_Candidate_Delivery_Data_eda_report.md
```

The report contains:

- Dataset name and pipeline status
- Part 1 ingestion details
- Part 2 structure validation details
- Part 3 raw profile details
- Detailed null and null-like value information
- Per-column profile table
- Part 4 preprocessing plan
- Part 5 execution log
- Part 6 before-and-after summary
- Part 7 future EDA steps

The report is intended to be read from top to bottom as a user guide for the EDA process.

## 12. Report Generation Design

The report is generated from the structured result returned by the preprocessing pipeline.

The report generator:

- Reads the pipeline result.
- Does not run the pipeline again.
- Does not modify the dataset.
- Converts technical pipeline data into readable Markdown.
- Can return the report as a string.
- Can save the report to a chosen output path.

The report generator is located at:

```text
backend/app/reporting/guide.py
```

Its public function is:

```python
generate_eda_guide_report(result, output_path)
```

## 13. Sample Pipeline

The sample runner is located at:

```text
backend/run_sample_pipeline.py
```

It currently:

1. Reads the configured CSV path.
2. Runs the preprocessing pipeline.
3. Prints pipeline status.
4. Prints ingestion and structure details.
5. Prints the raw profile.
6. Prints the null summary.
7. Prints the preprocessing plan.
8. Prints the execution log.
9. Prints the preprocessing summary.
10. Saves the processed CSV.
11. Saves the standalone Markdown EDA report.
12. Prints a cleaned-data preview.

The original CSV is not overwritten.

## 14. Testing and Fixes

The project has a backend test suite covering:

- Agent behavior
- Execution behavior
- File ingestion
- Raw profiling
- Pipeline behavior
- Preprocessing rules
- Summary generation
- Visualization module behavior

A pytest collection error was found in `tests/test_profiling.py`.

The problem was that a demonstration output block was placed outside the following guard:

```python
if __name__ == "__main__":
```

As a result, pytest executed the block while importing the test module. The variable `result` did not exist at import time, causing:

```text
NameError: name 'result' is not defined
```

The output block was moved inside the main guard so the file can be imported safely by pytest.

An existing execution test also expected the old behavior where `NA` was converted to a null value. Since the new policy preserves null-like values, the test was updated to expect `NA` to remain unchanged.

The Excel test required the `openpyxl` package. The dependency was installed in the project virtual environment.

The final test result was:

```text
22 passed
```

## 15. Dependencies and Environment

The backend dependencies are listed in:

```text
backend/requirements.txt
```

Important packages include:

- Pandas for data handling
- FastAPI for the future API layer
- Pydantic for structured schemas
- OpenPyXL for Excel files
- Pytest for testing
- NumPy and scikit-learn for future analysis support

The project is tested with Python 3.12 and a virtual environment.

Recommended test command:

```powershell
cd backend
..\venv\Scripts\python.exe -m pytest
```

## 16. Current Project Status

### Completed

- CSV ingestion
- Excel ingestion
- Encoding detection
- Delimiter detection
- Header detection
- Structure validation
- Duplicate column handling
- Raw profiling
- Null and null-like reporting
- Rule-based preprocessing planning
- Safe internal preprocessing
- Data-loss protection for conversions
- Before-and-after preprocessing summary
- Standalone Markdown report generation
- Sample pipeline output
- Automated tests

### Not yet fully connected

- End-to-end statistical analysis in the main pipeline
- End-to-end visualization recommendation flow
- End-to-end insight generation flow
- Complete FastAPI upload and analysis workflow
- Complete frontend dashboard integration
- Final combined report containing charts and insights

## 17. Future End-to-End Flow

The planned final flow is:

```text
User uploads dataset
        |
        v
Ingestion and validation
        |
        v
Raw data profile
        |
        v
Preprocessing plan
        |
        v
Safe internal preprocessing
        |
        v
Preprocessing summary
        |
        v
Statistical profiling
        |
        v
Visualization recommendations
        |
        v
Evidence-based insights
        |
        v
Final EDA report and dashboard
```

The current standalone report completes the first part of this journey and provides a clear foundation for the future visualization and insight stages.
