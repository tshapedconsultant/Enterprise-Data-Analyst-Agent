# Enterprise Data Analyst Agent

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Production--Ready-green.svg)
![LangGraph](https://img.shields.io/badge/Agentic_AI-LangGraph-orange.svg)
![OpenAI](https://img.shields.io/badge/LLM-GPT--4-purple.svg)

> 

**This system turns natural language business questions into automated multi-step AI workflows using specialized agents that collaborate autonomously.**

---

## 💡 Why This Project Matters

This project demonstrates **real-world Agentic AI design**: autonomous decision-making, multi-agent collaboration, tool use, and workflow orchestration — all core competencies for modern AI engineering roles. It showcases how to build production-ready systems where multiple specialized agents work together intelligently, making this an excellent portfolio piece for roles in applied AI, ML engineering, and agentic systems development.

---

## 📋 Quick Overview

A production-ready **multi-agent system** that demonstrates **Agentic AI** principles. Ask a business question in plain English, and watch three specialized AI agents collaborate:

1. **Supervisor Agent** → Routes the task intelligently
2. **Data Analyst Agent** → Performs analysis using tools
3. **Business Strategist Agent** → Provides strategic recommendations

Built with **LangGraph** for workflow orchestration, **FastAPI** for the API, and **OpenAI GPT-4** for agent intelligence. Perfect for demonstrating autonomous agent behavior, tool use, and multi-agent collaboration.

---

## 🎬 How It Works: End-to-End Example

**User Query:** *"Analyze Q1 revenue trends and propose strategies"*

```
1. Supervisor Agent receives query
   → Decides: "Needs data analysis first"
   → Routes to: Data Analyst Agent

2. Data Analyst Agent executes analysis
   → Uses execute_python_analysis tool
   → Returns: "ANALYSIS: Q1 Revenue = $2.3M, Q2 = $2.8M (+21.7%)"

3. Supervisor Agent sees analysis complete
   → Decides: "Now needs strategic recommendations"
   → Routes to: Business Strategist Agent

4. Business Strategist Agent analyzes insights
   → Generates 3 strategic actions with priority ratings (1-10)
   → Returns: "STRATEGY: {actions: [...], summary: '...'}"

5. Workflow completes → User receives complete analysis + strategies
```

**Result:** The user gets both data insights and actionable business recommendations, all from a single natural language query.

---

## 🖼️ Demo

> **📸 Screenshot Placeholder**  
> *Add a screenshot of the web interface showing agent collaboration in real-time*

> **📸 GIF Placeholder**  
> *Add a GIF showing the streaming workflow: Supervisor → Data Analyst → Business Strategist*

---

## 🤖 Agent Architecture

### Three Specialized Agents

| Agent | Role | Capabilities |
|-------|------|-------------|
| **Supervisor** | Orchestrator | Makes autonomous routing decisions based on context |
| **Data Analyst** | Analyst | Performs statistical analysis using specialized tools |
| **Business Strategist** | Strategist | Generates actionable recommendations with priority ratings |

### Key Capabilities

- ✅ **Autonomous Decision Making** - Agents make independent routing and analysis decisions
- ✅ **Tool Use & Function Calling** - Agents autonomously select and use appropriate tools
- ✅ **Multi-Agent Collaboration** - Agents communicate and build upon each other's work
- ✅ **LangGraph Orchestration** - Advanced workflow management for agent coordination
- ✅ **State Management** - Complex state handling across agent interactions
- ✅ **Streaming API** - Real-time event streaming via FastAPI

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd data-analyst-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key
export OPENAI_API_KEY="your-api-key-here"  # Windows: $env:OPENAI_API_KEY="..."

# 5. Run server
python main.py
```

**Access the web interface:** `http://127.0.0.1:8000`

---

## 📖 Usage

### Web Interface (Recommended)

Simply open `http://127.0.0.1:8000` in your browser:

- Type questions in plain English
- Watch agents collaborate in real-time
- See streaming results as agents work
- Get both analysis and strategic recommendations

### API Usage

**Run Analysis:**
```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze revenue trends for Q1 and Q2",
    "max_iterations": 10
  }'
```

**Streaming Response (NDJSON):**
```json
{"type": "start", "data": "Workflow started: ..."}
{"type": "decision", "agent": "Supervisor", "decision": "Data_Analyst", "reasoning": "..."}
{"type": "action", "agent": "Data_Analyst", "output": "ANALYSIS: ..."}
{"type": "decision", "agent": "Supervisor", "decision": "Business_Strategist", "reasoning": "..."}
{"type": "action", "agent": "Business_Strategist", "output": "STRATEGY: ..."}
{"type": "finish", "data": "Workflow completed successfully"}
```

**API Docs:** `http://localhost:8000/docs`

---

## 📝 Example Queries

- *"Analyze the profit margins for the last quarter"*
- *"What are the revenue trends for Q1 and Q2?"*
- *"Our sales dropped 15% last month. Analyze and suggest recovery strategies."*
- *"Analyze quarterly revenue trends for the past 4 quarters and provide strategic recommendations"*

---

## 📁 Project Structure

```
enterprise-data-analyst-agent/
├── agents/                    # Agent implementations
│   ├── __init__.py           # Agent exports
│   ├── supervisor.py         # Supervisor routing agent (orchestrates workflow)
│   └── worker.py             # Worker agent base classes (Data_Analyst, Business_Strategist)
│
├── api/                       # FastAPI application
│   ├── __init__.py
│   └── routes.py             # API endpoints (/run, /health, /)
│
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py           # Application settings (LLM config, API settings)
│
├── core/                      # Core state management
│   ├── __init__.py
│   └── state.py              # AgentState TypedDict and state utilities
│
├── tools/                     # Analysis tools and security
│   ├── __init__.py
│   ├── analysis_tools.py     # execute_python_analysis tool (with Excel support)
│   └── security.py           # Code safety validation (AST parsing)
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── logging_config.py    # Logging setup
│   └── query_validator.py    # Query validation (absurd/ambiguous detection)
│
├── workflow/                  # Workflow orchestration
│   ├── __init__.py
│   └── team.py               # EnterpriseDataTeam (LangGraph workflow)
│
├── examples/                  # Example files and mock data
│   ├── __init__.py
│   ├── example_usage.py      # Usage examples
│   └── mock_business_data.xlsx  # Mock Excel data (5 sheets: Revenue, Sales, ROI, etc.)
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_agents.py        # Agent unit tests
│   ├── test_api.py           # API integration tests
│   ├── test_workflow.py      # Workflow integration tests
│   ├── test_state.py         # State management tests
│   ├── test_analysis_tools.py # Tool tests
│   └── test_security.py      # Security validation tests
│
├── static/                    # Web interface (minimalist UI)
│   ├── index.html            # Main HTML interface
│   ├── app.js                # Frontend JavaScript (streaming, strategy rendering)
│   └── style.css             # Minimalist styling
│
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── IMPROVEMENTS.md           # V2 roadmap and enhancements
├── LICENSE                    # License file
└── README.md                 # This file
```

### Key Components Explained

- **`agents/`**: Implements the three-agent system (Supervisor, Data_Analyst, Business_Strategist)
- **`workflow/team.py`**: LangGraph orchestration - manages agent routing and state transitions
- **`tools/analysis_tools.py`**: Core analysis tool with Excel data integration (pandas-based)
- **`core/state.py`**: TypedDict-based state management for LangGraph workflows
- **`utils/query_validator.py`**: Prevents absurd queries and detects ambiguous inputs
- **`examples/mock_business_data.xlsx`**: Mock business data with 5 sheets (Quarterly Revenue, Monthly Sales, ROI Analysis, Regional Performance, Summary)
- **`static/`**: Minimalist web interface with real-time streaming and strategy visualization

---

## 🎓 Learning Objectives

This project demonstrates **DeepLearning.AI's Advanced AI** concepts:

1. **Agent Architecture** - Supervisor-worker pattern with specialized roles
2. **Autonomous Decision Making** - Agents routing tasks independently
3. **Tool Integration** - Agents using tools to perform analysis
4. **Workflow Orchestration** - LangGraph managing multi-step workflows
5. **State Management** - Complex state handling across agents
6. **Error Handling** - Robust error handling in agent workflows

---

## 🔧 Configuration

Key settings in `config/settings.py`:

- `MAX_ITERATIONS_DEFAULT`: Maximum workflow iterations (default: 10)
- `MESSAGE_WINDOW`: Conversation history window (default: 8)
- `DEFAULT_MODEL`: LLM model (default: "gpt-4o")

Environment variables:
- `OPENAI_API_KEY`: Required - Your OpenAI API key
- `API_HOST`: Server host (default: "127.0.0.1")
- `API_PORT`: Server port (default: 8000)

---

## 🛡️ Security

- **Code Validation**: AST parsing before execution
- **Forbidden Modules**: Blocks dangerous imports (os, sys, subprocess)
- **Input Validation**: Pydantic models validate all API inputs
- **Sandboxed Execution**: Isolated code execution (mocked in demo)

---

## 🧪 Development

### Adding New Agents

1. Create worker class in `agents/worker.py` extending `WorkerAgent`
2. Add to `VALID_AGENTS` in `config/settings.py`
3. Update supervisor routing in `agents/supervisor.py`
4. Add agent node to workflow graph in `workflow/team.py`

### Adding New Tools

1. Create tool function in `tools/analysis_tools.py` using `@tool` decorator
2. Add security validation if needed using `tools/security.py`
3. Assign the tool to the appropriate agent during agent initialization

---

## 🤝 Contributing

This is a portfolio project. For improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commits
4. Submit a pull request

---

## 🙏 Acknowledgments

- **DeepLearning.AI** - Advanced AI: Agentic AI and Multi-Agents course
- Built with [LangChain](https://www.langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph)
- API framework: [FastAPI](https://fastapi.tiangolo.com/)
- LLM: OpenAI GPT-4

---

## 📄 License

This project is open source and available for portfolio use.

---

**Note**: This is a demonstration system. For production use, implement real sandboxed execution, database persistence, authentication, rate limiting, and comprehensive testing.
