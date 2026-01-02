"""
Main service entry point - runs API server and workflow workers.
"""
import asyncio
import signal
import sys
import os
from threading import Thread
from typing import List
import uvicorn

from workers.workflow_worker import WorkflowWorker
from shared.logger import get_logger
from shared.database import get_db_manager

logger = get_logger(__name__)


class ResearchPlatformService:
    """Main service orchestrator"""
    
    def __init__(
        self,
        num_workers: int = None,
        api_host: str = "0.0.0.0",
        api_port: int = 8000,
        config_path: str = "/app/config/config.yaml"
    ):
        """
        Initialize research platform service.
        
        Args:
            num_workers: Number of workflow workers (defaults to CPU count)
            api_host: API server host
            api_port: API server port
            config_path: Path to configuration file
        """
        self.num_workers = num_workers or min(os.cpu_count() or 1, 4)
        self.api_host = api_host
        self.api_port = api_port
        self.config_path = config_path
        
        self.workers: List[WorkflowWorker] = []
        self.running = False
        self.api_server: Thread = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(
            "service_initialized",
            num_workers=self.num_workers,
            api_host=api_host,
            api_port=api_port
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("shutdown_signal_received", signal=signum)
        self.stop()
    
    def start_api_server(self):
        """Start FastAPI server in separate thread"""
        logger.info("starting_api_server", host=self.api_host, port=self.api_port)
        
        # Check if reload is enabled (for development)
        reload_enabled = os.getenv("RELOAD_ENABLED", "false").lower() == "true"
        
        try:
            uvicorn.run(
                "api.server:app",
                host=self.api_host,
                port=self.api_port,
                log_level="info",
                access_log=False,
                reload=reload_enabled,
                reload_dirs=["/app"] if reload_enabled else None
            )
        except Exception as e:
            logger.error("api_server_failed", error=str(e))
    
    async def start_workers(self):
        """Start workflow worker pool"""
        logger.info("starting_worker_pool", num_workers=self.num_workers)
        
        # Create workers
        self.workers = [
            WorkflowWorker(worker_id=i, config_path=self.config_path)
            for i in range(self.num_workers)
        ]
        
        # Start workers concurrently
        worker_tasks = [worker.run() for worker in self.workers]
        await asyncio.gather(*worker_tasks)
    
    async def run(self):
        """Main service loop (API only, workers started via lifespan)"""
        self.running = True
        
        logger.info("research_platform_service_starting")
        
        # Initialize database tables
        db_manager = get_db_manager()
        db_manager.create_tables()
        logger.info("database_tables_verified")
        
        # Start API server in main thread
        # Note: Workers are now started in api.server.lifespan
        self.start_api_server()
    
    def stop(self):
        """Stop the service"""
        if not self.running:
            return
        
        logger.info("service_stopping")
        self.running = False
        sys.exit(0)


async def main():
    """Main entry point for production"""
    # Get configuration from environment
    num_workers = int(os.getenv("NUM_WORKERS", "2"))
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    config_path = os.getenv("CONFIG_PATH", "/app/config/config.yaml")
    
    # Create and run service
    service = ResearchPlatformService(
        num_workers=num_workers,
        api_host=api_host,
        api_port=api_port,
        config_path=config_path
    )
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
        service.stop()
    except Exception as e:
        logger.error("service_fatal_error", error=str(e))
        service.stop()
        sys.exit(1)


def dev_main():
    """Main entry point for development (reload enabled)"""
    num_workers = int(os.getenv("NUM_WORKERS", "2"))
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    config_path = os.getenv("CONFIG_PATH", "/app/config/config.yaml")

    service = ResearchPlatformService(
        num_workers=num_workers,
        api_host=api_host,
        api_port=api_port,
        config_path=config_path
    )
    
    # Run API server in main thread (blocking)
    # Note: Workers are now started in api.server.lifespan
    service.start_api_server()


if __name__ == "__main__":
    if os.getenv("RELOAD_ENABLED", "false").lower() == "true":
        dev_main()
    else:
        asyncio.run(main())
