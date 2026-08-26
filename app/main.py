import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.models.database import init_db
from app.api.router import api_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_revenue_recovery")
settings = get_settings()

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing AI Revenue Recovery database...")
    await init_db()
    logger.info(f"System started successfully in {settings.ENVIRONMENT} mode.")
    yield
    # Shutdown
    logger.info("Shutting down AI Revenue Recovery system...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Revenue Recovery Engine with LangGraph, Guardrails, and Cryptographic Financial Ledger.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API Routers
app.include_router(api_router)


# Web Dashboard UI Route
@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
async def dashboard(request: Request):
    """Renders the real-time AI Revenue Recovery Dashboard."""
    return templates.TemplateResponse("index.html", {"request": request, "settings": settings})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
