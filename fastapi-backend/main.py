"""
JobHunt API — FastAPI application entry point.
A job aggregation platform that scrapes real job postings
from multiple trusted job boards and surfaces direct links.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import jobs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="JobHunt API",
    description="Job aggregation platform — scrapes multiple job boards and returns unified, deduplicated results with direct apply links.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — read from ALLOWED_ORIGINS env var (comma-separated) for production,
# fall back to localhost defaults for local development
_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
_env_origins = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include job search routes
app.include_router(jobs_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "JobHunt API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "search": "POST /api/jobs/search",
            "stream": "POST /api/jobs/search/stream",
            "sources": "GET /api/jobs/sources",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
