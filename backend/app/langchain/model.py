"""Hugging Face + LangChain visualization selection workflow."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableParallel

from langchain_google_genai import ChatGoogleGenerativeAI

from app.langchain.schemas import (
    LLMVisualizationValidationResponse,
)

from app.langchain.report_schemas import (
    FinalEDAReport,
)

load_dotenv()


# ================================================================
# Model
# ================================================================

def get_google_model() -> ChatGoogleGenerativeAI:
    """Create and return the Google Gemini chat model."""

    google_api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable "
            "is not set."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=google_api_key,
        temperature=0.0,
        max_output_tokens=4096,
    )

# ================================================================
# Parser
# ================================================================

def get_visualization_output_parser() -> PydanticOutputParser:
    """Create the Pydantic output parser."""

    return PydanticOutputParser(
        pydantic_object=LLMVisualizationValidationResponse
    )

def get_final_report_output_parser() -> PydanticOutputParser:
    """Create the Pydantic parser for the final EDA report."""

    return PydanticOutputParser(
        pydantic_object=FinalEDAReport
    )

# ================================================================
# Chart Type Normalization
# ================================================================

def _normalize_chart_type(
    chart_type: str | None,
) -> str | None:
    """
    Convert deterministic rule-engine chart names into the
    standardized chart names expected by the LLM schema.
    """

    if not chart_type:
        return None

    chart_type_mapping = {
        "pie_donut_chart": "pie_chart",
        "correlation_heatmap": "heatmap",
    }

    return chart_type_mapping.get(
        chart_type,
        chart_type,
    )


# ================================================================
# Prompt
# ================================================================

def get_visualization_prompt():

    parser = get_visualization_output_parser()

    system_message = """
You are an expert Exploratory Data Analysis assistant.

Your task is to REVIEW and SELECT the most useful visualization
recommendations produced by a deterministic rule-based EDA engine.

The deterministic rule engine generates visualization CANDIDATES.
It does NOT decide which visualizations should appear in the final
EDA report.

Your responsibility is to select a SMALL, USEFUL, COMPLEMENTARY and
NON-REDUNDANT set of visualizations for the final report.

You are a recommendation and decision-support system.

---------------------------------------------------------------
WHAT YOU MUST NOT DO
---------------------------------------------------------------

You MUST NOT:

- generate or render charts
- execute Python code
- modify the dataset
- perform preprocessing
- invent dataset values
- invent columns
- invent statistics
- recommend columns not present in the evidence
- calculate statistics that are not provided
- reproduce the complete rule-engine candidate list
- select visualizations merely because the rule engine generated them
- create new visualization types
- create new visualization candidates

The supplied evidence is the only source of truth.

---------------------------------------------------------------
PRIMARY OBJECTIVE
---------------------------------------------------------------

The rule engine answers:

"What visualizations are possible?"

You must answer:

"Which of those visualizations are actually useful for the
final EDA report?"

Therefore:

DO NOT select every technically valid candidate.

Select only visualizations that provide meaningful analytical value.

The final visualization set must:

- provide broad analytical coverage
- contain different analytical purposes
- be complementary
- avoid repetition
- avoid unnecessary charts
- be understandable to a human analyst
- be supported by the supplied evidence

The goal is NOT to maximize the number of charts.

The goal is to communicate the most important visual insights
with the FEWEST useful visualizations.

---------------------------------------------------------------
FINAL SELECTION SIZE
---------------------------------------------------------------

Normally select approximately 4 to 7 visualizations.

Prefer fewer visualizations when they are sufficient.

Do NOT add visualizations simply to reach 4.

Do NOT exceed 7 visualizations unless the dataset evidence
clearly requires additional visual coverage.

A small dataset may need only 3 or 4 visualizations.

A complex dataset may justify up to 7.

Every selected visualization must have a clear analytical purpose.

---------------------------------------------------------------
NON-REDUNDANCY PRINCIPLE
---------------------------------------------------------------

Before selecting a visualization, ask:

"Does this visualization communicate something meaningfully
different from the visualizations I have already selected?"

If NO:

DO NOT select it.

Avoid multiple charts that communicate essentially the same message.

The final set should not contain several visualizations explaining
the same variable or relationship unless they provide clearly
different analytical information.

---------------------------------------------------------------
1. NUMERIC DISTRIBUTIONS
---------------------------------------------------------------

Histogram:
Useful for distribution shape, concentration, skewness and spread.

Box plot:
Useful for median, quartiles, spread and potential outliers.

