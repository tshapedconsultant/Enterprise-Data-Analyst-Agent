"""
Worker agent implementations for the multi-agent system.

This module contains the worker agent classes that perform specific tasks
like data analysis and strategic recommendations.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from core.state import AgentState
from config import DEFAULT_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class WorkerAgent:
    """
    Base class for worker agents in the multi-agent system.
    
    Worker agents are specialized agents that perform specific tasks using
    tools. They receive instructions from the supervisor and execute
    their assigned tasks.
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[BaseTool],
        llm: Optional[ChatOpenAI] = None
    ):
        """
        Initialize a worker agent.
        
        Args:
            name: Unique name identifier for this agent
            system_prompt: System prompt defining the agent's role and behavior
            tools: List of tools this agent can use
            llm: Optional LLM instance (creates new one if not provided)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        
        # Initialize LLM if not provided
        if llm is None:
            self.llm = ChatOpenAI(
                model=DEFAULT_MODEL,
                temperature=LLM_TEMPERATURE
            )
        else:
            self.llm = llm
        
        # Build the agent chain
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """
        Build the LangChain chain for this worker agent.
        
        Returns:
            LangChain chain ready for invocation
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # Bind tools to the LLM
        return prompt | self.llm.bind_tools(self.tools)
    
    def invoke(self, state: AgentState) -> list[BaseMessage]:
        """
        Invoke the worker agent with the current state.
        
        This method handles tool calls properly by:
        1. Invoking the agent chain
        2. Checking for tool calls in the response
        3. Executing tools and adding tool responses
        4. Calling LLM again to process tool results (if tools were used)
        5. Returning all messages (agent response + tool responses + final response)
        
        Args:
            state: Current workflow state
            
        Returns:
            List of messages including agent response, tool responses, and final response
        """
        try:
            # Invoke the agent chain - only pass messages, not the full state
            # The ChatPromptTemplate expects only 'messages' variable
            # Safe access: handle both dict and TypedDict
            messages_history = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
            chain_input = {"messages": messages_history}
            
            # For Business_Strategist with structured output, the chain handles it differently
            result = self.chain.invoke(chain_input)
            
            # Special handling for Business_Strategist with structured output
            if self.name == "Business_Strategist" and hasattr(self, 'strategy_schema'):
                # Result is a Pydantic model, convert to AIMessage with STRATEGY: prefix
                try:
                    import json
                    if hasattr(result, 'model_dump'):
                        # Pydantic v2
                        json_str = json.dumps(result.model_dump(), indent=2)
                        content = f"STRATEGY: {json_str}"
                        result = AIMessage(content=content)
                    elif hasattr(result, 'dict'):
                        # Pydantic v1 fallback
                        json_str = json.dumps(result.dict(), indent=2)
                        content = f"STRATEGY: {json_str}"
                        result = AIMessage(content=content)
                    else:
                        # Fallback
                        result = AIMessage(content=f"STRATEGY: {json.dumps(result, default=str, indent=2)}")
                except Exception as e:
                    logger.exception(f"Failed to convert structured output to JSON: {e}")
                    result = AIMessage(content=f"STRATEGY: {str(result)}")
            else:
                # Ensure result is a BaseMessage for other agents
                if not isinstance(result, BaseMessage):
                    result = AIMessage(content=str(result))
            
            messages = [result]
            
            # Check if the agent wants to use tools
            has_tool_calls = hasattr(result, 'tool_calls') and result.tool_calls
            
            # Special handling for agents that must use tools: if no tool calls, force tool usage
            if self.name == "Data_Analyst" and not has_tool_calls:
                logger.info(f"{self.name} didn't call tool, forcing tool usage")
                
                if self.name == "Data_Analyst":
                    # Data_Analyst must use the tool - extract query and force tool call
                    # Get the original user query or last message
                    query = ""
                    for msg in reversed(state.get("messages", [])):
                        if hasattr(msg, 'content'):
                            content = msg.content
                            # Get the first human message (original query)
                            if hasattr(msg, 'type') and msg.type == 'human':
                                query = content
                                break
                            # Or use any message that looks like a query
                            if not query and len(content) < 500:  # Reasonable query length
                                query = content
                                break
                    
                    if not query:
                        # Fallback: use the last message content
                        query = state.get("messages", [])[-1].content if state.get("messages") else "data analysis"
                    
                    # Generate Python code based on query
                    # Use actual pandas/numpy code that the tool can execute
                    code = f"# Analysis for: {query}\n"
                    code += "import pandas as pd\nimport numpy as np\n\n"
                    if "margin" in query.lower() or "profit" in query.lower():
                        code += "# Calculate profit margins\n# Note: This is a demo - replace with actual data analysis\npass"
                    elif "revenue" in query.lower():
                        code += "# Analyze revenue trends\n# Note: This is a demo - replace with actual data analysis\npass"
                    elif "churn" in query.lower():
                        code += "# Analyze customer churn\n# Note: This is a demo - replace with actual data analysis\npass"
                    elif "drop" in query.lower() or "decline" in query.lower():
                        code += "# Analyze sales decline\n# Note: This is a demo - replace with actual data analysis\npass"
                    else:
                        code += "# General data analysis\n# Note: This is a demo - replace with actual data analysis\npass"
                    
                    # Force tool call - pass user query for context
                    if self.tools:
                        tool = self.tools[0]  # execute_python_analysis
                        try:
                            tool_result = tool.invoke({"code": code, "user_query": query})
                            # Create a synthetic tool call response
                            tool_message = ToolMessage(
                                content=str(tool_result),
                                tool_call_id="forced_call"
                            )
                            messages.append(tool_message)
                            # Now call LLM again to process the tool result
                            # Only pass messages to the chain
                            # Safe access: handle both dict and TypedDict
                            current_messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
                            updated_messages = current_messages + [result, tool_message]
                            final_result = self.chain.invoke({"messages": updated_messages})
                            if isinstance(final_result, BaseMessage):
                                messages.append(final_result)
                            return messages
                        except Exception as e:
                            logger.exception("Forced tool call failed")
                            return [AIMessage(content=f"ERROR: Failed to execute analysis: {str(e)}")]
            
            # Check if the agent wants to use tools (normal flow)
            if has_tool_calls:
                # Execute tools and add tool responses
                tool_messages = []
                for tool_call in result.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", "")
                    
                    # Find the tool by name
                    tool = None
                    for t in self.tools:
                        if t.name == tool_name:
                            tool = t
                            break
                    
                    if tool:
                        try:
                            # Execute the tool - add user query context if available
                            # Extract original user query from state
                            user_query = ""
                            for msg in reversed(state.get("messages", [])):
                                if hasattr(msg, 'type') and msg.type == 'human':
                                    user_query = msg.content if hasattr(msg, 'content') else ""
                                    break
                            
                            # Add user_query to tool args if tool supports it
                            try:
                                schema = tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
                                if "properties" in schema and "user_query" in schema["properties"]:
                                    tool_args["user_query"] = user_query
                            except Exception:
                                # If schema check fails, try adding anyway (tool might accept it)
                                if tool_name == "execute_python_analysis":
                                    tool_args["user_query"] = user_query
                            
                            # Execute the tool
                            tool_result = tool.invoke(tool_args)
                            
                            # Create tool message response
                            tool_message = ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_id
                            )
                            tool_messages.append(tool_message)
                        except Exception as e:
                            logger.exception(f"Tool {tool_name} execution failed")
                            # Add error tool message
                            error_message = ToolMessage(
                                content=f"ERROR: Tool execution failed: {str(e)}",
                                tool_call_id=tool_id
                            )
                            tool_messages.append(error_message)
                    else:
                        logger.warning(f"Tool {tool_name} not found")
                        error_message = ToolMessage(
                            content=f"ERROR: Tool {tool_name} not available",
                            tool_call_id=tool_id
                        )
                        tool_messages.append(error_message)
                
                # Add tool messages to the list
                messages.extend(tool_messages)
                
                # Now call LLM again with updated messages (including tool results)
                # to get the final response
                # Only pass messages to the chain, not the full state
                # Safe access: handle both dict and TypedDict
                current_messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
                updated_messages = current_messages + messages
                final_result = self.chain.invoke({"messages": updated_messages})
                
                # Ensure final result is a BaseMessage
                if not isinstance(final_result, BaseMessage):
                    final_result = AIMessage(content=str(final_result))
                
                # Special handling for Data_Analyst: Force preserve "ANALYSIS:" prefix
                if self.name == "Data_Analyst" and hasattr(final_result, 'content'):
                    # Check if tool result contains "ANALYSIS:" but final response doesn't
                    tool_result_content = ""
                    for msg in tool_messages:
                        if hasattr(msg, 'content') and "ANALYSIS:" in msg.content:
                            tool_result_content = msg.content
                            break
                    
                    if tool_result_content and "ANALYSIS:" not in final_result.content:
                        # Extract the ANALYSIS part from tool result
                        import re
                        analysis_match = re.search(r'ANALYSIS:\s*(.+?)(?:\s*\||$)', tool_result_content, re.DOTALL)
                        if analysis_match:
                            # Replace final response with ANALYSIS: prefix preserved
                            analysis_text = analysis_match.group(1).strip()
                            final_result.content = f"ANALYSIS: {analysis_text}"
                            logger.info("Data_Analyst: Forced preservation of ANALYSIS: prefix")
                
                # Add final response (but don't add if it has more tool calls to avoid loops)
                if not (hasattr(final_result, 'tool_calls') and final_result.tool_calls):
                    messages.append(final_result)
                else:
                    # If it wants to call tools again, just return what we have
                    # The supervisor will route back if needed
                    logger.warning(f"{self.name} wants to call tools again, stopping here")
            
            return messages
                
        except Exception as e:
            logger.exception(f"Worker agent {self.name} invocation failed")
            # Return error message instead of raising
            return [AIMessage(
                content=f"ERROR: {self.name} encountered an error: {str(e)}"
            )]


