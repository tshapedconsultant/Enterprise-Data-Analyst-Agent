"""
Supervisor agent implementation for routing decisions.

This module contains the supervisor agent that makes routing decisions
in the multi-agent workflow, determining which worker agent should handle
each task.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from core.state import AgentState
from config import DEFAULT_MODEL, LLM_TEMPERATURE, VALID_AGENTS

logger = logging.getLogger(__name__)


class RouteResponse(BaseModel):
    """
    Structured output schema for supervisor routing decisions.
    
    This Pydantic model ensures the supervisor always returns a valid
    routing decision with reasoning.
    """
    next: str = Field(
        description="Next agent to route to. MUST be one of: Data_Analyst, Business_Strategist, or FINISH. NEVER use Visualizer - it has been replaced by Business_Strategist."
    )
    reasoning: str = Field(
        description="Brief explanation for the routing decision"
    )


class SupervisorAgent:
    """
    Supervisor agent that makes routing decisions in the multi-agent workflow.
    
    The supervisor analyzes the current conversation state and decides which
    worker agent should handle the next task, or if the workflow should finish.
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the supervisor agent.
        
        Args:
            llm: Optional LLM instance (creates new one if not provided)
        """
        if llm is None:
            self.llm = ChatOpenAI(
                model=DEFAULT_MODEL,
                temperature=LLM_TEMPERATURE
            )
        else:
            self.llm = llm
        
        # Build the supervisor chain with structured output
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """
        Build the LangChain chain for the supervisor with structured output.
        
        Returns:
            LangChain chain with structured output enabled
        """
        system_prompt = """You are the Supervisor (router) for a multi-agent data analysis team.
Your job is to decide which agent should handle the next task.

AVAILABLE AGENTS:
- Data_Analyst: Performs data analysis and calculations
- Business_Strategist: Provides strategic recommendations based on analysis (replaced Visualizer)
- FINISH: Terminates the workflow

ROUTING RULES:
1. If the user asks for calculations, metrics, Python code, statistical analysis,
   or any numeric/data analysis => Route to Data_Analyst
2. If data has already been analyzed (you see "ANALYSIS:" in recent messages) => Route to Business_Strategist
3. **CRITICAL**: If strategic recommendations have already been generated (you see "STRATEGY:" 
   in recent messages), the strategy task is COMPLETE => Route to FINISH
4. If both analysis AND strategy are complete, or if the same agent has been 
   called multiple times with similar outputs => Route to FINISH
5. If the task is complete, all questions are answered, and no further action
   is needed => Route to FINISH
6. If you're unsure whether data has been analyzed, route to Data_Analyst first
   to ensure we have the necessary analysis before strategy recommendations

**IMPORTANT**: Visualizer no longer exists. It has been replaced by Business_Strategist.
NEVER route to "Visualizer" - always use "Business_Strategist" instead.

COMPLETION CRITERIA:
- Analysis is complete when you see "ANALYSIS:" in the messages
- Strategy is complete when you see "STRATEGY:" in the messages
- If both are present, the workflow is COMPLETE => FINISH
- If the same agent produces the same output multiple times => FINISH

Always provide clear reasoning for your decision. Be decisive and follow the rules. 
When in doubt about completion, choose FINISH to avoid infinite loops."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("system", "Analyze the conversation and decide the next agent. Return structured output.")
        ])
        
        # Use structured output to ensure valid routing decisions
        return prompt | self.llm.with_structured_output(RouteResponse)
    
    def decide(self, state: AgentState) -> tuple[str, str]:
        """
        Make a routing decision based on the current state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple of (next_agent, reasoning)
            
        Raises:
            Exception: If supervisor decision fails
        """
        try:
            decision = self.chain.invoke(state)
            
            # Extract next agent and reasoning
            next_agent = decision.next
            reasoning = decision.reasoning
            
            # CRITICAL: Replace any "Visualizer" references with "Business_Strategist"
            if next_agent == "Visualizer" or "visualizer" in next_agent.lower():
                logger.warning(f"Supervisor attempted to route to Visualizer. Replacing with Business_Strategist.")
                next_agent = "Business_Strategist"
                reasoning = reasoning.replace("Visualizer", "Business_Strategist").replace("visualizer", "Business_Strategist")
            
            # Validate the decision
            if next_agent not in VALID_AGENTS:
                logger.warning(
                    f"Supervisor returned invalid agent: {next_agent}. "
                    f"Valid agents: {VALID_AGENTS}"
                )
                return "FINISH", f"Invalid routing '{next_agent}' detected. Forcing termination."
            
            return next_agent, reasoning
            
        except Exception as e:
            logger.exception("Supervisor decision failed")
            return "FINISH", f"Supervisor error: {str(e)}"

