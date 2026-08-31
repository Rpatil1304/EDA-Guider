"""
Visualization rules
"""

class VisualizationRules:
    """Define rules for selecting appropriate visualizations"""
    
    CHART_SELECTION = {
        'numeric_numeric': ['scatter', 'heatmap', 'line'],
        'categorical_numeric': ['box_plot', 'bar', 'violin'],
        'categorical_categorical': ['count_plot', 'heatmap'],
        'single_numeric': ['histogram', 'kde', 'box_plot'],
        'single_categorical': ['bar', 'pie']
    }
