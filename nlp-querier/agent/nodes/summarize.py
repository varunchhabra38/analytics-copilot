from typing import Dict, Any, List
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from agent.tools.summary_tool import SummaryTool
from agent.state import AgentState

logger = logging.getLogger(__name__)


def summarize_node(state: AgentState) -> AgentState:
    """
    Node function to create a summary of the analytics workflow results.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with summary
    """
    try:
        logger.info("Creating summary...")
        
        question = state.get("question", "")
        execution_result = state.get("execution_result")
        sql_query = state.get("validated_sql", "")
        
        # Create new state copy
        new_state = state.copy()
        new_state['current_node'] = 'summarize'
        
        # Create an intelligent summary using LLM - focus on query interpretation
        summary = _create_query_summary(question, execution_result, sql_query)
        
        # Fallback to intelligent basic summary if LLM fails
        if not summary:
            summary = _create_query_summary_fallback(question, sql_query, execution_result is not None)
        
        # Add to conversation history
        history = new_state.get("history", [])
        new_state['history'] = history + [{"role": "assistant", "content": summary}]
        new_state['summary'] = summary
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['summarize']
        
        logger.info("✅ Summary created successfully")
        logger.info("📝 SUMMARY CONTENT:")
        logger.info("-" * 40)
        logger.info(summary)
        logger.info("-" * 40)
        
        return new_state
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        new_state = state.copy()
        new_state['summary'] = f"Error creating summary: {str(e)}"
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['summarize']
        return new_state


def _create_query_summary(question: str, execution_result, sql_query: str) -> str:
    """
    Use LLM to explain the SQL query that was generated, providing business context.
    """
    try:
        from agent.tools.sql_gen_tool import create_sql_gen_tool
        from config import get_config
        
        config = get_config()
        if not config or not config.get("ai"):
            logger.warning("⚠️ AI configuration not available, using fallback summary")
            return ""
        
        # Create focused prompt for SQL explanation
        summary_prompt = f"""
        Explain this SQL query in a detailed table format:

        Question: {question}
        SQL: {sql_query}

        Respond with exactly this format (complete the table):

        **Explanation of the Query**

        This query is designed to precisely filter and aggregate your data to answer the question. Let's break it down step-by-step:

        | Clause | Code | Explanation |
        |--------|------|-------------|
        | 1. SELECT | {sql_query.split('SELECT')[1].split('FROM')[0].strip() if 'SELECT' in sql_query.upper() else 'N/A'} | Explain what this SELECT clause calculates |
        | 2. FROM | FROM fact_transactions AS T1 | Explain the main table |
        | 3. WHERE | WHERE clause here | Explain the filtering logic |
        | 4. GROUP BY | GROUP BY clause here | Explain the grouping |

        **Execution Status:** {'Successfully executed' if execution_result is not None else 'Failed to execute'}

        Complete the table with the actual SQL clauses and business explanations.
        """
        
        # Use Vertex AI for SQL explanation
        sql_tool = create_sql_gen_tool(
            "vertex_ai",
            project_id=config["ai"]["project_id"],
            model_name=config["ai"]["model_name"],
            temperature=0.3  # Lower temperature for more consistent explanations
        )
        
        # Generate SQL explanation using LLM
        response = sql_tool.model.generate_content(
            summary_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 2000,  # Increased even more for detailed explanations
                "top_k": 20,
                "top_p": 0.8
            }
        )
        
        logger.info(f"🔍 FULL LLM RESPONSE (length: {len(response.text) if hasattr(response, 'text') else 'no text'})")
        logger.info("=" * 80)
        if hasattr(response, 'text'):
            logger.info(response.text)
        logger.info("=" * 80)
        
        summary = response.text.strip()
        if summary:
            logger.info(f"SQL query explanation created: {len(summary)} characters")
            logger.info(f"🔍 LLM Response Preview: {summary[:200]}...")
            return summary
        else:
            logger.warning("LLM returned empty response")
            return ""
        
    except Exception as e:
        logger.warning(f"LLM SQL explanation failed: {e}")
        return ""