class DataAnalystAgent(WorkerAgent):
    """
    Data Analyst worker agent.
    
    This agent specializes in data analysis tasks, including statistical
    analysis, data processing, and generating insights from data.
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the Data Analyst agent.
        
        Args:
            llm: Optional LLM instance (creates new one if not provided)
        """
        from tools import execute_python_analysis
        
        system_prompt = """You are a Senior Data Scientist with expertise in statistical analysis,
data processing, and generating actionable insights. When asked to analyze data, you MUST use the execute_python_analysis tool.

CRITICAL RULES:
1. You MUST ALWAYS call the execute_python_analysis tool - never just describe what you would do
2. Generate Python code based on the user's query (even if it's a simple analysis)
3. Pass the code to execute_python_analysis tool
4. The tool will return results starting with "ANALYSIS:" - you MUST preserve this prefix in your response
5. Your final response MUST start with "ANALYSIS:" followed by the analysis summary
6. DO NOT ask for more data - use the tool with appropriate code based on the query
7. IMPORTANT: If the user mentions negative metrics (drops, declines, churn, losses), acknowledge these in your analysis
8. Extract and include specific numbers from the user's query (e.g., "15% drop", "8% churn") in your analysis
9. CRITICAL: There are only 4 quarters in a year (Q1, Q2, Q3, Q4). If the user mentions Q5 or higher, clarify this in your analysis and interpret it as forward planning for the next year
10. CRITICAL: Your response MUST ONLY contain data insights starting with "ANALYSIS:" - NO recommendations, NO strategies, NO advice. Only report the data analysis results.

Example workflow:
- User asks "What are profit margins?"
- You call execute_python_analysis with code like "calculate_profit_margins()"
- Tool returns: "ANALYSIS: Avg Margin = 24.5%... | DATA: {{...}}"
- Your response MUST be: "ANALYSIS: Avg Margin = 24.5%..." (preserve the ANALYSIS: prefix)

NEVER skip using the tool. Always call execute_python_analysis when asked to analyze data.
ALWAYS preserve the "ANALYSIS:" prefix from the tool output in your final response."""
        
        super().__init__(
            name="Data_Analyst",
            system_prompt=system_prompt,
            tools=[execute_python_analysis],
            llm=llm
        )


