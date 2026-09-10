# EDA-Guider Report

Dataset: **03_Calfus_Candidate_Delivery_Data.csv**
Pipeline status: **Completed**

## How to use this report

Follow the completed sections from top to bottom. Each section explains what EDA-Guider checked, what it found, and what the user should know before continuing the analysis.

## Part 1 - File ingestion

The file was loaded without changing the original file.

- File type: csv
- Encoding: ascii
- Delimiter: ,
- Header detected: True
- Rows: 23153
- Columns: 12

## Part 2 - Structure validation

The dataset structure was checked before analysis.

- Validation status: success
- Duplicate columns: None
- Warnings: None
- Errors: None

## Part 3 - Raw data profile

This section describes the original values before preprocessing.

- Rows profiled: 23153
- Columns profiled: 12
- Profile warnings: 1

### Missing-value report

- Total cells: 277836
- Actual null values: 0 (0.0%)
- Null-like text values: 6204 (2.233%)
- Total missing values: 6204 (2.233%)
- Columns with actual nulls: None
- Columns with null-like values: order_date, zone, driver_id, vehicle_type, distance_km, package_weight_kg, promised_delivery_hours, actual_delivery_hours, delivery_status, customer_rating, weather_condition

Null and null-like values are reported, not automatically filled or replaced. They do not prevent later visualization or insight analysis.

### Column profile

| Column | Type | Nulls | Null-like values | Unique values |
| --- | --- | ---: | ---: | ---: |
| delivery_id | str | 0 (0.0%) | 0 | 23128 |
| order_date | str | 0 (0.0%) | 463 | 1462 |
| zone | str | 0 (0.0%) | 463 | 21 |
| driver_id | str | 0 (0.0%) | 465 | 26 |
| vehicle_type | str | 0 (0.0%) | 465 | 13 |
| distance_km | str | 0 (0.0%) | 464 | 342 |
| package_weight_kg | str | 0 (0.0%) | 464 | 247 |
| promised_delivery_hours | str | 0 (0.0%) | 465 | 197 |
| actual_delivery_hours | str | 0 (0.0%) | 464 | 418 |
| delivery_status | str | 0 (0.0%) | 463 | 4 |
| customer_rating | str | 0 (0.0%) | 1563 | 6 |
| weather_condition | str | 0 (0.0%) | 465 | 13 |

## Part 4 - Preprocessing plan

The rule engine created actions from the raw profile. These actions are recommendations for safe internal preparation, not changes to the original file.

| Columns | Action | Confidence | Reason |
| --- | --- | ---: | --- |
| delivery_id | preserve_identifier | 99.89% | The column has 23128 unique values across 23153 rows and is likely an identifier; preserve it as an identifier. |
| order_date | convert_to_datetime | 98.0% | 98.0% of non-null values parse as datetimes while the raw dtype is string-like. |
| order_date | classify_as_categorical | 93.69% | Only 1462 unique values occur across 23153 rows, indicating low cardinality. |
| zone | strip_whitespace | 0.23% | Detected leading or trailing whitespace in 53 value(s). |
| zone | classify_as_categorical | 99.91% | Only 21 unique values occur across 23153 rows, indicating low cardinality. |
| driver_id | classify_as_categorical | 99.89% | Only 26 unique values occur across 23153 rows, indicating low cardinality. |
| vehicle_type | strip_whitespace | 0.25% | Detected leading or trailing whitespace in 57 value(s). |
| vehicle_type | classify_as_categorical | 99.94% | Only 13 unique values occur across 23153 rows, indicating low cardinality. |
| distance_km | convert_to_numeric | 97.82% | 97.8% of non-null values match a numeric pattern while the raw dtype is string-like. |
| distance_km | classify_as_categorical | 98.52% | Only 342 unique values occur across 23153 rows, indicating low cardinality. |
| package_weight_kg | convert_to_numeric | 98.0% | 98.0% of non-null values match a numeric pattern while the raw dtype is string-like. |
| package_weight_kg | classify_as_categorical | 98.93% | Only 247 unique values occur across 23153 rows, indicating low cardinality. |
| promised_delivery_hours | convert_to_numeric | 97.99% | 98.0% of non-null values match a numeric pattern while the raw dtype is string-like. |
| promised_delivery_hours | classify_as_categorical | 99.15% | Only 197 unique values occur across 23153 rows, indicating low cardinality. |
| actual_delivery_hours | convert_to_numeric | 98.0% | 98.0% of non-null values match a numeric pattern while the raw dtype is string-like. |
| actual_delivery_hours | classify_as_categorical | 98.19% | Only 418 unique values occur across 23153 rows, indicating low cardinality. |
| delivery_status | classify_as_categorical | 99.98% | Only 4 unique values occur across 23153 rows, indicating low cardinality. |
| customer_rating | convert_to_numeric | 93.25% | 93.2% of non-null values match a numeric pattern while the raw dtype is string-like. |
| customer_rating | classify_as_categorical | 99.97% | Only 6 unique values occur across 23153 rows, indicating low cardinality. |
| weather_condition | strip_whitespace | 0.19% | Detected leading or trailing whitespace in 43 value(s). |
| weather_condition | classify_as_categorical | 99.94% | Only 13 unique values occur across 23153 rows, indicating low cardinality. |

## Part 5 - Internal execution

The planned safe actions were applied only to an internal copy. The uploaded source file was not modified.

- Execution log entries: 32

| Columns | Action | Status | Reason |
| --- | --- | --- | --- |
| delivery_id | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| order_date | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| zone | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| driver_id | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| vehicle_type | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| distance_km | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| package_weight_kg | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| promised_delivery_hours | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| actual_delivery_hours | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| delivery_status | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| customer_rating | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| weather_condition | strip_whitespace | executed | Stripped leading and trailing whitespace from string values. |
| None | detect_duplicate_columns | skipped | No duplicate columns detected. |
| None | detect_duplicate_rows | executed | Duplicate rows detected and retained for review; no rows were removed. |
| order_date | convert_to_datetime | executed | High-confidence conversion applied within the data-loss threshold. |
| distance_km | convert_to_numeric | executed | High-confidence conversion applied within the data-loss threshold. |
| package_weight_kg | convert_to_numeric | executed | High-confidence conversion applied within the data-loss threshold. |
| promised_delivery_hours | convert_to_numeric | executed | High-confidence conversion applied within the data-loss threshold. |
| actual_delivery_hours | convert_to_numeric | executed | High-confidence conversion applied within the data-loss threshold. |
| customer_rating | convert_to_numeric | executed | High-confidence conversion applied within the data-loss threshold. |
| order_date | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| zone | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| driver_id | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| vehicle_type | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| distance_km | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| package_weight_kg | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| promised_delivery_hours | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| actual_delivery_hours | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| delivery_status | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| customer_rating | normalize_case | skipped | Case normalization applies only to string-like categorical columns. |
| weather_condition | normalize_case | executed | Applied lower case normalization to a confirmed categorical column. |
| delivery_id | preserve_identifier | skipped | Preservation decision recorded; no transformation was required. |

## Part 6 - Before-and-after summary

The cleaned internal copy was profiled again and compared with the raw profile.

- Raw shape: 23153 rows x 12 columns
- Cleaned shape: 23153 rows x 12 columns
- Changed columns: 12

## Part 7 - Next EDA steps

This stage is planned for the next version. It will use the prepared internal data and the evidence above to provide:

1. Statistical analysis
2. Visualization recommendations
3. Evidence-based insights

Until Part 7 is implemented, use this report to review data quality, understand preprocessing decisions, and decide what analysis should be performed next.
