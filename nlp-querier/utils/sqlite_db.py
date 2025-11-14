"""
SQLite Database Manager for Analytics Agent
Provides a simplified database interface for testing without PostgreSQL setup.
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteManager:
    """SQLite database manager for the Analytics Agent."""
    
    def __init__(self, db_path: str = "output/fcfp_analytics.db"):
        """
        Initialize SQLite database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._ensure_db_directory()
        self._create_sample_data()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    def connect(self) -> bool:
        """
        Establish connection to SQLite database.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from SQLite database")
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Dictionary with query results
        """
        if not self.connection:
            if not self.connect():
                return {
                    'success': False,
                    'error': 'Failed to connect to database',
                    'columns': [],
                    'rows': [],
                    'row_count': 0
                }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Handle different query types
            if query.strip().upper().startswith(('SELECT', 'WITH', 'EXPLAIN')):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                row_data = [dict(row) for row in rows]
                
                return {
                    'success': True,
                    'error': None,
                    'columns': columns,
                    'rows': row_data,
                    'row_count': len(row_data)
                }
            else:
                # For INSERT, UPDATE, DELETE, CREATE, etc.
                self.connection.commit()
                return {
                    'success': True,
                    'error': None,
                    'columns': [],
                    'rows': [],
                    'row_count': cursor.rowcount
                }
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'rows': [],
                'row_count': 0
            }
    
    def get_dataframe(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute query and return results as pandas DataFrame.
        
        Args:
            query: SQL query to execute
            
        Returns:
            DataFrame with query results or None if error
        """
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            logger.error(f"DataFrame query error: {e}")
            return None
    
    def get_schema(self) -> str:
        """
        Get database schema information with relationship analysis.
        
        Returns:
            String representation of database schema including relationships
        """
        schema_parts = []
        
        if not self.connection:
            if not self.connect():
                return "Error: Cannot connect to database"
        
        # Get all tables
        tables_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
        
        result = self.execute_query(tables_query)
        if not result['success']:
            return "Error retrieving schema"

        # Collect all table info first
        all_tables = {}
        for table_row in result['rows']:
            table_name = table_row['name']
            
            # Get CREATE TABLE statement for accurate schema
            create_table_query = f"""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='{table_name}';
            """
            
            create_result = self.execute_query(create_table_query)
            create_sql = ""
            if create_result['success'] and create_result['rows']:
                create_sql = create_result['rows'][0]['sql']
            
            # Get column info
            try:
                sample_query = f"SELECT * FROM {table_name} LIMIT 1;"
                cursor = self.connection.cursor()
                cursor.execute(sample_query)
                columns = [description[0] for description in cursor.description] if cursor.description else []
            except Exception as e:
                columns = []
                logger.warning(f"Could not get column info for {table_name}: {e}")
            
            # Get sample data
            sample_query = f"SELECT * FROM {table_name} LIMIT 3;"
            sample_data = self.execute_query(sample_query)
            sample_rows = sample_data['rows'] if sample_data['success'] else []
            
            all_tables[table_name] = {
                'create_sql': create_sql,
                'columns': columns,
                'sample_rows': sample_rows
            }
        
        # Add relationship analysis
        schema_parts.append("=== DATABASE SCHEMA AND RELATIONSHIPS ===")
        schema_parts.append("")
        
        # Analyze potential relationships
        schema_parts.append("TABLE RELATIONSHIPS:")
        table_names = list(all_tables.keys())
        if len(table_names) >= 2:
            # Check for common columns that could indicate relationships
            customers_cols = set(all_tables.get('customers', {}).get('columns', []))
            sales_cols = set(all_tables.get('sales', {}).get('columns', []))
            
            common_cols = customers_cols.intersection(sales_cols)
            if common_cols:
                schema_parts.append(f"- Common columns between tables: {', '.join(common_cols)}")
                schema_parts.append("- CRITICAL JOIN INFORMATION:")
                for col in common_cols:
                    schema_parts.append(f"  * customers.{col} = sales.{col}")
                
                # Special handling for region-based relationships
                if 'region' in common_cols:
                    schema_parts.append("")
                    schema_parts.append("⚠️  CRITICAL DATABASE DESIGN NOTE:")
                    schema_parts.append("- sales table does NOT have customer_id column")
                    schema_parts.append("- Tables are linked ONLY by region: customers.region = sales.region")
                    schema_parts.append("- This means sales are aggregated by region, not by individual customer")
                    schema_parts.append("- Cannot determine which specific customer made which purchase")
                    schema_parts.append("- Can only calculate regional totals for customers in each region")
                    schema_parts.append("")
                    schema_parts.append("CORRECT SQL PATTERN:")
                    schema_parts.append("  SELECT c.name, SUM(s.total_amount) AS regional_total")
                    schema_parts.append("  FROM customers c")
                    schema_parts.append("  JOIN sales s ON c.region = s.region")
                    schema_parts.append("  WHERE c.region = 'desired_region'")
                    schema_parts.append("  GROUP BY c.customer_id, c.name")
                    schema_parts.append("")
                    schema_parts.append("WRONG SQL PATTERN (will fail):")
                    schema_parts.append("  JOIN sales s ON c.customer_id = s.customer_id  -- ❌ NO customer_id in sales!")
            else:
                schema_parts.append("- NO direct foreign key relationships found")
                schema_parts.append("- Individual customer purchases cannot be tracked")
                schema_parts.append("- Sales data is aggregated by region only")
                
            schema_parts.append("")
        
        # Add detailed table information
        for table_name, table_info in all_tables.items():
            schema_parts.append(f"--- Table: {table_name} ---")
            
            if table_info['create_sql']:
                schema_parts.append(f"  Schema: {table_info['create_sql']}")
            
            if table_info['columns']:
                schema_parts.append(f"  Columns: {', '.join(table_info['columns'])}")
            
            # Add sample data
            if table_info['sample_rows']:
                schema_parts.append("  Sample data:")
                for row in table_info['sample_rows']:
                    schema_parts.append(f"    {dict(row)}")
            schema_parts.append("")
        
        return "\n".join(schema_parts)
    
    def _create_sample_data(self):
        """Create sample tables with data for testing."""
        if not self.connect():
            return
        
        # Create sales table
        create_sales = """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            region VARCHAR(50) NOT NULL,
            product VARCHAR(100) NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL
        );
        """
        
        # Create customers table
        create_customers = """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            region VARCHAR(50) NOT NULL,
            registration_date DATE NOT NULL
        );
        """
        
        # Execute table creation
        self.execute_query(create_sales)
        self.execute_query(create_customers)
        
        # Check if data already exists
        count_sales = self.execute_query("SELECT COUNT(*) as count FROM sales;")
        if count_sales['success'] and count_sales['rows'][0]['count'] == 0:
            # Insert sample sales data
            sample_sales = """
            INSERT INTO sales (date, region, product, quantity, unit_price, total_amount) VALUES
            ('2024-01-15', 'North America', 'Laptop Pro', 5, 1200.00, 6000.00),
            ('2024-01-15', 'Europe', 'Laptop Pro', 3, 1200.00, 3600.00),
            ('2024-01-16', 'Asia', 'Tablet Max', 8, 800.00, 6400.00),
            ('2024-01-16', 'North America', 'Phone Elite', 12, 900.00, 10800.00),
            ('2024-01-17', 'Europe', 'Tablet Max', 6, 800.00, 4800.00),
            ('2024-01-17', 'Asia', 'Laptop Pro', 4, 1200.00, 4800.00),
            ('2024-01-18', 'North America', 'Tablet Max', 10, 800.00, 8000.00),
            ('2024-01-18', 'Europe', 'Phone Elite', 7, 900.00, 6300.00),
            ('2024-01-19', 'Asia', 'Phone Elite', 15, 900.00, 13500.00),
            ('2024-01-19', 'North America', 'Laptop Pro', 2, 1200.00, 2400.00),
            ('2024-02-01', 'Europe', 'Laptop Pro', 8, 1200.00, 9600.00),
            ('2024-02-01', 'Asia', 'Tablet Max', 12, 800.00, 9600.00),
            ('2024-02-02', 'North America', 'Phone Elite', 20, 900.00, 18000.00),
            ('2024-02-02', 'Europe', 'Tablet Max', 5, 800.00, 4000.00),
            ('2024-02-03', 'Asia', 'Laptop Pro', 7, 1200.00, 8400.00);
            """
            self.execute_query(sample_sales)
        
        # Check if customer data exists
        count_customers = self.execute_query("SELECT COUNT(*) as count FROM customers;")
        if count_customers['success'] and count_customers['rows'][0]['count'] == 0:
            # Insert sample customer data
            sample_customers = """
            INSERT INTO customers (name, email, region, registration_date) VALUES
            ('John Smith', 'john.smith@email.com', 'North America', '2023-06-15'),
            ('Marie Dubois', 'marie.dubois@email.com', 'Europe', '2023-07-22'),
            ('Hiroshi Tanaka', 'hiroshi.tanaka@email.com', 'Asia', '2023-08-10'),
            ('Sarah Johnson', 'sarah.johnson@email.com', 'North America', '2023-09-05'),
            ('Lars Anderson', 'lars.anderson@email.com', 'Europe', '2023-10-12'),
            ('Wei Chen', 'wei.chen@email.com', 'Asia', '2023-11-18'),
            ('Emma Wilson', 'emma.wilson@email.com', 'North America', '2023-12-03'),
            ('Giuseppe Rossi', 'giuseppe.rossi@email.com', 'Europe', '2024-01-08');
            """
            self.execute_query(sample_customers)
        
        self.disconnect()
        logger.info("Sample database created with sales and customers tables")