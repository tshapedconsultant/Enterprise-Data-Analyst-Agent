"""
FastAPI routes for the Enterprise Data Analyst Agent API.

This module defines the REST API endpoints for interacting with the
multi-agent data analysis system.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Generator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os

from workflow import EnterpriseDataTeam
from config import CORS_ORIGINS, MESSAGE_WINDOW, MAX_ITERATIONS_DEFAULT
from utils.query_validator import is_query_absurd, is_query_too_ambiguous

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Data Analyst Agent",
    description="Multi-agent data analysis system with supervisor-worker pattern",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for workflow execution."""
    query: str = Field(
        ...,
        description="User query to process through the multi-agent system",
        min_length=1,
        max_length=5000
    )
    max_iterations: int = Field(
        default=MAX_ITERATIONS_DEFAULT,
        description="Maximum number of workflow iterations",
        ge=1,
        le=50
    )
    message_window: int = Field(
        default=MESSAGE_WINDOW,
        description="Number of messages to keep in conversation history",
        ge=1,
        le=50
    )


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status and server information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@app.post("/run")
async def run_workflow(request: QueryRequest):
    """
    Execute the multi-agent workflow and stream results.
    
    This endpoint processes a user query through the supervisor-worker
    multi-agent system and streams events as they occur. Events are
    returned as NDJSON (newline-delimited JSON) for easy parsing.
    
    Args:
        request: QueryRequest containing the user query and optional parameters
        
    Returns:
        StreamingResponse with NDJSON events
        
    Example:
        POST /run
        {
            "query": "Analyze the revenue trends for Q1 and Q2",
            "max_iterations": 10,
            "message_window": 8
        }
    """
    try:
        # Validate query before processing
        is_absurd, absurd_reason = is_query_absurd(request.query)
        if is_absurd:
            logger.warning(f"Rejected absurd query: {request.query[:50]}... Reason: {absurd_reason}")
            raise HTTPException(
                status_code=400,
                detail=f"Query rejected: {absurd_reason}. Please provide a valid data analysis question."
            )
        
        # Check if query is too ambiguous (warn but allow)
        is_ambiguous, ambiguity_suggestion = is_query_too_ambiguous(request.query)
        if is_ambiguous:
            logger.info(f"Ambiguous query detected: {request.query}. Suggestion: {ambiguity_suggestion}")
            # Don't reject, but log for monitoring
        
        # Initialize the agent team with custom parameters
        agent_team = EnterpriseDataTeam(
            max_iterations=request.max_iterations,
            message_window=request.message_window
        )
        
        # Create async generator for streaming
        # This wraps the synchronous workflow stream into an async generator
        # that can be consumed by FastAPI's StreamingResponse
        async def event_generator() -> Generator[str, None, None]:
            """
            Async generator that wraps the synchronous workflow stream.
            
            Converts synchronous workflow events into async NDJSON stream
            for real-time client updates.
            
            Yields:
                JSON-encoded event strings (NDJSON format - newline-delimited JSON)
            """
            try:
                # Stream workflow events from the multi-agent team
                # Each event represents a step in the workflow (decision, action, etc.)
                for event in agent_team.run_stream(request.query):
                    # Small delay for better UX (prevents overwhelming the client)
                    # Also allows for smoother streaming experience
                    await asyncio.sleep(0.1)
                    
                    # Serialize event to JSON
                    try:
                        event_json = json.dumps(event, default=str)
                        yield event_json + "\n"
                    except Exception as e:
                        logger.exception("Event serialization failed")
                        error_event = {
                            "type": "error",
                            "time": datetime.utcnow().isoformat(),
                            "error": f"Event serialization failed: {str(e)}"
                        }
                        yield json.dumps(error_event) + "\n"
                        
            except asyncio.CancelledError:
                logger.info("Client disconnected during streaming")
                return
            except Exception as e:
                logger.exception("Streaming generator failed")
                error_event = {
                    "type": "error",
                    "time": datetime.utcnow().isoformat(),
                    "error": f"Server streaming error: {str(e)}"
                }
                yield json.dumps(error_event) + "\n"
        
        # Return streaming response
        return StreamingResponse(
            event_generator(),
            media_type="application/x-ndjson",
            headers={
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.exception("Workflow execution failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute workflow: {str(e)}"
        )


# Mount static files for the web interface
# Get the project root directory (parent of api directory)
_api_file_path = os.path.abspath(__file__)
_api_dir = os.path.dirname(_api_file_path)
_project_root = os.path.dirname(_api_dir)
static_dir = os.path.join(_project_root, "static")

# Normalize the path to handle any path issues
static_dir = os.path.normpath(static_dir)

# Store static_dir for use in routes
STATIC_DIR = static_dir

# Mount static files if directory exists
if os.path.exists(static_dir):
    # Mount CSS and JS files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static directory not found at: {static_dir}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Root endpoint - serves the web interface.
    
    Returns:
        HTML file for the web interface
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    
    # Debug logging
    logger.info(f"Root endpoint called")
    logger.info(f"Looking for index.html at: {index_path}")
    logger.info(f"File exists: {os.path.exists(index_path)}")
    
    if os.path.exists(index_path):
        try:
            # Read the HTML file and return it
            with open(index_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            logger.info(f"Successfully loaded index.html ({len(html_content)} bytes)")
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error reading index.html: {e}")
            return HTMLResponse(
                content=f"<h1>Error loading interface</h1><p>{str(e)}</p>",
                status_code=500
            )
    else:
        # Fallback to API info if static files not found
        logger.error(f"index.html not found at: {index_path}")
        logger.error(f"Static directory: {STATIC_DIR}")
        logger.error(f"Project root: {_project_root}")
        # Return HTML with error message
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Interface Not Found</title></head>
        <body>
            <h1>Web Interface Not Found</h1>
            <p>Expected path: {index_path}</p>
            <p>Static directory: {STATIC_DIR}</p>
            <p>Please ensure static/index.html exists.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=404)

