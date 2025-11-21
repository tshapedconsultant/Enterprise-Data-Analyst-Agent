"""
Multi-agent team workflow implementation.

This module contains the EnterpriseDataTeam class that orchestrates the
supervisor-worker pattern using LangGraph.
"""

import logging
from typing import Generator, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END

from core.state import AgentState, create_initial_state, merge_partial_state
from agents import DataAnalystAgent, BusinessStrategistAgent, SupervisorAgent
from config import (
    MAX_ITERATIONS_DEFAULT,
    MESSAGE_WINDOW,
    VALID_AGENTS,
    DEFAULT_MODEL,
    LLM_TEMPERATURE,
)

logger = logging.getLogger(__name__)


class EnterpriseDataTeam:
    """
    Enterprise multi-agent data analysis team.
    
    This class orchestrates a supervisor-worker pattern where:
    - Supervisor: Routes tasks to appropriate workers
    - Data_Analyst: Performs data analysis tasks
    - Business_Strategist: Provides strategic recommendations based on analysis
    
    The workflow uses LangGraph to manage state and control flow.
    """
    
    def __init__(
        self,
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        message_window: int = MESSAGE_WINDOW,
        llm: Optional[ChatOpenAI] = None
    ):
        """
        Initialize the multi-agent team.
        
        Args:
            max_iterations: Maximum number of workflow iterations before forcing termination
            message_window: Number of messages to keep in conversation history
            llm: Optional shared LLM instance (creates new one if not provided)
        """
        self.max_iterations = max_iterations
        self.message_window = message_window
        
        # Initialize shared LLM if not provided
        # Using a shared LLM instance ensures consistent behavior and reduces initialization overhead
        if llm is None:
            self.llm = ChatOpenAI(
                model=DEFAULT_MODEL,
                temperature=LLM_TEMPERATURE
            )
        else:
            self.llm = llm
        
        # Initialize agents with shared LLM instance
        # This allows all agents to use the same model configuration
        self.supervisor = SupervisorAgent(llm=self.llm)
        self.analyst_agent = DataAnalystAgent(llm=self.llm)
        self.strategist_agent = BusinessStrategistAgent(llm=self.llm)
        
        # Build and compile the workflow graph
        # The graph defines the flow: supervisor -> workers -> supervisor -> (finish or continue)
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow graph.
        
        The graph structure:
        - Entry point: supervisor
        - Nodes: supervisor, Data_Analyst, Business_Strategist
        - Edges: Workers return to supervisor, supervisor routes conditionally
        
        Returns:
            Compiled LangGraph workflow
        """
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("Data_Analyst", self._analyst_node)
        graph.add_node("Business_Strategist", self._strategist_node)
        
        # Set entry point
        graph.set_entry_point("supervisor")
        
        # Workers always return to supervisor
        graph.add_edge("Data_Analyst", "supervisor")
        graph.add_edge("Business_Strategist", "supervisor")
        
        # Supervisor routes conditionally based on next_agent
        graph.add_conditional_edges(
            "supervisor",
            lambda state: state.get("next_agent", "FINISH"),
            {
                "Data_Analyst": "Data_Analyst",
                "Business_Strategist": "Business_Strategist",
                "FINISH": END
            }
        )
        
        return graph.compile()
    
    def _analyst_node(self, state: AgentState) -> dict:
        """
        Execute the Data_Analyst worker node.
        
        This node:
        1. Invokes the Data_Analyst agent
        2. Extracts structured data from analysis results
        3. Stores the raw data in state for the Business_Strategist to use
        
        Args:
            state: Current workflow state
            
        Returns:
            Partial state update with analyst's response and raw_data
        """
        try:
            # Invoke agent - returns list of messages (agent response + tool responses)
            result_messages = self.analyst_agent.invoke(state)
            
            # Ensure we have a list
            if not isinstance(result_messages, list):
                result_messages = [result_messages] if isinstance(result_messages, BaseMessage) else [AIMessage(content=str(result_messages))]
            
            # Extract structured data from analysis results for Business_Strategist
            raw_data = None
            import json
            import re
            
            # Look for "DATA: {...}" in the result messages
            for msg in result_messages:
                if hasattr(msg, 'content'):
                    content = msg.content
                    # Try to extract structured data from "DATA: {...}" section
                    data_match = re.search(r'DATA:\s*(\{.*?\})', content, re.DOTALL)
                    if data_match:
                        try:
                            raw_data = json.loads(data_match.group(1))
                            logger.info(f"Extracted raw_data from analysis: {raw_data}")
                            break
                        except json.JSONDecodeError:
                            pass
            
            return {
                "messages": state["messages"] + result_messages,
                "iteration_count": state["iteration_count"] + 1,
                "next_agent": None,
                "last_error": None,
                "raw_data": raw_data,  # Store structured data for Business_Strategist
            }
            
        except Exception as e:
            logger.exception("Data_Analyst node failed")
            error_msg = AIMessage(content=f"ERROR: Data_Analyst failed: {str(e)}")
            return {
                "messages": state["messages"] + [error_msg],
                "iteration_count": state["iteration_count"] + 1,
                "next_agent": None,
                "last_error": str(e),
                "raw_data": state.get("raw_data"),  # Preserve existing raw_data
            }
    
    def _strategist_node(self, state: AgentState) -> dict:
        """
        Execute the Business Strategist worker node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Partial state update with strategist's response
        """
        try:
            # Invoke agent - returns list of messages (agent response)
            result_messages = self.strategist_agent.invoke(state)
            
            # Ensure we have a list
            if not isinstance(result_messages, list):
                result_messages = [result_messages] if isinstance(result_messages, BaseMessage) else [AIMessage(content=str(result_messages))]
            
            return {
                "messages": state["messages"] + result_messages,
                "iteration_count": state["iteration_count"] + 1,
                "next_agent": None,
                "last_error": None,
            }
            
        except Exception as e:
            logger.exception("Business_Strategist node failed")
            error_msg = AIMessage(content=f"ERROR: Business_Strategist failed: {str(e)}")
            return {
                "messages": state["messages"] + [error_msg],
                "iteration_count": state["iteration_count"] + 1,
                "next_agent": None,
                "last_error": str(e),
            }
    
    def _supervisor_node(self, state: AgentState) -> dict:
        """
        Execute the supervisor routing node.
        
        This node:
        1. Checks iteration limits
        2. Detects completion conditions (analysis + strategy done)
        3. Detects infinite loops (same agent called repeatedly)
        4. Calls supervisor to make routing decision
        5. Validates the decision
        6. Updates state with routing information
        
        Args:
            state: Current workflow state
            
        Returns:
            Partial state update with routing decision
        """
        # Enforce hard iteration limit
        if state["iteration_count"] >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return {
                "next_agent": "FINISH",
                "reasoning": "Maximum iterations reached. Terminating workflow.",
                "last_error": "Max iterations reached",
            }
        
        # Check for completion conditions by examining recent messages
        recent_messages = state["messages"][-5:] if len(state["messages"]) > 5 else state["messages"]
        message_contents = " ".join([msg.content for msg in recent_messages if hasattr(msg, 'content')])
        
        # Check if both analysis and strategy are complete
        has_analysis = "ANALYSIS:" in message_contents
        has_strategy = "STRATEGY:" in message_contents
        
        if has_analysis and has_strategy:
            logger.info("Both analysis and strategy complete. Terminating workflow.")
            return {
                "next_agent": "FINISH",
                "reasoning": "Analysis and strategy tasks completed successfully.",
                "last_error": None,
            }
        
        # Detect repetitive routing - check if same agent was called AND didn't produce useful output
        # Only terminate if agent was called multiple times AND didn't complete its task
        supervisor_messages = [msg.content for msg in recent_messages 
                              if hasattr(msg, 'content') and "[Supervisor]" in msg.content]
        if len(supervisor_messages) >= 2:
            # Extract agent names from supervisor messages
            last_routings = []
            for msg in supervisor_messages[-3:]:  # Check last 3 supervisor decisions
                if "Routing to" in msg:
                    agent_name = msg.split("Routing to")[1].split(".")[0].strip()
                    last_routings.append(agent_name)
            
            # If same agent routed 2+ times in a row, check if it actually completed its task
            if len(last_routings) >= 2 and len(set(last_routings[-2:])) == 1:
                repeated_agent = last_routings[-1]
                if repeated_agent != "FINISH":
                    # Check if the agent actually produced useful output
                    agent_completed = False
                    if repeated_agent == "Data_Analyst":
                        # Check if we have ANALYSIS: in messages
                        agent_completed = "ANALYSIS:" in message_contents
                    elif repeated_agent == "Business_Strategist":
                        # Check if we have STRATEGY: in messages
                        agent_completed = "STRATEGY:" in message_contents
                    
                    # Only terminate if agent was called multiple times AND didn't complete
                    if not agent_completed:
                        logger.warning(f"Detected repetitive routing to {repeated_agent} without completion. Terminating to prevent loop.")
                        return {
                            "next_agent": "FINISH",
                            "reasoning": f"Prevented infinite loop: {repeated_agent} was called multiple times without completing its task.",
                            "last_error": None,
                        }
                    else:
                        # Agent completed, allow supervisor to decide next step
                        logger.info(f"{repeated_agent} completed its task, allowing supervisor to decide next step.")
        
        # Get routing decision from supervisor
        try:
            next_agent, reasoning = self.supervisor.decide(state)
        except Exception as e:
            logger.exception("Supervisor decision failed")
            return {
                "next_agent": "FINISH",
                "reasoning": f"Supervisor error: {str(e)}",
                "last_error": f"Supervisor failure: {str(e)}",
            }
        
        # Validate routing decision
        if next_agent not in VALID_AGENTS:
            logger.warning(f"Invalid agent from supervisor: {next_agent}")
            return {
                "next_agent": "FINISH",
                "reasoning": f"Invalid routing '{next_agent}'. Forcing termination.",
                "last_error": f"Invalid routing: {next_agent}",
            }
        
        # Additional safety: if supervisor wants to route to same agent again
        # and we already have that agent's output, force finish
        if next_agent == "Business_Strategist" and has_strategy:
            logger.info("Strategy already exists. Preventing duplicate strategy generation.")
            return {
                "next_agent": "FINISH",
                "reasoning": "Strategy already completed. Task is finished.",
                "last_error": None,
            }
        
        # Create supervisor message for transparency
        supervisor_msg = AIMessage(
            content=f"[Supervisor] Routing to {next_agent}. Reasoning: {reasoning}"
        )
        
        return {
            "next_agent": next_agent,
            "reasoning": reasoning,
            "messages": state["messages"] + [supervisor_msg],
            "last_error": None,
        }
    
    def run_stream(self, query: str) -> Generator[dict, None, None]:
        """
        Execute the workflow and stream events as they occur.
        
        This method runs the workflow and yields structured events that can be
        consumed by a frontend or API. Events include:
        - start: Workflow initialization
        - decision: Supervisor routing decisions
        - action: Worker agent outputs
        - finish: Workflow completion
        - error: Error events
        
        Args:
            query: Initial user query to process
            
        Yields:
            Dictionary events with type, timestamp, and relevant data
        """
        # Initialize state
        state = create_initial_state(query)
        
        # Yield start event
        yield {
            "type": "start",
            "time": datetime.utcnow().isoformat(),
            "data": f"Workflow started: {query}",
        }
        
        try:
            # Stream workflow execution
            for step in self.workflow.stream(state):
                # Step is a dict: {node_name: partial_state}
                for node_name, partial in step.items():
                    # Merge partial state update
                    state = merge_partial_state(state, partial)
                    
                    # Apply message windowing to prevent token overflow
                    # This keeps only the most recent N messages, discarding older context
                    # This is critical for long-running conversations to stay within token limits
                    if len(state["messages"]) > self.message_window:
                        # Keep only the most recent messages (sliding window approach)
                        state["messages"] = state["messages"][-self.message_window:]
                    
                    # Yield appropriate event based on node
                    if node_name == "supervisor":
                        yield {
                            "type": "decision",
                            "time": datetime.utcnow().isoformat(),
                            "agent": "Supervisor",
                            "decision": state.get("next_agent"),
                            "reasoning": state.get("reasoning"),
                            "iteration_count": state["iteration_count"],
                            "last_error": state.get("last_error"),
                        }
                    else:
                        # Worker node output
                        last_msg = (
                            state["messages"][-1].content
                            if state["messages"]
                            else ""
                        )
                        yield {
                            "type": "action",
                            "time": datetime.utcnow().isoformat(),
                            "agent": node_name,
                            "output": last_msg,
                            "iteration_count": state["iteration_count"],
                            "last_error": state.get("last_error"),
                        }
            
            # Yield completion event
            yield {
                "type": "finish",
                "time": datetime.utcnow().isoformat(),
                "data": "Workflow completed successfully",
                "final_iteration_count": state["iteration_count"],
            }
            
        except Exception as e:
            logger.exception("Unexpected error during workflow streaming")
            yield {
                "type": "error",
                "time": datetime.utcnow().isoformat(),
                "error": f"Workflow runtime error: {str(e)}",
            }

