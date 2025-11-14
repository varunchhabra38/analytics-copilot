"""
Schema Lookup Tool for Analytics Agent.
Retrieves database schema information for SQL generation.
"""

from typing import Dict, Any
import logging
from config import get_database_manager

logger = logging.getLogger(__name__)


class SchemaLookupTool:
    """Tool for retrieving database schema information."""
    
    def __init__(self):
        """Initialize the schema lookup tool."""
        self.name = "schema_lookup"
        self.description = "Get database schema information for SQL generation"
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve database schema information.
        
        Args:
            input_data: Input parameters (currently unused)
            
        Returns:
            Dictionary containing schema information
        """
        try:
            # Get database manager
            db_manager = get_database_manager()
            
            # Get schema information
            schema = db_manager.get_schema()
            
            if db_manager:
                db_manager.disconnect()
            
            return {
                "success": True,
                "schema": schema,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Schema lookup error: {e}")
            return {
                "success": False,
                "schema": "",
                "error": str(e)
            }
from typing import Dict, List, Optional, Any
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SchemaLookupTool(ABC):
    """
    Abstract base class for database schema discovery tools.
    
    Provides interface for retrieving schema information from different
    database systems (PostgreSQL, MySQL, SQLite, etc.).
    """
    
    @abstractmethod
    def get_schema(self, table_filter: Optional[str] = None) -> str:
        """
        Retrieve formatted schema information.
        
        Args:
            table_filter: Optional filter for specific tables
            
        Returns:
            Formatted schema string with table and column information
        """
        pass
    
    @abstractmethod
    def get_table_names(self) -> List[str]:
        """Get list of available table names."""
        pass
    
    @abstractmethod
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific table."""
        pass


class PostgreSQLSchemaLookupTool(SchemaLookupTool):
    """
    PostgreSQL-specific implementation of schema lookup.
    
    Retrieves schema information from PostgreSQL databases using
    information_schema queries.
    """
    
    def __init__(self, connection_string: str, schema_name: str = "public"):
        """
        Initialize PostgreSQL schema lookup tool.
        
        Args:
            connection_string: Database connection string
            schema_name: Schema name to query (default: "public")
        """
        self.connection_string = connection_string
        self.schema_name = schema_name
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
    
    def get_schema(self, table_filter: Optional[str] = None) -> str:
        """
        Retrieve formatted PostgreSQL schema information.
        
        Args:
            table_filter: Optional SQL LIKE pattern for table names
            
        Returns:
            Formatted schema string with table and column details
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Query to get table and column information
            query = """
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                tc.constraint_type
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c 
                ON t.table_name = c.table_name 
                AND t.table_schema = c.table_schema
            LEFT JOIN information_schema.table_constraints tc 
                ON t.table_name = tc.table_name 
                AND t.table_schema = tc.table_schema
            LEFT JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name 
                AND c.column_name = kcu.column_name
            WHERE t.table_schema = %s
            AND t.table_type = 'BASE TABLE'
            """
            
            params = [self.schema_name]
            
            if table_filter:
                query += " AND t.table_name LIKE %s"
                params.append(f"%{table_filter}%")
            
            query += " ORDER BY t.table_name, c.ordinal_position"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return self._format_schema_results(results)
            
        except Exception as e:
            logger.error(f"Error retrieving schema: {e}")
            return f"Error retrieving schema: {str(e)}"
    
    def get_table_names(self) -> List[str]:
        """Get list of available PostgreSQL table names."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, [self.schema_name])
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error retrieving table names: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific PostgreSQL table."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, [self.schema_name, table_name])
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3],
                    'max_length': row[4]
                })
            
            # Get constraints
            cursor.execute("""
                SELECT 
                    tc.constraint_type,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = %s AND tc.table_name = %s
            """, [self.schema_name, table_name])
            
            constraints = {}
            for row in cursor.fetchall():
                constraint_type = row[0]
                column_name = row[1]
                if constraint_type not in constraints:
                    constraints[constraint_type] = []
                constraints[constraint_type].append(column_name)
            
            return {
                'table_name': table_name,
                'columns': columns,
                'constraints': constraints
            }
            
        except Exception as e:
            logger.error(f"Error retrieving table info for {table_name}: {e}")
            return {}
    
    def _format_schema_results(self, results: List[tuple]) -> str:
        """Format schema query results into readable text."""
        if not results:
            return "No tables found in the specified schema."
        
        schema_text = f"Database Schema (Schema: {self.schema_name}):\n\n"
        current_table = None
        
        for row in results:
            table_name, column_name, data_type, is_nullable, column_default, constraint_type = row
            
            if table_name != current_table:
                if current_table is not None:
                    schema_text += "\n"
                schema_text += f"Table: {table_name}\n"
                schema_text += "-" * (len(table_name) + 7) + "\n"
                current_table = table_name
            
            if column_name:
                nullable_text = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_text = f" DEFAULT {column_default}" if column_default else ""
                constraint_text = f" [{constraint_type}]" if constraint_type else ""
                
                schema_text += f"  {column_name}: {data_type} {nullable_text}{default_text}{constraint_text}\n"
        
        return schema_text
    
    def __del__(self):
        """Clean up database connection."""
        if self._connection:
            self._connection.close()


