"""
Logging configuration for the Enterprise Data Analyst Agent.

This module sets up structured logging for the entire application.
"""

import logging
import sys
from config import LOG_LEVEL


def setup_logging():
    """
    Configure application-wide logging.
    
    Sets up:
    - Log level from configuration
    - Format with timestamps and log levels
    - Console handler for output
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger

