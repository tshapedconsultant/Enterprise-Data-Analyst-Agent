"""
Security module for code validation and safety checks.

This module provides functions to validate Python code before execution,
preventing unsafe operations and security vulnerabilities.
"""

import ast
import logging
from typing import Optional
from config import FORBIDDEN_MODULES

logger = logging.getLogger(__name__)


class SecurityViolationError(Exception):
    """Raised when code security validation fails."""
    pass


def is_code_safe(code: str) -> bool:
    """
    Perform static analysis on Python code to detect unsafe patterns.
    
    This function uses AST parsing to check for:
    - Forbidden module imports (os, sys, subprocess, etc.)
    - Dangerous function calls (eval, exec, compile, open)
    - Dunder method usage (potential security risks)
    
    Args:
        code: Python code string to validate
        
    Returns:
        True if code appears safe, False otherwise
        
    Example:
        >>> is_code_safe("import pandas as pd")
        True
        >>> is_code_safe("import os; os.system('rm -rf /')")
        False
    """
    # Check for dunder methods (potential security risk)
    if "__" in code:
        logger.warning("Code contains dunder methods, rejecting for safety")
        return False
    
    # Parse code into AST for deeper analysis
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"Code syntax error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error parsing code: {e}")
        return False
    
    # Walk through AST nodes to find dangerous patterns
    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
                if module_name in FORBIDDEN_MODULES:
                    logger.warning(f"Forbidden import detected: {module_name}")
                    return False
        
        # Check import from statements
        if isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]
                if module_name in FORBIDDEN_MODULES:
                    logger.warning(f"Forbidden import from detected: {module_name}")
                    return False
        
        # Check for forbidden names in code
        if isinstance(node, ast.Name):
            if node.id in FORBIDDEN_MODULES:
                logger.warning(f"Forbidden name detected: {node.id}")
                return False
    
    return True


def validate_code_safety(code: str) -> Optional[SecurityViolationError]:
    """
    Validate code safety and return an error if unsafe, None if safe.
    
    Args:
        code: Python code string to validate
        
    Returns:
        SecurityViolationError if code is unsafe, None otherwise
    """
    if not is_code_safe(code):
        return SecurityViolationError("Security violation detected. Execution blocked.")
    return None

