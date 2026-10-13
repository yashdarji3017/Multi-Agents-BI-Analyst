"""Main application entry point for BusinessInsight AI."""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from businessinsight.api import router
from businessinsight.config import settings

app = FastAPI(
    title="BusinessInsight AI - Multi-Agent Business Intelligence Analyst",
    description=(
        "Production-grade Multi-Agent Business Intelligence Analyst powered by "
        "Microsoft Agent Framework (MAF) and Google Gemini. "
        "Analyzes sales trends, underperforming products, territorial shifts, "
        "verifies findings deterministically, and produces C-suite executive reports. "
        "Strictly runs in-memory without any database dependency."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


def start_api() -> None:
    """CLI script entrypoint to start FastAPI uvicorn server."""
    import uvicorn

    print(f"🚀 Starting BusinessInsight AI API at http://{settings.api_host}:{settings.api_port}")
    print("📁 Processing datasets in-memory (No database required).")
    uvicorn.run(
        "businessinsight.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


def start_dashboard() -> None:
    """CLI script entrypoint to launch Streamlit dashboard."""
    import subprocess
    from pathlib import Path

    dashboard_file = Path(__file__).parent.parent.parent / "frontend" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_file),
        "--server.port",
        str(settings.streamlit_server_port),
    ]
    print(f"📊 Launching BusinessInsight AI Streamlit Dashboard on port {settings.streamlit_server_port}...")
    subprocess.run(cmd)


if __name__ == "__main__":
    start_api()
