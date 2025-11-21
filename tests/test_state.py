"""
Unit tests for state management.

This module tests the state schema and state management utilities
used throughout the workflow.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from core.state import (
    AgentState,
    create_initial_state,
    merge_partial_state
)


class TestCreateInitialState:
    """Test suite for create_initial_state function."""
    
    def test_creates_state_with_query(self):
        """Test that initial state is created with the query."""
        query = "Analyze revenue data"
        state = create_initial_state(query)
        
        assert state["messages"][0].content == query
        assert isinstance(state["messages"][0], HumanMessage)
    
    def test_initial_state_has_correct_structure(self):
        """Test that initial state has all required fields."""
        query = "Test query"
        state = create_initial_state(query)
        
        assert "messages" in state
        assert "next_agent" in state
        assert "iteration_count" in state
        assert "last_error" in state
        assert "reasoning" in state
    
    def test_initial_state_defaults(self):
        """Test that initial state has correct default values."""
        query = "Test query"
        state = create_initial_state(query)
        
        assert state["next_agent"] is None
        assert state["iteration_count"] == 0
        assert state["last_error"] is None
        assert state["reasoning"] is None


class TestMergePartialState:
    """Test suite for merge_partial_state function."""
    
    def test_merges_messages(self, sample_state):
        """Test that messages are merged correctly."""
        new_message = AIMessage(content="Test response")
        partial = {"messages": sample_state["messages"] + [new_message]}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert len(updated["messages"]) == len(sample_state["messages"]) + 1
        assert updated["messages"][-1] == new_message
    
    def test_merges_iteration_count(self, sample_state):
        """Test that iteration count is merged correctly."""
        partial = {"iteration_count": 5}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["iteration_count"] == 5
        assert isinstance(updated["iteration_count"], int)
    
    def test_merges_next_agent(self, sample_state):
        """Test that next_agent is merged correctly."""
        partial = {"next_agent": "Data_Analyst"}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["next_agent"] == "Data_Analyst"
    
    def test_merges_last_error(self, sample_state):
        """Test that last_error is merged correctly."""
        partial = {"last_error": "Test error message"}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["last_error"] == "Test error message"
    
    def test_merges_reasoning(self, sample_state):
        """Test that reasoning is merged correctly."""
        partial = {"reasoning": "Test reasoning"}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["reasoning"] == "Test reasoning"
    
    def test_merges_multiple_fields(self, sample_state):
        """Test that multiple fields can be merged at once."""
        partial = {
            "iteration_count": 3,
            "next_agent": "Business_Strategist",
            "reasoning": "Need to generate strategic recommendations"
        }
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["iteration_count"] == 3
        assert updated["next_agent"] == "Business_Strategist"
        assert updated["reasoning"] == "Need to generate strategic recommendations"
    
    def test_preserves_unchanged_fields(self, sample_state):
        """Test that unchanged fields are preserved."""
        original_messages = sample_state["messages"]
        partial = {"iteration_count": 1}
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated["messages"] == original_messages
        assert updated["next_agent"] == sample_state["next_agent"]
    
    def test_empty_partial_does_not_change_state(self, sample_state):
        """Test that empty partial doesn't change state."""
        partial = {}
        original = sample_state.copy()
        
        updated = merge_partial_state(sample_state, partial)
        
        assert updated == original

