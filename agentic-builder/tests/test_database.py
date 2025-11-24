"""Tests for database operations."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentic_builder.storage.database import Database, get_db


class TestDatabase:
    """Test database management."""

    def test_database_initialization(self):
        """Test database initialization with schema."""
        # The isolate_database fixture already creates and initializes a database
        # We just need to verify that tables were created correctly
        from agentic_builder.storage.database import get_db
        db = get_db()

        with db.connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                'workflow_runs', 'workflow_stages', 'tasks', 'task_dependencies',
                'task_context', 'task_outputs', 'agent_instances', 'artifacts',
                'token_usage', 'config'
            ]

            for table in expected_tables:
                assert table in tables, f"Table {table} not created"

            # Check that tables were created
            with db.connection() as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                expected_tables = [
                    'workflow_runs', 'workflow_stages', 'tasks', 'task_dependencies',
                    'task_context', 'task_outputs', 'agent_instances', 'artifacts',
                    'token_usage', 'config'
                ]

                for table in expected_tables:
                    assert table in tables, f"Table {table} not created"

    def test_connection_context_manager(self):
        """Test database connection context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Test successful operation
            with db.connection() as conn:
                conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", ("test_key", "test_value"))
                # Should commit automatically

            # Verify the insert worked
            with db.connection() as conn:
                cursor = conn.execute("SELECT value FROM config WHERE key = ?", ("test_key",))
                row = cursor.fetchone()
                assert row[0] == "test_value"

    def test_connection_rollback_on_error(self):
        """Test that connection rolls back on exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Get initial count
            with db.connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM config")
                initial_count = cursor.fetchone()[0]

            # Test rollback on exception
            try:
                with db.connection() as conn:
                    conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", ("rollback_test", "value"))
                    raise Exception("Test exception")
            except Exception:
                pass  # Expected

            # Verify rollback worked - count should be unchanged
            with db.connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM config")
                final_count = cursor.fetchone()[0]
                assert final_count == initial_count

    def test_execute_query(self):
        """Test basic query execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Insert test data
            db.execute_write("INSERT INTO config (key, value) VALUES (?, ?)", ("test_key", "test_value"))

            # Query data
            rows = db.execute("SELECT * FROM config WHERE key = ?", ("test_key",))
            assert len(rows) == 1
            assert rows[0]["key"] == "test_key"
            assert rows[0]["value"] == "test_value"

    def test_execute_one_query(self):
        """Test single row query execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Insert test data
            db.execute_write("INSERT INTO config (key, value) VALUES (?, ?)", ("single_key", "single_value"))

            # Query single row
            row = db.execute_one("SELECT * FROM config WHERE key = ?", ("single_key",))
            assert row is not None
            assert row["key"] == "single_key"
            assert row["value"] == "single_value"

            # Query non-existent row
            row = db.execute_one("SELECT * FROM config WHERE key = ?", ("nonexistent",))
            assert row is None

    def test_execute_write(self):
        """Test write query execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Insert data
            affected = db.execute_write("INSERT INTO config (key, value) VALUES (?, ?)", ("write_key", "write_value"))
            assert affected == 1

            # Update data
            affected = db.execute_write("UPDATE config SET value = ? WHERE key = ?", ("updated_value", "write_key"))
            assert affected == 1

            # Delete data
            affected = db.execute_write("DELETE FROM config WHERE key = ?", ("write_key",))
            assert affected == 1

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            db.initialize()

            # Try to insert task with non-existent workflow
            with pytest.raises(sqlite3.IntegrityError):
                db.execute_write(
                    "INSERT INTO tasks (id, workflow_run_id, title, agent_type, status) VALUES (?, ?, ?, ?, ?)",
                    ("task1", "nonexistent_workflow", "Test Task", "PM", "pending")
                )


class TestGlobalDatabase:
    """Test global database instance management."""

    def test_get_db_returns_instance(self):
        """Test that get_db returns a Database instance."""
        with patch('agentic_builder.storage.database._db', None):
            with patch('agentic_builder.core.config.get_db_path', return_value=Path("/tmp/test.db")):
                db = get_db()
                assert isinstance(db, Database)

    def test_get_db_caching(self):
        """Test that get_db caches the instance."""
        with patch('agentic_builder.storage.database._db', None):
            with patch('agentic_builder.core.config.get_db_path', return_value=Path("/tmp/test.db")):
                db1 = get_db()
                db2 = get_db()
                assert db1 is db2  # Same instance


class TestDatabasePath:
    """Test database path handling."""

    def test_custom_db_path(self):
        """Test using a custom database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom.db"
            db = Database(custom_path)

            assert db.db_path == custom_path

            # Initialize and verify file creation
            db.initialize()
            assert custom_path.exists()

    def test_db_path_creation(self):
        """Test that database directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dirs" / "database.db"
            db = Database(nested_path)

            # Directory shouldn't exist yet
            assert not nested_path.parent.exists()

            # Initialize should create directories
            db.initialize()
            assert nested_path.parent.exists()
            assert nested_path.exists()