def _create_query_summary_fallback(question: str, sql_query: str, execution_success: bool) -> str:
    """
    Create a detailed fallback SQL explanation when LLM is not available.
    """
    try:
        import re
        
        execution_status = "Successfully executed" if execution_success else "Failed to execute"
        
        # Parse the SQL query to identify components
        query_upper = sql_query.upper()
        query_lines = [line.strip() for line in sql_query.split('\n') if line.strip()]
        
        explanation_parts = []
        explanation_parts.append("**Explanation of the Query**")
        explanation_parts.append("")
        explanation_parts.append("This query is designed to precisely filter and aggregate your data to answer the question. Let's break it down step-by-step:")
        explanation_parts.append("")
        explanation_parts.append("| Clause | Code | Explanation |")
        explanation_parts.append("|--------|------|-------------|")
        
        step = 1
        
        # Analyze SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1).strip()
            if 'AVG(' in select_clause.upper():
                explanation_parts.append(f"| {step}. SELECT | SELECT {select_clause} | Calculates the average values for the specified columns, grouped by the dimensions needed to answer your business question. |")
            elif 'COUNT(' in select_clause.upper():
                explanation_parts.append(f"| {step}. SELECT | SELECT {select_clause} | Counts the number of records that match the specified criteria to provide frequency analysis. |")
            elif 'SUM(' in select_clause.upper():
                explanation_parts.append(f"| {step}. SELECT | SELECT {select_clause} | Sums up the total values for the specified columns to provide aggregate totals. |")
            elif '%' in select_clause or 'PERCENTAGE' in select_clause.upper():
                explanation_parts.append(f"| {step}. SELECT | SELECT {select_clause} | Calculates percentage values by comparing counts or amounts between different categories. |")
            else:
                explanation_parts.append(f"| {step}. SELECT | SELECT {select_clause} | Retrieves the specified columns and performs the necessary calculations to answer your question. |")
            step += 1
        
        # Analyze FROM clause
        from_match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            if 'fact_transactions' in table_name.lower():
                explanation_parts.append(f"| {step}. FROM | FROM {table_name} | Starts with the transaction data table as it contains the core business data needed for the analysis. |")
            elif 'fact_alerts' in table_name.lower():
                explanation_parts.append(f"| {step}. FROM | FROM {table_name} | Uses the alerts data table as the primary source for compliance and risk analysis. |")
            elif 'dim_customer' in table_name.lower():
                explanation_parts.append(f"| {step}. FROM | FROM {table_name} | Starts with customer dimension data to analyze customer-related metrics. |")
            else:
                explanation_parts.append(f"| {step}. FROM | FROM {table_name} | Uses the {table_name} table as the primary data source for this analysis. |")
            step += 1
        
        # Analyze JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+).*?ON\s+([^WHERE\s]+)', sql_query, re.IGNORECASE | re.DOTALL)
        for join_match in join_matches:
            table_name = join_match[0]
            join_condition = join_match[1].strip()
            if 'dim_account' in table_name.lower():
                explanation_parts.append(f"| {step}. JOIN | JOIN {table_name} ON {join_condition} | Connects transaction data to account information to access customer risk segments and account details. |")
            elif 'dim_customer' in table_name.lower():
                explanation_parts.append(f"| {step}. JOIN | JOIN {table_name} ON {join_condition} | Links to customer dimension data to access customer demographics and characteristics. |")
            elif 'dim_calendar' in table_name.lower():
                explanation_parts.append(f"| {step}. JOIN | JOIN {table_name} ON {join_condition} | Connects to calendar data to enable time-based filtering and analysis by dates, quarters, or years. |")
            else:
                explanation_parts.append(f"| {step}. JOIN | JOIN {table_name} ON {join_condition} | Joins with {table_name} to access additional data dimensions needed for the analysis. |")
            step += 1
        
        # Analyze WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s*$)', sql_query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            if 'risk_segment' in where_clause.lower() and 'high' in where_clause.lower():
                explanation_parts.append(f"| {step}. WHERE | WHERE {where_clause} | Filters to include only high-risk customers by checking the risk segment classification. |")
            elif 'quarter' in where_clause.lower():
                explanation_parts.append(f"| {step}. WHERE | WHERE {where_clause} | Filters data to the specified quarter using calendar dimension for time-based analysis. |")
            elif 'year' in where_clause.lower():
                explanation_parts.append(f"| {step}. WHERE | WHERE {where_clause} | Limits the analysis to the specified year for temporal filtering. |")
            else:
                explanation_parts.append(f"| {step}. WHERE | WHERE {where_clause} | Applies business filters to focus the analysis on the relevant subset of data. |")
            step += 1
        
        # Analyze GROUP BY clause
        groupby_match = re.search(r'GROUP\s+BY\s+(.+?)(?:\s+ORDER\s+BY|\s*$)', sql_query, re.IGNORECASE | re.DOTALL)
        if groupby_match:
            groupby_clause = groupby_match.group(1).strip()
            if 'channel' in groupby_clause.lower():
                explanation_parts.append(f"| {step}. GROUP BY | GROUP BY {groupby_clause} | Groups transactions by channel (Online, ATM, Branch, etc.) to calculate separate metrics for each channel type. |")
            elif 'country' in groupby_clause.lower():
                explanation_parts.append(f"| {step}. GROUP BY | GROUP BY {groupby_clause} | Groups data by country to provide geographic analysis and regional comparisons. |")
            else:
                explanation_parts.append(f"| {step}. GROUP BY | GROUP BY {groupby_clause} | Groups the filtered data by {groupby_clause} to enable aggregation calculations for each category. |")
            step += 1
        
        # Analyze ORDER BY clause
        orderby_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s*$)', sql_query, re.IGNORECASE | re.DOTALL)
        if orderby_match:
            orderby_clause = orderby_match.group(1).strip()
            if 'DESC' in orderby_clause.upper():
                explanation_parts.append(f"| {step}. ORDER BY | ORDER BY {orderby_clause} | Sorts results in descending order to show the highest values first, making it easy to identify top performers. |")
            else:
                explanation_parts.append(f"| {step}. ORDER BY | ORDER BY {orderby_clause} | Sorts results to organize the output in a logical order for business analysis. |")
        
        explanation_parts.append("")
        explanation_parts.append(f"**Execution Status:** {execution_status}")
        
        if execution_success:
            explanation_parts.append("The query completed successfully and returned the requested business metrics.")
        else:
            explanation_parts.append("The query encountered an error during execution. Please check the parameters and data availability.")
        
        return "\n".join(explanation_parts)
        
    except Exception as e:
        logger.error(f"Error creating detailed fallback summary: {e}")
        # Ultra-simple fallback
        status = "completed successfully" if execution_success else "encountered an error"
        return f"**Query Analysis**\n\nThe SQL query for '{question}' has {status}. This query was designed to extract the specific business metrics you requested from the database."


