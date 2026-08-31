# EDA-Guider Architecture

## Overview

EDA-Guider is a comprehensive data profiling and exploratory data analysis system that leverages AI agents to automate the EDA process.

## Components

### Backend (FastAPI)
- **Ingestion**: Load data from various formats
- **Profiling**: Analyze data characteristics
- **Rules Engine**: Define preprocessing and visualization rules
- **Agent**: AI-driven decision making
- **Execution**: Apply transformations
- **Visualization**: Generate charts and visualizations
- **Insights**: Extract meaningful insights
- **Audit**: Track all decisions and transformations

### Frontend (Next.js)
- **File Upload**: Upload datasets
- **Progress Tracking**: Monitor pipeline execution
- **Profile Display**: View data profiles
- **Decision Audit**: Review AI decisions
- **Chart Viewer**: Interactive visualizations
- **Insight Report**: Key findings and recommendations

## Data Flow

1. User uploads data
2. Ingestion module loads the data
3. Profiling module analyzes data characteristics
4. Rule engine applies rules and makes preliminary decisions
5. AI agent analyzes profile and makes enhanced decisions
6. Execution module applies decisions to the data
7. Visualization module creates appropriate charts
8. Insights module synthesizes findings
9. Results displayed in frontend with full audit trail
