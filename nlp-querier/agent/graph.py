"""
LangGraph workflow implementation for the Analytics Agent.

This module defines the complete workflow graph with conditional edges,
retry logic, and user clarification support using LangGraph.
"""
from typing import List, Dict, Any, Literal
import logging
import os
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes.intent import intent_node
from agent.nodes.clarification import clarification_node
from agent.nodes.lookup_schema import lookup_schema_node
from agent.nodes.generate_sql import generate_sql_node
from agent.nodes.validate_sql import validate_sql_node
from agent.nodes.execute_sql import execute_sql_node
from agent.nodes.fix_sql_error import fix_sql_error_node
from agent.nodes.summarize import summarize_node
from agent.nodes.interpret_results import interpret_results

logger = logging.getLogger(__name__)


def generate_execution_mermaid_diagram(executed_nodes: List[str], question: str) -> tuple[str, str]:
    """
    Generate a Mermaid flowchart diagram showing the actual execution flow.
    
    Args:
        executed_nodes: List of nodes that were executed in order
        question: User's original question
        
    Returns:
        Tuple of (mermaid_content, file_path)
    """
    # Node styling and icons
    node_styles = {
        "intent": ("🎯", "fill:#e1f5fe,stroke:#0277bd,stroke-width:2px"),
        "clarification": ("❓", "fill:#fff3e0,stroke:#f57c00,stroke-width:2px"),
        "lookup_schema": ("🗂️", "fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px"),
        "generate_sql": ("🔧", "fill:#e8f5e8,stroke:#388e3c,stroke-width:2px"),
        "validate_sql": ("🔍", "fill:#fff8e1,stroke:#f9a825,stroke-width:2px"),
        "execute_sql": ("⚡", "fill:#e0f2f1,stroke:#00695c,stroke-width:2px"),
        "fix_sql_error": ("🔧", "fill:#ffebee,stroke:#d32f2f,stroke-width:2px"),
        "visualize": ("📊", "fill:#f1f8e9,stroke:#689f38,stroke-width:2px"),
        "summarize": ("📝", "fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px")
    }
    
    # Start building the diagram
    lines = [
        "flowchart TD",
        f"    START([\"🚀 START<br/>Query: {question[:30]}{'...' if len(question) > 30 else ''}\"])",
        "    START --> " + (executed_nodes[0] if executed_nodes else "END")
    ]
    
    # Add executed nodes with styling
    for i, node in enumerate(executed_nodes):
        icon, style = node_styles.get(node, ("🔹", "fill:#f5f5f5,stroke:#757575,stroke-width:2px"))
        
        # Node definition
        lines.append(f"    {node}[\"{icon} {node.replace('_', ' ').title()}\"]")
        
        # Connect to next node
        if i < len(executed_nodes) - 1:
            next_node = executed_nodes[i + 1]
            lines.append(f"    {node} --> {next_node}")
        else:
            # Last node connects to END
            lines.append(f"    {node} --> END([\"✅ COMPLETED\"])")
    
    # Add END node
    lines.append("    END")
    lines.append("")
    
    # Add styling
    lines.append("    %% Node Styling")
    for node in executed_nodes:
        if node in node_styles:
            lines.append(f"    style {node} {node_styles[node][1]}")
    
    lines.append("    style START fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px")
    lines.append("    style END fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px")
    
    mermaid_content = "\n".join(lines)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output/diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mermaid_file = output_dir / f"workflow_execution_{timestamp}.mmd"
    
    with open(mermaid_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_content)
    
    return mermaid_content, str(mermaid_file)


