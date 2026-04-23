"""
api/main.py — FastAPI application entry point.

Serves:
  - API routes: /evaluate, /compare, /health
  - React SPA: everything else → frontend/dist/index.html

Run with:
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from api.routes.evaluate import router as evaluate_router
from api.routes.compare import router as compare_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Path to the built React app
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate config on startup."""
    try:
        settings.validate()
        logger.info("✅ Config validated — API key present.")
        if FRONTEND_DIST.exists():
            logger.info("✅ Serving React build from: %s", FRONTEND_DIST)
        else:
            logger.warning("⚠ frontend/dist not found — run `npm run build` in frontend/")
    except EnvironmentError as e:
        logger.error("❌ Startup failed: %s", e)
        raise
    yield
    logger.info("🛑 Shutting down AI Resume Evaluator API.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Resume Evaluator API",
    description=(
        "Evidence-based resume scoring engine. "
        "Every point awarded is backed by a verbatim quote from the resume."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Wide-open CORS for public deployment (tunnel or hosted)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API Routes (registered BEFORE static files to avoid shadowing)
# ---------------------------------------------------------------------------

app.include_router(evaluate_router, tags=["Evaluation"])
app.include_router(compare_router, tags=["Comparison"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe."""
    return {"status": "ok", "version": app.version}


# ---------------------------------------------------------------------------
# Serve React SPA (static assets + catch-all for client-side routing)
# ---------------------------------------------------------------------------

if FRONTEND_DIST.exists():
    # Serve /assets/* (JS, CSS, images)
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react(full_path: str):
        """
        Catch-all: return index.html for any non-API path.
        Enables React Router client-side navigation on direct URL access.
        """
        index = FRONTEND_DIST / "index.html"
        return FileResponse(str(index))
