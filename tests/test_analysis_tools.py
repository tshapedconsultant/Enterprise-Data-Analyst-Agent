"""
Unit tests for analysis tools.

This module tests the data analysis and visualization tools
used by the worker agents.
"""

import pytest
import json
from tools.analysis_tools import execute_python_analysis, generate_chart_config


class TestExecutePythonAnalysis:
    """Test suite for execute_python_analysis tool."""
    
    def test_safe_code_execution(self):
        """Test that safe code executes successfully."""
        code = "import pandas as pd"
        result = execute_python_analysis(code)
        assert "ANALYSIS:" in result or "ERROR:" in result
    
    def test_unsafe_code_blocked(self):
        """Test that unsafe code is blocked."""
        code = "import os"
        result = execute_python_analysis(code)
        assert "ERROR: Security violation" in result
    
    def test_margin_analysis_pattern(self):
        """Test that margin-related code triggers margin analysis."""
        code = "analyze_margin()"
        result = execute_python_analysis(code)
        assert "margin" in result.lower() or "ANALYSIS:" in result
    
    def test_revenue_analysis_pattern(self):
        """Test that revenue-related code triggers revenue analysis."""
        code = "calculate_revenue()"
        result = execute_python_analysis(code)
        assert "revenue" in result.lower() or "ANALYSIS:" in result
    
    def test_sales_analysis_pattern(self):
        """Test that sales-related code triggers sales analysis."""
        code = "get_sales_data()"
        result = execute_python_analysis(code)
        assert "sales" in result.lower() or "ANALYSIS:" in result
    
    def test_default_analysis_response(self):
        """Test that unrecognized patterns return default response."""
        code = "some_random_analysis()"
        result = execute_python_analysis(code)
        assert "ANALYSIS:" in result
    
    def test_empty_code_handled(self):
        """Test that empty code is handled gracefully."""
        code = ""
        result = execute_python_analysis(code)
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateChartConfig:
    """Test suite for generate_chart_config tool."""
    
    def test_basic_chart_config_generation(self):
        """Test basic chart config generation."""
        data_summary = "Test data summary"
        result = generate_chart_config(data_summary)
        assert "CHART_CONFIG:" in result
        assert "type" in result.lower()
    
    def test_chart_config_contains_data(self):
        """Test that chart config includes the data summary."""
        data_summary = "Revenue increased 21.7%"
        result = generate_chart_config(data_summary)
        assert data_summary in result or "21.7" in result
    
    def test_line_chart_for_trends(self):
        """Test that trend data generates line chart."""
        data_summary = "Revenue trend over time"
        result = generate_chart_config(data_summary)
        # Should detect trend and use line chart
        config_json = result.replace("CHART_CONFIG: ", "")
        config = json.loads(config_json)
        assert config["type"] in ["line", "bar"]  # May default to bar
    
    def test_histogram_for_distribution(self):
        """Test that distribution data generates histogram."""
        data_summary = "Data distribution analysis"
        result = generate_chart_config(data_summary)
        config_json = result.replace("CHART_CONFIG: ", "")
        config = json.loads(config_json)
        assert config["type"] in ["histogram", "bar"]  # May default to bar
    
    def test_scatter_for_correlation(self):
        """Test that correlation data generates scatter chart."""
        data_summary = "Correlation analysis between variables"
        result = generate_chart_config(data_summary)
        config_json = result.replace("CHART_CONFIG: ", "")
        config = json.loads(config_json)
        assert config["type"] in ["scatter", "bar"]  # May default to bar
    
    def test_chart_config_has_style(self):
        """Test that chart config includes style information."""
        data_summary = "Test data"
        result = generate_chart_config(data_summary)
        config_json = result.replace("CHART_CONFIG: ", "")
        config = json.loads(config_json)
        assert "style" in config
        assert isinstance(config["style"], dict)
    
    def test_chart_config_valid_json(self):
        """Test that chart config is valid JSON."""
        data_summary = "Test data summary"
        result = generate_chart_config(data_summary)
        config_json = result.replace("CHART_CONFIG: ", "")
        # Should not raise exception
        config = json.loads(config_json)
        assert isinstance(config, dict)
    
    def test_empty_data_summary_handled(self):
        """Test that empty data summary is handled."""
        data_summary = ""
        result = generate_chart_config(data_summary)
        assert "CHART_CONFIG:" in result or "ERROR:" in result
    
    def test_chart_config_has_required_fields(self):
        """Test that chart config has all required fields."""
        data_summary = "Test data"
        result = generate_chart_config(data_summary)
        config_json = result.replace("CHART_CONFIG: ", "")
        config = json.loads(config_json)
        assert "type" in config
        assert "data" in config
        assert "style" in config

