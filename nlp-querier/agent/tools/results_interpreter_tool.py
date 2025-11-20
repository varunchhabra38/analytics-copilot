"""
Results Interpreter Tool - Generate business insights from query results
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from agent.tools.sql_gen_tool import create_sql_gen_tool
import config
from utils.pii_redactor import get_pii_redactor

logger = logging.getLogger(__name__)

class ResultsInterpreterTool:
    """Tool for generating business insights from SQL query results using LLM."""
    
    def __init__(self):
        """Initialize the results interpreter tool."""
        self.logger = logging.getLogger(__name__)
        
    def interpret_results(self, 
                         question: str, 
                         sql_query: str, 
                         execution_result: pd.DataFrame, 
                         context: Optional[str] = None) -> str:
        """
        Generate business insights from query results using LLM.
        
        Args:
            question: Original business question asked by user
            sql_query: SQL query that was executed 
            execution_result: DataFrame with query results
            context: Additional context about the data/business
            
        Returns:
            Business interpretation of the results
        """
        try:
            self.logger.info("🔍 Starting business results interpretation...")
            self.logger.info(f"  - Question: {question}")
            self.logger.info(f"  - Result rows: {len(execution_result)}")
            self.logger.info(f"  - Result columns: {list(execution_result.columns)}")
            
            # Convert results to text format for LLM
            results_text = self._format_results_for_llm(execution_result)
            
            # Create business interpretation prompt
            interpretation_prompt = self._create_interpretation_prompt(
                question, sql_query, results_text, context
            )
            
            # Get LLM interpretation
            interpretation = self._get_llm_interpretation(interpretation_prompt)
            self.logger.info(f"🔍 Raw LLM response length: {len(interpretation)} characters")
            self.logger.info(f"🔍 Raw LLM response preview: {interpretation[:300]}...")
            
            # Try to parse as JSON first, fall back to raw text
            try:
                import json
                self.logger.info("🔍 Attempting JSON parsing...")
                
                # Clean the interpretation text - remove markdown code blocks if present
                cleaned_interpretation = interpretation.strip()
                if cleaned_interpretation.startswith('```json'):
                    # Remove ```json at the start and ``` at the end
                    cleaned_interpretation = cleaned_interpretation[7:]  # Remove ```json
                    if cleaned_interpretation.endswith('```'):
                        cleaned_interpretation = cleaned_interpretation[:-3]  # Remove ```
                    cleaned_interpretation = cleaned_interpretation.strip()
                    self.logger.info("🧹 Cleaned markdown code blocks from LLM response")
                elif cleaned_interpretation.startswith('```'):
                    # Remove ``` at the start and end
                    cleaned_interpretation = cleaned_interpretation[3:]  # Remove ```
                    if cleaned_interpretation.endswith('```'):
                        cleaned_interpretation = cleaned_interpretation[:-3]  # Remove ```
                    cleaned_interpretation = cleaned_interpretation.strip()
                    self.logger.info("🧹 Cleaned generic markdown code blocks from LLM response")
                
                self.logger.info(f"🔍 Cleaned interpretation preview: {cleaned_interpretation[:200]}...")
                
                parsed_json = json.loads(cleaned_interpretation)
                self.logger.info(f"✅ JSON parsing successful! Keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
                
                # Format JSON into readable business insights
                formatted_interpretation = self._format_json_interpretation(parsed_json)
                
                # Apply PII redaction to business interpretation
                self.logger.info("🔒 Applying PII redaction to business interpretation...")
                pii_redactor = get_pii_redactor(enable_name_redaction=False)  # Reduce name redaction in interpretations
                redacted_interpretation, pii_findings = pii_redactor.redact_text(formatted_interpretation)
                
                if pii_findings:
                    self.logger.warning(f"🚨 PII DETECTED: {len(pii_findings)} instances found and redacted in business interpretation")
                    for finding in pii_findings:
                        self.logger.warning(f"  - {finding['type']}: {finding['description']}")
                else:
                    self.logger.info("✅ No PII detected in business interpretation")
                
                self.logger.info(f"✅ Business interpretation generated: {len(redacted_interpretation)} characters (parsed from JSON)")
                self.logger.info(f"🔍 Redacted interpretation preview: {redacted_interpretation[:300]}...")
                return redacted_interpretation
                
            except json.JSONDecodeError as json_error:
                # If not JSON, apply PII redaction to raw text
                self.logger.warning(f"❌ JSON parsing failed: {json_error}")
                
                # Apply PII redaction to raw interpretation
                self.logger.info("🔒 Applying PII redaction to raw business interpretation...")
                pii_redactor = get_pii_redactor(enable_name_redaction=False)  # Reduce name redaction
                redacted_interpretation, pii_findings = pii_redactor.redact_text(interpretation)
                
                if pii_findings:
                    self.logger.warning(f"🚨 PII DETECTED: {len(pii_findings)} instances found and redacted in raw interpretation")
                else:
                    self.logger.info("✅ No PII detected in raw interpretation")
                
                self.logger.info(f"✅ Business interpretation generated: {len(redacted_interpretation)} characters (raw text)")
                return redacted_interpretation
            
        except Exception as e:
            self.logger.error(f"❌ Error in results interpretation: {e}")
            return self._create_fallback_interpretation(question, execution_result)
    
    def _format_results_for_llm(self, df: pd.DataFrame) -> str:
        """Format DataFrame results for LLM consumption with emphasis on business metrics."""
        if df.empty:
            return "No data returned from the query."
        
        # Limit to first 20 rows to avoid token limits
        display_df = df.head(20)
        
        # Identify business-relevant columns (non-PII columns)
        business_columns = []
        redacted_columns = []
        
        for col in display_df.columns:
            # Check if column contains mostly redacted values
            if display_df[col].dtype == 'object':
                sample_values = display_df[col].dropna().astype(str).head(5)
                redacted_count = sum(1 for val in sample_values if 'REDACTED' in val)
                if redacted_count > len(sample_values) * 0.5:  # More than 50% redacted
                    redacted_columns.append(col)
                else:
                    business_columns.append(col)
            else:
                business_columns.append(col)
        
        # Format result text with business focus
        result_text = f"📊 BUSINESS METRICS ANALYSIS\n"
        result_text += f"Dataset: {len(df)} total records, {len(df.columns)} columns\n\n"
        
        # Emphasize business metrics
        if business_columns:
            result_text += "🔍 KEY BUSINESS DATA (Focus your analysis on these columns):\n"
            business_df = display_df[business_columns]
            result_text += business_df.to_string(index=False, float_format='{:.2f}'.format)
            result_text += "\n\n"
        
        # Minimize mention of redacted data
        if redacted_columns:
            result_text += f"📝 Note: {len(redacted_columns)} columns contain privacy-protected data (ignore these): {', '.join(redacted_columns)}\n\n"
        
        # Add summary statistics for numeric columns
        numeric_cols = [col for col in business_columns if display_df[col].dtype in ['int64', 'float64']]
        if numeric_cols:
            result_text += "📈 SUMMARY STATISTICS:\n"
            for col in numeric_cols:
                if not display_df[col].dropna().empty:
                    result_text += f"• {col}: Total={display_df[col].sum():,.0f}, "
                    result_text += f"Avg={display_df[col].mean():,.1f}, "
                    result_text += f"Range={display_df[col].min():,.0f}-{display_df[col].max():,.0f}\n"
            result_text += "\n"
        
        # Add categorical summaries
        categorical_cols = [col for col in business_columns if display_df[col].dtype == 'object' and col not in redacted_columns]
        if categorical_cols:
            result_text += "📋 CATEGORY DISTRIBUTIONS:\n"
            for col in categorical_cols[:3]:  # Limit to top 3 categorical columns
                value_counts = display_df[col].value_counts().head(5)
                if not value_counts.empty:
                    result_text += f"• {col}: {dict(value_counts)}\n"
            result_text += "\n"
        
        if len(df) > 20:
            result_text += f"⚠️  Showing first 20 rows of {len(df)} total records for analysis\n"
            
        return result_text
    
#     def _create_interpretation_prompt(self, question: str, sql_query: str, results_text: str, context: str = None) -> str:
#         """Create a more robust prompt for business interpretation that handles redaction."""
        
#         prompt = f"""You are a senior business analyst specializing in financial crime and fraud prevention. 
# Your task is to analyze the provided SQL query results and deliver actionable business insights in a structured executive summary format.

