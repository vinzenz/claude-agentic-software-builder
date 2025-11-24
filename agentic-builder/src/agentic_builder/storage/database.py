"""SQLite database connection management."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from agentic_builder.core.config import get_db_path
from agentic_builder.storage.schema import SCHEMA_DDL


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Path | None = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Defaults to .agentic/agentic.db
        """
        self.db_path = db_path or get_db_path()
        self._connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Initialize database with schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA_DDL)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection.

        Yields:
            sqlite3.Connection with row factory set to sqlite3.Row
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of sqlite3.Row objects
        """
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_one(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """Execute a query and return single result.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single sqlite3.Row or None
        """
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute a write query and return rows affected.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of rows affected
        """
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount


# Global database instance (lazy init)
_db: Database | None = None


def get_db() -> Database:
    """Get the global database instance.

    Returns:
        Database instance
    """
    global _db
    if _db is None:
        _db = Database()
    return _db