Violin plot:
Useful for distribution density when it provides additional
information beyond the selected distribution chart.

QQ plot:
Useful only when distributional/normality information is
meaningfully relevant.

IMPORTANT:

Do NOT select histogram, box plot, violin plot and QQ plot
for the same numeric variable.

For a numeric variable, normally select ONE distribution
visualization.

Select a second distribution visualization only when it provides
clearly different analytical information.

Prefer numeric variables with:

- meaningful skewness
- meaningful outliers
- unusual distributions
- important analytical relevance
- sufficient statistical evidence

If several numeric variables have similar distributions,
select only the most informative ones.

Do NOT create a separate distribution chart for every numeric column.

---------------------------------------------------------------
2. CATEGORICAL DISTRIBUTIONS
---------------------------------------------------------------

Bar charts are useful for categorical frequency distributions.

Pie charts can be useful for small-cardinality categorical
variables when proportions are meaningful.

IMPORTANT:

Do NOT select both a bar chart and pie chart for the same
categorical variable unless there is a very clear analytical
reason.

Normally select only the most informative categorical variables.

Do NOT create a separate categorical chart for every categorical
column.

Prefer categories with:

- meaningful frequency differences
- low or moderate cardinality
- analytical importance

---------------------------------------------------------------
3. NUMERIC-NUMERIC RELATIONSHIPS
---------------------------------------------------------------

Scatter plots show relationships between two numeric variables.

Review the supplied correlation information before selecting
scatter plots.

Do NOT select every numeric pair.

Prefer only relationships that appear meaningful according to
the supplied evidence.

Normally select no more than 2 individual scatter plots.

If a correlation heatmap already provides broad relationship
information, reduce the number of scatter plots.

A scatter plot should be selected only when it adds information
beyond the heatmap.

---------------------------------------------------------------
4. CORRELATION HEATMAP
---------------------------------------------------------------

A correlation heatmap provides a compact overview of relationships
among multiple numeric variables.

If there are multiple numeric variables and a correlation heatmap
candidate exists, consider selecting ONE heatmap.

Do NOT combine a heatmap with many scatter plots unless the
scatter plots provide clearly additional information.

The heatmap should normally replace several redundant
numeric-pair visualizations.

---------------------------------------------------------------
5. DATETIME-NUMERIC RELATIONSHIPS
---------------------------------------------------------------

Line charts are useful when a datetime column and numeric column
provide meaningful temporal information.

Do NOT select every datetime-numeric combination.

Select only the most analytically meaningful relationship.

Normally select no more than 1 or 2 line charts.

If several line charts communicate similar temporal patterns,
select only the most informative one.

---------------------------------------------------------------
6. GROUPED BAR CHARTS
---------------------------------------------------------------

Grouped bar charts may be useful when a categorical variable
is meaningfully compared against a numeric measure.

Select only when the relationship provides useful analytical
information.

Do NOT select grouped bar charts simply because a categorical
and numeric column exist.

Avoid grouped bar charts that duplicate a simple categorical
distribution chart.

Normally select at most 1 grouped bar chart unless additional
evidence clearly justifies another.

---------------------------------------------------------------
7. STACKED BAR CHARTS
---------------------------------------------------------------

Stacked bar charts can be useful for understanding relationships
between two categorical variables.

Select only when the relationship provides meaningful information.

Do NOT select multiple stacked charts that communicate the same
categorical relationship.

Normally select at most 1 stacked bar chart.

---------------------------------------------------------------
8. 100% STACKED BAR CHARTS
---------------------------------------------------------------

100% stacked bar charts are useful for comparing proportions
across groups.

Select them only when proportional comparison provides meaningful
information.

Do NOT select both a normal stacked bar chart and a 100% stacked
bar chart for the same two categorical variables.

Choose the form that communicates the relationship more clearly.

Normally select at most 1 of these two chart types for a
given categorical relationship.

---------------------------------------------------------------
9. MISSINGNESS VISUALIZATIONS
---------------------------------------------------------------

Missingness charts should be selected ONLY when missing values
actually exist.

If there are no missing values:

DO NOT select:

- missingness_bar_chart
- missingness_heatmap

If missing values exist, normally select ONE missingness
visualization.

Do NOT select multiple missingness charts that communicate
the same data-quality issue.

---------------------------------------------------------------
10. PAIR PLOTS
---------------------------------------------------------------

Pair plots provide a broad overview of multiple numeric
relationships.

However, pair plots can become redundant when:

