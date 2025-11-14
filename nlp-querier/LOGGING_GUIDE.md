# 📊 Analytics Agent - Comprehensive Logging Guide

## 🎯 Overview

The Analytics Agent now includes detailed logging across all components to help you understand the complete workflow execution. This guide explains what's logged, where to find the logs, and how to interpret them.

## 📁 Log File Locations

### Main Application Logs
- **Location**: `output/logs/analytics_agent_YYYYMMDD_HHMMSS.log`
- **Format**: Timestamped with component names and detailed messages
- **Rotation**: New log file created each time the app starts

### Console Output
- All logs are also written to the console/terminal where you run the app
- Real-time visibility into the workflow execution

## 🔍 What Gets Logged

### 1. **Application Startup** 🚀
```
================================================================================
🚀 ANALYTICS AGENT - STREAMLIT APPLICATION STARTED
================================================================================
📝 Logging to file: analytics_agent_20241111_142530.log
📊 Log level: INFO
```

### 2. **User Interactions** 💬
```
💬 USER INTERACTION
  - User Input: Show me sales by region
  - Awaiting Clarification: False
  - Message Count: 0
🔄 Starting agent processing...
🆕 Starting new conversation
```

### 3. **LangGraph Workflow Execution** 🔨
```
================================================================================
🚀 STARTING ANALYTICS AGENT WORKFLOW
================================================================================
📥 User Question: Show me sales by region
📚 History Length: 0 messages
⚙️  Max Retries: 3
🔧 Initial state prepared
🔨 Creating and compiling LangGraph workflow...
✅ Workflow compiled successfully
🧵 Starting workflow execution (thread_id: default)
```

### 4. **Node Execution Progress** 📍
```
📍 Step 1: Executing node 'intent'
📍 Step 2: Executing node 'lookup_schema'
📍 Step 3: Executing node 'generate_sql'
🔍 Generated SQL: SELECT region, SUM(total_amount) as total_sales FROM sales GROUP BY region...
📍 Step 4: Executing node 'validate_sql'
✅ SQL validation passed
📍 Step 5: Executing node 'execute_sql'
📍 Step 6: Executing node 'visualize'
📍 Step 7: Executing node 'summarize'
🏁 Workflow completed after 7 steps
```

### 5. **SQL Generation Details** 🔧
```
🔧 SQL GENERATION NODE - STARTING
------------------------------------------------------------
📥 Input Parameters:
  - Question: Show me sales by region
  - Schema Length: 2847 chars
  - History Length: 0 messages
  - Retry Count: 0
🔧 Loading AI configuration...
  - Project ID: your-project-id
  - Model: gemini-1.5-flash
  - Temperature: 0.0
🤖 Attempting Vertex AI SQL generation...
🔄 Calling Vertex AI for SQL generation...
✅ Vertex AI successfully generated SQL (127 chars)
📊 SQL Generation Results:
  - SQL Generated: ✅ Yes
  - SQL Length: 127 characters
  - Explanation: This query groups sales data by region and calculates total sales for each region.
📝 Generated SQL:
     1: SELECT region, SUM(total_amount) as total_sales 
     2: FROM sales 
     3: GROUP BY region 
     4: ORDER BY total_sales DESC;
✅ SQL GENERATION NODE - COMPLETED SUCCESSFULLY
------------------------------------------------------------
```

### 6. **SQL Validation Process** 🔍
```
🔍 SQL VALIDATION NODE - STARTING
------------------------------------------------------------
📥 Input Parameters:
  - SQL Length: 127 characters
  - Retry Count: 0
📝 SQL to validate:
     1: SELECT region, SUM(total_amount) as total_sales 
     2: FROM sales 
     3: GROUP BY region 
     4: ORDER BY total_sales DESC;
🔧 Setting up database connection for schema validation...
  - Database Type: sqlite
  - Connected to SQLite: output/analytics.db
🔍 Starting SQL validation process...
🔍 SQLValidatorTool initialized (DB connection: ✅)
🔍 Starting SQL validation process...
  - SQL length: 127 characters
  - SQL preview: SELECT region, SUM(total_amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC;
🛡️  Checking for dangerous keywords...
✅ Security check passed - no dangerous keywords found
📋 Checking query type...
✅ Query type check passed - valid SELECT query
🗂️  Starting schema validation...
📋 Using cached schema information
  - Tables available: ['sales', 'customers']
✅ Schema validation passed
✅ SQL validation completed successfully
✅ Database connection closed
🔍 SQL VALIDATION NODE - COMPLETED
------------------------------------------------------------
```

