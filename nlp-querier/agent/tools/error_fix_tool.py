from typing import Any, Dict
import logging
import json

class SQLErrorFixTool:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        logging.basicConfig(level=logging.INFO)

    def fix_error(self, sql: str, error: str, schema: str = "") -> Dict[str, Any]:
        """
        Uses LLM to intelligently fix SQL errors.
        
        Args:
            sql (str): The SQL query that caused the error.
            error (str): The error message returned from the SQL execution.
            schema (str): Database schema for context.

        Returns:
            Dict[str, Any]: A dictionary containing the fixed SQL and a success flag.
        """
        try:
            # Use LLM to fix the SQL error
            fixed_sql = self._llm_fix_sql(sql, error, schema)
            
            if fixed_sql and fixed_sql.strip() != sql.strip():
                logging.info("SQL error fixed using LLM.")
                return {"fixed_sql": fixed_sql, "success": True}
            else:
                logging.warning("LLM could not fix the SQL error.")
                return {"fixed_sql": sql, "success": False}
                
        except Exception as e:
            logging.error(f"Error during LLM SQL fixing: {e}")
            # Fallback to rule-based fixes
            return self._rule_based_fix(sql, error)
    
    def _llm_fix_sql(self, sql: str, error: str, schema: str) -> str:
        """
        Use LLM to intelligently fix SQL errors.
        """
        try:
            from agent.tools.sql_gen_tool import create_sql_gen_tool
            from config import get_config
            
            config = get_config()
            
            fix_prompt = f"""Fix this SQL query that has an error.

Original SQL:
{sql}

Error Message:
{error}

Database Schema:
{schema}

CRITICAL SCHEMA INFORMATION:
- customers table has: customer_id, name, email, region, registration_date
- sales table has: id, date, region, product, quantity, unit_price, total_amount
- IMPORTANT: sales table does NOT have customer_id column
- Tables can only be joined on: customers.region = sales.region
- This represents regional sales totals, not individual customer purchases

The error occurred when executing the SQL. Please provide a corrected version that:
1. Fixes the specific error mentioned
2. Uses customers.region = sales.region for joins (NOT customer_id)
3. Maintains the original intent of the query
4. Uses proper SQLite syntax
5. Is safe and secure

Respond with JSON:
{{"fixed_sql": "SELECT ...", "explanation": "What was fixed"}}"""

            # Use Vertex AI to fix the SQL
            sql_tool = create_sql_gen_tool(
                "vertex_ai",
                project_id=config["ai"]["project_id"],
                model_name=config["ai"]["model_name"],
                temperature=0.1
            )
            
            response = sql_tool._get_client().generate_content(
                fix_prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 500}
            )
            
            result_text = response.text.strip()
            
            # Parse JSON response
            if '{' in result_text and '}' in result_text:
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                json_str = result_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                fixed_sql = result.get("fixed_sql", "").strip()
                if fixed_sql:
                    logging.info(f"LLM fixed SQL: {result.get('explanation', 'No explanation')}")
                    return fixed_sql
            
            return ""
            
        except Exception as e:
            logging.error(f"LLM SQL fix failed: {e}")
            return ""
    
    def _rule_based_fix(self, sql: str, error: str) -> Dict[str, Any]:
        """
        Fallback rule-based fixes for common SQL errors.
        """
        fixed_sql = sql
        success = False
        
        # Common SQLite error fixes
        if "no such column" in error.lower() and "customer_id" in error.lower():
            # Fix customer_id relationship error - tables are linked by region, not customer_id
            logging.info("Detected customer_id relationship error - fixing to use region join")
            
            # Replace customer_id joins with region joins
            fixed_sql = sql.replace(
                "c.customer_id = s.customer_id", 
                "c.region = s.region"
            )
            fixed_sql = fixed_sql.replace(
                "customers.customer_id = sales.customer_id",
                "customers.region = sales.region"
            )
            
            # Also remove customer_id from GROUP BY and replace with region-based grouping
            if "GROUP BY c.customer_id" in fixed_sql:
                fixed_sql = fixed_sql.replace("GROUP BY c.customer_id", "GROUP BY c.customer_id")
                # Keep customer_id in GROUP BY since it's in customers table
            
            success = True
            logging.info(f"Fixed SQL: {fixed_sql}")
            
        elif "no such column" in error.lower():
            # Try to suggest column name fixes for other cases
            fixed_sql = sql  # Keep original for now
        elif "syntax error" in error.lower():
            # Basic syntax fixes
            fixed_sql = sql.replace("'", "'").replace(""", '"').replace(""", '"')
            success = True
        elif "no such table" in error.lower():
            # Table name fixes
            fixed_sql = sql  # Keep original for now
            
        return {"fixed_sql": fixed_sql, "success": success}
        """
        Validates the fixed SQL query to ensure it is executable.
        
        Args:
            sql (str): The SQL query to validate.

        Returns:
            bool: True if the SQL is valid, False otherwise.
        """
        # Placeholder for actual validation logic
        return True  # Assume the fixed SQL is valid for this example