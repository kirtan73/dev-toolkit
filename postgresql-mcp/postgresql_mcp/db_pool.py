"""
PostgreSQL connection pool manager for scalable database access.
Implements connection pooling for efficient resource management.
"""

import asyncpg
from typing import Optional
import structlog
from contextlib import asynccontextmanager

from postgresql_mcp.config import settings

logger = structlog.get_logger(__name__)


class DatabasePool:
    """Manages PostgreSQL connection pool with automatic lifecycle management."""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._dsn = settings.postgres_dsn
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            logger.warning("Pool already initialized")
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=settings.postgres_min_pool_size,
                max_size=settings.postgres_max_pool_size,
                command_timeout=60,
            )
            logger.info(
                "Database pool initialized",
                min_size=settings.postgres_min_pool_size,
                max_size=settings.postgres_max_pool_size,
            )
        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            raise
    
    async def close(self) -> None:
        """Close the connection pool and all connections."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool (context manager)."""
        if self._pool is None:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def fetch(self, query: str, *args) -> list[dict]:
        """
        Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_one(self, query: str, *args) -> Optional[dict]:
        """
        Execute a SELECT query and return first result as dictionary.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Dictionary representing the first row, or None if no results
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute a query (for schema introspection, etc.).
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Query result status
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False


# Global pool instance
db_pool = DatabasePool()

