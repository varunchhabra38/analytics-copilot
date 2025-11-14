"""
Interpret Results Node - Generate business insights from query results
"""
import logging
from typing import Dict, Any
from agent.state import AgentState
from agent.tools.results_interpreter_tool import ResultsInterpreterTool

logger = logging.getLogger(__name__)

def interpret_results(state: AgentState) -> AgentState:
    """
    Generate business insights from SQL query results using LLM.
    
    Args:
        state: Current agent state with execution results
        
    Returns:
        Updated state with business interpretation
    """
    try:
        logger.info("🔍 RESULTS INTERPRETATION NODE - STARTING")
        logger.info("-" * 60)
        
        question = state.get("question", "")
        sql_query = state.get("validated_sql", "")
        execution_result = state.get("execution_result")
        
        logger.info(f"📥 Input Parameters:")
        logger.info(f"  - Question: {question}")
        logger.info(f"  - SQL length: {len(sql_query)} characters")
        logger.info(f"  - Results available: {'✅' if execution_result is not None else '❌'}")
        
        # Create new state copy
        new_state = state.copy()
        new_state['current_node'] = 'interpret_results'
        
        # Check if we have results to interpret
        if execution_result is None:
            logger.warning("⚠️ No execution results available for interpretation")
            new_state['business_interpretation'] = "No results available to interpret."
            new_state['completed_nodes'] = new_state.get('completed_nodes', []) + ['interpret_results']
            return new_state
        
        # Extract DataFrame from execution result
        df = None
        if isinstance(execution_result, dict):
            if execution_result.get("type") == "dataframe" and execution_result.get("data"):
                # Convert back to DataFrame for interpretation
                import pandas as pd
                df = pd.DataFrame(execution_result["data"])
            else:
                logger.warning("⚠️ Execution result is not in expected DataFrame format")
                new_state['business_interpretation'] = "Unable to interpret results: unexpected data format."
                new_state['completed_nodes'] = new_state.get('completed_nodes', []) + ['interpret_results']
                return new_state
        else:
            logger.warning(f"⚠️ Unexpected execution result type: {type(execution_result)}")
            new_state['business_interpretation'] = "Unable to interpret results: unexpected result type."
            new_state['completed_nodes'] = new_state.get('completed_nodes', []) + ['interpret_results']
            return new_state
        
        logger.info(f"📊 DataFrame for interpretation:")
        logger.info(f"  - Rows: {len(df)}")
        logger.info(f"  - Columns: {list(df.columns)}")
        
        # Create results interpreter tool
        interpreter = ResultsInterpreterTool()
        
        # Generate business interpretation
        logger.info("🤖 Generating business interpretation...")
        business_interpretation = interpreter.interpret_results(
            question=question,
            sql_query=sql_query,
            execution_result=df,
            context="Financial Crime & Fraud Prevention analytics data"
        )
        
        # Add interpretation to state
        new_state['business_interpretation'] = business_interpretation
        new_state['completed_nodes'] = new_state.get('completed_nodes', []) + ['interpret_results']
        
        logger.info("✅ Business interpretation created successfully")
        logger.info(f"📝 INTERPRETATION CONTENT:")
        logger.info("-" * 40)
        logger.info(business_interpretation)
        logger.info("-" * 40)
        
        logger.info("🔍 RESULTS INTERPRETATION NODE - COMPLETED")
        logger.info("-" * 60)
        
        return new_state
        
    except Exception as e:
        logger.error(f"❌ Error in results interpretation: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return state with error but don't fail the whole workflow
        new_state = state.copy()
        new_state['current_node'] = 'interpret_results'
        new_state['business_interpretation'] = f"Error generating business interpretation: {str(e)}"
        new_state['completed_nodes'] = new_state.get('completed_nodes', []) + ['interpret_results']
        
        return new_state