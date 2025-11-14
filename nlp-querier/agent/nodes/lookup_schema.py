"""
Schema Lookup Node for LangGraph Analytics Agent.
Retrieves database schema for SQL generation.
"""

from typing import Dict, Any
import logging
from agent.state import AgentState
from agent.tools.schema_tool import SQLiteSchemaLookupTool
from config import get_config

logger = logging.getLogger(__name__)


def lookup_schema_node(state: AgentState) -> AgentState:
    """
    Node to retrieve database schema information.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with schema information
    """
    try:
        logger.info("Looking up database schema...")
        
        # Get database path for SQLite
        config = get_config()
        db_config = config["database"]
        
        if db_config["type"] == "sqlite":
            # Extract path from sqlite:///./output/fcfp_analytics.db
            db_path = db_config["connection_string"].replace("sqlite:///./", "")
        else:
            raise ValueError(f"Unsupported database type: {db_config['type']}")
        
        logger.info(f"Using database: {db_path}")
        
        # Initialize schema tool
        schema_tool = SQLiteSchemaLookupTool(db_path)
        
        # Get schema
        schema = schema_tool.get_schema()
        
        logger.info("Schema lookup completed")
        
        # Create new state copy
        new_state = state.copy()
        new_state['schema'] = schema
        new_state['current_node'] = 'lookup_schema'
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['lookup_schema']
        
        return new_state
        
    except Exception as e:
        logger.error(f"Schema lookup failed: {e}")
        new_state = state.copy()
        new_state['schema'] = f"Error retrieving schema: {str(e)}"
        new_state['current_node'] = 'lookup_schema'
        return new_state