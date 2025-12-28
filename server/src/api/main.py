"""FastAPI application."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.auth import APIKeyInfo, require_auth
from src.billing import UsageInfo, get_usage_stats, require_rate_limit
from src.config import settings
from src.db import init_db

logger = logging.getLogger(__name__)

# Paths
SRC_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = SRC_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.app_debug else None,
    redoc_url=None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def get_template_context(request: Request, **kwargs) -> dict[str, Any]:
    """Build template context with common variables."""
    return {
        "request": request,
        "app_name": settings.app_name,
        "current_year": datetime.now().year,
        **kwargs,
    }


# =============================================================================
# Health & Info
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.app_environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/info")
async def api_info():
    """API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "Lautrek Product API",
    }


# =============================================================================
# Landing Pages (if templates exist)
# =============================================================================


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    if templates:
        return templates.TemplateResponse("pages/home.html", get_template_context(request))
    return JSONResponse({"message": f"Welcome to {settings.app_name}"})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Pricing page."""
    if templates:
        return templates.TemplateResponse("pages/pricing.html", get_template_context(request))
    return JSONResponse({"message": "Pricing page"})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page."""
    if templates:
        return templates.TemplateResponse("pages/login.html", get_template_context(request))
    return JSONResponse({"message": "Login page"})


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    """Signup page."""
    if templates:
        return templates.TemplateResponse("pages/signup.html", get_template_context(request))
    return JSONResponse({"message": "Signup page"})


# =============================================================================
# API Routes
# =============================================================================


class StatusResponse(BaseModel):
    status: str
    tools: list[str]


@app.get("/api/v1/tools/status", response_model=StatusResponse)
async def tools_status(user: APIKeyInfo = Depends(require_auth)):
    """Get available tools."""
    return StatusResponse(
        status="ok",
        tools=["example-tool"],  # Add your tools here
    )


class ExampleToolRequest(BaseModel):
    param1: str
    param2: int = 10


class ExampleToolResponse(BaseModel):
    status: str
    result: dict


@app.post("/api/v1/tools/example-tool", response_model=ExampleToolResponse)
async def example_tool(
    body: ExampleToolRequest,
    user: APIKeyInfo = Depends(require_auth),
    usage: UsageInfo = Depends(require_rate_limit),
):
    """Example tool endpoint - replace with your product tools."""
    # Your business logic here
    result = {
        "param1": body.param1,
        "param2": body.param2,
        "processed": True,
    }
    return ExampleToolResponse(status="success", result=result)


@app.get("/api/v1/usage")
async def get_usage(user: APIKeyInfo = Depends(require_auth)):
    """Get current usage stats."""
    return get_usage_stats(user.user_id, user.tier)


# =============================================================================
# Error Handlers
# =============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception(f"Unhandled error: {exc}")
    if settings.app_debug:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
