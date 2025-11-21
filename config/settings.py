"""
Configuration module for the Enterprise Data Analyst Agent.

This module contains all configuration constants, settings, and environment
variables used throughout the application.

SECURITY NOTE: All API keys are loaded from environment variables and never
hardcoded. Use a .env file for local development (not committed to git).
"""

import os
from typing import Final, Optional

# Try to load environment variables from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    # python-dotenv not installed, rely on system environment variables
    pass

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Maximum number of iterations before forcing workflow termination
MAX_ITERATIONS_DEFAULT: Final[int] = 10

# Number of messages to keep in conversation history (prevents token overflow)
MESSAGE_WINDOW: Final[int] = 8

# Valid agent names that can be routed by the supervisor
VALID_AGENTS: Final[set[str]] = {"Data_Analyst", "Business_Strategist", "FINISH"}

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Default model to use for all agents
DEFAULT_MODEL: Final[str] = "gpt-4o"

# Temperature setting for LLM (0 = deterministic, higher = more creative)
LLM_TEMPERATURE: Final[float] = 0.0

# ============================================================================
# API CONFIGURATION
# ============================================================================

# API server host
# Use 127.0.0.1 for localhost-only access, or 0.0.0.0 for all interfaces
API_HOST: Final[str] = os.getenv("API_HOST", "127.0.0.1")

# API server port
API_PORT: Final[int] = int(os.getenv("API_PORT", "8000"))

# CORS allowed origins (use "*" for development, restrict in production)
CORS_ORIGINS: Final[list[str]] = ["*"]

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Forbidden module names that cannot be imported in user code
FORBIDDEN_MODULES: Final[set[str]] = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "eval",
    "exec",
    "compile",
    "open"
}

# ============================================================================
# API KEYS (SECURE - FROM ENVIRONMENT VARIABLES ONLY)
# ============================================================================

# OpenAI API key - REQUIRED for LLM functionality
# Set via environment variable: OPENAI_API_KEY
OPENAI_API_KEY: Final[Optional[str]] = os.getenv("OPENAI_API_KEY")

# Anthropic API key - Optional, for Claude models
# Set via environment variable: ANTHROPIC_API_KEY
ANTHROPIC_API_KEY: Final[Optional[str]] = os.getenv("ANTHROPIC_API_KEY")

# Google API key - Optional, for Gemini models
# Set via environment variable: GOOGLE_API_KEY
GOOGLE_API_KEY: Final[Optional[str]] = os.getenv("GOOGLE_API_KEY")


# ============================================================================
# API KEY VALIDATION
# ============================================================================

def validate_api_keys() -> tuple[bool, list[str]]:
    """
    Validate that required API keys are set.
    
    Returns:
        Tuple of (is_valid, missing_keys)
        - is_valid: True if all required keys are present
        - missing_keys: List of missing required key names
    """
    missing = []
    
    # OpenAI is required for default model
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    return len(missing) == 0, missing


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