def _analyze_query_results(question: str, execution_result, sql_query: str) -> Dict[str, Any]:
    """
    Perform intelligent analysis of query results to extract insights.
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    insights = {
        "row_count": 0,
        "data_type": "unknown",
        "key_metrics": {},
        "patterns": [],
        "business_context": "",
        "data_quality": {},
        "time_context": None,
        "anomalies": []
    }
    
    if execution_result is None:
        insights["patterns"].append("No data found matching the query criteria")
        insights["business_context"] = "Consider checking filters or data availability"
        return insights
    
    try:
        # Convert to DataFrame if needed
        if isinstance(execution_result, list):
            if len(execution_result) > 0 and isinstance(execution_result[0], dict):
                df = pd.DataFrame(execution_result)
            else:
                insights["row_count"] = len(execution_result)
                return insights
        elif hasattr(execution_result, 'shape'):
            df = execution_result
        else:
            return insights
        
        insights["row_count"] = len(df)
        insights["data_type"] = "tabular"
        
        if len(df) == 0:
            insights["patterns"].append("Query executed successfully but returned no data")
            return insights
        
        # Analyze columns and data types
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Key metrics analysis - PRIVACY COMPLIANT: Only statistical aggregates, no actual data
        for col in numeric_cols:
            # Calculate statistical metadata without storing actual values
            col_data = df[col].dropna()
            if len(col_data) > 0:
                insights["key_metrics"][col] = {
                    "count": int(len(col_data)),
                    "has_data": True,
                    "data_type": "numeric",
                    "statistical_range": "calculated",  # Don't store actual min/max
                    "completeness": f"{(len(col_data) / len(df)) * 100:.1f}%"
                }
                
                # Only store variability indicators, not actual statistical values
                if len(col_data) > 1:
                    mean_val = float(col_data.mean())
                    std_val = float(col_data.std()) if len(col_data) > 1 else 0
                    cv = (std_val / mean_val * 100) if mean_val > 0 else 0
                    
                    # Store variability classification, not actual coefficient
                    if cv > 50:
                        insights["key_metrics"][col]["variability"] = "high"
                    elif cv > 20:
                        insights["key_metrics"][col]["variability"] = "medium"
                    else:
                        insights["key_metrics"][col]["variability"] = "low"
                else:
                    insights["key_metrics"][col]["variability"] = "single_value"
        
        # Pattern detection
        if len(df) == 1:
            insights["patterns"].append("Single record result - likely a specific lookup or aggregation")
        elif len(df) < 10:
            insights["patterns"].append(f"Small dataset with {len(df)} records - detailed analysis possible")
        elif len(df) < 100:
            insights["patterns"].append(f"Medium dataset with {len(df)} records - good for trend analysis")
        else:
            insights["patterns"].append(f"Large dataset with {len(df)} records - suitable for statistical analysis")
        
        # Business context detection based on columns
        business_context = _detect_business_context(df.columns.tolist(), question)
        insights["business_context"] = business_context
        
        # Time-based analysis
        if date_cols:
            insights["time_context"] = _analyze_time_patterns(df, date_cols)
        
        # Data quality insights
        insights["data_quality"] = {
            "completeness": f"{(1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}%",
            "missing_data": df.isnull().sum().to_dict() if df.isnull().sum().any() else None
        }
        
        # Anomaly detection for numeric data
        for col in numeric_cols:
            if len(df) > 10:  # Need sufficient data for anomaly detection
                q75, q25 = np.percentile(df[col].dropna(), [75, 25])
                iqr = q75 - q25
                outlier_threshold = q75 + (1.5 * iqr)
                outliers = len(df[df[col] > outlier_threshold])
                if outliers > 0:
                    insights["anomalies"].append(f"{outliers} potential outliers in {col}")
        
        return insights
        
    except Exception as e:
        logging.warning(f"Error in result analysis: {e}")
        insights["patterns"].append("Basic analysis completed")
        return insights


def _detect_business_context(columns: List[str], question: str) -> str:
    """
    Detect business domain based on column names and question.
    """
    column_text = " ".join(columns).lower()
    question_text = question.lower()
    combined_text = f"{column_text} {question_text}"
    
    # Financial/Compliance Analytics
    if any(term in combined_text for term in ['alert', 'risk', 'sanctions', 'aml', 'transaction', 'compliance']):
        return "financial_compliance"
    
    # Sales Analytics
    if any(term in combined_text for term in ['sales', 'revenue', 'customer', 'product', 'order']):
        return "sales_analytics"
    
    # Operational Analytics
    if any(term in combined_text for term in ['performance', 'operation', 'efficiency', 'process']):
        return "operational_analytics"
    
    # HR Analytics
    if any(term in combined_text for term in ['employee', 'staff', 'hr', 'payroll', 'department']):
        return "hr_analytics"
    
    return "general_analytics"


def _analyze_time_patterns(df: pd.DataFrame, date_cols: List[str]) -> Dict[str, Any]:
    """
    Analyze time-based patterns in the data - PRIVACY COMPLIANT.
    Only returns time span metadata, not specific dates or values.
    """
    time_insights = {}
    
    try:
        for date_col in date_cols:
            if date_col in df.columns:
                dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
                if len(dates) > 0:
                    # Only store time span information, not actual dates
                    span_days = (dates.max() - dates.min()).days
                    recency_days = (datetime.now() - dates.max()).days
                    
                    time_insights[date_col] = {
                        "has_time_data": True,
                        "span_days": span_days,
                        "data_recency_category": _categorize_recency(recency_days),
                        "date_coverage": "analyzed"  # Don't store actual date range
                    }
    except Exception as e:
        logging.warning(f"Time analysis error: {e}")
    
    return time_insights

def _categorize_recency(days: int) -> str:
    """Categorize data recency without exposing specific dates."""
    if days <= 7:
        return "very_recent"
    elif days <= 30:
        return "recent"
    elif days <= 90:
        return "moderately_recent" 
    elif days <= 365:
        return "older"
    else:
        return "historical"

def _audit_privacy_compliance(insights: Dict[str, Any], prompt: str) -> bool:
    """
    Audit the insights and prompt to ensure no customer data is exposed.
    
    Returns:
        bool: True if privacy compliant, False if data leakage detected
    """
    # Check insights for actual data values
    privacy_violations = []
    
    # Check key_metrics for actual numeric values
    if "key_metrics" in insights:
        for col, stats in insights["key_metrics"].items():
            # Look for suspicious numeric values that might be actual data
            for key, value in stats.items():
                if isinstance(value, (int, float)) and key not in ["count"] and value > 100:
                    # Large numbers might be actual data values
                    if key in ["total", "sum", "average", "mean", "min", "max"]:
                        privacy_violations.append(f"Potential data leak: {key} value for {col}")
    
    # Check time_context for actual dates
    if "time_context" in insights:
        for col, time_info in insights["time_context"].items():
            for key, value in time_info.items():
                if isinstance(value, str) and any(char.isdigit() for char in value):
                    if "date_range" in key or "most_recent" in key:
                        privacy_violations.append(f"Potential date leak: {key} in {col}")
    
    # Check prompt for data patterns
    prompt_lower = prompt.lower()
    suspicious_patterns = [
        "total=", "sum=", "avg=", "mean=", "date_range=", 
        r"\d{4}-\d{2}-\d{2}",  # Date pattern
        r"total \d+",          # Large numbers
        r"average \d+",        # Specific averages
    ]
    
    import re
    for pattern in suspicious_patterns:
        if re.search(pattern, prompt_lower):
            privacy_violations.append(f"Suspicious pattern in prompt: {pattern}")
    
    # Log any violations
    if privacy_violations:
        logger.warning(f"🔒 Privacy compliance violations detected: {privacy_violations}")
        return False
    
    logger.info("🔒 Privacy compliance audit passed - no customer data exposed")
    return True

def _create_privacy_safe_summary(question: str, insights: Dict[str, Any]) -> str:
    """
    Create a summary using only metadata when LLM usage is blocked for privacy.
    This ensures business value is still delivered without compromising data security.
    """
    try:
        # Use the enhanced SummaryTool which operates only on metadata
        summary_tool = SummaryTool()
        
        # Create a mock DataFrame with just structural info for analysis
        mock_data = {
            'row_count': insights.get('row_count', 0),
            'column_count': len(insights.get('key_metrics', {})),
            'business_context': insights.get('business_context', 'general_analytics')
        }
        
        context = {
            "question": question,
            "privacy_mode": True,
            "business_context": insights.get('business_context', 'general_analytics')
        }
        
        # Generate privacy-safe summary using only metadata
        summary_parts = []
        
        row_count = insights.get('row_count', 0)
        if row_count == 0:
            summary_parts.append("Analysis completed but no matching records found.")
        elif row_count == 1:
            summary_parts.append("Analysis identified 1 matching record.")
        else:
            summary_parts.append(f"Analysis completed on {row_count:,} records.")
        
        # Add business context insights
        business_context = insights.get('business_context', 'general_analytics')
        if business_context == 'financial_compliance':
            summary_parts.append("Compliance analysis indicates data patterns consistent with regulatory monitoring.")
        elif business_context == 'sales_analytics':
            summary_parts.append("Sales performance data shows measurable business activity patterns.")
        elif business_context == 'operational_analytics':
            summary_parts.append("Operational metrics indicate process performance within expected parameters.")
        
        # Add data quality insights
        if insights.get('data_quality', {}).get('completeness'):
            completeness = insights['data_quality']['completeness']
            if 'concerns' in completeness:
                summary_parts.append("Data quality assessment indicates areas for improvement.")
            else:
                summary_parts.append("Data quality assessment shows good completeness.")
        
        privacy_safe_summary = " ".join(summary_parts)
        
        logger.info(f"🔒 Generated privacy-safe summary: {len(privacy_safe_summary)} characters")
        return privacy_safe_summary
        
    except Exception as e:
        logger.error(f"Error creating privacy-safe summary: {e}")
        return f"Analysis completed for: '{question}'. Results processed with privacy protection active."


def _build_intelligent_summary_prompt(question: str, sql_query: str, insights: Dict[str, Any]) -> str:
    """
    Build a sophisticated prompt for intelligent summary generation.
    
    CRITICAL SECURITY: This function ONLY sends metadata and statistical summaries to LLM.
    NO actual customer data is included to protect privacy and comply with data protection regulations.
    """
    business_context_map = {
        "financial_compliance": {
            "focus": "risk management, compliance status, alert patterns, and regulatory insights",
            "terminology": "alerts, risk levels, compliance status, sanctions screening, AML monitoring",
            "key_phrases": ["compliance posture", "risk exposure", "alert trends", "investigation status"]
        },
        "sales_analytics": {
            "focus": "revenue performance, customer behavior, sales trends, and growth opportunities",
            "terminology": "revenue, sales performance, customer segments, growth rates, market trends",
            "key_phrases": ["sales performance", "revenue growth", "customer insights", "market opportunities"]
        },
        "operational_analytics": {
            "focus": "operational efficiency, process performance, and improvement opportunities", 
            "terminology": "efficiency metrics, process performance, operational KPIs, bottlenecks",
            "key_phrases": ["operational efficiency", "process optimization", "performance indicators"]
        },
        "general_analytics": {
            "focus": "data patterns, key metrics, and actionable insights",
            "terminology": "data insights, key metrics, trends, patterns",
            "key_phrases": ["data analysis", "key findings", "notable patterns"]
        }
    }
    
    context_info = business_context_map.get(insights["business_context"], business_context_map["general_analytics"])
    
    # Build ANONYMIZED metrics summary - only statistical aggregates, no actual values
    metrics_text = ""
    if insights["key_metrics"]:
        metrics_list = []
        for col, stats in insights["key_metrics"].items():
            if stats.get("has_data", False):
                # Only send aggregated statistics, never actual data values
                variability = stats.get("variability", "unknown")
                completeness = stats.get("completeness", "unknown")
                metrics_list.append(f"{col}: {stats['count']} records, {variability} variability, {completeness} complete")
        if metrics_list:
            metrics_text = f"Statistical analysis: {'; '.join(metrics_list[:3])}"  # Limit to top 3
    
    # Build patterns text (metadata only)
    patterns_text = ". ".join(insights["patterns"][:2]) if insights["patterns"] else "Standard data analysis completed"
    
    # Time context (only ranges, no specific dates)
    time_text = ""
    if insights["time_context"]:
        for col, time_info in insights["time_context"].items():
            # Only send time span information, not specific dates
            time_text = f"Time series data spanning {time_info['span_days']} days"
            break  # Use first date column
    
    # SQL structure analysis (no actual query content)
    sql_structure = _analyze_sql_structure_metadata(sql_query)
    
    prompt = f"""You are an expert business analyst creating an intelligent summary for stakeholders. 

