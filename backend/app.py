"""FastAPI backend API for the Python terminal."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

from terminal import PythonTerminal
from utils import colorize_text


# Pydantic models for API
class ExecRequest(BaseModel):
    cmd: str
    cwd: Optional[str] = None


class ExecResponse(BaseModel):
    stdout: str
    stderr: str
    rc: int
    cwd: str




# FastAPI app
app = FastAPI(
    title="Python Terminal API",
    description="Backend API for Python Command Terminal (Frontend: Streamlit)",
    version="1.0.0"
)

# Global terminal instance
terminal_instance = None


def get_terminal_instance(working_directory: str = None) -> PythonTerminal:
    """Get or create terminal instance."""
    global terminal_instance

    if terminal_instance is None or (working_directory and
                                   str(terminal_instance.working_directory) != working_directory):
        terminal_instance = PythonTerminal(working_directory)

    return terminal_instance


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Python Terminal API",
        "version": "1.0.0",
        "description": "Backend API for Python Command Terminal",
        "frontend": "Use Streamlit frontend at http://localhost:8501",
        "endpoints": {
            "POST /exec": "Execute terminal commands",
            "GET /sysinfo": "Get system information",
            "GET /docs": "API documentation"
        }
    }


@app.post("/exec", response_model=ExecResponse)
async def execute_command(request: ExecRequest):
    """Execute a terminal command."""
    try:
        # Get terminal instance with optional cwd change
        terminal = get_terminal_instance()

        # Handle relative cwd if provided
        if request.cwd:
            # Change to relative path if provided
            cd_result = terminal.execute_command(f"cd {request.cwd}")
            if "Error:" in cd_result:
                # Return error if cd fails
                return ExecResponse(
                    stdout="",
                    stderr=cd_result,
                    rc=1,
                    cwd=str(terminal.working_directory)
                )

        # Execute the actual command
        result = terminal.execute_command(request.cmd)

        # Parse result to separate stdout/stderr (basic approach)
        stdout = ""
        stderr = ""
        rc = 0

        if result:
            # Check for error indicators
            if "Error:" in result or "blocked by sandbox" in result:
                stderr = result
                rc = 1
            else:
                stdout = result
                rc = 0

        # Check if terminal wants to exit
        if terminal.should_exit:
            stdout = "Terminal session ended"
            rc = 0

        return ExecResponse(
            stdout=stdout,
            stderr=stderr,
            rc=rc,
            cwd=str(terminal.working_directory)
        )

    except Exception as e:
        return ExecResponse(
            stdout="",
            stderr=f"Internal error: {str(e)}",
            rc=1,
            cwd="/"
        )


@app.get("/sysinfo")
async def get_system_info():
    """Get system information - same data as CLI sysinfo."""
    try:
        terminal = get_terminal_instance()

        # Use the same get_sysinfo method as CLI
        sysinfo = terminal.system_monitor.get_sysinfo(top_n=5)

        return sysinfo

    except Exception as e:
        return {
            "cpu_percent": 0.0,
            "mem_percent": 0.0,
            "top": [],
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Python Terminal API"}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error"}


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    return app


def run_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Python Terminal Web API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print(f"Starting Python Terminal API on http://{args.host}:{args.port}")
    print("API documentation available at http://{args.host}:{args.port}/docs")

    run_server(host=args.host, port=args.port, debug=args.debug)