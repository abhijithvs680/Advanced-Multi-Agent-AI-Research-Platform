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
import os
from workers.workflow_worker import WorkflowWorker

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

    # Set main event loop for WebSockets
    import asyncio
    from api.routes.websocket import set_main_loop
    set_main_loop(asyncio.get_running_loop())
    
    # Initialize job queue
    job_queue = get_job_queue()
    if job_queue.health_check():
        logger.info("job_queue_initialized")
    else:
        logger.error("job_queue_initialization_failed")

    # Start Workflow Workers in background
    num_workers = int(os.getenv("NUM_WORKERS", "2"))
    config_path = os.getenv("CONFIG_PATH", "/app/config/config.yaml")
    
    logger.info("starting_workflow_workers", count=num_workers)
    app.state.workers = [
        WorkflowWorker(worker_id=i, config_path=config_path)
        for i in range(num_workers)
    ]
    
    # Start worker run loops as background tasks
    app.state.worker_tasks = [
        asyncio.create_task(worker.run())
        for worker in app.state.workers
    ]
    
    yield
    
    # Shutdown
    logger.info("api_server_shutting_down")
    
    # Stop workers
    if hasattr(app.state, 'workers'):
        for worker in app.state.workers:
            worker.stop()
    
    if hasattr(app.state, 'worker_tasks'):
        for task in app.state.worker_tasks:
            task.cancel()
            
    logger.info("workers_stopped")


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
