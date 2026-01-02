"""
Database session management and utilities.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
import os
from typing import Generator

from shared.models import Base
from shared.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL (defaults to env var DATABASE_URL)
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://research:research@postgres:5432/research_db"
        )
        self.echo = echo
        
        # Configure engine based on environment
        pool_class = QueuePool if "postgresql" in self.database_url else NullPool
        
        self.engine = create_engine(
            self.database_url,
            echo=self.echo,
            poolclass=pool_class,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
        )
        
        # Add connection event listeners for better error handling
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("database_connection_established")
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("database_initialized", url=self.database_url.split("@")[-1])
    
    def create_tables(self):
        """Create all tables in the database"""
        logger.info("creating_database_tables")
        Base.metadata.create_all(bind=self.engine)
        logger.info("database_tables_created")
    
    def drop_tables(self):
        """Drop all tables in the database (use with caution!)"""
        logger.warning("dropping_database_tables")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("database_tables_dropped")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                job = session.query(Job).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """
        Check if database is healthy and accessible.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage in FastAPI:
        @app.get("/jobs")
        async def list_jobs(db: Session = Depends(get_db_session)):
            jobs = db.query(Job).all()
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session