# **IMPORTANT CONTEXT: DATA PRIVACY & REDACTION**
# - The query results you are seeing have been intentionally redacted for security and privacy.
# - You will see placeholders like `[XXX_REDACTED]`. This is NOT a data quality issue.
# - **Your primary directive is to IGNORE the redacted fields completely.**
# - **DO NOT mention the redaction or data quality in your analysis.**
# - Base your entire analysis ONLY on the visible, non-redacted data (e.g., counts, dates, risk levels, channels, amounts).

# **CRITICAL REQUIREMENTS:**
# 1.  **Focus ONLY on the actual, visible data** - do not mention redaction.
# 2.  Return your response in the specified JSON format.
# 3.  Provide detailed, actionable analysis using specific numbers from the visible data.
# 4.  Identify trends, anomalies, and patterns from the non-sensitive metrics.

# **QUERY CONTEXT:**
# - User's Business Question: "{question}"
# - Executed SQL Query: "{sql_query}"

# **ACTUAL QUERY RESULTS (with intentional redaction):**
# {results_text}

# **REQUIRED JSON OUTPUT FORMAT:**
# {{
#     "executive_summary": "A 2-3 sentence summary of the main findings based on the visible data.",
#     "key_findings": [
#         {{
#             "finding_title": "A clear title for the finding (e.g., 'Spike in High-Risk Alerts in Q4')",
#             "description": "A detailed explanation using specific, non-redacted data points from the results (e.g., 'The number of high-risk alerts increased from 50 in Q3 to 85 in Q4, a 70% increase.')",
#             "business_impact": "Why this finding matters for fraud prevention, operational efficiency, or risk management."
#         }}
#     ],
#     "notable_patterns": [
#         "Identify a specific, measurable pattern from the visible data.",
#         "Highlight another significant trend using real data points."
#     ],
#     "recommendations": [
#         {{
#             "action": "A specific, recommended next step (e.g., 'Investigate the root cause of the Q4 high-risk alert spike.')",
#             "priority": "High/Medium/Low",
#             "rationale": "Why this action is necessary based on the data-driven findings."
#         }}
#     ]
# }}

