"""
SQL Execution Node for LangGraph Analytics Agent.
Executes validated SQL queries and captures results.
"""

from typing import Dict, Any
import logging
import pandas as pd
from agent.state import AgentState
from agent.tools.sql_executor_tool import create_sql_executor_tool
from utils.enhanced_pii_redactor import EnhancedPIIRedactor, RedactionMode
from config import get_config

logger = logging.getLogger(__name__)


def execute_sql_node(state: AgentState) -> AgentState:
    """
    Node to execute validated SQL query.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with execution results
    """
    logger.info("⚡ SQL EXECUTION NODE - STARTING")
    logger.info("-" * 60)
    
    try:
        # Check for validation errors first - SECURITY CHECK
        validation_error = state.get("validation_error")
        validated_sql = state.get("validated_sql", "")
        
        logger.info("🔒 SECURITY CHECKS:")
        logger.info(f"  - Validation Error: {'❌ ' + str(validation_error) if validation_error else '✅ None'}")
        logger.info(f"  - Validated SQL: {'✅ Present' if validated_sql else '❌ Missing'}")
        
        if validation_error:
            logger.warning(f"🛡️  EXECUTION BLOCKED - Validation failed: {validation_error}")
            new_state = state.copy()
            new_state['current_node'] = 'execute_sql'
            new_state['execution_result'] = None
            new_state['execution_error'] = f"Query blocked by validation: {validation_error}"
            new_state['completed_nodes'] = new_state['completed_nodes'] + ['execute_sql']
            
            logger.warning("🚫 SQL EXECUTION NODE - BLOCKED FOR SECURITY")
            logger.info("-" * 60)
            return new_state
        
        # Create new state copy
        new_state = state.copy()
        new_state['current_node'] = 'execute_sql'
        
        if not validated_sql:
            logger.warning("⚠️  No validated SQL query to execute")
            new_state['execution_result'] = None
            new_state['execution_error'] = "No validated SQL query to execute"
            return new_state
        
        logger.info("📝 SQL to execute:")
        for i, line in enumerate(validated_sql.split('\n')[:10], 1):  # First 10 lines
            logger.info(f"    {i:2d}: {line}")
        if len(validated_sql.split('\n')) > 10:
            logger.info("    ... (truncated)")
        
        # Get configuration
        logger.info("🔧 Setting up database executor...")
        config = get_config()
        db_config = config["database"]
        db_type = db_config["type"]
        logger.info(f"  - Database Type: {db_type}")
        
        # Create SQL executor tool
        if db_type == "sqlite":
            # Extract path from sqlite:///./output/fcfp_analytics.db
            db_path = db_config["connection_string"].replace("sqlite:///./", "")
            executor_tool = create_sql_executor_tool(
                db_type="sqlite",
                db_path=db_path
            )
            logger.info(f"  - SQLite Path: {db_path}")
        elif db_type == "postgresql":
            executor_tool = create_sql_executor_tool(
                db_type="postgresql",
                connection_string=db_config["connection_string"]
            )
            logger.info("  - PostgreSQL connection configured")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        # Execute the query
        logger.info("⚡ Executing SQL query...")
        result = executor_tool.execute_query(validated_sql)
        
        if result.get("error"):
            logger.error("❌ SQL EXECUTION FAILED")
            logger.error(f"  - Error: {result['error']}")
            new_state['execution_result'] = None
            new_state['execution_error'] = result["error"]
        else:
            result_data = result.get("result", [])
            logger.info("✅ SQL EXECUTION SUCCESSFUL")
            logger.info(f"  - Rows returned: {len(result_data)}")
            
            # Show sample of results - safely check for data
            has_data = False
            if result_data is not None:
                if hasattr(result_data, 'empty'):  # DataFrame
                    has_data = not result_data.empty
                elif isinstance(result_data, list):
                    has_data = len(result_data) > 0
                else:
                    has_data = bool(result_data)
            
            if has_data:
                if hasattr(result_data, 'head'):  # DataFrame
                    logger.info("  - Result type: pandas.DataFrame")
                    logger.info(f"  - Columns: {list(result_data.columns)}")
                    logger.info("  - Sample data:")
                    for idx, row in result_data.head(3).iterrows():
                        logger.info(f"      Row {idx}: {dict(row)}")
                elif isinstance(result_data, list) and result_data:
                    logger.info("  - Result type: List of records")
                    logger.info("  - Sample records:")
                    for i, record in enumerate(result_data[:3], 1):
                        logger.info(f"      {i}: {record}")
            else:
                logger.info("  - No data returned")
                
            # Convert DataFrame to serializable format for LangGraph state management
            if hasattr(result_data, 'to_dict'):  # DataFrame
                # Apply enhanced PII redaction optimized for business intelligence
                logger.info("🔒 Applying enhanced PII redaction to query results...")
                logger.info("   - Mode: BUSINESS_INTELLIGENCE (pattern-preserving for better BI analysis)")
                
                # Use BUSINESS_INTELLIGENCE mode to preserve data patterns for LLM analysis
                pii_redactor = EnhancedPIIRedactor(
                    mode=RedactionMode.BUSINESS_INTELLIGENCE, 
                    enable_name_redaction=True
                )
                
                # Apply redaction to all string columns
                redacted_df = result_data.copy()
                pii_findings = {}
                total_pii_count = 0
                
                for column in redacted_df.columns:
                    if redacted_df[column].dtype == 'object':  # String columns
                        column_findings = []
                        
                        # Apply redaction to each cell
                        for idx in redacted_df.index:
                            original_value = str(redacted_df.at[idx, column])
                            if original_value and original_value != 'None':
                                redacted_value, findings = pii_redactor.redact_text(original_value)
                                redacted_df.at[idx, column] = redacted_value
                                column_findings.extend(findings)
                        
                        if column_findings:
                            pii_findings[column] = column_findings
                            total_pii_count += len(column_findings)
                
                if pii_findings:
                    logger.warning(f"🚨 PII DETECTED: {total_pii_count} instances found and pseudonymized in {len(pii_findings)} columns")
                    for column, findings in pii_findings.items():
                        pattern_counts = {}
                        for finding in findings:
                            pattern = finding['type']
                            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                        
                        pattern_summary = ", ".join([f"{pattern}: {count}" for pattern, count in pattern_counts.items()])
                        logger.warning(f"  - Column '{column}': {len(findings)} PII instances ({pattern_summary})")
                else:
                    logger.info("✅ No PII detected in query results")
                
                # Log redaction statistics
                stats = pii_redactor.get_stats()
                logger.info(f"📊 Redaction cache stats: {stats}")
                
                # Store both the serialized data and a flag indicating it was a DataFrame
                serialized_result = {
                    'type': 'dataframe',
                    'data': redacted_df.to_dict('records'),
                    'columns': list(redacted_df.columns),
                    'shape': redacted_df.shape
                }
                logger.info(f"  - Converted redacted DataFrame to serializable format ({redacted_df.shape[0]} rows, {redacted_df.shape[1]} cols)")
                
                # Log detailed query results for testing
                logger.info("📊 QUERY RESULTS:")
                logger.info(f"  - Columns: {list(redacted_df.columns)}")
                logger.info(f"  - Row Count: {redacted_df.shape[0]}")
                
                # Log first few rows for inspection (limit to avoid excessive logs)
                if len(redacted_df) > 0:
                    logger.info("  - Sample Data:")
                    for i, row in redacted_df.head(5).iterrows():
                        logger.info(f"    Row {i+1}: {dict(row)}")
                    if len(redacted_df) > 5:
                        logger.info(f"    ... ({len(redacted_df)-5} more rows)")
                else:
                    logger.info("  - No data returned")
                    
                new_state['execution_result'] = serialized_result
                
                # Store PII findings for audit purposes
                if pii_findings:
                    new_state['pii_findings'] = pii_findings
            else:
                logger.info(f"📊 QUERY RESULTS: {result_data}")
                new_state['execution_result'] = result_data
                
            new_state['execution_error'] = None
            
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['execute_sql']
        
        logger.info("⚡ SQL EXECUTION NODE - COMPLETED")
        logger.info("-" * 60)
        
        return new_state
        
    except Exception as e:
        logger.error("❌ SQL EXECUTION NODE - ERROR")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Message: {e}")
        logger.error("-" * 60)
        
        new_state = state.copy()
        new_state['execution_result'] = None
        new_state['execution_error'] = str(e)
        new_state['current_node'] = 'execute_sql'
        return new_state