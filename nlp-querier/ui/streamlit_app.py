"""
Fixed Streamlit Chat Interface for the LangGraph Analytics Agent.
Clean implementation without duplicate elements.
"""
import streamlit as st
import sys
from pathlib import Path
import json
from typing import Dict, List, Any
import os
import logging
from datetime import datetime

# Configure comprehensive logging for the application
def setup_logging():
    """Set up detailed logging configuration for the Analytics Agent."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("output/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"analytics_agent_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also log to console
        ]
    )
    
    # Set specific loggers to INFO level
    for logger_name in [
        'agent.graph',
        'agent.nodes.generate_sql',
        'agent.nodes.validate_sql', 
        'agent.nodes.execute_sql',
        'agent.tools.sql_validator_tool',
        'agent.tools.sql_executor_tool',
        'agent.tools.schema_tool'
    ]:
        logging.getLogger(logger_name).setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("🚀 ANALYTICS AGENT - STREAMLIT APPLICATION STARTED")
    logger.info("="*80)
    logger.info(f"📝 Logging to file: {log_filename}")
    logger.info(f"📊 Log level: {logging.getLevelName(logging.getLogger().level)}")
    
    return log_filename

# Setup logging before anything else
log_file = setup_logging()
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Analytics Agent",
    page_icon="🤖",
    layout="wide"
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import agent components
try:
    from agent.graph import run_agent_chat
    from agent.state import AgentState
except ImportError as e:
    st.error(f"Error importing agent components: {e}")
    st.stop()


import streamlit as st
import json
import sys
import os

# Add the parent directory to the path so we can import the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import common libraries
import pandas as pd
import json
from pathlib import Path

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "thread_id" not in st.session_state:
        import uuid
        st.session_state.thread_id = f"user_{str(uuid.uuid4())[:8]}"
    
    if "awaiting_clarification" not in st.session_state:
        st.session_state.awaiting_clarification = False
    
    if "clarification_question" not in st.session_state:
        st.session_state.clarification_question = None


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Main interface
    st.title("🤖 Analytics Agent")
    st.caption("Ask natural language questions about your data")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Clear chat button with unique key
        if st.button("🗑️ Clear Chat", key="sidebar_clear_chat"):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.awaiting_clarification = False
            # Reset thread_id to start fresh memory
            import uuid
            st.session_state.thread_id = f"user_{str(uuid.uuid4())[:8]}"
            st.rerun()
        
        # Stats
        st.subheader("Stats")
        st.metric("Messages", len(st.session_state.messages))
        
        # Memory persistence info
        st.subheader("🧠 Memory")
        st.info(f"**Session ID:** `{st.session_state.thread_id}`")
        st.caption("Each conversation has persistent memory across messages")
        
        # Logging Information
        st.subheader("📊 Logging")
        st.info(f"**Log File:** `{log_file.name}`")
        st.caption("All workflow steps are logged in detail. Check the console or log file for full execution trace.")
        
        # Log level controls
        current_level = logging.getLogger().level
        level_name = logging.getLevelName(current_level)
        st.write(f"**Log Level:** {level_name}")
        
        if st.button("🔍 View Log File Location", key="show_log_location"):
            st.write(f"Full path: `{log_file}`")
        
        st.divider()
        
        # Export if messages exist
        if st.session_state.messages:
            # Create a serializable version of messages for export
            exportable_messages = []
            for msg in st.session_state.messages:
                export_msg = {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                # Only include serializable metadata
                if "metadata" in msg and msg["metadata"]:
                    export_metadata = {}
                    for key, value in msg["metadata"].items():
                        # Skip DataFrames and other non-serializable objects
                        if key == "execution_result":
                            if value is not None:
                                try:
                                    import pandas as pd
                                    if isinstance(value, pd.DataFrame):
                                        export_metadata[key] = f"DataFrame with {len(value)} rows and {len(value.columns)} columns"
                                    else:
                                        export_metadata[key] = str(value)
                                except:
                                    export_metadata[key] = str(value)
                        elif isinstance(value, (str, int, float, bool, type(None))):
                            export_metadata[key] = value
                        else:
                            export_metadata[key] = str(value)
                    if export_metadata:
                        export_msg["metadata"] = export_metadata
                exportable_messages.append(export_msg)
            
            conversation_json = json.dumps(exportable_messages, indent=2)
            st.download_button(
                label="📥 Export Chat",
                data=conversation_json,
                file_name="analytics_chat.json",
                mime="application/json",
                key="sidebar_export_chat"
            )
    
    # Display existing messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show metadata if available (SQL, results, etc.)
            if "metadata" in message and message["metadata"]:
                metadata = message["metadata"]
                
                # Show SQL
                if metadata.get("sql"):
                    with st.expander("Generated SQL"):
                        st.code(metadata["sql"], language="sql")
                
                # Show execution results
                execution_result = metadata.get("execution_result")
                if execution_result is not None:
                    # Handle both formats: 'dataframe' from execution node and 'DataFrame' from UI processing
                    if isinstance(execution_result, dict) and execution_result.get("type") in ["DataFrame", "dataframe"]:
                        # Handle serialized DataFrame
                        data = execution_result.get("data", [])
                        if data:
                            import pandas as pd
                            df = pd.DataFrame(data)
                            # Use shape if available, otherwise count data
                            shape = execution_result.get("shape", (len(df), len(df.columns) if len(df) > 0 else 0))
                            row_count = shape[0] if isinstance(shape, (tuple, list)) else len(df)
                            truncated = execution_result.get("truncated", False)
                            
                            title = f"Query Results ({row_count} rows, {shape[1] if isinstance(shape, (tuple, list)) else len(df.columns)} columns)"
                            if truncated:
                                title += " - Showing first 50"
                                
                            with st.expander(title, expanded=True):
                                # Show PII protection status if available
                                if "pii_findings" in metadata:
                                    pii_findings = metadata["pii_findings"]
                                    if pii_findings:
                                        pii_count = sum(len(findings) for findings in pii_findings.values())
                                        st.warning(f"🔒 **Privacy Protection:** {pii_count} PII instances detected and redacted")
                                        
                                        with st.expander("PII Detection Details", expanded=False):
                                            for column, findings in pii_findings.items():
                                                st.write(f"**Column '{column}':** {len(findings)} instances")
                                                for finding in findings[:3]:  # Show first 3
                                                    st.write(f"  • {finding.get('description', finding.get('type', 'Unknown'))}")
                                                if len(findings) > 3:
                                                    st.write(f"  • ... and {len(findings) - 3} more")
                                    else:
                                        st.success("🔒 **Privacy Protection:** No PII detected in results")
                                
                                st.dataframe(df, use_container_width=True)
                                
                                # Data preview is sufficient - no need for raw statistics
                                # The agent summary provides business context instead
                                
                                if truncated:
                                    st.info(f"Showing first 50 rows of {row_count} total rows")
                        else:
                            st.info("**Result:** Query executed successfully but returned no data")
                            st.write("**Possible reasons:**")
                            st.write("• The filter criteria don't match any data")
                            st.write("• The date range may be outside available data")
                            st.write("• Try using different filter values or check table contents")
                    elif execution_result is not None:
                        st.write("**Result:** ", str(execution_result))
                
                # Show errors
                if metadata.get("execution_error"):
                    st.error(f"Execution Error: {metadata['execution_error']}")
                
                # Show SQL explanation in collapsible section
                if metadata.get("summary"):
                    with st.expander("Query Explanation"):
                        st.markdown(metadata["summary"])
                else:
                    st.warning("⚠️ No query explanation available in metadata")
                
                # Show business interpretation in collapsible section
                if metadata.get("business_interpretation"):
                    content = metadata["business_interpretation"]
                    with st.expander("Business Insights"):
                        # Check if it looks like JSON
                        if content.strip().startswith('{') and content.strip().endswith('}'):
                            st.error("⚠️ Raw JSON detected instead of formatted content. This should be formatted markdown.")
                            st.code(content, language='json')
                        else:
                            st.markdown(content)
                        st.caption("LLM-powered business analysis of query results")
                
                # Show other metadata in collapsed section
                other_metadata = {k: v for k, v in metadata.items() 
                                if k not in ['sql', 'execution_result', 'execution_error', 'summary', 'business_interpretation'] and v}
                if other_metadata:
                    with st.expander("Additional Details"):
                        st.json(other_metadata)
    
    # Chat input
    prompt_text = "Provide clarification:" if st.session_state.awaiting_clarification else "Ask a question about your data:"
    
    if user_input := st.chat_input(prompt_text):
        # Log user interaction
        logger.info("💬 USER INTERACTION")
        logger.info(f"  - User Input: {user_input}")
        logger.info(f"  - Awaiting Clarification: {st.session_state.awaiting_clarification}")
        logger.info(f"  - Message Count: {len(st.session_state.messages)}")
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                logger.info("🔄 Starting agent processing...")
                try:
                    if st.session_state.awaiting_clarification:
                        logger.info("📝 Processing clarification response")
                        # Use full LangGraph with memory persistence
                        result = run_agent_chat(
                            user_input, 
                            st.session_state.conversation_history,
                            thread_id=st.session_state.thread_id
                        )
                    else:
                        logger.info("🆕 Starting new conversation")
                        # Use full LangGraph with memory persistence
                        result = run_agent_chat(
                            user_input, 
                            st.session_state.conversation_history,
                            thread_id=st.session_state.thread_id
                        )
                    
                    logger.info("📊 Agent processing completed")
                    
                    # Handle response
                    if result:
                        # Check if clarification is needed
                        if result.get("clarification_needed", False):
                            clarification_msg = result.get("clarification_question", "Could you please clarify your request?")
                            logger.info(f"❓ Clarification needed: {clarification_msg}")
                            st.write(clarification_msg)
                            
                            # Add to messages
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": clarification_msg,
                                "metadata": {"type": "clarification"}
                            })
                            
                            st.session_state.awaiting_clarification = True
                            st.session_state.clarification_question = clarification_msg
                            
                        else:
                            # Regular response
                            summary = result.get("summary", "I've processed your request.")
                            logger.info(f"✅ Successful response generated")
                            logger.info(f"  - Summary length: {len(summary)} characters")
                            logger.info(f"  - SQL generated: {'✅' if result.get('sql') else '❌'}")
                            logger.info(f"  - Execution result: {'✅' if result.get('execution_result') is not None else '❌'}")
                            
                            # Display a brief acknowledgment instead of the full summary
                            # The detailed explanation will be in the collapsible section
                            st.success("✅ Query completed successfully! Check the Query Explanation section below for details.")
                            
                            # Add to messages (with DataFrame handling for session state)
                            execution_result = result.get("execution_result")
                            serializable_result = None
                            if execution_result is not None:
                                try:
                                    # Check if it's already serialized from our execution node
                                    if isinstance(execution_result, dict) and execution_result.get('type') == 'dataframe':
                                        # It's already in the format we want, just rename the type for consistency
                                        serializable_result = execution_result.copy()
                                        serializable_result['type'] = 'DataFrame'  # Keep UI consistent
                                    else:
                                        # Handle other formats (fallback)
                                        import pandas as pd
                                        if isinstance(execution_result, pd.DataFrame) and not execution_result.empty:
                                            # Store DataFrame info instead of the full DataFrame for session state
                                            serializable_result = {
                                                "type": "DataFrame",
                                                "rows": len(execution_result),
                                                "columns": list(execution_result.columns),
                                                "data": execution_result.to_dict('records') if len(execution_result) <= 50 else execution_result.head(50).to_dict('records'),
                                                "truncated": len(execution_result) > 50
                                            }
                                        elif isinstance(execution_result, pd.DataFrame):
                                            # Handle empty DataFrame
                                            serializable_result = {
                                                "type": "DataFrame",
                                                "rows": 0,
                                                "columns": list(execution_result.columns),
                                                "data": [],
                                                "truncated": False
                                            }
                                        else:
                                            serializable_result = execution_result if execution_result is not None else {"type": "empty", "data": []}
                                except:
                                    serializable_result = str(execution_result)
                            
                            message_data = {
                                "role": "assistant",
                                "content": "✅ Query completed successfully! Check the Query Explanation section below for details.",
                                "metadata": {
                                    "sql": result.get("sql"),
                                    "execution_result": serializable_result,
                                    "execution_error": result.get("execution_error"),
                                    "visualization_path": result.get("visualization_path"),
                                    "summary": summary,
                                    "business_interpretation": result.get("business_interpretation")
                                }
                            }
                            st.session_state.messages.append(message_data)
                            
                            # Show SQL if available
                            if result.get("sql"):
                                with st.expander("Generated SQL"):
                                    st.code(result["sql"], language="sql")
                            
                            # Show Query Explanation immediately
                            if result.get("summary"):
                                with st.expander("Query Explanation", expanded=False):
                                    st.markdown(result["summary"])
                            
                            # Show Business Insights immediately if available
                            if result.get("business_interpretation"):
                                with st.expander("Business Insights", expanded=False):
                                    st.markdown(result["business_interpretation"])
                                    st.caption("LLM-powered business analysis of query results")
                            else:
                                st.write(f"🔍 **Business Insights value**: {repr(result.get('business_interpretation'))}")
                            
                            # Show execution results if available (for live display)
                            execution_result = result.get("execution_result")
                            if execution_result is not None:
                                try:
                                    # Handle serialized DataFrame from execution node
                                    if isinstance(execution_result, dict) and execution_result.get('type') == 'dataframe':
                                        data = execution_result.get('data', [])
                                        shape = execution_result.get('shape', (len(data) if data else 0, 0))
                                        
                                        if data:
                                            import pandas as pd
                                            df = pd.DataFrame(data)
                                            
                                            with st.expander(f"Query Results ({shape[0]} rows, {shape[1]} columns)", expanded=True):
                                                st.dataframe(df, use_container_width=True)
                                                
                                                # Data preview is sufficient - agent summary provides business context
                                        else:
                                            st.info("**Result:** Query executed successfully but returned no data")
                                            st.write("**Possible reasons:**")
                                            st.write("- The filter criteria don't match any data")
                                            st.write("- Try using different region names (e.g., 'North America' instead of 'USA')")
                                    
                                    # Handle direct pandas DataFrame (fallback)
                                    elif hasattr(execution_result, 'empty'):  # pandas DataFrame
                                        import pandas as pd
                                        if not execution_result.empty:
                                            with st.expander(f"Query Results ({len(execution_result)} rows)", expanded=True):
                                                st.dataframe(execution_result, use_container_width=True)
                                                
                                                # Data preview is sufficient - agent summary provides business context
                                        else:
                                            st.info("**Result:** Query executed successfully but returned no data")
                                            st.write("**Possible reasons:**")
                                            st.write("• The filter criteria don't match any data")
                                            st.write("• The date range may be outside available data")
                                            st.write("• Try using different filter values or check table contents")
                                    
                                    # Handle other result types
                                    else:
                                        st.write("**Result:** ", str(execution_result))
                                        
                                except Exception as e:
                                    logger.error(f"Error displaying execution result: {e}")
                                    st.write("**Result:** ", str(execution_result))
                            
                            # Show execution error if any
                            if result.get("execution_error"):
                                st.error(f"Execution Error: {result['execution_error']}")
                            
                            # Reset clarification state
                            st.session_state.awaiting_clarification = False
                            st.session_state.clarification_question = None
                    
                    else:
                        error_msg = "Sorry, I couldn't process your request."
                        logger.error(f"❌ Agent returned empty result")
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "metadata": {"type": "error"}
                        })
                
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    logger.error("❌ STREAMLIT APPLICATION ERROR")
                    logger.error(f"  - Error Type: {type(e).__name__}")
                    logger.error(f"  - Error Message: {e}")
                    logger.error(f"  - User Input: {user_input}")
                    
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "metadata": {"type": "error", "exception": str(e)}
                    })
        
        # Update conversation history with detailed context
        logger.info(f"📝 Updating conversation history (current length: {len(st.session_state.conversation_history)})")
        
        # Add user message
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Add assistant response with SQL context if available
        if len(st.session_state.messages) > 0:
            last_message = st.session_state.messages[-1]
            if last_message["role"] == "assistant":
                assistant_content = last_message["content"]
                
                # Extract metadata for context
                metadata = last_message.get("metadata", {})
                
                # Build enriched assistant message with SQL context
                enriched_content = assistant_content
                if metadata.get("sql"):
                    enriched_content += f"\n\nGenerated SQL: {metadata['sql']}"
                if metadata.get("result_summary"):
                    enriched_content += f"\n\nResult: {metadata['result_summary']}"
                
                st.session_state.conversation_history.append({
                    "role": "assistant", 
                    "content": enriched_content,
                    "sql": metadata.get("sql"),
                    "result_summary": metadata.get("result_summary")
                })
        
        logger.info(f"💬 Conversation updated (new length: {len(st.session_state.conversation_history)})")


if __name__ == "__main__":
    main()