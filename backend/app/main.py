"""FastAPI main application."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.app.api.v1 import jobs, resumes, projects, skills, experience, analytics, resume_generation, ai_skills, ai_bullets, google_sheets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    yield
    # Shutdown
    pass


app = FastAPI(
    title="ATS Pipeline API",
    description="REST API for ATS Pipeline job application management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Next.js fallback port
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])
app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(skills.router, prefix="/api/v1", tags=["skills"])
app.include_router(experience.router, prefix="/api/v1", tags=["experience"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(resume_generation.router, prefix="/api/v1", tags=["resume-generation"])
app.include_router(ai_skills.router, prefix="/api/v1", tags=["ai-skills"])
app.include_router(ai_bullets.router, prefix="/api/v1", tags=["ai-bullets"])
app.include_router(google_sheets.router, prefix="/api/v1", tags=["google-sheets"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ATS Pipeline API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