- a correlation heatmap is selected
- meaningful scatter plots are selected

Therefore, select a pair plot only when it provides significant
additional analytical value.

Do NOT select a pair plot simply because the rule engine generated it.

Normally choose between:

- pair plot

OR

- correlation heatmap + selected scatter plots

rather than automatically selecting both.

---------------------------------------------------------------
11. COMPLEMENTARY COVERAGE
---------------------------------------------------------------

The final visualization set should ideally cover different
analytical purposes where the dataset supports them.

Possible purposes include:

1. Important numeric distribution
2. Important categorical distribution
3. Important numeric relationship
4. Important relationship overview
5. Important temporal trend
6. Important categorical relationship
7. Important data-quality issue

Do NOT force all categories.

Only use categories supported by the dataset.

---------------------------------------------------------------
12. VISUALIZATION SELECTION ORDER
---------------------------------------------------------------

When many candidates are available, evaluate them in this order:

1. Important distribution information
2. Important relationship information
3. Important categorical patterns
4. Important temporal patterns
5. Important data-quality information
6. Additional specialized visualizations only when necessary

Prefer broad analytical coverage over multiple charts about
the same variable.

---------------------------------------------------------------
13. FINAL REDUNDANCY CHECK
---------------------------------------------------------------

Before producing the final answer, perform an internal
redundancy check.

For every selected visualization ask:

- Does it add a distinct analytical message?
- Is its information already communicated by another selected chart?
- Is it supported by the statistical evidence?
- Is it important enough to appear in the final report?

If a visualization is redundant, REMOVE it.

Examples of combinations that should normally be avoided:

- histogram + box plot + violin plot for the same variable
- bar chart + pie chart for the same variable
- stacked bar + 100% stacked bar for the same relationship
- correlation heatmap + many scatter plots showing the same relationships
- pair plot + correlation heatmap + many scatter plots
- multiple missingness charts for the same missing-data pattern

---------------------------------------------------------------
IMPORTANT
---------------------------------------------------------------

The deterministic rule engine generates CANDIDATES.

The LLM performs FINAL SELECTION.

Therefore:

RULE ENGINE:
"What visualizations are possible?"

GEMINI:
"Which visualizations are actually useful and non-redundant
for the final EDA report?"

Do NOT simply reproduce the rule-engine output.

---------------------------------------------------------------
OUTPUT RULES
---------------------------------------------------------------

Return ONLY the visualization recommendations that should
actually appear in the final report.

For every selected recommendation:

- decision MUST be "accepted"
- original_chart_type must match the supplied chart type
- original_columns must match the supplied columns
- final_chart_type must equal original_chart_type
- final_columns must equal original_columns
- reason must briefly explain why the visualization is useful
- confidence must be a decimal between 0 and 1

Use "modified" only when a correction is clearly necessary
according to the supplied evidence.

Prefer "accepted" when the original recommendation is already
appropriate.

Do NOT return rejected recommendations.

Do NOT return unnecessary recommendations.

Do NOT return duplicate recommendations.

Every final column name MUST exist in the supplied evidence.

---------------------------------------------------------------
SUPPORTED CHART TYPES
---------------------------------------------------------------

histogram
box_plot
bar_chart
pie_chart
scatter_plot
line_chart
grouped_bar_chart
stacked_bar_chart
100_percent_stacked_bar_chart
heatmap
missingness_bar_chart
missingness_heatmap
violin_plot
qq_plot
pair_plot

Every confidence value MUST be between 0 and 1.

---------------------------------------------------------------
OUTPUT FORMAT
---------------------------------------------------------------

Return ONLY the JSON object required by the format instructions.

Do not include markdown.

Do not include explanations outside the JSON object.

Do not add trailing commas.

Do not change the required field names.

Do not add fields that are not defined by the schema.

{format_instructions}
"""

    human_message = """
You are now performing the FINAL SELECTION of visualization
recommendations.

The deterministic rule engine has generated a broad candidate set.

The candidate list is NOT the final answer.

Your task is to select a SMALL set of high-value,
complementary and non-redundant visualizations.

Review the supplied evidence and candidates carefully.

---------------------------------------------------------------
SELECTION TARGET
---------------------------------------------------------------

Normally select approximately 4 to 7 visualizations.

Prefer fewer when fewer are sufficient.

Do NOT exceed 7 unless the evidence clearly justifies it.

Do NOT add visualizations simply to reach a target number.

Every selected visualization must have a distinct analytical purpose.

