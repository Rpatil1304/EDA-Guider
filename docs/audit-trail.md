# Audit Trail

## Overview

The audit trail system tracks all decisions, transformations, and operations performed on the data throughout the EDA pipeline.

## What is Logged

### Data Ingestion
- File name and format
- Number of rows and columns
- Data types detected
- Initial data quality metrics

### Profiling
- Data type inferences
- Missing value analysis
- Statistical summaries
- Outlier detection results
- Duplicate detection results

### Rule Engine Decisions
- Rules evaluated
- Decisions made
- Parameters applied
- Rationale for decisions

### Agent Decisions
- Prompt used
- LLM response
- Parsed decisions
- Confidence scores
- Alternative recommendations

### Execution
- Transformations applied
- Before/after statistics
- Validation results
- Any errors or warnings

### Visualization
- Charts generated
- Chart specifications
- Data slices used
- Rendering status

## Audit Log Format

Each log entry contains:
- Timestamp
- Component/Module
- Operation type
- Details (JSON)
- Status (success/failure)
- User/Session ID

## Access and Review

Audit logs can be:
- Reviewed in the Decision Audit UI
- Exported as CSV/JSON
- Searched and filtered by date, component, or operation
- Used for compliance and reproducibility
