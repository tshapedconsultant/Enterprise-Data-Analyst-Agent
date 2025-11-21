"""
State management for the multi-agent workflow.

This module defines the state schema and state management utilities used
throughout the LangGraph workflow.
"""

from typing import Annotated, Sequence, Optional, TypedDict
from operator import add
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State schema for the multi-agent workflow.
    
    This TypedDict defines the structure of state that flows through the
    LangGraph workflow. All nodes must return partial state dictionaries
    that conform to this schema.
    
    Attributes:
        messages: Sequence of conversation messages (HumanMessage, AIMessage, etc.)
        next_agent: Name of the next agent to route to (or None if not decided)
        iteration_count: Current iteration number (prevents infinite loops)
        last_error: Most recent error message (or None if no error)
        reasoning: Supervisor's reasoning for the last routing decision
        raw_data: Structured data that the Data_Analyst is working with (for Business_Strategist to use)
    """
    # Use operator.add as reducer for messages - this tells LangGraph how to merge message sequences
    messages: Annotated[Sequence[BaseMessage], add]
    next_agent: Optional[str]
    iteration_count: int
    last_error: Optional[str]
    reasoning: Optional[str]
    raw_data: Optional[dict]  # Structured data extracted from analysis results


def create_initial_state(query: str) -> AgentState:
    """
    Create initial workflow state from a user query.
    
    Args:
        query: Initial user query string
        
    Returns:
        AgentState dictionary with initialized values
    """
    from langchain_core.messages import HumanMessage
    
    return {
        "messages": [HumanMessage(content=query)],
        "next_agent": None,
        "iteration_count": 0,
        "last_error": None,
        "reasoning": None,
        "raw_data": None,
    }


def merge_partial_state(state: AgentState, partial: dict) -> AgentState:
    """
    Safely merge a partial state update into the full state.
    
    This function ensures that state updates are applied correctly and
    that all required fields are maintained.
    
    Args:
        state: Current full state
        partial: Partial state update from a node
        
    Returns:
        Updated state with partial changes applied
    """
    updated = state.copy()
    
    # Update messages if provided
    if "messages" in partial:
        updated["messages"] = list(partial["messages"])
    
    # Update iteration count if provided
    if "iteration_count" in partial:
        updated["iteration_count"] = int(partial["iteration_count"])
    
    # Update next agent if provided
    if "next_agent" in partial:
        updated["next_agent"] = partial["next_agent"]
    
    # Update error if provided
    if "last_error" in partial:
        updated["last_error"] = partial["last_error"]
    
    # Update reasoning if provided
    if "reasoning" in partial:
        updated["reasoning"] = partial["reasoning"]
    
    return updated