PRIVACY NOTICE: You are working with METADATA ONLY - no actual customer data is included in this analysis.

ANALYSIS CONTEXT:
- Business Domain: {insights['business_context'].replace('_', ' ').title()}
- Focus Areas: {context_info['focus']}
- User Question: "{question}"
- Data Volume: {insights['row_count']} records analyzed
- {metrics_text}
- Data Patterns: {patterns_text}
- {time_text}
- Query Complexity: {sql_structure}
- Data Quality: {insights['data_quality'].get('completeness', 'standard')} completeness

INTELLIGENCE REQUIREMENTS:
1. Answer the user's question based on the statistical metadata provided
2. Highlight 2-3 most important insights using {context_info['terminology']}
3. Reference data volume and patterns, not specific values
4. Use business language appropriate for {insights['business_context'].replace('_', ' ')} domain
5. Mention any notable patterns, trends, or anomalies from the metadata
6. Keep the summary concise but insightful (3-4 sentences max)

CONSTRAINTS:
- Use ONLY the provided metadata and statistical summaries
- Do NOT reference specific data values or records
- Focus on patterns, volumes, and analytical insights
- Maintain business context without exposing sensitive information

EXAMPLE TONE for {insights['business_context']}:
- Use phrases like: {', '.join(context_info['key_phrases'][:2])}
- Focus on analytical insights and data patterns
- Be specific about volumes and statistical patterns, not individual records