# **ANALYSIS INSTRUCTIONS:**
# - Write in the style of a professional, executive-level briefing.
# - Use specific numbers, percentages, and trends from the actual, visible results.
# - Your entire analysis must be derived from the non-sensitive data provided.
# - Generate the complete JSON object and nothing else. Ensure it is valid.

# Generate your comprehensive JSON analysis based *only* on the visible query results:"""

#         return prompt



    def _create_interpretation_prompt(self, question: str, sql_query: str, results_text: str, context: str = None) -> str:
        """Create a more robust prompt for business interpretation that handles redaction."""
        
        prompt = f"""You are a senior business analyst specializing in financial crime and fraud prevention. 
Your task is to analyze the provided SQL query results  in a structured executive summary format.

**IMPORTANT CONTEXT: DATA PRIVACY & REDACTION**
- The query results you are seeing have been intentionally redacted for security and privacy.
- You will see placeholders like `[XXX_REDACTED]`. This is NOT a data quality issue.
- **Your primary directive is to IGNORE the redacted fields completely.**
- **DO NOT mention the redaction or data quality in your analysis.**
- Base your entire analysis ONLY on the visible, non-redacted data (e.g., counts, dates, risk levels, channels, amounts).

**CRITICAL REQUIREMENTS:**
1.  **Focus ONLY on the actual, visible data** - do not mention redaction.
2.  Return your response in the specified JSON format.
3.  Provide concise, actionable analysis using specific numbers from the visible data.
4.  Identify trends, anomalies, and patterns from the non-sensitive metrics.

**QUERY CONTEXT:**
- User's Business Question: "{question}"
- Executed SQL Query: "{sql_query}"

**ACTUAL QUERY RESULTS (with intentional redaction):**
{results_text}

**REQUIRED JSON OUTPUT FORMAT:**
{{
    "executive_summary": "A 2-3 sentence summary of the main findings based on the visible data.",
    "key_findings": [
        {{
            "finding_title": "A clear title for the finding (e.g., 'Spike in High-Risk Alerts in Q4')",
            "description": "A detailed explanation using specific, non-redacted data points from the results (e.g., 'The number of high-risk alerts increased from 50 in Q3 to 85 in Q4, a 70% increase.')",
            "business_impact": "Why this finding matters for fraud prevention, operational efficiency, or risk management."
        }}
    ]
}}

**ANALYSIS INSTRUCTIONS:**
- Write in the style of a professional, executive-level briefing.
- Use specific numbers, percentages, and trends from the actual, visible results.
- Your entire analysis must be derived from the non-sensitive data provided.
- Generate the complete JSON object and nothing else. Ensure it is valid.

Generate your concise JSON analysis based *only* on the visible query results:"""

        return prompt

    
    def _format_json_interpretation(self, json_data: dict) -> str:
        """Format JSON interpretation into readable business insights."""
        try:
            # Start with executive summary format
            formatted = "## Executive Summary: Business Intelligence Analysis\n\n"
            
            # Add executive summary
            if "executive_summary" in json_data:
                formatted += f"{json_data['executive_summary']}\n\n"
            
            # Add key findings section
            if "key_findings" in json_data and isinstance(json_data["key_findings"], list):
                formatted += "### Key Findings\n\n"
                for i, finding in enumerate(json_data["key_findings"], 1):
                    if isinstance(finding, dict):
                        formatted += f"**Finding #{i}: {finding.get('finding_title', 'Key Finding')}**\n"
                        formatted += f"- *What it is:* {finding.get('description', 'No description provided')}\n"
                        formatted += f"- *Why it matters:* {finding.get('business_impact', 'Impact not specified')}\n\n"
                    else:
                        formatted += f"**Finding #{i}:** {finding}\n\n"
            
            # Add notable patterns
            if "notable_patterns" in json_data and isinstance(json_data["notable_patterns"], list):
                formatted += "### Notable Patterns\n\n"
                for pattern in json_data["notable_patterns"]:
                    formatted += f"• {pattern}\n"
                formatted += "\n"
            
            # Add recommendations
            if "recommendations" in json_data and isinstance(json_data["recommendations"], list):
                formatted += "### Recommended Next Steps\n\n"
                for i, rec in enumerate(json_data["recommendations"], 1):
                    if isinstance(rec, dict):
                        priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(rec.get('priority', 'Medium'), "🔵")
                        formatted += f"{i}. **{rec.get('action', 'Action not specified')}** {priority_icon}\n"
                        formatted += f"   *Rationale:* {rec.get('rationale', 'No rationale provided')}\n\n"
                    else:
                        formatted += f"{i}. {rec}\n\n"
            
            return formatted.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Error formatting JSON interpretation: {e}")
            return str(json_data)  # Fallback to raw JSON string
    
    def _get_llm_interpretation(self, prompt: str) -> str:
        """Get interpretation from LLM."""
        try:
            # Use the same SQL generation tool for LLM access
            from config import get_config
            config_data = get_config()
            
            sql_tool = create_sql_gen_tool(
                "vertex_ai",
                project_id=config_data["ai"]["project_id"],
                model_name='gemini-2.5-flash',#config_data["ai"]["model_name"],#'gemini-2.5-flash'
                temperature=0.7  # Higher temperature for more creative business insights
            )
            
            # Generate interpretation using LLM
            response = sql_tool.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.,
                    "max_output_tokens": 4000,  # Increased for complete responses
                    "top_k": 40,
                    "top_p": 0.95
                }
            )
            
            interpretation = response.text if hasattr(response, 'text') else str(response)
            
            self.logger.info(f"🔍 FULL LLM INTERPRETATION RESPONSE (length: {len(interpretation)})")
            self.logger.info("=" * 80)
            self.logger.info(interpretation)
            self.logger.info("=" * 80)
            
            return interpretation
            
        except Exception as e:
            self.logger.error(f"❌ LLM interpretation failed: {e}")
            raise
    
    def _create_fallback_interpretation(self, question: str, df: pd.DataFrame) -> str:
        """Create fallback interpretation when LLM fails."""
        
        if df.empty:
            return f"""## 📊 Query Results Analysis

**Question:** {question}

**Finding:** No data was returned for this query.

**Possible Reasons:**
- The specified criteria don't match any records in the database
- The date range might be outside available data
- Filters may be too restrictive

**Recommendation:** Consider broadening the search criteria or checking data availability for the specified parameters."""

        # Basic statistical analysis
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        interpretation = f"""## 📊 Query Results Analysis

**Question:** {question}

**Key Findings:**
- Query returned {len(df)} records with {len(df.columns)} columns
- Data covers: {', '.join(df.columns)}

"""
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if not df[col].empty:
                    interpretation += f"""
**{col.title()} Analysis:**
- Total: {df[col].sum():,.2f}
- Average: {df[col].mean():,.2f}
- Range: {df[col].min():,.2f} to {df[col].max():,.2f}
"""
        
        interpretation += """
**Business Impact:** Review the detailed data above to understand the specific metrics and trends relevant to your business question.

**Next Steps:** Consider drilling down into specific segments or time periods for deeper insights."""

        return interpretation