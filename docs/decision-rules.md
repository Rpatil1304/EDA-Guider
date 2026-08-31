# Decision Rules

## Preprocessing Rules

### Imputation Strategies
- **Mean**: For numeric columns with normal distribution
- **Median**: For numeric columns with skewed distribution
- **Forward Fill**: For time series data
- **Drop**: For columns with >50% missing values

### Encoding Rules
- **One-Hot Encoding**: For low cardinality categorical features (<10 unique values)
- **Label Encoding**: For ordinal categorical features
- **Target Encoding**: For high cardinality categorical features with target correlation

### Outlier Handling
- **IQR Method**: Remove points outside 1.5*IQR
- **Z-Score Method**: Remove points with |z-score| > 3
- **Cap**: Replace outliers with 95th/5th percentile

## Visualization Rules

### Chart Selection
- **Numeric vs Numeric**: Scatter plot, heatmap, line chart
- **Categorical vs Numeric**: Box plot, bar chart, violin plot
- **Categorical vs Categorical**: Count plot, heatmap
- **Single Numeric**: Histogram, KDE, box plot
- **Single Categorical**: Bar chart, pie chart

### Distribution Analysis
- Check for normality using Shapiro-Wilk test
- Identify multimodality
- Detect skewness and kurtosis