Generate a privacy-compliant, executive-ready summary based on metadata analysis:"""

    return prompt

def _analyze_sql_structure_metadata(sql_query: str) -> str:
    """
    Analyze SQL query structure for metadata without exposing query content.
    Returns only structural information about the query complexity.
    """
    if not sql_query:
        return "basic query"
    
    sql_upper = sql_query.upper()
    complexity_indicators = []
    
    # Count structural elements (not content)
    join_count = sql_upper.count('JOIN')
    if join_count > 0:
        complexity_indicators.append(f"{join_count} table joins")
    
    if 'GROUP BY' in sql_upper:
        complexity_indicators.append("data aggregation")
    
    if 'ORDER BY' in sql_upper:
        complexity_indicators.append("result sorting")
    
    if 'WHERE' in sql_upper:
        complexity_indicators.append("filtered analysis")
    
    if 'HAVING' in sql_upper:
        complexity_indicators.append("aggregate filtering")
    
    if complexity_indicators:
        return f"complex query with {', '.join(complexity_indicators)}"
    else:
        return "simple data retrieval query"


def _post_process_summary(summary: str, insights: Dict[str, Any]) -> str:
    """
    Post-process the summary to ensure quality and consistency.
    """
    import re
    
    # Remove any JSON formatting that might have leaked through
    summary = re.sub(r'[{}":]', '', summary)
    
    # Ensure first letter is capitalized
    if summary:
        summary = summary[0].upper() + summary[1:] if len(summary) > 1 else summary.upper()
    
    # Add data quality note if significant missing data
    if insights.get("data_quality", {}).get("missing_data"):
        missing_info = insights["data_quality"]["missing_data"]
        significant_missing = {k: v for k, v in missing_info.items() if v > 0 and v > insights["row_count"] * 0.1}
        if significant_missing:
            summary += f" Note: Some data fields have missing values that may affect completeness."
    
    # Ensure summary doesn't exceed reasonable length
    if len(summary) > 800:
        sentences = summary.split('.')
        summary = '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else summary
    
    return summary.strip()


def summarize_conversation(history: list[Dict[str, Any]]) -> str:
    """
    Legacy function for backward compatibility.
    
    Generate a summary of the conversation history.

    Args:
        history (list[Dict[str, Any]]): The conversation history containing messages.

    Returns:
        str: A summary of the conversation.
    """
    summary_tool = SummaryTool()
    summary = summary_tool.generate_summary(history)
    return summary


def _create_intelligent_fallback_summary(question: str, execution_result, sql_query: str) -> str:
    """
    Create an intelligent business-focused summary when LLM is not available.
    This function analyzes the actual query results to provide meaningful insights.
    """
    try:
        if execution_result is None:
            return f"No data found for: '{question}'. This could be due to filters not matching any records in the specified time period."
        
        # Convert to DataFrame if needed
        if isinstance(execution_result, list):
            if len(execution_result) > 0 and isinstance(execution_result[0], dict):
                df = pd.DataFrame(execution_result)
            else:
                return f"Query completed for: '{question}', but returned unexpected data format."
        elif hasattr(execution_result, 'shape'):
            df = execution_result
        else:
            return f"Query completed for: '{question}', but data format could not be processed."
        
        if len(df) == 0:
            return f"No records found matching the criteria for: '{question}'. Please check your filters and date ranges."
        
        # Analyze the data and create intelligent summary based on question type
        question_lower = question.lower()
        
        # Percentage queries (like the current example)
        if any(word in question_lower for word in ['percentage', 'percent', '%']):
            return _analyze_percentage_query(question, df, sql_query)
        
        # Count queries
        elif any(word in question_lower for word in ['how many', 'count', 'number of']):
            return _analyze_count_query(question, df, sql_query)
        
        # Total/Sum queries
        elif any(word in question_lower for word in ['total', 'sum', 'amount']):
            return _analyze_sum_query(question, df, sql_query)
        
        # Top/Bottom queries
        elif any(word in question_lower for word in ['top', 'highest', 'largest', 'biggest', 'best']):
            return _analyze_ranking_query(question, df, sql_query, ascending=False)
        elif any(word in question_lower for word in ['bottom', 'lowest', 'smallest', 'worst']):
            return _analyze_ranking_query(question, df, sql_query, ascending=True)
        
        # Trend/Time analysis
        elif any(word in question_lower for word in ['trend', 'over time', 'by month', 'by quarter']):
            return _analyze_trend_query(question, df, sql_query)
        
        # Generic analysis
        else:
            return _analyze_generic_query(question, df, sql_query)
            
    except Exception as e:
        logger.error(f"Error creating intelligent fallback summary: {e}")
        # Ultra-simple fallback
        row_count = len(execution_result) if hasattr(execution_result, '__len__') else 0
        return f"Analysis completed for: '{question}'. Found {row_count} result(s)."


def _analyze_percentage_query(question: str, df: pd.DataFrame, sql_query: str) -> str:
    """Analyze percentage-based queries to provide business insights."""
    try:
        # Get the percentage value from the first row, first column
        if len(df) > 0 and len(df.columns) > 0:
            percentage_value = df.iloc[0, 0]
            
            if pd.isna(percentage_value):
                return f"Analysis for '{question}' could not be completed due to insufficient data in the specified time period."
            
            # Round to meaningful precision
            if isinstance(percentage_value, (int, float)):
                pct = round(float(percentage_value), 2)
                
                # Create contextual summary based on the question
                if 'alert' in question.lower() and 'transaction' in question.lower():
                    if pct < 5:
                        context = "which indicates a low alert rate"
                    elif pct < 15:
                        context = "indicating a moderate alert rate"  
                    else:
                        context = "showing a high alert rate that may require attention"
                    
                    return f"In Q1 2025, {pct}% of transactions resulted in alerts, {context}. This analysis covers the complete transaction volume for the quarter."
                
                elif 'compliance' in question.lower() or 'regulatory' in question.lower():
                    return f"The compliance rate analysis shows {pct}%, providing insights into regulatory adherence for the specified period."
                
                else:
                    # Generic percentage summary
                    return f"The analysis shows {pct}% for '{question}', based on comprehensive data analysis."
            
            else:
                return f"The percentage analysis for '{question}' returned a non-numeric result: {str(percentage_value)}"
        
        else:
            return f"The percentage query for '{question}' returned empty results. Please verify your filters and date ranges."
            
    except Exception as e:
        return f"Analysis completed for '{question}', but result formatting encountered an issue: {str(e)}"


def _analyze_count_query(question: str, df: pd.DataFrame, sql_query: str) -> str:
    """Analyze count-based queries."""
    try:
        if len(df) > 0 and len(df.columns) > 0:
            count_value = df.iloc[0, 0]
            if isinstance(count_value, (int, float)):
                count = int(count_value)
                return f"Found {count:,} records matching the criteria for '{question}'."
        return f"Count analysis for '{question}' completed with {len(df)} result(s)."
    except:
        return f"Count analysis completed for '{question}'."


def _analyze_sum_query(question: str, df: pd.DataFrame, sql_query: str) -> str:
    """Analyze sum/total queries."""
    try:
        if len(df) > 0 and len(df.columns) > 0:
            sum_value = df.iloc[0, 0]
            if isinstance(sum_value, (int, float)):
                if sum_value > 1000000:
                    formatted = f"{sum_value/1000000:.1f}M"
                elif sum_value > 1000:
                    formatted = f"{sum_value/1000:.1f}K"
                else:
                    formatted = f"{sum_value:,.0f}"
                return f"Total value of {formatted} found for '{question}'."
        return f"Sum analysis for '{question}' completed with {len(df)} result(s)."
    except:
        return f"Total analysis completed for '{question}'."


def _analyze_ranking_query(question: str, df: pd.DataFrame, sql_query: str, ascending: bool = False) -> str:
    """Analyze ranking/top/bottom queries."""
    try:
        direction = "lowest" if ascending else "highest"
        if len(df) > 0:
            return f"Ranking analysis shows {len(df)} result(s) for '{question}', sorted by {direction} values."
        return f"No results found for ranking query: '{question}'."
    except:
        return f"Ranking analysis completed for '{question}'."


def _analyze_trend_query(question: str, df: pd.DataFrame, sql_query: str) -> str:
    """Analyze trend/time-based queries.""" 
    try:
        return f"Time series analysis for '{question}' shows {len(df)} data points across the specified period."
    except:
        return f"Trend analysis completed for '{question}'."


def _analyze_generic_query(question: str, df: pd.DataFrame, sql_query: str) -> str:
    """Generic analysis for unclassified queries."""
    try:
        if len(df) == 1 and len(df.columns) == 1:
            # Single value result
            value = df.iloc[0, 0]
            return f"Analysis for '{question}' returned: {value}"
        else:
            return f"Analysis for '{question}' returned {len(df)} rows with {len(df.columns)} column(s) of data."
    except:
        return f"Analysis completed for '{question}' with {len(df) if hasattr(df, '__len__') else 'unknown'} results."