class SQLiteSchemaLookupTool(SchemaLookupTool):
    """
    SQLite-specific implementation of schema lookup.
    
    Retrieves schema information from SQLite databases using
    PRAGMA statements and sqlite_master queries.
    """
    
    def __init__(self, database_path: str):
        """
        Initialize SQLite schema lookup tool.
        
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
    
    def get_schema(self, table_filter: Optional[str] = None) -> str:
        """
        Retrieve formatted SQLite schema information.
        
        Args:
            table_filter: Optional filter for table names
            
        Returns:
            Formatted schema string with table and column details
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get table names
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            if table_filter:
                query += f" AND name LIKE '%{table_filter}%'"
            
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_text = "Database Schema (SQLite):\n\n"
            
            for table_name in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema_text += f"Table: {table_name}\n"
                schema_text += "-" * (len(table_name) + 7) + "\n"
                
                for col in columns:
                    cid, name, data_type, not_null, default_value, pk = col
                    nullable_text = "NOT NULL" if not_null else "NULL"
                    default_text = f" DEFAULT {default_value}" if default_value else ""
                    pk_text = " [PRIMARY KEY]" if pk else ""
                    
                    schema_text += f"  {name}: {data_type} {nullable_text}{default_text}{pk_text}\n"
                
                schema_text += "\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error retrieving SQLite schema: {e}")
            return f"Error retrieving schema: {str(e)}"
    
    def get_table_names(self) -> List[str]:
        """Get list of available SQLite table names."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error retrieving table names: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific SQLite table."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            columns = []
            constraints = {'PRIMARY KEY': []}
            
            for col in columns_info:
                cid, name, data_type, not_null, default_value, pk = col
                columns.append({
                    'name': name,
                    'type': data_type,
                    'nullable': not not_null,
                    'default': default_value
                })
                
                if pk:
                    constraints['PRIMARY KEY'].append(name)
            
            return {
                'table_name': table_name,
                'columns': columns,
                'constraints': constraints
            }
            
        except Exception as e:
            logger.error(f"Error retrieving table info for {table_name}: {e}")
            return {}
    
    def __del__(self):
        """Clean up database connection."""
        if self._connection:
            self._connection.close()


class BigQuerySchemaLookupTool(SchemaLookupTool):
    """
    BigQuery-specific implementation of schema lookup.
    
    Retrieves schema information from Google BigQuery datasets using
    the BigQuery client library.
    """
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None, dataset_id: Optional[str] = None):
        """
        Initialize BigQuery schema lookup tool.
        
        Args:
            project_id: Google Cloud project ID
            credentials_path: Path to service account JSON file (optional)
            dataset_id: Specific dataset to query (optional, will query all if None)
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.dataset_id = dataset_id
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
                    # Use default credentials (ADC, service account, etc.)
                    self._client = bigquery.Client(project=self.project_id)
            except ImportError:
                raise ImportError("google-cloud-bigquery is required for BigQuery connections")
            except Exception as e:
                logger.error(f"Failed to connect to BigQuery: {e}")
                raise
        return self._client
    
    def get_schema(self, table_filter: Optional[str] = None) -> str:
        """
        Retrieve formatted BigQuery schema information.
        
        Args:
            table_filter: Optional filter for table names
            
        Returns:
            Formatted schema string with dataset, table and column details
        """
        try:
            client = self._get_client()
            schema_text = f"BigQuery Schema (Project: {self.project_id}):\n\n"
            
            # Get datasets to query
            if self.dataset_id:
                datasets = [self.dataset_id]
            else:
                datasets = [dataset.dataset_id for dataset in client.list_datasets()]
            
            for dataset_id in datasets:
                schema_text += f"Dataset: {dataset_id}\n"
                schema_text += "=" * (len(dataset_id) + 9) + "\n"
                
                # List tables in the dataset
                dataset_ref = client.dataset(dataset_id)
                tables = client.list_tables(dataset_ref)
                
                for table in tables:
                    if table_filter and table_filter.lower() not in table.table_id.lower():
                        continue
                    
                    # Get table schema
                    table_ref = dataset_ref.table(table.table_id)
                    table_obj = client.get_table(table_ref)
                    
                    schema_text += f"\nTable: {table.table_id}\n"
                    schema_text += "-" * (len(table.table_id) + 7) + "\n"
                    
                    for field in table_obj.schema:
                        mode_text = f" ({field.mode})" if field.mode != "NULLABLE" else ""
                        description_text = f" -- {field.description}" if field.description else ""
                        
                        schema_text += f"  {field.name}: {field.field_type}{mode_text}{description_text}\n"
                
                schema_text += "\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error retrieving BigQuery schema: {e}")
            return f"Error retrieving schema: {str(e)}"
    
    def get_table_names(self) -> List[str]:
        """Get list of available BigQuery table names."""
        try:
            client = self._get_client()
            table_names = []
            
            # Get datasets to query
            if self.dataset_id:
                datasets = [self.dataset_id]
            else:
                datasets = [dataset.dataset_id for dataset in client.list_datasets()]
            
            for dataset_id in datasets:
                dataset_ref = client.dataset(dataset_id)
                tables = client.list_tables(dataset_ref)
                
                for table in tables:
                    table_names.append(f"{dataset_id}.{table.table_id}")
            
            return table_names
            
        except Exception as e:
            logger.error(f"Error retrieving BigQuery table names: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific BigQuery table."""
        try:
            client = self._get_client()
            
            # Parse table name (dataset.table or project.dataset.table)
            parts = table_name.split('.')
            if len(parts) == 2:
                dataset_id, table_id = parts
                project_id = self.project_id
            elif len(parts) == 3:
                project_id, dataset_id, table_id = parts
            else:
                raise ValueError(f"Invalid table name format: {table_name}")
            
            # Get table reference
            table_ref = client.dataset(dataset_id, project=project_id).table(table_id)
            table_obj = client.get_table(table_ref)
            
            # Build column information
            columns = []
            for field in table_obj.schema:
                columns.append({
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description
                })
            
            # Get table metadata
            return {
                'table_name': table_name,
                'full_table_id': f"{table_obj.project}.{table_obj.dataset_id}.{table_obj.table_id}",
                'columns': columns,
                'num_rows': table_obj.num_rows,
                'num_bytes': table_obj.num_bytes,
                'created': table_obj.created.isoformat() if table_obj.created else None,
                'modified': table_obj.modified.isoformat() if table_obj.modified else None,
                'description': table_obj.description,
                'labels': dict(table_obj.labels) if table_obj.labels else {}
            }
            
        except Exception as e:
            logger.error(f"Error retrieving BigQuery table info for {table_name}: {e}")
            return {}


def create_schema_tool(db_type: str = "postgresql", **kwargs) -> SchemaLookupTool:
    """
    Factory function to create appropriate schema lookup tool.
    
    Simplified to use only PostgreSQL and SQLite.
    
    Args:
        db_type: Type of database ("postgresql" or "sqlite")
        **kwargs: Database-specific connection parameters
        
    Returns:
        Configured schema lookup tool instance
        
    Raises:
        ValueError: If unsupported db_type is specified
        ImportError: If required dependencies are not available
    """
    if db_type == "postgresql":
        try:
            connection_string = kwargs.get("connection_string")
            if not connection_string:
                raise ValueError("connection_string is required for PostgreSQL")
            
            return PostgreSQLSchemaLookupTool(connection_string=connection_string)
        except ImportError as e:
            logger.warning(f"PostgreSQL dependencies not available: {e}")
            logger.info("Install with: pip install psycopg2-binary")
            raise
    
    elif db_type == "sqlite":
        db_path = kwargs.get("db_path")
        if not db_path:
            raise ValueError("db_path is required for SQLite")
        
        return SQLiteSchemaLookupTool(db_path=db_path)
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Example usage configurations:
#
# For PostgreSQL:
# schema_tool = create_schema_tool(
#     db_type="postgresql",
#     connection_string="postgresql://user:password@localhost:5432/dbname"
# )
#
# For SQLite (development/testing):
# schema_tool = create_schema_tool(
#     db_type="sqlite",
#     db_path="path/to/database.db"
# )