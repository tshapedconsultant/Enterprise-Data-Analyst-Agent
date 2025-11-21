"""
Core package for the Enterprise Data Analyst Agent.

This package contains state management and core workflow utilities.
"""

from core.state import (
    AgentState,
    create_initial_state,
    merge_partial_state,
)

__all__ = [
    "AgentState",
    "create_initial_state",
    "merge_partial_state",
]

