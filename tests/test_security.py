"""
Unit tests for the security module.

This module tests code validation and security checks to ensure
unsafe code patterns are properly detected and blocked.
"""

import pytest
from tools.security import is_code_safe, validate_code_safety, SecurityViolationError


class TestCodeSafety:
    """Test suite for code safety validation."""
    
    def test_safe_code_imports_pandas(self, safe_code_samples):
        """Test that safe pandas imports are allowed."""
        code = "import pandas as pd"
        assert is_code_safe(code) is True
    
    def test_safe_code_basic_operations(self, safe_code_samples):
        """Test that basic mathematical operations are safe."""
        code = "x = 5 + 3; y = x * 2"
        assert is_code_safe(code) is True
    
    def test_safe_code_dataframe_operations(self, safe_code_samples):
        """Test that DataFrame operations are safe."""
        code = "df = pd.DataFrame({'a': [1, 2, 3]}); result = df.describe()"
        assert is_code_safe(code) is True
    
    def test_unsafe_code_import_os(self, unsafe_code_samples):
        """Test that os module import is blocked."""
        code = "import os"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_import_sys(self, unsafe_code_samples):
        """Test that sys module import is blocked."""
        code = "import sys"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_import_subprocess(self, unsafe_code_samples):
        """Test that subprocess module import is blocked."""
        code = "import subprocess"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_eval(self, unsafe_code_samples):
        """Test that eval() usage is blocked."""
        code = "eval('malicious_code')"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_exec(self, unsafe_code_samples):
        """Test that exec() usage is blocked."""
        code = "exec('dangerous_code')"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_dunder_methods(self):
        """Test that code with dunder methods is blocked."""
        code = "obj.__class__"
        assert is_code_safe(code) is False
    
    def test_unsafe_code_open_function(self, unsafe_code_samples):
        """Test that open() function usage is blocked."""
        code = "open('/etc/passwd', 'r')"
        assert is_code_safe(code) is False
    
    def test_invalid_syntax_handled(self):
        """Test that invalid Python syntax is handled gracefully."""
        code = "def invalid syntax here"
        assert is_code_safe(code) is False
    
    def test_empty_code(self):
        """Test that empty code is considered safe."""
        code = ""
        # Empty code should parse but be safe
        assert is_code_safe(code) is True
    
    def test_validate_code_safety_returns_none_for_safe_code(self):
        """Test that validate_code_safety returns None for safe code."""
        code = "import pandas as pd"
        result = validate_code_safety(code)
        assert result is None
    
    def test_validate_code_safety_returns_error_for_unsafe_code(self):
        """Test that validate_code_safety returns error for unsafe code."""
        code = "import os"
        result = validate_code_safety(code)
        assert isinstance(result, SecurityViolationError)
        assert "Security violation" in str(result)
    
    def test_import_from_statement_blocked(self):
        """Test that 'from os import' statements are blocked."""
        code = "from os import system"
        assert is_code_safe(code) is False
    
    def test_nested_import_blocked(self):
        """Test that nested dangerous imports are blocked."""
        code = "from subprocess import call"
        assert is_code_safe(code) is False
    
    def test_multiple_safe_imports(self):
        """Test that multiple safe imports are allowed."""
        code = "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt"
        assert is_code_safe(code) is True
    
    def test_mixed_safe_and_unsafe_imports(self):
        """Test that mixed imports are blocked if any unsafe."""
        code = "import pandas as pd\nimport os"
        assert is_code_safe(code) is False

