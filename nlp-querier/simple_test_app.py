"""
Simple Streamlit Test App for Analytics Agent
Tests the basic functionality without complex UI elements.
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test imports
try:
    from agent.tools.schema_tool import SQLiteSchemaLookupTool
    from agent.tools.sql_gen_tool import create_sql_gen_tool
    from agent.tools.sql_executor_tool import SQLiteExecutorTool
    from config import get_database_manager
    
    st.success("✅ All imports successful!")
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

st.title("🤖 Analytics Agent - Simple Test")

st.header("Database Test")
try:
    db_manager = get_database_manager()
    schema = db_manager.get_schema()
    
    with st.expander("Database Schema", expanded=True):
        st.text(schema)
    
    # Simple query test
    result = db_manager.execute_query("SELECT region, SUM(total_amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC")
    
    if result['success']:
        st.success("✅ Database query successful!")
        st.dataframe(result['rows'])
    else:
        st.error(f"❌ Database query failed: {result['error']}")
        
except Exception as e:
    st.error(f"❌ Database test failed: {e}")

st.header("SQL Generation Test")
try:
    # Test SQL generation
    schema_tool = SQLiteSchemaLookupTool("output/analytics.db")
    schema = schema_tool.get_schema()
    
    sql_gen_tool = create_sql_gen_tool("rule_based")
    result = sql_gen_tool.generate_sql("Show me total sales by region", schema, [])
    
    st.success("✅ SQL generation successful!")
    st.code(result['sql'], language='sql')
    st.write(f"**Explanation:** {result['explanation']}")
    
except Exception as e:
    st.error(f"❌ SQL generation test failed: {e}")

st.header("Manual Query Test")
user_query = st.text_area("Enter your question:", "Show me total sales by region")

if st.button("Test Query", key="test_query_btn"):
    try:
        # Use the SQL generation and execution tools
        schema_tool = SQLiteSchemaLookupTool("output/analytics.db")
        schema = schema_tool.get_schema()
        
        sql_gen_tool = create_sql_gen_tool("rule_based")
        sql_result = sql_gen_tool.generate_sql(user_query, schema, [])
        
        st.write("**Generated SQL:**")
        st.code(sql_result['sql'], language='sql')
        
        # Execute the SQL
        executor = SQLiteExecutorTool("output/analytics.db")
        exec_result = executor.execute_query(sql_result['sql'])
        
        if exec_result.get("error"):
            st.error(f"Execution error: {exec_result['error']}")
        else:
            st.success("✅ Query executed successfully!")
            st.dataframe(exec_result["result"])
            
    except Exception as e:
        st.error(f"❌ Query test failed: {e}")

st.markdown("---")
st.markdown("**Analytics Agent Status:** 🟢 Components Working")