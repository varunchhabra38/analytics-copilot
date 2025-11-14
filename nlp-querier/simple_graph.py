"""
Simplified LangGraph workflow for testing.
"""
from typing import List, Dict, Any, Literal
import logging
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.intent import intent_node
from agent.nodes.lookup_schema import lookup_schema_node
from agent.nodes.generate_sql import generate_sql_node
from agent.nodes.validate_sql import validate_sql_node
from agent.nodes.execute_sql import execute_sql_node
from agent.nodes.summarize import summarize_node

logger = logging.getLogger(__name__)


def create_simple_analytics_graph() -> StateGraph:
    """Create a simplified LangGraph workflow for testing."""
    workflow = StateGraph(AgentState)
    
    # Add only essential nodes
    workflow.add_node("intent", intent_node)
    workflow.add_node("lookup_schema", lookup_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("summarize", summarize_node)
    
    # Set entry point
    workflow.set_entry_point("intent")
    
    # Simple linear flow for now
    workflow.add_conditional_edges(
        "intent",
        lambda state: "lookup_schema" if not state.get("clarification_needed", False) else "end",
        {
            "lookup_schema": "lookup_schema",
            "end": END
        }
    )
    
    # Simple linear progression
    workflow.add_edge("lookup_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql") 
    workflow.add_edge("validate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "summarize")
    workflow.add_edge("summarize", END)
    
    return workflow


def run_simple_agent_chat(question: str, history: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
    """
    Run a simplified analytics agent chat workflow.
    """
    # Initialize state
    initial_state: AgentState = {
        "question": question,
        "history": history.copy(),
        "schema": None,
        "generated_sql": None,
        "validated_sql": None,
        "execution_result": None,
        "execution_error": None,
        "visualization_path": None,
        "summary": None,
        "last_sql": None,
        "clarification_needed": False,
        "clarification_question": None,
        "user_clarification_response": None,
        "retry_count": 0,
        "max_retries": 3,
        "current_node": None,
        "completed_nodes": []
    }
    
    try:
        # Create and compile the workflow
        workflow = create_simple_analytics_graph()
        app = workflow.compile()
        
        # Run the workflow with increased recursion limit
        config = {
            "recursion_limit": 100
        }
        
        final_state = None
        for state in app.stream(initial_state, config):
            final_state = state
            logger.info(f"Current state keys: {list(state.keys()) if isinstance(state, dict) else type(state)}")
        
        # Extract results from final state
        if final_state:
            if isinstance(final_state, dict):
                # Get the last node's state
                result_state = list(final_state.values())[-1]
            else:
                result_state = final_state
                
            return {
                "sql": result_state.get("validated_sql"),
                "summary": result_state.get("summary"),
                "visualization_path": result_state.get("visualization_path"),
                "history": result_state.get("history", []),
                "clarification_question": result_state.get("clarification_question"),
                "clarification_needed": result_state.get("clarification_needed", False),
                "execution_error": result_state.get("execution_error"),
                "execution_result": result_state.get("execution_result"),  # MISSING FIELD!
                "completed_nodes": result_state.get("completed_nodes", [])
            }
        else:
            return {
                "error": "Workflow failed to produce results",
                "history": history
            }
            
    except Exception as e:
        logger.error(f"Error running simple agent chat: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "history": history
        }