# EDA-Guider Report

Dataset: **europe.csv**
Pipeline status: **Completed**

## How to use this report

Follow the completed sections from top to bottom. Each section explains what EDA-Guider checked, what it found, and what the user should know before continuing the analysis.

## Part 1 - File ingestion

The file was loaded without changing the original file.

- File type: csv
- Encoding: utf_8
- Delimiter: ,
- Header detected: True
- Rows: 36
- Columns: 11

## Part 2 - Structure validation

The dataset structure was checked before analysis.

- Validation status: success
- Duplicate columns: None
- Warnings: Index-like columns were detected and retained for review: 
- Errors: None
- Index-like columns retained for review: <blank>

## Part 3 - Raw data profile

This section describes the original values before preprocessing.

- Rows profiled: 36
- Columns profiled: 11
- Profile warnings: 8

### Missing-value report

- Total cells: 396
- Actual null values: 0 (0.0%)
- Null-like text values: 0 (0.0%)
- Total missing values: 0 (0.0%)
- Columns with actual nulls: None
- Columns with null-like values: None

Raw null and null-like values are reported first. Where the rule engine detects them, the internal copy may replace them while preserving the uploaded source file.

### Column profile

| Column | Type | Nulls | Null-like values | Unique values |
| --- | --- | ---: | ---: | ---: |
|  | int64 | 0 (0.0%) | 0 | 36 |
| country_name | str | 0 (0.0%) | 0 | 36 |
| Continent | str | 0 (0.0%) | 0 | 1 |
| region | str | 0 (0.0%) | 0 | 4 |
| area | str | 0 (0.0%) | 0 | 36 |
| population | str | 0 (0.0%) | 0 | 36 |
| population_per_sq_km | str | 0 (0.0%) | 0 | 36 |
| male_life_expectancy | float64 | 0 (0.0%) | 0 | 33 |
| female_life_expectancy | float64 | 0 (0.0%) | 0 | 30 |
| birth_rate | float64 | 0 (0.0%) | 0 | 25 |
| death_rate | float64 | 0 (0.0%) | 0 | 34 |

## Part 4 - Preprocessing plan

The rule engine created actions from the raw profile. These actions are recommendations for safe internal preparation, not changes to the original file.

| Columns | Action | Confidence | Reason |
| --- | --- | ---: | --- |
| <blank> | review_index_column | 100.0% | The column looks like an exported row index; review whether it should be removed. |
| country_name | preserve_free_text | 100.0% | The column has high cardinality and variable-length string values, so it is likely free text. |
| region | classify_as_categorical | 88.89% | Only 4 unique values occur across 36 rows, indicating low cardinality. |
| area | preserve_free_text | 100.0% | The column has high cardinality and variable-length string values, so it is likely free text. |
| population | convert_to_numeric | 100.0% | 100.0% of non-null values match a numeric pattern while the raw dtype is string-like. |
| population | preserve_free_text | 100.0% | The column has high cardinality and variable-length string values, so it is likely free text. |
| population_per_sq_km | convert_to_numeric | 100.0% | 100.0% of non-null values match a numeric pattern while the raw dtype is string-like. |

## Part 5 - Internal execution

The planned safe actions were applied only to an internal copy. The uploaded source file was not modified.

- Execution log entries: 15

| Columns | Action | Status | Reason |
| --- | --- | --- | --- |
| country_name | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| Continent | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| region | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| area | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| population | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| population_per_sq_km | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| None | detect_duplicate_columns | skipped | No duplicate columns detected. |
| None | detect_duplicate_rows | skipped | No duplicate rows detected. |
| population | convert_to_numeric | executed | High-confidence lossless conversion applied. |
| population_per_sq_km | convert_to_numeric | executed | High-confidence lossless conversion applied. |
| region | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| <blank> | review_index_column | skipped | Action requires manual review and was not applied. |
| country_name | preserve_free_text | skipped | Preservation decision recorded; no transformation was required. |
| area | preserve_free_text | skipped | Preservation decision recorded; no transformation was required. |
| population | preserve_free_text | skipped | Preservation decision recorded; no transformation was required. |

## Part 6 - Before-and-after summary

The cleaned internal copy was profiled again and compared with the raw profile.

- Raw shape: 36 rows x 11 columns
- Cleaned shape: 36 rows x 11 columns
- Changed columns: 7
- Cleaned missing values: 0

## Part 7 - Next EDA steps

This stage is planned for the next version. It will use the prepared internal data and the evidence above to provide:

1. Statistical analysis
2. Visualization recommendations
3. Evidence-based insights

Until Part 7 is implemented, use this report to review data quality, understand preprocessing decisions, and decide what analysis should be performed next.