### 7. **SQL Execution** ⚡
```
⚡ SQL EXECUTION NODE - STARTING
------------------------------------------------------------
🔒 SECURITY CHECKS:
  - Validation Error: ✅ None
  - Validated SQL: ✅ Present
📝 SQL to execute:
     1: SELECT region, SUM(total_amount) as total_sales 
     2: FROM sales 
     3: GROUP BY region 
     4: ORDER BY total_sales DESC;
🔧 Setting up database executor...
  - Database Type: sqlite
  - SQLite Path: output/analytics.db
⚡ Executing SQL query...
✅ SQL EXECUTION SUCCESSFUL
  - Rows returned: 3
  - Result type: pandas.DataFrame
  - Columns: ['region', 'total_sales']
  - Sample data:
      Row 0: {'region': 'North America', 'total_sales': 44200.0}
      Row 1: {'region': 'Europe', 'total_sales': 28300.0}
      Row 2: {'region': 'Asia', 'total_sales': 42700.0}
⚡ SQL EXECUTION NODE - COMPLETED
------------------------------------------------------------
```

### 8. **Security Events** 🛡️
When dangerous SQL is blocked:
```
🛡️  EXECUTION BLOCKED - Validation failed: SQL contains potentially dangerous keyword: DROP
🚫 SQL EXECUTION NODE - BLOCKED FOR SECURITY
```

### 9. **Error Handling** ❌
```
❌ SQL GENERATION NODE - ERROR
  Error Type: ValueError
  Error Message: Invalid model configuration
------------------------------------------------------------
```

### 10. **Final Results** 📊
```
📊 WORKFLOW RESULTS:
  - SQL Generated: ✅
  - Visualization: ✅
  - Summary: ✅
  - Errors: ✅ None
================================================================================
🎉 ANALYTICS AGENT WORKFLOW COMPLETED SUCCESSFULLY
================================================================================
```

## 🎛️ Log Configuration

### Current Settings
- **Log Level**: INFO (captures all important events)
- **Format**: `%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s`
- **Output**: File + Console
- **Encoding**: UTF-8

### Component Loggers
- `agent.graph` - Main workflow orchestration
- `agent.nodes.generate_sql` - SQL generation process
- `agent.nodes.validate_sql` - SQL validation steps
- `agent.nodes.execute_sql` - SQL execution and security
- `agent.tools.sql_validator_tool` - Validation tool details
- `agent.tools.sql_executor_tool` - Execution tool details
- `agent.tools.schema_tool` - Database schema operations

## 🔍 How to Monitor the Flow

### 1. **Real-time Monitoring**
- Open your terminal where the Streamlit app is running
- Watch the console output for live logging
- Each user interaction triggers a complete logged workflow

### 2. **Log File Analysis**
- Check the `output/logs/` directory for detailed log files
- Use text editors or log viewers to analyze the full execution trace
- Search for specific keywords like "ERROR", "WARNING", or workflow stages

### 3. **Streamlit UI Indicators**
- The sidebar shows the current log file location
- Log level information is displayed
- Error messages appear directly in the chat interface

### 4. **Key Patterns to Look For**

**Successful Flow:**
```
🚀 STARTING → 📍 Steps 1-7 → 🏁 Workflow completed → 🎉 COMPLETED SUCCESSFULLY
```

**Validation Issues:**
```
🔍 SQL VALIDATION → ❌ Schema validation failed → 🛡️ EXECUTION BLOCKED
```

**AI Fallbacks:**
```
🤖 Attempting Vertex AI → ⚠️ Vertex AI failed → 🔄 Falling back to rule-based
```

## 📈 Performance Insights

The logs include timing information and step counts to help you understand:
- Which nodes take the longest to execute
- How many retry attempts occur
- Database connection performance
- AI model response times

## 🐛 Debugging Tips

1. **Search for Error Patterns**: Look for "❌", "ERROR", "FAILED"
2. **Check Security Blocks**: Look for "🛡️ EXECUTION BLOCKED"
3. **Trace User Input**: Find "💬 USER INTERACTION" sections
4. **Follow Node Progression**: Track "📍 Step X: Executing node" messages
5. **Monitor AI Fallbacks**: Watch for "⚠️ Vertex AI failed" warnings

## 🎯 Usage Examples

### Finding a Specific User Query
```bash
grep -A 20 -B 5 "User Input: show sales data" output/logs/analytics_agent_*.log
```

### Checking for SQL Validation Issues
```bash
grep -A 10 "SQL VALIDATION FAILED" output/logs/analytics_agent_*.log
```

### Monitoring Security Events
```bash
grep -A 5 "EXECUTION BLOCKED" output/logs/analytics_agent_*.log
```

---

This comprehensive logging system provides full visibility into the Analytics Agent's operation, making it easy to understand, debug, and monitor the system's behavior in real-time.