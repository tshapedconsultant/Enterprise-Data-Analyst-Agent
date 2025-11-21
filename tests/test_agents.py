"""
Unit tests for agent implementations.

This module tests the worker agents and supervisor agent
functionality and behavior.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import AIMessage
from agents.worker import WorkerAgent, DataAnalystAgent, BusinessStrategistAgent
from agents.supervisor import SupervisorAgent, RouteResponse
from core.state import create_initial_state
from config import VALID_AGENTS


class TestWorkerAgent:
    """Test suite for WorkerAgent base class."""
    
    def test_worker_initialization(self, mock_llm):
        """Test that worker agent initializes correctly."""
        worker = WorkerAgent(
            name="TestWorker",
            system_prompt="You are a test worker",
            tools=[],
            llm=mock_llm
        )
        
        assert worker.name == "TestWorker"
        assert worker.system_prompt == "You are a test worker"
        assert worker.llm == mock_llm
    
    def test_worker_builds_chain(self, mock_llm):
        """Test that worker builds a chain."""
        worker = WorkerAgent(
            name="TestWorker",
            system_prompt="Test prompt",
            tools=[],
            llm=mock_llm
        )
        
        assert worker.chain is not None
    
    @patch('agents.worker.ChatOpenAI')
    def test_worker_creates_llm_if_none(self, mock_chat_openai):
        """Test that worker creates LLM if not provided."""
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        worker = WorkerAgent(
            name="TestWorker",
            system_prompt="Test prompt",
            tools=[]
        )
        
        assert worker.llm is not None


class TestDataAnalystAgent:
    """Test suite for DataAnalystAgent."""
    
    def test_analyst_agent_initialization(self, mock_llm):
        """Test that DataAnalystAgent initializes correctly."""
        agent = DataAnalystAgent(llm=mock_llm)
        
        assert agent.name == "Data_Analyst"
        assert "Data Scientist" in agent.system_prompt or "analysis" in agent.system_prompt.lower()
    
    def test_analyst_has_tools(self, mock_llm):
        """Test that DataAnalystAgent has analysis tools."""
        agent = DataAnalystAgent(llm=mock_llm)
        
        assert len(agent.tools) > 0
        # Should have execute_python_analysis tool
        tool_names = [tool.name for tool in agent.tools]
        assert any("analysis" in name.lower() for name in tool_names)


class TestBusinessStrategistAgent:
    """Test suite for BusinessStrategistAgent."""
    
    def test_strategist_agent_initialization(self, mock_llm):
        """Test that BusinessStrategistAgent initializes correctly."""
        agent = BusinessStrategistAgent(llm=mock_llm)
        
        assert agent.name == "Business_Strategist"
        assert "strategist" in agent.system_prompt.lower() or "strategy" in agent.system_prompt.lower()
    
    def test_strategist_has_structured_output(self, mock_llm):
        """Test that BusinessStrategistAgent uses structured output."""
        agent = BusinessStrategistAgent(llm=mock_llm)
        
        # Should have strategy_schema for structured output
        assert hasattr(agent, 'strategy_schema')
        assert agent.chain is not None


class TestSupervisorAgent:
    """Test suite for SupervisorAgent."""
    
    def test_supervisor_initialization(self, mock_llm):
        """Test that SupervisorAgent initializes correctly."""
        supervisor = SupervisorAgent(llm=mock_llm)
        
        assert supervisor.llm == mock_llm
        assert supervisor.chain is not None
    
    @patch('agents.supervisor.ChatOpenAI')
    def test_supervisor_creates_llm_if_none(self, mock_chat_openai):
        """Test that supervisor creates LLM if not provided."""
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        supervisor = SupervisorAgent()
        
        assert supervisor.llm is not None
    
    def test_supervisor_decide_returns_valid_agent(self, mock_llm, sample_state):
        """Test that supervisor returns valid agent names."""
        supervisor = SupervisorAgent(llm=mock_llm)
        
        # Mock the chain to return a valid decision
        mock_decision = Mock(spec=RouteResponse)
        mock_decision.next = "Data_Analyst"
        mock_decision.reasoning = "Need to analyze data"
        
        # Replace chain with a MagicMock that has an invoke method
        mock_chain = MagicMock()
        mock_chain.invoke = Mock(return_value=mock_decision)
        supervisor.chain = mock_chain
        
        next_agent, reasoning = supervisor.decide(sample_state)
        
        assert next_agent in VALID_AGENTS
        assert isinstance(reasoning, str)
    
    def test_supervisor_handles_invalid_agent(self, mock_llm, sample_state):
        """Test that supervisor handles invalid agent names."""
        supervisor = SupervisorAgent(llm=mock_llm)
        
        # Mock the chain to return an invalid decision
        mock_decision = Mock(spec=RouteResponse)
        mock_decision.next = "InvalidAgent"
        mock_decision.reasoning = "Invalid reasoning"
        
        # Replace chain with a MagicMock that has an invoke method
        mock_chain = MagicMock()
        mock_chain.invoke = Mock(return_value=mock_decision)
        supervisor.chain = mock_chain
        
        next_agent, reasoning = supervisor.decide(sample_state)
        
        assert next_agent == "FINISH"
        assert "Invalid" in reasoning or "invalid" in reasoning.lower()
    
    def test_supervisor_handles_exceptions(self, mock_llm, sample_state):
        """Test that supervisor handles exceptions gracefully."""
        supervisor = SupervisorAgent(llm=mock_llm)
        
        # Replace chain with a MagicMock that raises an exception
        mock_chain = MagicMock()
        mock_chain.invoke = Mock(side_effect=Exception("Test error"))
        supervisor.chain = mock_chain
        
        next_agent, reasoning = supervisor.decide(sample_state)
        
        assert next_agent == "FINISH"
        assert "error" in reasoning.lower() or "Error" in reasoning

