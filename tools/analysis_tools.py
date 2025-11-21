"""
Analysis tools for data processing and visualization.

This module provides LangChain tools that can be used by agents to perform
data analysis and generate chart configurations. In production, these would
connect to actual data sources and execution environments.
"""

import json
import logging
from typing import Any
from langchain_core.tools import tool
from tools.security import is_code_safe

logger = logging.getLogger(__name__)


@tool
def execute_python_analysis(code: str, user_query: str = "") -> str:
    """
    Execute Python code for data analysis in a safe, controlled environment.
    
    This tool performs security validation before executing code and returns
    structured analysis results with both human-readable summary and structured data.
    In production, this would execute in a sandboxed environment with access to real data sources.
    
    Args:
        code: Python code string to execute for analysis
        user_query: Optional original user query for context (helps detect negative trends)
        
    Returns:
        String containing analysis results in format: "ANALYSIS: <summary> | DATA: <json>"
        The DATA section contains structured data that can be used directly for visualization.
        
    Example:
        >>> execute_python_analysis("df.describe()")
        "ANALYSIS: Summary statistics computed successfully. | DATA: {...}"
    """
    # Security check before execution
    if not is_code_safe(code):
        logger.error("Security violation detected in analysis code")
        return "ERROR: Security violation detected. Execution blocked."
    
    try:
        # Mock execution logic - replace with actual sandboxed execution in production
        code_lower = code.lower()
        query_lower = user_query.lower() if user_query else ""
        combined_context = f"{code_lower} {query_lower}"
        
        # Detect negative trends from user query
        negative_keywords = ["drop", "dropped", "decline", "declined", "decrease", "decreased", 
                           "down", "fall", "fell", "loss", "lost", "churn", "churning"]
        is_negative = any(keyword in combined_context for keyword in negative_keywords)
        
        # Extract specific numbers from query (e.g., "15%", "8%")
        import re
        percentages = re.findall(r'(\d+(?:\.\d+)?)%', query_lower)
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', query_lower)
        
        # Detect invalid quarter references (Q5, Q6, etc. - only Q1-Q4 exist)
        quarter_pattern = r'\bq([5-9]|\d{2,})\b'
        invalid_quarters = re.findall(quarter_pattern, query_lower)
        has_invalid_quarter = len(invalid_quarters) > 0
        
        # Pattern matching for demo purposes - return both summary and structured data
        # Handle negative scenarios first
        if is_negative and ("sales" in combined_context or "revenue" in combined_context):
            # Extract sales drop percentage if mentioned
            sales_drop = None
            if percentages:
                sales_drop = float(percentages[0])
            elif "15" in query_lower:
                sales_drop = 15.0
            
            summary = f"ANALYSIS: Sales declined {sales_drop}% last month. "
            structured_data = {
                "labels": ["Sales Change"],
                "values": [-sales_drop if sales_drop else -15.0],
                "units": ["%"],
                "type": "decline",
                "is_negative": True
            }
            
            # Add churn if mentioned
            if "churn" in combined_context:
                churn_rate = None
                if len(percentages) > 1:
                    churn_rate = float(percentages[1])
                elif "8" in query_lower and "churn" in query_lower:
                    churn_rate = 8.0
                
                if churn_rate:
                    summary += f"Customer churn increased to {churn_rate}% (concerning level). "
                    structured_data["labels"].append("Customer Churn")
                    structured_data["values"].append(churn_rate)
                    structured_data["units"].append("%")
            
            summary += "This indicates a significant performance issue requiring immediate attention."
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        if "margin" in code_lower:
            summary = "ANALYSIS: Avg Margin = 24.5%, Top Region = North America (32.1%)."
            structured_data = {
                "labels": ["Average Margin", "Top Region"],
                "values": [24.5, 32.1],
                "units": ["%", "%"],
                "type": "margin"
            }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        if "revenue" in code_lower or ("quarter" in combined_context and "revenue" in combined_context):
            # Handle multi-quarter analysis requests
            if "4 quarters" in query_lower or "past 4" in query_lower or "q1" in query_lower and "q4" in query_lower:
                # Multi-quarter analysis
                if has_invalid_quarter:
                    # User mentioned Q5 or invalid quarter - clarify and provide Q1-Q4 analysis
                    summary = "ANALYSIS: Note: There are only 4 quarters in a year (Q1-Q4). Interpreting 'Q5 planning' as forward planning for next year. "
                    summary += "Q1 Revenue = $120M, Q2 = $135M, Q3 = $150M (best), Q4 = $145M. "
                    summary += "YoY Growth: Q1 (N/A), Q2 (+12.5%), Q3 (+11.1%), Q4 (-3.3%). "
                    summary += "Best Quarter: Q3 ($150M). Worst Quarter: Q1 ($120M). "
                    summary += "For forward planning, focus on replicating Q3 success and addressing Q1 challenges."
                    structured_data = {
                        "labels": ["Q1", "Q2", "Q3", "Q4"],
                        "values": [120, 135, 150, 145],
                        "units": ["M", "M", "M", "M"],
                        "type": "revenue",
                        "best_quarter": "Q3",
                        "worst_quarter": "Q1",
                        "yoy_growth": [None, 12.5, 11.1, -3.3],
                        "note": "Q5 does not exist - interpreted as forward planning"
                    }
                else:
                    # Standard 4-quarter analysis
                    summary = "ANALYSIS: Q1 Revenue = $120M, Q2 = $135M, Q3 = $150M (best), Q4 = $145M. "
                    summary += "YoY Growth: Q1 (N/A), Q2 (+12.5%), Q3 (+11.1%), Q4 (-3.3%). "
                    summary += "Best Quarter: Q3 ($150M). Worst Quarter: Q1 ($120M)."
                    structured_data = {
                        "labels": ["Q1", "Q2", "Q3", "Q4"],
                        "values": [120, 135, 150, 145],
                        "units": ["M", "M", "M", "M"],
                        "type": "revenue",
                        "best_quarter": "Q3",
                        "worst_quarter": "Q1",
                        "yoy_growth": [None, 12.5, 11.1, -3.3]
                    }
            else:
                # Simple 2-quarter analysis (default)
                summary = "ANALYSIS: Q1 Revenue = $2.3M, Q2 = $2.8M (+21.7%)."
                structured_data = {
                    "labels": ["Q1", "Q2"],
                    "values": [2.3, 2.8],
                    "units": ["M", "M"],
                    "type": "revenue",
                    "growth_percentage": 21.7
                }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        if "sales" in code_lower:
            # Check if it's a negative scenario
            if is_negative:
                sales_drop = float(percentages[0]) if percentages else 15.0
                summary = f"ANALYSIS: Sales declined {sales_drop}% last month. This represents a significant drop requiring immediate attention."
                structured_data = {
                    "labels": ["Sales Change"],
                    "values": [-sales_drop],
                    "units": ["%"],
                    "type": "decline",
                    "is_negative": True
                }
            else:
                summary = "ANALYSIS: Total Sales = $5.1M, Growth Rate = 18.3% YoY."
                structured_data = {
                    "labels": ["Total Sales"],
                    "values": [5.1],
                    "units": ["M"],
                    "type": "sales",
                    "growth_percentage": 18.3
                }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        # Handle churn specifically
        if "churn" in combined_context:
            churn_rate = float(percentages[0]) if percentages else 8.0
            summary = f"ANALYSIS: Customer churn increased to {churn_rate}% (concerning level). This indicates customer retention issues requiring immediate intervention."
            structured_data = {
                "labels": ["Customer Churn"],
                "values": [churn_rate],
                "units": ["%"],
                "type": "churn",
                "is_negative": True
            }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        # Handle ROI (Return on Investment) queries
        if "roi" in combined_context or "return on investment" in combined_context:
            # Check if asking how to increase ROI
            is_increase_query = "increase" in query_lower or "improve" in query_lower or "boost" in query_lower or "enhance" in query_lower
            
            if is_increase_query:
                # Provide current ROI metrics and areas for improvement
                summary = "ANALYSIS: Current ROI Analysis - Overall ROI: 18.5%, " 
                summary += "Marketing ROI: 22.3% (highest), Product Development ROI: 15.2%, " 
                summary += "Operations ROI: 12.8% (lowest). Key Insight: Marketing shows strongest returns. "
                summary += "To increase ROI: 1) Scale high-performing marketing channels, 2) Optimize operations costs, "
                summary += "3) Focus product development on high-margin offerings."
                structured_data = {
                    "labels": ["Overall ROI", "Marketing ROI", "Product Dev ROI", "Operations ROI"],
                    "values": [18.5, 22.3, 15.2, 12.8],
                    "units": ["%", "%", "%", "%"],
                    "type": "roi",
                    "highest": "Marketing ROI",
                    "lowest": "Operations ROI",
                    "recommendation": "Scale marketing, optimize operations"
                }
            else:
                # General ROI query
                summary = "ANALYSIS: ROI Metrics - Overall ROI: 18.5%, " 
                summary += "Marketing ROI: 22.3%, Product Development ROI: 15.2%, Operations ROI: 12.8%. "
                summary += "Average ROI across all channels: 17.2%."
                structured_data = {
                    "labels": ["Overall ROI", "Marketing ROI", "Product Dev ROI", "Operations ROI"],
                    "values": [18.5, 22.3, 15.2, 12.8],
                    "units": ["%", "%", "%", "%"],
                    "type": "roi",
                    "average_roi": 17.2
                }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        # Handle ambiguous/vague queries (e.g., "What's our performance like?")
        vague_keywords = ["performance", "how are we", "how is", "what's our", "status", "situation"]
        is_vague = any(keyword in query_lower for keyword in vague_keywords) and len(query_lower.split()) < 8
        
        if is_vague:
            # Provide a comprehensive performance overview for vague queries
            summary = "ANALYSIS: Overall Performance Overview - Revenue: $5.1M (18.3% YoY growth), "
            summary += "Profit Margin: 24.5% (Top Region: North America at 32.1%), "
            summary += "Customer Metrics: Stable. Key Insight: Strong revenue growth with healthy margins. "
            summary += "Note: For more specific analysis, please specify metrics of interest (e.g., revenue trends, profit margins, customer churn)."
            structured_data = {
                "labels": ["Revenue", "Profit Margin", "Top Region Margin"],
                "values": [5.1, 24.5, 32.1],
                "units": ["M", "%", "%"],
                "type": "performance_overview",
                "growth_percentage": 18.3,
                "note": "General performance overview - specify metrics for detailed analysis"
            }
            return f"{summary} | DATA: {json.dumps(structured_data)}"
        
        # Default response for valid but unrecognized patterns
        summary = "ANALYSIS: Summary statistics computed successfully."
        structured_data = {
            "labels": ["Category 1", "Category 2"],
            "values": [100, 200],
            "units": [None, None],
            "type": "general"
        }
        return f"{summary} | DATA: {json.dumps(structured_data)}"
        
    except Exception as e:
        logger.exception(f"Runtime error during analysis execution: {e}")
        return f"ERROR: Runtime failure during analysis: {str(e)}"


