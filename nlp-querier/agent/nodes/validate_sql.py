"""
SQL Validation Node for LangGraph Analytics Agent.
Validates generated SQL for safety and correctness.
"""

from typing import Dict, Any
import logging
import re
from agent.state import AgentState
from agent.tools.sql_validator_tool import SQLValidatorTool
from config import get_config

logger = logging.getLogger(__name__)


def validate_sql_node(state: AgentState) -> AgentState:
    """
    Node to validate generated SQL for safety and correctness.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with validation results
    """
    logger.info("🔍 SQL VALIDATION NODE - STARTING")
    logger.info("-" * 60)
    
    try:
        generated_sql = state.get("generated_sql", "")
        retry_count = state.get("retry_count", 0)
        
        logger.info(f"📥 Input Parameters:")
        logger.info(f"  - SQL Length: {len(generated_sql)} characters")
        logger.info(f"  - Retry Count: {retry_count}")
        
        # Create new state copy
        new_state = state.copy()
        new_state['current_node'] = 'validate_sql'
        
        if not generated_sql:
            logger.warning("⚠️  No SQL to validate")
            new_state['validated_sql'] = ""
            new_state['validation_error'] = "No SQL to validate"
            return new_state

        logger.info("📝 SQL to validate:")
        for i, line in enumerate(generated_sql.split('\n')[:10], 1):  # First 10 lines
            logger.info(f"    {i:2d}: {line}")
        if len(generated_sql.split('\n')) > 10:
            logger.info("    ... (truncated)")

        # Get database connection for schema validation
        logger.info("🔧 Setting up database connection for schema validation...")
        db_connection = None
        try:
            config = get_config()
            db_config = config["database"]
            db_type = db_config["type"]
            logger.info(f"  - Database Type: {db_type}")
            
            if db_type == "sqlite":
                import sqlite3
                # Extract path from sqlite:///./output/fcfp_analytics.db
                db_path = db_config["connection_string"].replace("sqlite:///./", "")
                db_connection = sqlite3.connect(db_path)
                logger.info(f"  - Connected to SQLite: {db_path}")
            # Add other database types if needed
        except Exception as e:
            logger.warning(f"⚠️  Could not establish database connection for schema validation: {e}")
            logger.info("  - Proceeding with basic validation only")
        
        # Use the SQL validator tool with database connection
        logger.info("🔍 Starting SQL validation process...")
        validator = SQLValidatorTool(db_connection=db_connection)
        is_valid, error_message = validator.validate(generated_sql)
        
        # Clean up database connection
        if db_connection:
            try:
                db_connection.close()
                logger.info("✅ Database connection closed")
            except Exception:
                logger.warning("⚠️  Error closing database connection")
        
        # Log validation results
        if is_valid:
            logger.info("✅ SQL VALIDATION PASSED")
            logger.info("  - SQL is safe and syntactically correct")
            logger.info("  - Schema compliance verified")
            new_state['validated_sql'] = generated_sql
            new_state['validation_error'] = None
        else:
            logger.warning("❌ SQL VALIDATION FAILED")
            logger.warning(f"  - Error: {error_message}")
            logger.warning("  - SQL will not be executed")
            new_state['validated_sql'] = ""
            new_state['validation_error'] = error_message
            
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['validate_sql']
        
        logger.info("🔍 SQL VALIDATION NODE - COMPLETED")
        logger.info("-" * 60)
        
        return new_state
        
    except Exception as e:
        logger.error("❌ SQL VALIDATION NODE - ERROR")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Message: {e}")
        logger.error("-" * 60)
        
        new_state = state.copy()
        new_state['validated_sql'] = ""
        new_state['validation_error'] = str(e)
        new_state['current_node'] = 'validate_sql'
        return new_state


def validate_sql(agent_state: AgentState) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    Args:
        agent_state: The current state of the agent containing the generated SQL.
        
    Returns:
        Dictionary containing the validation result and any error messages.
    """
    sql = agent_state['generated_sql']
    validator = SQLValidatorTool()
    
    is_valid, error_message = validator.validate(sql)
    
    if is_valid:
        agent_state['validated_sql'] = sql
        return {
            "is_valid": True,
            "message": "SQL is valid."
        }
    else:
        agent_state['execution_error'] = error_message
        return {
            "is_valid": False,
            "message": f"SQL validation error: {error_message}"
        }