---------------------------------------------------------------
SELECTION RULE
---------------------------------------------------------------

For every candidate, ask:

1. Is it supported by the evidence?
2. Does it provide meaningful analytical information?
3. Is the information important enough for the final report?
4. Is the information already communicated by another
   selected visualization?

If it is redundant, do NOT select it.

---------------------------------------------------------------
RAW DATA INFORMATION
---------------------------------------------------------------

{raw_dataset_information}

---------------------------------------------------------------
PREPROCESSING INFORMATION
---------------------------------------------------------------

{preprocessing_information}

---------------------------------------------------------------
CLEANED DATA INFORMATION
---------------------------------------------------------------

{cleaned_data_information}

---------------------------------------------------------------
STATISTICAL INFORMATION
---------------------------------------------------------------

{statistical_information}

---------------------------------------------------------------
RULE-BASED VISUALIZATION CANDIDATES
---------------------------------------------------------------

{rule_recommendations}

---------------------------------------------------------------
FINAL CHECK
---------------------------------------------------------------

Before returning the result:

- remove redundant visualizations
- remove weak visualizations
- remove unnecessary visualizations
- remove duplicate visualizations
- keep only useful complementary visualizations
- prefer approximately 4 to 7 total
- use fewer if the dataset does not require more

Remember:

The rule engine provides possibilities.

You provide the final concise selection.

Return ONLY the selected recommendations inside the required
JSON structure.

Do NOT return rejected recommendations.

Do NOT return the full candidate list.

Do NOT include markdown or any text outside the JSON object.
"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_message,
            ),
            (
                "human",
                human_message,
            ),
        ]
    ).partial(
        format_instructions=parser.get_format_instructions()
    )


