"""
Main entry point for the Enterprise Data Analyst Agent.

This module starts the FastAPI server and initializes the application.
Run this file to start the API server.

SECURITY: API keys are loaded from environment variables (.env file).
Never commit API keys to version control.
"""

import logging
import sys
import uvicorn
from utils import setup_logging
from config import API_HOST, API_PORT, validate_api_keys
from api import app

# Setup logging
logger = setup_logging()


def main():
    """
    Start the FastAPI server.
    
    This function validates API keys, initializes and runs the uvicorn server
    with the configured host and port.
    
    Raises:
        SystemExit: If required API keys are missing
    """
    # Validate API keys before starting server
    is_valid, missing_keys = validate_api_keys()
    
    if not is_valid:
        logger.error("=" * 80)
        logger.error("ERROR: Required API keys are missing!")
        logger.error("=" * 80)
        logger.error("Missing API keys:")
        for key in missing_keys:
            logger.error(f"  - {key}")
        logger.error("")
        logger.error("Please set the required API keys:")
        logger.error("  1. Copy .env.example to .env")
        logger.error("  2. Edit .env and add your API keys")
        logger.error("  3. Or set environment variables directly")
        logger.error("")
        logger.error("Example:")
        logger.error('  export OPENAI_API_KEY="your-key-here"')
        logger.error("=" * 80)
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Starting Enterprise Data Analyst Agent API server")
    logger.info("=" * 80)
    logger.info(f"Server will be available at http://{API_HOST}:{API_PORT}")
    logger.info(f"API documentation available at http://{API_HOST}:{API_PORT}/docs")
    logger.info("=" * 80)
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()

