"""
Main FastAPI application.
Configures middleware, routers, and lifespan events.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db, get_engine
from app.routers import auth, upload, chat, admin
from app.utils.logger import setup_logging

# Initialize logging
logger = setup_logging(settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting application")
    
    # Initialize database tables
    await init_db()
    
    # Create default admin user if not exists
    from sqlalchemy import select
    from app.core.database import get_session_factory
    from app.models.user import User
    from app.core.security import get_password_hash
    
    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.email == "admin@demo.com"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                email="admin@demo.com",
                hashed_password=get_password_hash("Admin@123"),
                role="admin"
            )
            session.add(admin_user)
            await session.commit()
            logger.info("Created default admin user")
    
    logger.info("Application started successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Indian SME Document Intelligence RAG",
    description="Multi-tenant RAG system for GST invoices, contracts, and legal documents",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )


# Include routers with API v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Indian SME Document Intelligence RAG API",
        "docs": "/api/docs",
        "health": "/api/health"
    }