def generate_mermaid_image(mermaid_content: str, output_path: str) -> bool:
    """
    Generate a PNG image from Mermaid diagram content.
    
    Args:
        mermaid_content: The Mermaid diagram content
        output_path: Path where to save the PNG file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess
        import shutil
        
        # Save mermaid content to temp file
        temp_mmd = output_path.replace('.png', '_temp.mmd')
        with open(temp_mmd, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)
        
        # Try different commands for mermaid CLI
        commands = [
            ['npx', 'mmdc', '-i', temp_mmd, '-o', output_path, '-t', 'neutral', '-w', '1200', '-H', '800'],
            ['mmdc', '-i', temp_mmd, '-o', output_path, '-t', 'neutral', '-w', '1200', '-H', '800']
        ]
        
        success = False
        for cmd in commands:
            try:
                # Check if the first command in the list exists
                if not shutil.which(cmd[0]):
                    continue
                    
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    logger.info(f"Mermaid CLI success with {cmd[0]}")
                    success = True
                    break
                else:
                    logger.warning(f"Mermaid CLI error with {cmd[0]} (exit code {result.returncode}): {result.stderr}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                logger.warning(f"Command {cmd[0]} failed: {e}")
                continue
        
        # Clean up temp file
        try:
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)
        except Exception:
            pass  # Ignore cleanup errors
        
        if not success:
            logger.info(f"💡 To manually generate PNG: npx mmdc -i {mermaid_content.split()[0] if mermaid_content else 'diagram.mmd'} -o {output_path}")
            
        return success
            
    except Exception as e:
        logger.error(f"Error generating Mermaid image: {e}")
        return False


def log_execution_flow_diagram(executed_nodes: List[str], question: str, step_count: int):
    """
    Log the complete execution flow as a Mermaid diagram and generate visual output.
    
    Args:
        executed_nodes: List of nodes that were executed
        question: User's original question
        step_count: Number of steps executed
    """
    logger.info("📊 EXECUTION FLOW DIAGRAM")
    logger.info("=" * 80)
    
    # Generate the diagram
    mermaid_content, mermaid_file = generate_execution_mermaid_diagram(executed_nodes, question)
    
    # Log the diagram source
    logger.info("```mermaid")
    for line in mermaid_content.split('\n'):
        logger.info(line)
    logger.info("```")
    
    logger.info(f"💾 Mermaid diagram saved to: {mermaid_file}")
    
    # Try to generate PNG image
    png_file = mermaid_file.replace('.mmd', '.png')
    if generate_mermaid_image(mermaid_content, png_file):
        logger.info(f"🖼️  PNG diagram saved to: {png_file}")
    else:
        logger.warning("⚠️  Could not generate PNG diagram automatically")
        logger.info(f"💡 To generate PNG manually, run: npx mmdc -i {mermaid_file} -o {png_file}")
        logger.info("   Or view the .mmd file in any Mermaid-compatible viewer")
    
    logger.info("=" * 80)
    logger.info(f"📈 Flow Summary: {step_count} steps, {len(executed_nodes)} nodes executed")
    logger.info(f"🔗 Path: {' → '.join(executed_nodes)}")
    logger.info("=" * 80)


def create_analytics_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the analytics agent.
    
    Returns:
        Configured StateGraph with all nodes and conditional edges
    """
    # Initialize the state graph
    workflow = StateGraph(AgentState)
    
    # Add all nodes (removed visualize node)
    workflow.add_node("intent", intent_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("lookup_schema", lookup_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("fix_sql_error", fix_sql_error_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("interpret_results", interpret_results)
    
    # Set entry point
    workflow.set_entry_point("intent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "intent",
        decide_after_intent,
        {
            "clarification": "clarification",
            "lookup_schema": "lookup_schema",
            "operation_not_permitted": END  # This new route tells the graph to stop.
        }
    )
    
    # Clarification can either wait for user or continue
    workflow.add_conditional_edges(
        "clarification",
        decide_after_clarification,
        {
            "wait_for_user": END,  # This will pause the workflow
            "lookup_schema": "lookup_schema"
        }
    )
    
    # Schema lookup always goes to SQL generation
    workflow.add_edge("lookup_schema", "generate_sql")
    
    # SQL generation always goes to validation
    workflow.add_edge("generate_sql", "validate_sql")
    
    # Validation can either proceed to execution or retry generation
    workflow.add_conditional_edges(
        "validate_sql",
        decide_after_validation,
        {
            "execute_sql": "execute_sql",
            "retry_generation": "generate_sql",
            "error": END
        }
    )
    
    # Execution can succeed, fail, or need error fixing (removed visualize)
    workflow.add_conditional_edges(
        "execute_sql",
        decide_after_execution,
        {
            "summarize": "summarize",
            "fix_error": "fix_sql_error",
            "error": END
        }
    )
    
    # Error fixing goes back to validation
    workflow.add_conditional_edges(
        "fix_sql_error",
        decide_after_error_fix,
        {
            "validate_sql": "validate_sql",
            "error": END
        }
    )
    
    # Workflow continues to business interpretation after summarization
    workflow.add_edge("summarize", "interpret_results")
    
    # Business interpretation ends the workflow
    workflow.add_edge("interpret_results", END)
    
    return workflow


# In agent/graph.py

def decide_after_intent(state: AgentState) -> Literal["clarification", "lookup_schema", "operation_not_permitted"]:
    """
    Decide whether to halt, ask for clarification, or proceed with schema lookup.
    """
    # First, check for the security block. This is the highest priority.
    if state.get("operation_not_permitted", False):
        logger.error(f"HALTING: Intent check blocked a non-GET operation.")
        return "operation_not_permitted"
    
    # If the operation is permitted, then check for ambiguity.
    elif state.get("clarification_needed", False):
        logger.info("Intent detected ambiguity, proceeding to clarification")
        return "clarification"
        
    # If the operation is permitted and no clarification is needed, proceed.
    else:
        logger.info("Intent clear, proceeding to schema lookup")
        return "lookup_schema"


def decide_after_clarification(state: AgentState) -> Literal["wait_for_user", "lookup_schema"]:
    """
    Decide whether to wait for user input or continue with resolved clarification.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute or wait signal
    """
    if state.get("user_clarification_response"):
        logger.info("User clarification received, proceeding to schema lookup")
        return "lookup_schema"
    else:
        logger.info("Waiting for user clarification")
        return "wait_for_user"


def decide_after_validation(state: AgentState) -> Literal["execute_sql", "retry_generation", "error"]:
    """
    Decide what to do after SQL validation.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    if state.get("validated_sql"):
        logger.info("SQL validation successful, proceeding to execution")
        return "execute_sql"
    elif state.get("retry_count", 0) < state.get("max_retries", 3):
        logger.info("SQL validation failed, retrying generation")
        return "retry_generation"
    else:
        logger.error("SQL validation failed, max retries exceeded")
        return "error"


def decide_after_execution(state: AgentState) -> Literal["summarize", "fix_error", "error"]:
    """
    Decide what to do after SQL execution.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    execution_result = state.get("execution_result")
    execution_error = state.get("execution_error")
    
    # Properly check if we have results (handle serialized DataFrames)
    has_results = False
    if execution_result is not None:
        try:
            # Check if it's a serialized DataFrame from our execution node
            if isinstance(execution_result, dict) and execution_result.get('type') == 'dataframe':
                has_results = len(execution_result.get('data', [])) > 0
            # Check if it's a pandas DataFrame (fallback)
            elif hasattr(execution_result, 'empty'):
                has_results = not execution_result.empty
            elif isinstance(execution_result, list):
                has_results = len(execution_result) > 0
            else:
                has_results = True  # Other types of results
        except Exception as e:
            # If any check fails, use basic check
            logger.warning(f"Error checking execution results: {e}")
            has_results = execution_result is not None
    
    if has_results:
        logger.info("SQL execution successful, proceeding to summary")
        return "summarize"
    elif execution_error and state.get("retry_count", 0) < state.get("max_retries", 3):
        logger.info("SQL execution failed, attempting error fix")
        return "fix_error"
    else:
        logger.error("SQL execution failed, max retries exceeded")
        return "error"


def decide_after_error_fix(state: AgentState) -> Literal["validate_sql", "error"]:
    """
    Decide what to do after attempting to fix SQL errors.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    if state.get("generated_sql") and state.get("retry_count", 0) < state.get("max_retries", 3):
        logger.info("SQL error fix attempted, proceeding to validation")
        return "validate_sql"
    else:
        logger.error("SQL error fix failed, max retries exceeded")
        return "error"


def run_agent_chat(question: str, history: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
    """
    Run the analytics agent chat workflow.
    
    Args:
        question: User's natural language question
        history: Conversation history
        **kwargs: Additional configuration parameters
        
    Returns:
        Dictionary containing results and updated conversation history
    """
    logger.info("="*80)
    logger.info("🚀 STARTING ANALYTICS AGENT WORKFLOW")
    logger.info("="*80)
    logger.info(f"📥 User Question: {question}")
    logger.info(f"📚 History Length: {len(history)} messages")
    logger.info(f"⚙️  Max Retries: {kwargs.get('max_retries', 3)}")
    
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
        "max_retries": kwargs.get("max_retries", 3),
        "current_node": None,
        "completed_nodes": []
    }
    
    logger.info("🔧 Initial state prepared")
    
    try:
        # Create and compile the workflow
        logger.info("🔨 Creating and compiling LangGraph workflow...")
        workflow = create_analytics_graph()
        app = workflow.compile(checkpointer=MemorySaver())
        logger.info("✅ Workflow compiled successfully")
        
        # Run the workflow
        thread_id = kwargs.get("thread_id", "default")
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": kwargs.get("recursion_limit", 50)  # Increase recursion limit
        }
        
        logger.info(f"🧵 Starting workflow execution (thread_id: {thread_id})")
        
        step_count = 0
        executed_nodes = []  # Track the actual execution path
        final_state = None
        for state in app.stream(initial_state, config):
            step_count += 1
            final_state = state
            
            # Log current step and track executed nodes
            if isinstance(state, dict) and state:
                current_node = list(state.keys())[0]
                logger.info(f"📍 Step {step_count}: Executing node '{current_node}'")
                
                # Track unique nodes in execution order
                if current_node not in executed_nodes:
                    executed_nodes.append(current_node)
                
                # Log key state information
                node_state = state[current_node]
                if isinstance(node_state, dict):
                    if node_state.get("execution_error"):
                        logger.warning(f"⚠️  Execution error in {current_node}: {node_state.get('execution_error')}")
                    if node_state.get("generated_sql"):
                        logger.info(f"🔍 Generated SQL: {node_state.get('generated_sql')[:100]}...")
                    if node_state.get("validated_sql"):
                        logger.info("✅ SQL validation passed")
                    if node_state.get("summary"):
                        logger.info("📝 Summary generated")
            
            # Check if we need to wait for user input
            if "clarification" in state and state["clarification"]["clarification_needed"]:
                if not state["clarification"].get("user_clarification_response"):
                    logger.info("⏸️  Workflow paused for user clarification")
                    break
        
        logger.info(f"🏁 Workflow completed after {step_count} steps")
        
        # Extract results from final state
        if final_state:
            # Debug: Log the structure of the final state
            logger.info(f"🔍 Final state type: {type(final_state)}")
            logger.info(f"🔍 Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'not a dict'}")
            
            result_state = list(final_state.values())[0] if isinstance(final_state, dict) else final_state
            
            # Debug: Log the result state
            logger.info(f"🔍 Result state type: {type(result_state)}")
            if isinstance(result_state, dict):
                logger.info(f"🔍 Result state keys: {list(result_state.keys())}")
                logger.info(f"🔍 Summary in result state: {'✅' if result_state.get('summary') else '❌'}")
                if result_state.get('summary'):
                    logger.info(f"🔍 Summary length: {len(result_state.get('summary'))}")
            
            logger.info("📊 WORKFLOW RESULTS:")
            logger.info(f"  - SQL Generated: {'✅' if result_state.get('validated_sql') else '❌'}")
            logger.info(f"  - Summary: {'✅' if result_state.get('summary') else '❌'}")
            logger.info(f"  - Errors: {'❌ ' + str(result_state.get('execution_error')) if result_state.get('execution_error') else '✅ None'}")
            
            if result_state.get("operation_not_permitted"):
                result = {
                    "error": result_state.get("operation_feedback"),
                    "operation_not_permitted": True, # Pass the flag to the UI
                    "history": result_state.get("history", []),
                    "completed_nodes": result_state.get("completed_nodes", [])
                }
            else:
                # If not halted, build the normal success/error response.
                result = {
                    "sql": result_state.get("validated_sql"),
                    "generated_sql": result_state.get("validated_sql"),
                    "summary": result_state.get("summary"),
                    "business_interpretation": result_state.get("business_interpretation"),
                    "history": result_state.get("history", []),
                    "clarification_question": result_state.get("clarification_question"),
                    "clarification_needed": result_state.get("clarification_needed", False),
                    "execution_result": result_state.get("execution_result"),
                    "execution_error": result_state.get("execution_error"),
                    "completed_nodes": result_state.get("completed_nodes", [])
                }
            
            logger.info("="*80)
            logger.info("🎉 ANALYTICS AGENT WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            
            # Generate and log the execution flow diagram
            #log_execution_flow_diagram(executed_nodes, question, step_count)
            
            return result
        else:
            logger.error("❌ Workflow failed to produce results")
            return {
                "error": "Workflow failed to produce results",
                "history": history
            }
            
    except Exception as e:
        logger.error("="*80)
        logger.error("💥 ANALYTICS AGENT WORKFLOW ERROR")
        logger.error("="*80)
        logger.error(f"❌ Error Type: {type(e).__name__}")
        logger.error(f"❌ Error Message: {e}")
        logger.error(f"❌ Question: {question}")
        logger.error("="*80)
        return {
            "error": str(e),
            "history": history
        }


def continue_agent_chat(
    user_response: str, 
    thread_id: str, 
    **kwargs
) -> Dict[str, Any]:
    """
    Continue a paused agent workflow with user clarification.
    
    Args:
        user_response: User's clarification response
        thread_id: Thread ID for the conversation
        **kwargs: Additional configuration parameters
        
    Returns:
        Dictionary containing results and updated conversation history
    """
    try:
        # Create and compile the workflow
        workflow = create_analytics_graph()
        app = workflow.compile(checkpointer=MemorySaver())
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Update state with user response
        update_state = {
            "user_clarification_response": user_response,
            "clarification_needed": False
        }
        
        # Continue the workflow
        final_state = None
        for state in app.stream(update_state, config):
            final_state = state
        
        # Extract results from final state
        if final_state:
            result_state = list(final_state.values())[0] if isinstance(final_state, dict) else final_state
            
            return {
                "sql": result_state.get("validated_sql"),
                "summary": result_state.get("summary"),
                "business_interpretation": result_state.get("business_interpretation"),  # ✅ Add business interpretation
                "visualization_path": result_state.get("visualization_path"),
                "history": result_state.get("history", []),
                "execution_error": result_state.get("execution_error"),
                "completed_nodes": result_state.get("completed_nodes", [])
            }
        else:
            return {
                "error": "Workflow failed to produce results"
            }
            
    except Exception as e:
        logger.error(f"Error continuing agent chat: {e}")
        return {
            "error": str(e)
        }

    return {
        "sql": result.get("validated_sql"),
        "summary": result.get("summary"),
        "visualization_path": result.get("visualization_path"),
        "history": result.get("history"),
    }