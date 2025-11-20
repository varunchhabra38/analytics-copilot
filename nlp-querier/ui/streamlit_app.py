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
# caching
    if "query_cache" not in st.session_state:
        st.session_state.query_cache = {}


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
                
                # Check for operation_not_permitted flag
                if metadata.get("operation_not_permitted"):
                    st.warning("⚠️ Operation not permitted: The requested delete operation was blocked.")

                # Show execution results
                execution_result = metadata.get("execution_result")
                logger.info(f"DEBUG: execution_result = {execution_result}")  # Debugging log

                if execution_result is not None:
                    # Handle both formats: 'dataframe' from execution node and 'DataFrame' from UI processing
                    if isinstance(execution_result, dict) and execution_result.get("type") in ["DataFrame", "dataframe"]:
                        # Handle serialized DataFrame
                        data = execution_result.get("data", []) or []  # Ensure data is a list
                        logger.info(f"DEBUG: data = {data}")  # Debugging log

                        if data:
                            df = pd.DataFrame(data)
                            # Use shape if available, otherwise count data
                            shape = execution_result.get("shape") or (len(df), len(df.columns) if len(df) > 0 else 0)  # Ensure shape is valid
                            logger.info(f"DEBUG: shape = {shape}")  # Debugging log

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
                # skipping summarization
                # if metadata.get("summary"):
                #     with st.expander("Query Explanation"):
                #         st.markdown(metadata["summary"])
                # else:
                #     st.warning("⚠️ No query explanation available in metadata")
                
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
                    # --- CACHING LOGIC ---
                    if not st.session_state.awaiting_clarification and user_input in st.session_state.query_cache:
                        logger.info("✅ Cache hit! Returning cached result.")
                        st.info("⚡️ Returning a cached response for this question.")
                        result = st.session_state.query_cache[user_input]
                    else:
                        logger.info("❌ Cache miss. Running full agent workflow.")
                        result = run_agent_chat(
                            user_input, 
                            st.session_state.conversation_history,
                            thread_id=st.session_state.thread_id
                        )
                        if result and not result.get("error") and not result.get("operation_not_permitted") and not result.get("clarification_needed"):
                            logger.info("✅ Caching successful result for future use.")
                            st.session_state.query_cache[user_input] = result
                    # --- END OF CACHING LOGIC ---

                    logger.info("📊 Agent processing completed")
                    
                    if result:
                        if result.get("operation_not_permitted"):
                            error_msg = result.get("error", "This operation is not permitted.")
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg, "metadata": {"type": "error", "operation_not_permitted": True}})
                        
                        elif result.get("clarification_needed", False):
                            clarification_msg = result.get("clarification_question", "Could you please clarify your request?")
                            st.write(clarification_msg)
                            st.session_state.messages.append({"role": "assistant", "content": clarification_msg, "metadata": {"type": "clarification"}})
                            st.session_state.awaiting_clarification = True
                            st.session_state.clarification_question = clarification_msg
                            
                        else:
                            # Regular successful response
                            st.success("✅ Query completed successfully!")
                            
                            # Prepare serializable result for session state
                            execution_result = result.get("execution_result")
                            serializable_result = None
                            if isinstance(execution_result, dict) and execution_result.get('type') == 'dataframe':
                                serializable_result = execution_result
                            
                            message_data = {
                                "role": "assistant",
                                "content": "Query completed. See details below.",
                                "metadata": {
                                    "sql": result.get("sql"),
                                    "execution_result": serializable_result,
                                    "execution_error": result.get("execution_error"),
                                    "business_interpretation": result.get("business_interpretation")
                                }
                            }
                            st.session_state.messages.append(message_data)
                            
                            # Display results immediately
                            if result.get("sql"):
                                with st.expander("Generated SQL"):
                                    st.code(result["sql"], language="sql")
                            
                            if result.get("business_interpretation"):
                                with st.expander("Business Insights", expanded=True):
                                    st.markdown(result["business_interpretation"])
                            
                            if serializable_result and serializable_result.get("data"):
                                df = pd.DataFrame(serializable_result["data"])
                                shape = serializable_result.get("shape", (len(df), len(df.columns)))
                                with st.expander(f"Query Results ({shape[0]} rows, {shape[1]} columns)", expanded=True):
                                    st.dataframe(df, use_container_width=True)
                            elif result.get("execution_result") is not None:
                                st.info("Query executed successfully but returned no data.")

                            if result.get("execution_error"):
                                st.error(f"Execution Error: {result['execution_error']}")
                            
                            st.session_state.awaiting_clarification = False
                            st.session_state.clarification_question = None
                    
                    else:
                        error_msg = "Sorry, I couldn't process your request. The agent returned an empty result."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg, "metadata": {"type": "error"}})
                
                except Exception as e:
                    error_msg = f"An unexpected application error occurred: {str(e)}"
                    logger.error(f"❌ STREAMLIT APPLICATION ERROR: {e}", exc_info=True)
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg, "metadata": {"type": "error", "exception": str(e)}})
        
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