"""
AI Planet - Full Stack Application
Main FastAPI application with PostgreSQL and Gemini AI integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import warnings
import logging
from pathlib import Path

# Import configuration and database
from app.core.config import settings
from app.core.database import check_db_connection, create_tables

# Import API routers
from app.api.V1.auth import router as auth_router
# Fixed import
from app.api.V1.docs import router as docs_router
from app.api.V1.workflows import router as wf_router
from app.api.V1.chat import router as chat_router
from app.api.V1.search import router as search_router
from app.api.V1.users import router as users_router
from app.api.V1.analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "True"
warnings.filterwarnings("ignore", message=".*telemetry.*")
warnings.filterwarnings("ignore", message=".*capture.*")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("🚀 Starting AI Planet application...")
    
    # Check database connection
    logger.info("🔍 Checking database connection...")
    if await check_db_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Upload directory: {upload_dir}")
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI Planet application...")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-stack AI-powered document processing and workflow automation platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(docs_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(wf_router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

# Compatibility routes for old frontend URLs
app.include_router(docs_router, prefix="/docs", tags=["Documents-Compat"], include_in_schema=False)
app.include_router(wf_router, prefix="/workflow", tags=["Workflows-Compat"], include_in_schema=False)

@app.get("/")
async def root():
    """
    Root endpoint with application information
    """
    return {
        "status": "healthy",
        "service": "AI Planet - Full Stack Application",
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "docs": "/api/docs",
        "features": [
            "Document Processing with Gemini AI",
            "Workflow Automation", 
            "Intelligent Chat Interface",
            "Advanced Search & Analytics",
            "User Management",
            "PostgreSQL Database"
        ]
    }

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    db_status = "healthy" if await check_db_connection() else "unhealthy"
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "services": {
            "database": db_status,
            "api": "healthy",
            "gemini": "configured" if settings.GEMINI_API_KEY else "not_configured"
        },
        "timestamp": "2024-01-01T00:00:00Z"  # Will be dynamic in production
    }

@app.get("/api/info")
async def app_info():
    """
    Application information endpoint
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "debug": settings.DEBUG,
        "features": {
            "authentication": True,
            "document_processing": True,
            "workflow_automation": True,
            "chat_interface": True,
            "search_functionality": True,
            "analytics": True,
            "gemini_ai": bool(settings.GEMINI_API_KEY),
            "postgresql": True
        }
    }
