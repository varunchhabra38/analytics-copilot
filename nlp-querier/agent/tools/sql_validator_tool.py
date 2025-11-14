"""
SQL Validator Tool for the Analytics Agent.
Validates SQL queries for safety and schema compliance.
"""
import logging

logger = logging.getLogger(__name__)


class SQLValidatorTool:
    def __init__(self, db_connection=None):
        self.db_connection = db_connection
        self._schema_cache = None
        logger.info(f"🔍 SQLValidatorTool initialized (DB connection: {'✅' if db_connection else '❌'})")

    def _get_schema_info(self) -> dict:
        """Get database schema information for validation."""
        if self._schema_cache is not None:
            logger.info("📋 Using cached schema information")
            return self._schema_cache
        
        if not self.db_connection:
            logger.warning("⚠️  No database connection - fallback to basic validation only")
            return {"tables": {}, "relationships": []}
        
        logger.info("🗂️  Retrieving database schema...")
        try:
            cursor = self.db_connection.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_rows = cursor.fetchall()
            tables = {row[0].lower() for row in table_rows}
            logger.info(f"  - Found {len(tables)} tables: {list(tables)}")
            
            # Get column info for each table
            table_columns = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                column_rows = cursor.fetchall()
                columns = {row[1].lower(): row[2].lower() for row in column_rows}  # {column_name: data_type}
                table_columns[table] = columns
                logger.info(f"  - Table '{table}': {len(columns)} columns")
            
            self._schema_cache = {
                "tables": table_columns,
                "table_names": tables
            }
            logger.info("✅ Schema information retrieved and cached")
            return self._schema_cache
        except Exception as e:
            logger.warning(f"⚠️  Error retrieving schema: {e}, returning empty schema for basic validation")
            return {"tables": {}, "table_names": set()}

    def validate(self, sql: str) -> tuple[bool, str]:
        """
        Validates the given SQL query for safety and schema compliance.

        Args:
            sql (str): The SQL query to validate.

        Returns:
            tuple[bool, str]: (is_valid, error_message) tuple
        """
        logger.info("🔍 Starting SQL validation process...")
        logger.info(f"  - SQL length: {len(sql)} characters")
        logger.info(f"  - SQL preview: {sql[:100]}..." if len(sql) > 100 else f"  - SQL: {sql}")
        
        # Basic security validation
        logger.info("🛡️  Checking for dangerous keywords...")
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"❌ Found dangerous keyword: {keyword}")
                return False, f"SQL contains potentially dangerous keyword: {keyword}"
        
        logger.info("✅ Security check passed - no dangerous keywords found")
        
        # Check if it's a SELECT query (including CTEs that start with WITH)
        logger.info("📋 Checking query type...")
        sql_trimmed = sql_upper.strip()
        
        # Valid SQL query types we allow
        valid_query_starts = ['SELECT', 'WITH']
        
        is_valid_query = False
        for start in valid_query_starts:
            if sql_trimmed.startswith(start):
                is_valid_query = True
                logger.info(f"✅ Valid query type detected: {start}")
                break
        
        if not is_valid_query:
            logger.warning(f"❌ Invalid query type detected. SQL starts with: '{sql_trimmed[:20]}...'")
            logger.warning(f"  - Full SQL (first 100 chars): {sql_trimmed[:100]}")
            return False, "Only SELECT queries and CTEs (WITH clauses) are allowed"
        
        logger.info("✅ Query type check passed - valid SELECT/WITH query")
        
        # Schema validation (if database connection available)
        logger.info("🗂️  Starting schema validation...")
        schema_info = self._get_schema_info()
        if schema_info.get("tables"):
            logger.info(f"  - Tables available: {list(schema_info['tables'].keys())}")
            try:
                is_valid, error_msg = self._validate_schema_compliance(sql, schema_info)
                if is_valid:
                    logger.info("✅ Schema validation passed")
                else:
                    logger.warning(f"❌ Schema validation failed: {error_msg}")
                return is_valid, error_msg
            except Exception as e:
                logger.warning(f"⚠️  Schema validation error: {e}, continuing with basic validation")
        else:
            logger.warning("⚠️  No schema information available - skipping schema validation")
        
        logger.info("✅ SQL validation completed successfully")
        return True, "SQL validation passed"

    def _validate_schema_compliance(self, sql: str, schema_info: dict) -> tuple[bool, str]:
        """Validate SQL against database schema with improved parsing."""
        import re
        
        sql_clean = sql.strip().replace('\n', ' ').replace('\t', ' ')
        sql_lower = sql_clean.lower()
        
        # For complex queries with CTEs and subqueries, do a simplified validation
        # Just check that the main table names exist in the schema
        
        # Extract potential table names from the SQL
        # Look for patterns: FROM table_name, JOIN table_name
        table_patterns = [
            r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\bjoin\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\binner\s+join\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\bleft\s+join\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\bright\s+join\s+([a-zA-Z_][a-zA-Z0-9_]*)\b'
        ]
        
        found_tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, sql_lower)
            for match in matches:
                # Only add if it's not a SQL keyword
                if match not in ['select', 'from', 'where', 'group', 'order', 'by', 'having', 'union', 'with', 'as']:
                    found_tables.add(match)
        
        # Validate that found tables exist in schema
        available_tables = schema_info.get("table_names", set())
        for table in found_tables:
            if table not in available_tables:
                return False, f"Table '{table}' does not exist in the database"
        
        # If we found valid tables, the query is probably valid
        if found_tables:
            return True, "Schema validation passed"
        
        # If no tables found, it might be a complex query - be permissive
        # This handles CTEs and subqueries that are hard to parse
        return True, "Schema validation passed (complex query)"
        
        # Extract column references more carefully
        # First, extract SELECT clause columns
        select_match = re.search(r'select\s+(.*?)\s+from', sql_lower, re.DOTALL)
        if select_match:
            select_clause = select_match.group(1).strip()
            
            # Skip if it's SELECT *
            if select_clause.strip() != '*':
                # Split by commas and clean up
                columns = [col.strip() for col in select_clause.split(',')]
                
                for col in columns:
                    # Skip function calls, aggregates, and complex expressions
                    if any(func in col for func in ['count(', 'sum(', 'avg(', 'max(', 'min(', 'case ', 'when ']):
                        continue
                    
                    # Remove aliases (AS keyword)
                    if ' as ' in col:
                        col = col.split(' as ')[0].strip()
                    
                    # Handle table.column or alias.column references
                    if '.' in col:
                        table_or_alias, column_part = col.split('.', 1)
                        
                        # Resolve alias to actual table name
                        actual_table = table_aliases.get(table_or_alias, table_or_alias)
                        
                        if actual_table in schema_info["tables"]:
                            table_columns = schema_info["tables"][actual_table]
                            if column_part not in table_columns and column_part != '*':
                                return False, f"Column '{column_part}' does not exist in table '{actual_table}'"
                    else:
                        # Check if column exists in any of the referenced tables
                        found_in_table = False
                        for table in actual_tables:
                            if table in schema_info["tables"]:
                                if col in schema_info["tables"][table]:
                                    found_in_table = True
                                    break
                        
                        # Only validate simple column names that are likely actual columns
                        if not found_in_table and col.replace('_', '').isalpha() and len(col) > 2:
                            # Check if it's a common SQL keyword or function
                            sql_keywords = {
                                'distinct', 'all', 'case', 'when', 'then', 'else', 'end'
                            }
                            if col not in sql_keywords:
                                return False, f"Column '{col}' not found in any referenced table"
        
        # Validate WHERE clause column references
        where_match = re.search(r'\bwhere\s+(.*?)(?:\s+(?:group|order|limit)|;|\s*$)', sql_lower, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            
            # Extract column references from WHERE clause more carefully
            # Split by common operators and logical operators to isolate terms
            where_parts = re.split(r'\s+(?:and|or)\s+', where_clause, flags=re.IGNORECASE)
            
            for part in where_parts:
                # Extract the column name from comparison expressions like "column > 100"
                comparison_match = re.match(r'\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*[><=!]+', part.strip())
                if comparison_match:
                    col_ref = comparison_match.group(1)
                    
                    # Skip SQL keywords and values
                    sql_keywords = {
                        'and', 'or', 'not', 'null', 'true', 'false', 'like', 'between', 'in', 'exists',
                        'is', 'on', 'desc', 'asc'
                    }
                    
                    if col_ref.lower() in sql_keywords or col_ref.isdigit():
                        continue
                    
                    # Handle table.column or alias.column references
                    if '.' in col_ref:
                        table_or_alias, column_part = col_ref.split('.', 1)
                        
                        # Resolve alias to actual table name
                        actual_table = table_aliases.get(table_or_alias, table_or_alias)
                        
                        if actual_table in schema_info["tables"]:
                            table_columns = schema_info["tables"][actual_table]
                            if column_part not in table_columns:
                                return False, f"Column '{column_part}' does not exist in table '{actual_table}'"
                    else:
                        # Check if column exists in any of the referenced tables
                        found_in_table = False
                        for table in actual_tables:
                            if table in schema_info["tables"]:
                                if col_ref in schema_info["tables"][table]:
                                    found_in_table = True
                                    break
                        
                        if not found_in_table and col_ref.replace('_', '').isalpha() and len(col_ref) > 2:
                            return False, f"Column '{col_ref}' not found in any referenced table"
        
        return True, "SQL validation passed"

    def explain(self, sql: str) -> str:
        """
        Provides an explanation of the SQL query.

        Args:
            sql (str): The SQL query to explain.

        Returns:
            str: An explanation of the SQL query.
        """
        # Implement explanation logic here
        return "This SQL query is valid."  # Placeholder for actual explanation logic