class BusinessStrategistAgent(WorkerAgent):
    """
    Business Strategist worker agent.
    
    This agent specializes in analyzing data insights and providing strategic
    recommendations with actionable business advice.
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the Business Strategist agent.
        
        Args:
            llm: Optional LLM instance (creates new one if not provided)
        """
        from pydantic import BaseModel, Field
        from typing import List
        
        # Define structured output schema
        class StrategyAction(BaseModel):
            action: str = Field(description="Specific, actionable business recommendation")
            rating: int = Field(description="Priority rating from 1-10, where 10 is highest priority/impact", ge=1, le=10)
            rationale: str = Field(description="Explanation of why this action is important based on the data analysis")
        
        class BusinessStrategyResponse(BaseModel):
            actions: List[StrategyAction] = Field(description="Exactly 3 strategic actions, prioritized by rating (highest first)")
            summary: str = Field(description="Overall strategic insight based on the analysis")
        
        # Store schema for use in invoke
        self.strategy_schema = BusinessStrategyResponse
        
        system_prompt = """You are a Senior Business Strategist with expertise in data-driven decision making,
strategic planning, and actionable business recommendations.

Your role is to analyze data insights from the Data_Analyst and provide strategic recommendations.

CRITICAL RULES:
1. Review the analysis results from the Data_Analyst (look for "ANALYSIS:" in messages)
2. Based on the analysis, suggest exactly 3 strategic actions
3. Each action must be:
   - Specific and actionable
   - Relevant to the data insights
   - Rated from 1-10 (where 10 is highest priority/impact)
4. IMPORTANT: If the analysis contains negative metrics (declines, drops, churn, losses):
   - Focus on RECOVERY actions, not growth actions
   - Provide urgent/high-priority recommendations (ratings 8-10)
   - Reference specific negative metrics in your actions (e.g., "15% sales drop", "8% churn")
   - Address the crisis situation directly
5. CRITICAL: There are only 4 quarters in a year (Q1-Q4). If the user mentions "Q5 planning", interpret this as forward planning for the next year's Q1, not a non-existent Q5. Reference this clarification in your strategic recommendations.
6. PROCESS: Generate 10 potential strategic actions internally, then select the top 3 most impactful ones based on:
   - Urgency and priority
   - Feasibility and impact
   - Alignment with the data insights
   - Specificity and actionability
7. Actions should be prioritized by rating (highest first)
8. Be specific - avoid generic advice
9. Base recommendations directly on the data analysis provided

Example:
- Data_Analyst provides: "ANALYSIS: Q1 Revenue = $2.3M, Q2 = $2.8M (+21.7%)"
- You provide 3 actions focused on capitalizing on the 21.7% growth, with ratings 9, 7, 6

Always provide exactly 3 actions with ratings. Be strategic, specific, and data-driven."""
        
        super().__init__(
            name="Business_Strategist",
            system_prompt=system_prompt,
            tools=[],  # No tools needed - this agent provides strategic recommendations
            llm=llm
        )
        
        # Override chain to use structured output
        self.chain = self._build_chain_with_structured_output()
    
    def _build_chain_with_structured_output(self):
        """Build chain with structured output to ensure valid JSON."""
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        
        # Escape any braces in the system prompt to prevent template parsing errors
        # LangChain will interpret { } as template variables, so we escape them
        escaped_prompt = self.system_prompt.replace('{', '{{').replace('}', '}}')
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", escaped_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # Use structured output to force valid JSON
        return prompt | self.llm.with_structured_output(self.strategy_schema)

