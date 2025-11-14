"""
SQL Generation Node for LangGraph Analytics Agent.
Generates SQL queries from natural language using AI models.
"""

from typing import Dict, Any
import logging
from agent.state import AgentState
from agent.tools.sql_gen_tool import create_sql_gen_tool
from config import get_config

logger = logging.getLogger(__name__)


def generate_sql_node(state: AgentState) -> AgentState:
    """
    Node to generate SQL from natural language question.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with generated SQL
    """
    logger.info("🔧 SQL GENERATION NODE - STARTING")
    logger.info("-" * 60)
    
    try:
        question = state.get("question", "")
        schema = state.get("schema", "")
        history = state.get("history", [])
        retry_count = state.get("retry_count", 0)
        
        logger.info(f"📥 Input Parameters:")
        logger.info(f"  - Question: {question}")
        logger.info(f"  - Schema Length: {len(schema) if schema else 0} chars")
        logger.info(f"  - History Length: {len(history)} messages")
        logger.info(f"  - Retry Count: {retry_count}")
        
        # Create new state copy
        new_state = state.copy()
        new_state['current_node'] = 'generate_sql'
        
        if not question:
            logger.warning("⚠️  No question provided")
            new_state['generated_sql'] = ""
            new_state['sql_explanation'] = "No question provided"
            return new_state
        
        if not schema:
            logger.warning("⚠️  No schema available")
            new_state['generated_sql'] = ""
            new_state['sql_explanation'] = "No schema available"
            return new_state
        
        # Get configuration
        logger.info("🔧 Loading AI configuration...")
        config = get_config()
        logger.info(f"  - Project ID: {config['ai']['project_id']}")
        logger.info(f"  - Model: {config['ai']['model_name']}")
        logger.info(f"  - Temperature: {config['ai']['temperature']}")
        
        # Create SQL generation tool (fallback to rule-based if Vertex AI fails)
        try:
            logger.info("🤖 Attempting Vertex AI SQL generation...")
            sql_gen_tool = create_sql_gen_tool(
                "vertex_ai",
                project_id=config["ai"]["project_id"],
                model_name=config["ai"]["model_name"],
                temperature=config["ai"]["temperature"]
            )
            
            # Extract last SQL from history for context
            last_sql = None
            if history:
                for msg in reversed(history):
                    if msg.get("role") == "assistant" and msg.get("sql"):
                        last_sql = msg.get("sql")
                        break
            
            # Generate SQL with context
            logger.info("🔄 Calling Vertex AI for SQL generation...")
            result = sql_gen_tool.generate_sql(question, schema, history, last_sql=last_sql)
            
            # Check if Vertex AI actually generated SQL
            generated_sql = result.get("sql", "").strip()
            if not generated_sql:
                logger.warning("⚠️  Vertex AI returned empty SQL, falling back to rule-based generation")
                raise Exception("Empty SQL from Vertex AI")
            else:
                logger.info(f"✅ Vertex AI successfully generated SQL ({len(generated_sql)} chars)")
                
        except Exception as e:
            logger.warning(f"⚠️  Vertex AI failed: {e}")
            logger.info("🔄 Falling back to rule-based SQL generation...")
            
            # Extract last SQL for rule-based fallback too
            last_sql = None
            if history:
                for msg in reversed(history):
                    if msg.get("role") == "assistant" and msg.get("sql"):
                        last_sql = msg.get("sql")
                        break
            
            sql_gen_tool = create_sql_gen_tool("rule_based")
            result = sql_gen_tool.generate_sql(question, schema, history, last_sql=last_sql)
            logger.info("✅ Rule-based SQL generation completed")
        
        # Log the results
        generated_sql = result.get("sql", "")
        explanation = result.get("explanation", "")
        
        logger.info("📊 SQL Generation Results:")
        logger.info(f"  - SQL Generated: {'✅ Yes' if generated_sql else '❌ No'}")
        logger.info(f"  - SQL Length: {len(generated_sql)} characters")
        logger.info(f"  - Explanation: {explanation[:100]}..." if len(explanation) > 100 else f"  - Explanation: {explanation}")
        
        if generated_sql:
            logger.info("📝 Generated SQL:")
            for i, line in enumerate(generated_sql.split('\n')[:10], 1):  # First 10 lines
                logger.info(f"    {i:2d}: {line}")
            if len(generated_sql.split('\n')) > 10:
                logger.info("    ... (truncated)")
        
        new_state['generated_sql'] = generated_sql
        new_state['sql_explanation'] = explanation
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['generate_sql']
        
        logger.info("✅ SQL GENERATION NODE - COMPLETED SUCCESSFULLY")
        logger.info("-" * 60)
        
        return new_state
        
    except Exception as e:
        logger.error("❌ SQL GENERATION NODE - ERROR")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Message: {e}")
        logger.error("-" * 60)
        
        new_state = state.copy()
        new_state['generated_sql'] = ""
        new_state['sql_explanation'] = f"Error generating SQL: {str(e)}"
        new_state['current_node'] = 'generate_sql'
        return new_state