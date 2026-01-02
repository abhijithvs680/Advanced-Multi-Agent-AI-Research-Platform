"""
FastAPI application setup and configuration.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from shared.logger import get_logger
from shared.database import get_db_manager
from shared.queue import get_job_queue

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown logic.
    """
    # Startup
    logger.info("api_server_starting")
    
    # Initialize database
    db_manager = get_db_manager()
    db_manager.create_tables()
    logger.info("database_initialized")
    
    # Initialize job queue
    job_queue = get_job_queue()
    if job_queue.health_check():
        logger.info("job_queue_initialized")
    else:
        logger.error("job_queue_initialization_failed")
    
    yield
    
    # Shutdown
    logger.info("api_server_shutting_down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Multi-Agent Research Platform API",
        description="API for managing autonomous AI research workflows",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None
        )
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            "api_response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "api_unhandled_exception",
            path=request.url.path,
            error=str(exc),
            exc_type=type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            }
        )
    
    # Register routes
    from api.routes import jobs, health, websocket
    
    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
    app.include_router(health.router, tags=["health"])
    app.include_router(websocket.router, tags=["websocket"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "Multi-Agent Research Platform",
            "version": "1.0.0",
            "status": "running"
        }
    
    return app


# Create application instance
app = create_app()
