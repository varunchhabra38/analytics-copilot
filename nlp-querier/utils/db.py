"""
Database utilities for the NLP Querier Analytics Agent.

Provides simplified database connection management for PostgreSQL.
"""
import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Simplified database connection manager for PostgreSQL.
    
    Handles connection pooling and provides context managers for
    safe database operations.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize database manager.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self._connection = None
    
    def test_connection(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            import psycopg2
            
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            logger.info("Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            Database connection object
        """
        conn = None
        try:
            import psycopg2
            
            conn = psycopg2.connect(self.connection_string)
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            
        Returns:
            Dictionary with results and metadata
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Fetch results
                rows = cursor.fetchall()
                
                cursor.close()
                
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows)
                }
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "rows": [],
                "row_count": 0
            }


# Legacy Database class for backwards compatibility
class Database:
    """Legacy SQLite database class for backwards compatibility."""
    
    def __init__(self, db_path: str):
        """Initialize the Database connection."""
        import sqlite3
        import pandas as pd
        
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)

    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return the results as a DataFrame."""
        import pandas as pd
        
        with self.connection:
            df = pd.read_sql_query(query, self.connection, params=params)
        return df

    def close_connection(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()


def create_database_manager(connection_string: Optional[str] = None) -> DatabaseManager:
    """
    Create database manager from configuration.
    
    Args:
        connection_string: Optional connection string, defaults to DATABASE_URL env var
        
    Returns:
        Configured DatabaseManager instance
        
    Raises:
        ValueError: If no connection string provided
    """
    if not connection_string:
        connection_string = os.getenv("DATABASE_URL")
    
    if not connection_string:
        raise ValueError("Database connection string is required")
    
    return DatabaseManager(connection_string)


# Example usage:
#
# from utils.db import create_database_manager
#
# db_manager = create_database_manager()
# 
# # Test connection
# if db_manager.test_connection():
#     print("Database connected successfully")
#
# # Execute query
# result = db_manager.execute_query("SELECT * FROM users LIMIT 10")
# if result["success"]:
#     print(f"Found {result['row_count']} rows")
# else:
#     print(f"Query failed: {result['error']}")