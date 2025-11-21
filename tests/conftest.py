"""
Pytest configuration and shared fixtures.

This module provides common test fixtures and configuration for all tests.
"""

"""
Pytest configuration and shared fixtures.

This module provides common test fixtures and configuration for all tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Generator

# Try to import LangChain modules (may not be available in test environment)
try:
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create mock classes if LangChain is not available
    class HumanMessage:
        def __init__(self, content):
            self.content = content
    
    class AIMessage:
        def __init__(self, content):
            self.content = content
    
    class ChatOpenAI:
        pass

# Import project modules
try:
    from core.state import AgentState, create_initial_state
    from tools.security import is_code_safe
    from tools.analysis_tools import execute_python_analysis, generate_chart_config
except ImportError as e:
    # Handle import errors gracefully for test discovery
    pytest.skip(f"Project modules not available: {e}", allow_module_level=True)


@pytest.fixture
def sample_state() -> AgentState:
    """
    Create a sample workflow state for testing.
    
    Returns:
        AgentState with test data
    """
    return create_initial_state("Test query for data analysis")


@pytest.fixture
def mock_llm():
    """
    Create a mock LLM instance for testing.
    
    Returns:
        Mock ChatOpenAI instance
    """
    mock = Mock(spec=ChatOpenAI)
    mock.model_name = "gpt-4o"
    mock.temperature = 0.0
    return mock


@pytest.fixture
def safe_code_samples() -> list[str]:
    """
    Provide a list of safe code samples for testing.
    
    Returns:
        List of safe Python code strings
    """
    return [
        "import pandas as pd",
        "df = pd.DataFrame({'a': [1, 2, 3]})",
        "result = df.describe()",
        "x = 5 + 3",
        "data = [1, 2, 3, 4, 5]",
        "avg = sum(data) / len(data)",
    ]


@pytest.fixture
def unsafe_code_samples() -> list[str]:
    """
    Provide a list of unsafe code samples for testing.
    
    Returns:
        List of unsafe Python code strings
    """
    return [
        "import os",
        "import sys",
        "import subprocess",
        "os.system('rm -rf /')",
        "eval('malicious_code')",
        "exec('dangerous_code')",
        "__import__('os')",
        "open('/etc/passwd', 'r')",
    ]


@pytest.fixture
def mock_analysis_response() -> str:
    """
    Provide a mock analysis response for testing.
    
    Returns:
        Mock analysis result string
    """
    return "ANALYSIS: Summary statistics computed successfully."


@pytest.fixture
def mock_chart_config() -> str:
    """
    Provide a mock chart configuration for testing.
    
    Returns:
        Mock chart config string
    """
    return 'CHART_CONFIG: {"type": "bar", "data": "test", "style": {}}'

