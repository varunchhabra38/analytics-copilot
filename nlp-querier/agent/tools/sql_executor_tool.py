"""
SQL Execution tool for the LangGraph Analytics Agent.

This tool executes SQL queries against different database systems including
BigQuery, PostgreSQL, and SQLite with proper error handling and result formatting.
"""
from typing import Any, Dict, Optional, Union
import pandas as pd
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SQLExecutorTool(ABC):
    """
    Abstract base class for SQL execution tools.
    
    Provides interface for executing SQL queries against different
    database systems with consistent error handling.
    """
    
    @abstractmethod
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query string to execute
            
        Returns:
            Dictionary with 'result' (DataFrame) and 'error' keys
        """
        pass


class BigQuerySQLExecutorTool(SQLExecutorTool):
    """
    BigQuery-specific implementation of SQL execution.
    
    Executes queries against Google BigQuery with proper error handling
    and result set management.
    """
    
    def __init__(
        self, 
        project_id: str, 
        credentials_path: Optional[str] = None,
        max_results: int = 10000
    ):
        """
        Initialize BigQuery SQL executor.
        
        Args:
            project_id: Google Cloud project ID
            credentials_path: Path to service account JSON file (optional)
            max_results: Maximum number of rows to return (default: 10000)
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.max_results = max_results
        self._client = None
    
    def _get_client(self):
        """Get BigQuery client, creating if needed."""
        if self._client is None:
            try:
                from google.cloud import bigquery
                from google.auth import load_credentials_from_file
                
                if self.credentials_path:
                    credentials, _ = load_credentials_from_file(self.credentials_path)
                    self._client = bigquery.Client(project=self.project_id, credentials=credentials)
                else:
                    self._client = bigquery.Client(project=self.project_id)
                    
            except ImportError:
                raise ImportError("google-cloud-bigquery is required for BigQuery execution")
            except Exception as e:
                logger.error(f"Failed to create BigQuery client: {e}")
                raise
        return self._client
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute BigQuery SQL query and return results as DataFrame.
        
        Args:
            sql: BigQuery SQL query string
            
        Returns:
            Dictionary with 'result' (DataFrame) and 'error' keys
        """
        try:
            client = self._get_client()
            
            # Validate SQL (basic safety checks)
            sql_upper = sql.upper().strip()
            if any(keyword in sql_upper for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']):
                return {
                    "result": None,
                    "error": "Modification queries (DROP, DELETE, UPDATE, INSERT, CREATE, ALTER) are not allowed"
                }
            
            # Configure job
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = 1024 * 1024 * 1024  # 1 GB limit
            job_config.use_query_cache = True
            
            # Execute query
            logger.info(f"Executing BigQuery SQL: {sql[:100]}...")
            query_job = client.query(sql, job_config=job_config)
            
            # Convert to pandas DataFrame
            df = query_job.to_dataframe(max_results=self.max_results)
            
            logger.info(f"Query completed successfully. Rows returned: {len(df)}")
            
            return {
                "result": df,
                "error": None,
                "metadata": {
                    "total_bytes_processed": query_job.total_bytes_processed,
                    "total_bytes_billed": query_job.total_bytes_billed,
                    "cache_hit": query_job.cache_hit,
                    "job_id": query_job.job_id
                }
            }
            
        except Exception as e:
            error_msg = f"BigQuery execution error: {str(e)}"
            logger.error(error_msg)
            return {
                "result": None,
                "error": error_msg
            }


class PostgreSQLExecutorTool(SQLExecutorTool):
    """
    PostgreSQL-specific implementation of SQL execution.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL executor.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self._connection = None
    
    def _get_connection(self):
        """Get database connection, creating if needed."""
        if self._connection is None:
            try:
                import psycopg2
                self._connection = psycopg2.connect(self.connection_string)
            except ImportError:
                raise ImportError("psycopg2 is required for PostgreSQL connections")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise
        return self._connection
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute PostgreSQL query and return results."""
        try:
            # Validate SQL (basic safety checks)
            sql_upper = sql.upper().strip()
            if any(keyword in sql_upper for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']):
                return {
                    "result": None,
                    "error": "Modification queries are not allowed"
                }
            
            conn = self._get_connection()
            df = pd.read_sql_query(sql, conn)
            
            logger.info(f"PostgreSQL query completed. Rows returned: {len(df)}")
            
            return {
                "result": df,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"PostgreSQL execution error: {str(e)}"
            logger.error(error_msg)
            return {
                "result": None,
                "error": error_msg
            }


class SQLiteExecutorTool(SQLExecutorTool):
    """
    SQLite-specific implementation of SQL execution.
    """
    
    def __init__(self, database_path: str):
        """
        Initialize SQLite executor.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self._connection = None
    
    def _get_connection(self):
        """Get database connection, creating if needed."""
        if self._connection is None:
            try:
                import sqlite3
                self._connection = sqlite3.connect(self.database_path)
            except Exception as e:
                logger.error(f"Failed to connect to SQLite: {e}")
                raise
        return self._connection
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQLite query and return results."""
        try:
            # Validate SQL (basic safety checks)
            sql_upper = sql.upper().strip()
            if any(keyword in sql_upper for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']):
                return {
                    "result": None,
                    "error": "Modification queries are not allowed"
                }
            
            conn = self._get_connection()
            df = pd.read_sql_query(sql, conn)
            
            logger.info(f"SQLite query completed. Rows returned: {len(df)}")
            
            return {
                "result": df,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"SQLite execution error: {str(e)}"
            logger.error(error_msg)
            return {
                "result": None,
                "error": error_msg
            }


def create_sql_executor_tool(db_type: str = "postgresql", **kwargs) -> SQLExecutorTool:
    """
    Factory function to create appropriate SQL executor tool.
    
    Simplified to use only PostgreSQL and SQLite.
    
    Args:
        db_type: Type of database ("postgresql" or "sqlite")
        **kwargs: Database-specific connection parameters
        
    Returns:
        Configured SQL executor tool instance
        
    Raises:
        ValueError: If unsupported db_type is specified
        ImportError: If required dependencies are not available
    """
    if db_type == "postgresql":
        try:
            connection_string = kwargs.get("connection_string")
            if not connection_string:
                raise ValueError("connection_string is required for PostgreSQL")
            
            return PostgreSQLExecutorTool(connection_string=connection_string)
        except ImportError as e:
            logger.warning(f"PostgreSQL dependencies not available: {e}")
            logger.info("Install with: pip install psycopg2-binary")
            raise
    
    elif db_type == "sqlite":
        db_path = kwargs.get("db_path")
        if not db_path:
            raise ValueError("db_path is required for SQLite")
        
        return SQLiteExecutorTool(database_path=db_path)
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Example usage configurations:
#
# For PostgreSQL:
# executor_tool = create_sql_executor_tool(
#     db_type="postgresql",
#     connection_string="postgresql://user:password@localhost:5432/dbname"
# )
#
# For SQLite (development/testing):
# executor_tool = create_sql_executor_tool(
#     db_type="sqlite",
#     db_path="path/to/database.db"
# )