@tool
def generate_chart_config(data_summary: str, user_query: str = "") -> str:
    """
    Generate chart configuration from structured data analysis results.
    
    This tool creates a structured chart configuration (JSON) that can be
    used by visualization libraries to render charts. It extracts structured
    data from the analysis results (looks for "DATA: {...}" section) and
    identifies which data to display based on the user's query.
    
    Args:
        data_summary: String containing analysis results, may include "DATA: {...}" section
        user_query: Optional user query to help identify which data to visualize
        
    Returns:
        String containing chart configuration in JSON format with structured data
        
    Example:
        >>> generate_chart_config("ANALYSIS: Q1 Revenue = $2.3M | DATA: {'labels': ['Q1', 'Q2'], 'values': [2.3, 2.8]}")
        'CHART_CONFIG: {"type": "bar", "data": {"labels": ["Q1", "Q2"], "values": [2.3, 2.8]}, ...}'
    """
    try:
        import re
        
        # First, try to extract structured data from "DATA: {...}" section
        structured_data = None
        data_match = re.search(r'DATA:\s*(\{.*?\})', data_summary, re.DOTALL)
        if data_match:
            try:
                structured_data = json.loads(data_match.group(1))
                logger.info(f"Extracted structured data: {structured_data}")
            except json.JSONDecodeError:
                logger.warning("Failed to parse DATA section, falling back to text extraction")
        
        # If we have structured data, use it directly
        if structured_data and isinstance(structured_data, dict):
            labels = structured_data.get("labels", [])
            values = structured_data.get("values", [])
            data_type = structured_data.get("type", "general")
            growth_percentage = structured_data.get("growth_percentage")
            units = structured_data.get("units", [])
        else:
            # Fallback: extract from text summary (backward compatibility)
            labels = []
            values = []
            growth_percentage = None
            data_type = "general"
            units = []
            
            summary_lower = data_summary.lower()
            
            # Extract Q1, Q2 patterns
            if "q1" in summary_lower and "q2" in summary_lower:
                q1_pattern = r"q1[^=]*=\s*\$?([\d.]+)\s*([km]?)"
                q2_pattern = r"q2[^=]*=\s*\$?([\d.]+)\s*([km]?)"
                
                q1_match = re.search(q1_pattern, summary_lower)
                q2_match = re.search(q2_pattern, summary_lower)
                
                if q1_match and q2_match:
                    labels = ["Q1", "Q2"]
                    q1_val = float(q1_match.group(1))
                    q2_val = float(q2_match.group(1))
                    values = [q1_val, q2_val]
                    units = [q1_match.group(2) or "M", q2_match.group(2) or "M"]
            
            # Extract growth percentage if present
            growth_match = re.search(r'\([+\-]?([\d.]+)%\)', data_summary)
            if growth_match:
                growth_percentage = float(growth_match.group(1))
            
            # If no structured data found, try to extract any numeric values
            if not labels or not values:
                value_pattern = r'(\w+)\s*=\s*\$?([\d.]+)\s*([km]?)'
                matches = re.findall(value_pattern, data_summary, re.IGNORECASE)
                if matches:
                    labels = [match[0] for match in matches]
                    values = [float(match[1]) for match in matches]
                    units = [match[2] or "" for match in matches]
            
            # Fallback: extract any numbers as values
            if not values:
                numbers = re.findall(r'[\d.]+', data_summary)
                if numbers:
                    values = [float(n) for n in numbers[:5]]  # Limit to 5 values
                    labels = [f"Data Point {i+1}" for i in range(len(values))]
                    units = [""] * len(values)
        
        # Ensure we have data
        if not labels or not values:
            labels = ["Category 1", "Category 2"]
            values = [100, 200]
            units = ["", ""]
        
        # Determine chart type based on user query and data
        query_lower = user_query.lower() if user_query else ""
        summary_lower = data_summary.lower()
        
        chart_type = "bar"
        if "trend" in query_lower or "trend" in summary_lower or "time" in query_lower or "time" in summary_lower:
            chart_type = "line"
        elif "distribution" in query_lower or "distribution" in summary_lower or "histogram" in query_lower:
            chart_type = "histogram"
        elif "correlation" in query_lower or "scatter" in query_lower:
            chart_type = "scatter"
        elif "pie" in query_lower:
            chart_type = "pie"
        
        # Determine appropriate ylabel based on data and query
        ylabel = "Value"
        if "revenue" in query_lower or "revenue" in summary_lower:
            ylabel = "Revenue (Millions USD)"
        elif "sales" in query_lower or "sales" in summary_lower:
            ylabel = "Sales (Millions USD)"
        elif "margin" in query_lower or "margin" in summary_lower or "%" in data_summary:
            ylabel = "Percentage (%)"
        elif "$" in data_summary:
            ylabel = "Amount (USD)"
        
        # Determine appropriate xlabel
        xlabel = "Category"
        if "q1" in summary_lower or "q2" in summary_lower or "quarter" in query_lower:
            xlabel = "Quarter"
        elif "month" in query_lower or "month" in summary_lower:
            xlabel = "Month"
        elif "region" in query_lower or "region" in summary_lower:
            xlabel = "Region"
        
        # Determine title based on query
        title = "Data Analysis Visualization"
        if "revenue" in query_lower:
            title = "Revenue Analysis"
        elif "sales" in query_lower:
            title = "Sales Analysis"
        elif "margin" in query_lower:
            title = "Profit Margin Analysis"
        
        # Build structured chart configuration
        config: dict[str, Any] = {
            "type": chart_type,
            "title": title,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "data": {
                "labels": labels,
                "values": values
            },
            "style": {
                "palette": ["#003366", "#FF9900", "#4F4F4F", "#00CC66", "#CC0000"],
                "font": "Helvetica",
                "background": "white",
                "grid": True,
                "legend": False
            }
        }
        
        # Add metadata if available
        if growth_percentage is not None:
            config["meta"] = {
                "growth_percentage": growth_percentage
            }
        
        # Return as JSON string
        config_str = json.dumps(config, indent=2)
        return f"CHART_CONFIG: {config_str}"
        
    except Exception as e:
        logger.exception(f"Error generating chart config: {e}")
        return f"ERROR: Failed to generate chart config: {str(e)}"


# Export all tools for easy import
__all__ = ["execute_python_analysis", "generate_chart_config"]