def get_final_report_prompt():

    parser = get_final_report_output_parser()

    system_message = """
You are an expert Exploratory Data Analysis reporting assistant.

Your task is to generate the FINAL human-readable EDA report from
structured, privacy-safe evidence produced by the EDA pipeline.

The deterministic rule engine has already performed profiling,
preprocessing, statistical analysis, and visualization candidate
generation.

Gemini #1 has already reviewed the visualization candidates and
selected the most useful visualizations.

You are Gemini #2.

Your responsibility is to synthesize ALL supplied evidence into
ONE concise, readable, dataset-specific final EDA report.

---------------------------------------------------------------
IMPORTANT ROLE
---------------------------------------------------------------

You are the FINAL REPORT GENERATOR.

You MUST:

- explain the dataset clearly
- explain important data-quality issues
- explain preprocessing in normal human language
- explain the resulting cleaned dataset
- summarize important statistical findings
- explain only the visualizations selected by Gemini #1
- use the rule-engine information as supporting evidence
- keep the report concise and non-repetitive
- use only information supplied in the evidence

You MUST NOT:

- access the original dataset
- access raw dataset rows
- invent dataset values
- invent columns
- invent statistics
- perform preprocessing
- modify the dataset
- generate or render charts
- create new visualization recommendations
- select additional visualizations
- override Gemini #1's visualization selection
- expose internal pipeline implementation details
- reproduce the complete preprocessing execution log
- reproduce every statistic mechanically
- reproduce every visualization candidate

---------------------------------------------------------------
FINAL REPORT STRUCTURE
---------------------------------------------------------------

The final report MUST contain EXACTLY these five sections:

1. Raw Data Information
2. Preprocessing Done
3. Cleaned Data Information
4. Statistical Information
5. Visualization Information

Do not create additional sections.

Do not create a separate dataset overview section.

Do not create a separate data-quality section.

Do not create a separate preprocessing summary section.

Do not create a separate visualization-selection section.

Everything must be incorporated into the five required sections.

---------------------------------------------------------------
1. RAW DATA INFORMATION
---------------------------------------------------------------

Explain the original dataset in simple human-readable language.

Include important information such as:

- number of rows
- number of columns
- column types
- numeric columns
- categorical columns
- datetime columns
- boolean columns
- missing-value information
- important data-quality issues supported by the evidence

The purpose of this section is to answer:

"What did the original dataset look like, and what important
issues were present?"

If missing values exist, clearly mention them.

If there are no missing values, state that clearly.

Do not list unnecessary metadata that does not help the user
understand the dataset.

Do not expose individual dataset records.

---------------------------------------------------------------
2. PREPROCESSING DONE
---------------------------------------------------------------

Explain what preprocessing was performed by the backend.

This section MUST be written in normal language that a user,
analyst, or interviewer can understand.

Do NOT reproduce the internal execution log.

Do NOT list the same operation separately for every column.

Instead, GROUP similar preprocessing operations into meaningful
statements.

For example, if multiple columns had whitespace removed, explain
that together rather than listing:

- column A whitespace removed
- column B whitespace removed
- column C whitespace removed

Instead, summarize them as one understandable statement.

Similarly, group repeated type conversions, normalization,
duplicate handling, or similar transformations.

Mention:

- important preprocessing actions
- important transformations
- rows before and after preprocessing
- columns before and after preprocessing
- excluded columns when relevant
- unresolved or review-required issues when relevant

Only mention operations that actually appear in the supplied
evidence.

Do not invent preprocessing operations.

The purpose of this section is to answer:

"What did the backend do to prepare the data for analysis?"

---------------------------------------------------------------
3. CLEANED DATA INFORMATION
---------------------------------------------------------------

Describe the dataset after preprocessing.

Include:

- cleaned row count
- cleaned column count
- retained columns or important retained column groups
- excluded columns when available
- important resulting changes

Explain the resulting dataset structure in simple language.

Do not repeat the complete preprocessing explanation.

Do not expose raw dataset rows.

The purpose of this section is to answer:

"What does the dataset look like after preprocessing?"

---------------------------------------------------------------
4. STATISTICAL INFORMATION
---------------------------------------------------------------

Summarize the important statistical findings.

Do NOT reproduce every statistic.

Select only meaningful findings supported by the evidence.

Possible findings include:

- central tendency
- spread
- skewness
- important outliers
- important categorical distributions
- datetime ranges
- boolean distributions
- meaningful correlations
- notable differences between variables

Use actual values when they are supplied in the evidence and
help explain the finding.

Do not invent values.

Do not create unsupported interpretations.

Do not turn every statistic into a separate bullet.

Group related findings where appropriate.

The purpose of this section is to answer:

"What important patterns or characteristics were found in the data?"

---------------------------------------------------------------
5. VISUALIZATION INFORMATION
---------------------------------------------------------------

IMPORTANT:

Gemini #1 has already selected the final visualizations.

You MUST use ONLY the visualizations supplied in:

"Gemini #1 Selected Visualizations"

The rule-engine visualization candidates are provided only as
supporting context.

They are NOT additional visualizations to explain.

DO NOT select new visualizations.

DO NOT explain rejected candidates.

DO NOT explain every rule-engine candidate.

DO NOT expand the visualization list.

For each selected visualization, briefly state:

- visualization type
- relevant column(s)
- what analytical purpose it serves

Keep each explanation concise.

Do not write long explanations for individual charts.

Do not repeat the same analytical message across multiple
visualization descriptions.

If Gemini #1 selected only a few visualizations, explain only
those visualizations.

The purpose of this section is to answer:

"Which visualizations are recommended and what will each help
the analyst understand?"

---------------------------------------------------------------
WRITING STYLE
---------------------------------------------------------------

The final report must be:

- clear
- concise
- professional
- natural
- easy to understand
- dataset-specific
- evidence-based
- useful to a human analyst

Write like a human analyst is explaining the result to another
human.

Avoid:

- unnecessary technical jargon
- internal implementation terminology
- repeated statements
- long paragraphs
- generic EDA explanations
- repetitive preprocessing steps
- repetitive visualization explanations
- unnecessary lists
- unsupported conclusions

Do not make the report sound like a raw JSON dump.

Convert structured evidence into natural language.

---------------------------------------------------------------
REPORT LENGTH
---------------------------------------------------------------

Keep the final report concise.

Each section should contain only the information necessary to
understand the dataset and the analysis.

Do not attempt to describe every piece of supplied evidence.

Prioritize meaningful information over completeness of repetition.

---------------------------------------------------------------
PRIVACY
---------------------------------------------------------------

The supplied evidence does not contain raw dataset rows.

Do not attempt to reconstruct or infer individual records.

Only describe aggregate, statistical, structural, and metadata-level
information.

---------------------------------------------------------------
OUTPUT RULES
---------------------------------------------------------------

Return ONLY the JSON object required by the Pydantic schema.

Do not return markdown.

Do not return explanations outside the JSON object.

Do not add fields that are not defined by the schema.

Do not invent information.

Follow the five required report sections exactly.

{format_instructions}
"""

    human_message = """
Generate the FINAL EDA REPORT using ONLY the supplied evidence.

You are Gemini #2, the final report generator.

The evidence is divided into:

1. Raw dataset information
2. Preprocessing information
3. Cleaned dataset information
4. Statistical information
5. Rule-engine visualization candidates
6. Gemini #1 selected visualizations

---------------------------------------------------------------
RAW DATA INFORMATION
---------------------------------------------------------------

{raw_dataset_information}

---------------------------------------------------------------
PREPROCESSING INFORMATION
---------------------------------------------------------------

{preprocessing_information}

---------------------------------------------------------------
CLEANED DATA INFORMATION
---------------------------------------------------------------

{cleaned_data_information}

---------------------------------------------------------------
STATISTICAL INFORMATION
---------------------------------------------------------------

{statistical_information}

---------------------------------------------------------------
RULE-ENGINE VISUALIZATION CANDIDATES
---------------------------------------------------------------

These are the visualizations that the deterministic rule engine
considered possible.

Use them only as supporting context.

Do NOT automatically include them in the final report.

Do NOT create new visualization recommendations.

{visualization_candidates}

---------------------------------------------------------------
GEMINI #1 SELECTED VISUALIZATIONS
---------------------------------------------------------------

These are the final visualizations selected by Gemini #1.

ONLY these visualizations should be described in the final
Visualization Information section.

{visualization_information}

---------------------------------------------------------------
FINAL INSTRUCTION
---------------------------------------------------------------

Generate one concise, human-readable final EDA report.

The report MUST contain exactly these five sections:

1. Raw Data Information
2. Preprocessing Done
3. Cleaned Data Information
4. Statistical Information
5. Visualization Information

Important:

- summarize preprocessing instead of repeating every operation
- summarize statistics instead of listing every statistic
- explain only Gemini #1 selected visualizations
- do not add visualization candidates
- do not create additional sections
- do not expose raw records
- do not invent information
- use normal human-readable language
- keep the report concise and non-repetitive

Return ONLY the required JSON object.
"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_message,
            ),
            (
                "human",
                human_message,
            ),
        ]
    ).partial(
        format_instructions=parser.get_format_instructions()
    )

# ================================================================
# Runnable Chain
# ================================================================

def build_visualization_validation_chain():
    """Build the LangChain Runnable visualization selection chain."""

    prompt = get_visualization_prompt()

    model = get_google_model()

    parser = get_visualization_output_parser()

    prepare_input = RunnableParallel(
        raw_dataset_information=RunnableLambda(
            lambda data: data["raw_dataset_information"]
        ),
        preprocessing_information=RunnableLambda(
            lambda data: data["preprocessing_information"]
        ),
        cleaned_data_information=RunnableLambda(
            lambda data: data["cleaned_data_information"]
        ),
        statistical_information=RunnableLambda(
            lambda data: data["statistical_information"]
        ),
        rule_recommendations=RunnableLambda(
            lambda data: data["rule_recommendations"]
        ),
    )

    chain = (
        prepare_input
        | prompt
        | model
        | parser
    )

    return chain



def build_final_report_chain():
    """Build the LangChain Runnable for final EDA report generation."""

    prompt = get_final_report_prompt()

    model = get_google_model()

    parser = get_final_report_output_parser()

    prepare_input = RunnableParallel(
        raw_dataset_information=RunnableLambda(
            lambda data: data["raw_dataset_information"]
        ),
        preprocessing_information=RunnableLambda(
            lambda data: data["preprocessing_information"]
        ),
        cleaned_data_information=RunnableLambda(
            lambda data: data["cleaned_data_information"]
        ),
        statistical_information=RunnableLambda(
            lambda data: data["statistical_information"]
        ),
        visualization_candidates=RunnableLambda(
            lambda data: data["visualization_candidates"]
        ),
        visualization_information=RunnableLambda(
            lambda data: data["visualization_information"]
        ),
    )

    chain = (
        prepare_input
        | prompt
        | model
        | parser
    )

    return chain
# ================================================================
# Main Validation Function
# ================================================================

def validate_visualization_recommendations(
    raw_profile_report: dict[str, Any],
    preprocessing_summary_report: dict[str, Any],
    statistical_profile: dict[str, Any],
    visualization_recommendations: list[dict[str, Any]],
) -> LLMVisualizationValidationResponse:
    """
    Review deterministic visualization recommendations using
    complete privacy-safe rule-engine evidence.

    Gemini receives raw dataset information, preprocessing information,
    cleaned dataset information, statistical information, and
    rule-based visualization candidates.
    """

    chain = build_visualization_validation_chain()

    prepared_input = prepare_visualization_validation_input(
        raw_profile_report,
        preprocessing_summary_report,
        statistical_profile,
        visualization_recommendations,
    )

    return chain.invoke(
        prepared_input
    )

# ================================================================
# Input Preparation
# ================================================================

def prepare_visualization_validation_input(
    raw_profile_report: dict[str, Any],
    preprocessing_summary_report: dict[str, Any],
    statistical_profile: dict[str, Any],
    visualization_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Prepare complete privacy-safe evidence for Gemini visualization
    selection.

    No raw dataset rows are passed to the LLM.

    The evidence contains:

    - raw dataset information
    - preprocessing information
    - cleaned dataset information
    - statistical information
    - rule-based visualization candidates
    """

    # ------------------------------------------------------------
    # Raw dataset information
    # ------------------------------------------------------------

    raw_dataset_information = {
        "row_count": raw_profile_report.get(
            "row_count",
            0,
        ),
        "column_count": raw_profile_report.get(
            "column_count",
            0,
        ),
        "columns": raw_profile_report.get(
            "columns",
            [],
        ),
        "null_summary": raw_profile_report.get(
            "null_summary",
            {},
        ),
    }

    # ------------------------------------------------------------
    # Preprocessing information
    # ------------------------------------------------------------

    preprocessing_information = {
        "summary": preprocessing_summary_report.get(
            "summary",
            {},
        ),
        "execution_log": preprocessing_summary_report.get(
            "execution_log",
            [],
        ),
        "columns": preprocessing_summary_report.get(
            "columns",
            [],
        ),
        "excluded_columns": preprocessing_summary_report.get(
            "excluded_columns",
            [],
        ),
        "unresolved_columns": preprocessing_summary_report.get(
            "unresolved_columns",
            [],
        ),
        "needs_review_columns": preprocessing_summary_report.get(
            "needs_review_columns",
            [],
        ),
    }

    # ------------------------------------------------------------
    # Cleaned dataset information
    # ------------------------------------------------------------

    cleaned_profile = preprocessing_summary_report.get(
        "cleaned_profile",
        {},
    )

    cleaned_dataset_information = {
        "row_count": cleaned_profile.get(
            "row_count",
            0,
        ),
        "column_count": cleaned_profile.get(
            "column_count",
            0,
        ),
        "columns": cleaned_profile.get(
            "columns",
            [],
        ),
        "excluded_columns": preprocessing_summary_report.get(
            "excluded_columns",
            [],
        ),
        "downstream_handoff": preprocessing_summary_report.get(
            "downstream_handoff",
            {},
        ),
    }

    # ------------------------------------------------------------
    # Statistical information
    # ------------------------------------------------------------

    statistical_information = {
        "row_count": statistical_profile.get(
            "n_rows",
            0,
        ),
        "column_count": statistical_profile.get(
            "n_cols",
            0,
        ),
        "columns": statistical_profile.get(
            "columns",
            {},
        ),
        "numeric_columns": statistical_profile.get(
            "numeric_columns",
            {},
        ),
        "categorical_columns": statistical_profile.get(
            "categorical_columns",
            {},
        ),
        "datetime_columns": statistical_profile.get(
            "datetime_columns",
            {},
        ),
        "boolean_columns": statistical_profile.get(
            "boolean_columns",
            {},
        ),
        "correlation_matrix": statistical_profile.get(
            "correlation_matrix",
            {},
        ),
    }

    # ------------------------------------------------------------
    # Rule-based visualization candidates
    # ------------------------------------------------------------

    rule_recommendations = []

    for recommendation in visualization_recommendations:

        normalized_chart_type = _normalize_chart_type(
            recommendation.get(
                "chart_type"
            )
        )

        rule_recommendations.append(
            {
                "rule_id": recommendation.get(
                    "rule_id"
                ),
                "chart_type": normalized_chart_type,
                "columns": recommendation.get(
                    "columns",
                    [],
                ),
                "reason": recommendation.get(
                    "reason",
                    "",
                ),
                "confidence": recommendation.get(
                    "confidence",
                    0.0,
                ),
                "priority": recommendation.get(
                    "priority",
                    "medium",
                ),
            }
        )

    # ------------------------------------------------------------
    # Final Gemini #1 input
    # ------------------------------------------------------------

    return {
        "raw_dataset_information": raw_dataset_information,
        "preprocessing_information": preprocessing_information,
        "cleaned_data_information": cleaned_dataset_information,
        "statistical_information": statistical_information,
        "rule_recommendations": rule_recommendations,
    }

