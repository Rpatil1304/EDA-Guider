"""Test script for clean query executor."""

import sys
sys.path.append("backend")

import pandas as pd
from app.clean_query.metadata_extractor import extract_dataset_metadata
from app.clean_query.executor import execute_with_self_correction, validate_code_ast, CodeSecurityError

df = pd.read_csv("Datasets/Raw/europe.csv")
meta = extract_dataset_metadata(df)

# Test 1: Simple calculation
res1 = execute_with_self_correction("output_result = df['birth_rate'].mean()", df, "mean birth rate", meta)
print("Test 1 (Calc):", res1["status"], "Result:", res1["result_data"])

# Test 2: Chart creation
chart_code = """import plotly.express as px
fig = px.histogram(df, x='birth_rate', title='Birth Rate Distribution')
"""
res2 = execute_with_self_correction(chart_code, df, "histogram of birth rate", meta)
print("Test 2 (Chart):", res2["status"], "Has Fig:", res2["has_figure"])

# Test 3: Security check
try:
    validate_code_ast("import os\nos.system('ls')")
    print("Test 3 (Security): FAILED to block")
except CodeSecurityError as e:
    print("Test 3 (Security): PASSED blocking ->", e)

# Test 4: Deliberate error with self-correction (calling non-existent column 'birthrate')
bad_code = "output_result = df['birthrate'].mean()"
res4 = execute_with_self_correction(bad_code, df, "mean birth rate", meta)
print("Test 4 (Self-Healing):", res4["status"], "Attempts:", res4["attempts_count"])
print("Fixed Code:", res4["final_code"])
print("Fixed Result:", res4["result_data"])
