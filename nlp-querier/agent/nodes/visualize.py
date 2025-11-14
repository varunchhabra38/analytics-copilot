from typing import Any, Dict
import pandas as pd
import os
import logging
from agent.tools.viz_tool import VizTool
from agent.state import AgentState

logger = logging.getLogger(__name__)


def visualize_node(state: AgentState) -> Dict[str, Any]:
    """
    Node function to create visualizations from query results.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with visualization path
    """
    try:
        logger.info("Creating visualization...")
        
        execution_result = state.get("execution_result")
        
        if execution_result is None:
            logger.warning("No execution result available for visualization")
            return {
                **state,
                "visualization_path": None,
                "visualization_error": "No execution result available for visualization"
            }
        
        # Convert serialized DataFrame back to pandas DataFrame if needed
        if isinstance(execution_result, dict) and execution_result.get('type') == 'dataframe':
            logger.info("Converting serialized DataFrame back to pandas DataFrame")
            df = pd.DataFrame(execution_result.get('data', []))
            logger.info(f"Restored DataFrame with shape: {df.shape}")
        elif isinstance(execution_result, pd.DataFrame):
            df = execution_result
        else:
            logger.warning(f"Execution result is not a DataFrame: {type(execution_result)}")
            return {
                **state,
                "visualization_path": None,
                "visualization_error": "Execution result is not suitable for visualization"
            }
        
        # Create visualization using the tool
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        viz_tool = VizTool(output_dir=output_dir)
        
        # Generate a meaningful title from the question
        question = state.get("question", "Query Results")
        title = f"Results: {question}" if question and question != "Query Results" else "Query Results"
        
        # Choose chart type based on data characteristics
        chart_type = "bar"  # Default to bar chart
        if len(df.columns) > 2:
            chart_type = "bar"  # Multiple columns - use bar chart
        elif df.select_dtypes(include=['number']).shape[1] > 0:
            chart_type = "line"  # Numeric data - use line chart
        
        try:
            visualization_path = viz_tool.create_visualization(df, chart_type, title)
            logger.info(f"Visualization saved to: {visualization_path}")
            
            return {
                **state,
                "visualization_path": visualization_path,
                "visualization_error": None
            }
            
        except Exception as viz_error:
            logger.warning(f"Visualization creation failed: {viz_error}")
            return {
                **state,
                "visualization_path": None,
                "visualization_error": str(viz_error)
            }
        
    except Exception as e:
        logger.error(f"Visualization node error: {e}")
        return {
            **state,
            "visualization_path": None,
            "visualization_error": str(e)
        }


def visualize_data(state: AgentState) -> str:
    """
    Legacy function for backward compatibility.
    
    Generates a visualization from the execution results and saves it to the output directory.

    Args:
        state (AgentState): The current state of the agent containing execution results.

    Returns:
        str: The path to the saved visualization.
    """
    if state.execution_result is None:
        raise ValueError("No execution result available for visualization.")

    viz_tool = VizTool(output_dir="output")
    
    # Generate title and chart type
    title = f"Results: {state.get('question', 'Query Results')}"
    chart_type = "bar"  # Default chart type
    
    # Create the visualization
    visualization_path = viz_tool.create_visualization(state.execution_result, chart_type, title)

    return visualization_path