def prepare_final_report_input(
    pipeline_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepare complete privacy-safe evidence for final EDA report
    generation.

    Gemini #2 receives:

    - raw dataset information
    - preprocessing information
    - cleaned dataset information
    - statistical information
    - rule-based visualization candidates
    - Gemini #1 selected visualizations

    Raw dataset rows are never included.
    """

    # ------------------------------------------------------------
    # Raw dataset information
    # ------------------------------------------------------------

    raw_profile = pipeline_result.get(
        "raw_profile_report",
        {},
    )

    raw_dataset_information = {
        "row_count": raw_profile.get(
            "row_count",
            0,
        ),
        "column_count": raw_profile.get(
            "column_count",
            0,
        ),
        "columns": raw_profile.get(
            "columns",
            [],
        ),
        "null_summary": raw_profile.get(
            "null_summary",
            {},
        ),
    }

    # ------------------------------------------------------------
    # Preprocessing information
    # ------------------------------------------------------------

    preprocessing_summary = pipeline_result.get(
        "preprocessing_summary_report",
        {},
    )

    preprocessing_information = {
        "summary": preprocessing_summary.get(
            "summary",
            {},
        ),
        "execution_log": preprocessing_summary.get(
            "execution_log",
            [],
        ),
        "columns": preprocessing_summary.get(
            "columns",
            [],
        ),
        "excluded_columns": preprocessing_summary.get(
            "excluded_columns",
            [],
        ),
        "unresolved_columns": preprocessing_summary.get(
            "unresolved_columns",
            [],
        ),
        "needs_review_columns": preprocessing_summary.get(
            "needs_review_columns",
            [],
        ),
    }

    # ------------------------------------------------------------
    # Cleaned dataset information
    # ------------------------------------------------------------

    cleaned_profile = preprocessing_summary.get(
        "cleaned_profile",
        {},
    )

    cleaned_dataset_information = {
        "row_count": cleaned_profile.get(
            "row_count",
            0,
        ),
        "column_count": cleaned_profile.get(
            "column_count",
            0,
        ),
        "columns": cleaned_profile.get(
            "columns",
            [],
        ),
        "excluded_columns": preprocessing_summary.get(
            "excluded_columns",
            [],
        ),
        "downstream_handoff": preprocessing_summary.get(
            "downstream_handoff",
            {},
        ),
    }

    # ------------------------------------------------------------
    # Statistical information
    # ------------------------------------------------------------

    statistical_profile = pipeline_result.get(
        "statistical_profile",
    )

    if hasattr(
        statistical_profile,
        "model_dump",
    ):
        statistical_information = (
            statistical_profile.model_dump()
        )
    else:
        statistical_information = (
            statistical_profile or {}
        )

    # ------------------------------------------------------------
    # Rule-based visualization candidates
    # ------------------------------------------------------------

    visualization_recommendations = pipeline_result.get(
        "visualization_recommendations",
    )

    if hasattr(
        visualization_recommendations,
        "model_dump",
    ):
        visualization_candidates = (
            visualization_recommendations.model_dump()
        )
    else:
        visualization_candidates = (
            visualization_recommendations or {}
        )

    # ------------------------------------------------------------
    # Gemini #1 selected visualizations
    # ------------------------------------------------------------

    visualization_validation = pipeline_result.get(
        "llm_visualization_validation",
    )

    if hasattr(
        visualization_validation,
        "model_dump",
    ):
        selected_visualizations = (
            visualization_validation.model_dump()
        )
    else:
        selected_visualizations = (
            visualization_validation or {}
        )

    # ------------------------------------------------------------
    # Final Gemini #2 input
    # ------------------------------------------------------------

    return {
        "raw_dataset_information": raw_dataset_information,
        "preprocessing_information": preprocessing_information,
        "cleaned_data_information": cleaned_dataset_information,
        "statistical_information": statistical_information,
        "visualization_candidates": visualization_candidates,
        "visualization_information": selected_visualizations,
    }


def generate_final_report(
    pipeline_result: dict[str, Any],
) -> FinalEDAReport:
    """
    Generate the final structured EDA report using the LLM.

    The LLM receives only privacy-safe structured evidence.
    """

    chain = build_final_report_chain()

    prepared_input = prepare_final_report_input(
        pipeline_result
    )

    return chain.invoke(
        prepared_input
    )