"""
SQL Generation tool for the LangGraph Analytics Agent.

This tool converts natural language queries into SQL statements using
conversation context and database schema information.
"""
from typing import Dict, List, Optional, Any
import json
import logging
import re
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SQLGenTool(ABC):
    """
    Abstract base class for SQL generation tools.
    
    Provides interface for converting natural language to SQL using
    different AI models or rule-based approaches.
    """
    
    @abstractmethod
    def generate_sql(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, str]:
        """
        Generate SQL from natural language question.
        
        Args:
            question: Natural language question
            schema: Database schema information
            history: Conversation history for context
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        pass


class OpenAISQLGenTool(SQLGenTool):
    """
    OpenAI-based SQL generation tool.
    
    Uses OpenAI's GPT models to convert natural language queries to SQL
    with schema awareness and conversation context.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.1):
        """
        Initialize OpenAI SQL generation tool.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4)
            temperature: Sampling temperature (default: 0.1 for consistency)
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None
    
    def _get_client(self):
        """Get OpenAI client, creating if needed."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package is required for OpenAI SQL generation")
        return self._client
    
    def generate_sql(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, str]:
        """
        Generate SQL using OpenAI GPT model.
        
        Args:
            question: Natural language question
            schema: Database schema information
            history: Conversation history for context
            **kwargs: Additional parameters (last_sql, etc.)
            
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        try:
            client = self._get_client()
            
            # Build context-aware prompt
            prompt = self._build_prompt(question, schema, history, **kwargs)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"Error generating SQL with OpenAI: {e}")
            return {
                "sql": "",
                "explanation": f"Error generating SQL: {str(e)}"
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for SQL generation."""
        return """You are an expert SQL analyst. Your job is to convert natural language questions into accurate, efficient SQL queries.

Rules:
1. Always return valid SQL that matches the provided schema
2. Use proper table and column names from the schema
3. Consider conversation history for context and follow-up queries
4. Generate safe queries (no DROP, DELETE, or modification statements)
5. Include appropriate WHERE clauses, JOINs, and aggregations
6. Return response as JSON with 'sql' and 'explanation' fields
7. For follow-up questions, modify the previous SQL appropriately

Response format:
{
    "sql": "SELECT ... FROM ... WHERE ...",
    "explanation": "This query retrieves ... by joining ... and filtering ..."
}"""
    
    def _build_prompt(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Build the user prompt with all context."""
        prompt_parts = []
        
        # Add schema information
        prompt_parts.append(f"Database Schema:\n{schema}\n")
        
        # Add conversation history if available
        if len(history) > 1:
            prompt_parts.append("Conversation History:")
            for msg in history[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.capitalize()}: {content}")
            prompt_parts.append("")
        
        # Add previous SQL if available (for follow-ups)
        last_sql = kwargs.get('last_sql')
        if last_sql:
            prompt_parts.append(f"Previous SQL query:\n{last_sql}\n")
        
        # Add the current question
        prompt_parts.append(f"Question: {question}")
        prompt_parts.append("\nGenerate SQL query for this question:")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, content: str) -> Dict[str, str]:
        """
        Bulletproof SQL extraction from LLM responses with comprehensive parsing strategies.
        
        This method uses multiple sophisticated extraction strategies but NEVER generates
        fallback SQL. If parsing fails completely, it returns a clear error message.
        
        Parsing Strategies (in order):
        1. Direct JSON parsing
        2. JSON extraction from markdown code blocks
        3. Regex-based JSON extraction with SQL key detection
        4. Balanced brace matching for JSON objects
        5. SQL extraction from code blocks (```sql or ```)
        6. Raw SQL detection with SELECT statement patterns
        7. Malformed JSON repair and extraction
        8. Content analysis for SQL-like patterns
        
        NO FALLBACK SQL GENERATION - Always clear error messages on failure
        """
        try:
            logger.info(f"🔍 PARSING - Starting response parsing for {len(content)} character response")
            
            if not content or not content.strip():
                logger.error("❌ PARSING - Empty or whitespace-only response")
                return {
                    'sql': '',
                    'explanation': 'LLM returned empty response - please try rephrasing your question'
                }
            
            # Clean up the response text
            cleaned_text = content.strip()
            
            # Remove common markdown artifacts that interfere with parsing
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_text = re.sub(r'^```\s*', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^\s*```json\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)
            
            logger.info(f"🧹 PARSING - Cleaned text length: {len(cleaned_text)} characters")
            
            # STRATEGY 1: Direct JSON parsing
            try:
                parsed = json.loads(cleaned_text)
                if isinstance(parsed, dict):
                    if 'sql' in parsed and parsed['sql'].strip():
                        logger.info("✅ PARSING - Successfully parsed as direct JSON")
                        return {
                            'sql': parsed['sql'].strip(),
                            'explanation': parsed.get('explanation', 'SQL query generated successfully')
                        }
                    elif 'query' in parsed and parsed['query'].strip():
                        logger.info("✅ PARSING - Successfully parsed as direct JSON (query key)")
                        return {
                            'sql': parsed['query'].strip(),
                            'explanation': parsed.get('explanation', 'SQL query generated successfully')
                        }
            except json.JSONDecodeError:
                logger.debug("⚠️ PARSING - Direct JSON parsing failed, trying extraction methods")
                pass
            
            # STRATEGY 2: JSON extraction from markdown code blocks
            markdown_patterns = [
                r'```json\s*(\{.*?\})\s*```',          # ```json {...} ```
                r'```\s*(\{.*?\})\s*```',              # ``` {...} ```
                r'```json\s*(\{[^`]*?\})\s*```',       # More permissive JSON in markdown
                r'```\s*(\{[^`]*?\})\s*```',           # More permissive generic markdown
            ]
            
            for i, pattern in enumerate(markdown_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    json_str = match.strip()
                    if json_str:
                        try:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict) and ('sql' in parsed or 'query' in parsed):
                                sql_key = 'sql' if 'sql' in parsed else 'query'
                                if parsed[sql_key].strip():
                                    logger.info(f"✅ PARSING - Extracted JSON from markdown pattern {i+1}")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted from markdown')
                                    }
                        except json.JSONDecodeError as e:
                            logger.debug(f"⚠️ PARSING - Failed to parse markdown JSON: {e}")
                            continue
            
            # STRATEGY 3: Regex-based JSON extraction with SQL key detection
            json_patterns = [
                r'(\{[^{}]*"sql"[^{}]*"[^"]*"[^{}]*\})',                    # Simple SQL key detection
                r'(\{[^{}]*"query"[^{}]*"[^"]*"[^{}]*\})',                  # Simple query key detection  
                r'(\{[^{}]*"sql"\s*:\s*"[^"]*SELECT[^"]*"[^{}]*\})',        # SQL with SELECT keyword
                r'(\{[^{}]*"query"\s*:\s*"[^"]*SELECT[^"]*"[^{}]*\})',      # Query with SELECT keyword
                r'(\{.*?"sql"\s*:\s*".*?".*?\})',                          # Flexible SQL key
                r'(\{.*?"query"\s*:\s*".*?".*?\})',                        # Flexible query key
            ]
            
            for i, pattern in enumerate(json_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if match.strip():
                        try:
                            parsed = json.loads(match)
                            if isinstance(parsed, dict):
                                sql_key = 'sql' if 'sql' in parsed else 'query' if 'query' in parsed else None
                                if sql_key and parsed[sql_key].strip():
                                    logger.info(f"✅ PARSING - Extracted JSON using regex pattern {i+1}")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted via regex')
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # STRATEGY 4: Balanced brace matching for complex JSON
            brace_stack = []
            start_indices = []
            
            for i, char in enumerate(content):
                if char == '{':
                    if not brace_stack:
                        start_indices.append(i)
                    brace_stack.append(char)
                elif char == '}' and brace_stack:
                    brace_stack.pop()
                    if not brace_stack and start_indices:
                        start_idx = start_indices.pop()
                        json_candidate = content[start_idx:i+1]
                        try:
                            parsed = json.loads(json_candidate)
                            if isinstance(parsed, dict):
                                sql_key = 'sql' if 'sql' in parsed else 'query' if 'query' in parsed else None
                                if sql_key and parsed[sql_key].strip():
                                    logger.info("✅ PARSING - Extracted JSON using balanced brace matching")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted via brace matching')
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # STRATEGY 5: SQL extraction from code blocks
            sql_block_patterns = [
                r'```sql\s*(.*?)\s*```',                    # SQL code blocks
                r'```\s*(SELECT.*?)\s*```',                 # Generic SELECT blocks
                r'```sql\s*(SELECT.*?)```',                 # SQL with SELECT (no end whitespace)
                r'```\s*(WITH.*?SELECT.*?)\s*```',          # CTE queries
            ]
            
            for i, pattern in enumerate(sql_block_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip()
                    if sql and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info(f"✅ PARSING - Extracted SQL from code block pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from code block'
                        }
            
            # STRATEGY 6: Raw SQL detection with SELECT statement patterns
            raw_sql_patterns = [
                r'(SELECT\s+(?:[^;])+?)(?:\s*[;}]|\s*$)',               # Complete SELECT statements
                r'(WITH\s+.+?SELECT\s+(?:[^;])+?)(?:\s*[;}]|\s*$)',     # CTE queries
                r'(SELECT\s+.+?FROM\s+.+?)(?:\n\s*\n|\s*$|;)',          # SELECT...FROM with end detection
            ]
            
            for i, pattern in enumerate(raw_sql_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip().rstrip(';')
                    # Validate it's a substantial SQL query
                    if (len(sql) > 15 and 
                        sql.upper().startswith(('SELECT', 'WITH')) and 
                        'FROM' in sql.upper()):
                        logger.info(f"✅ PARSING - Extracted raw SQL using pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from response text'
                        }
            
            # STRATEGY 7: Malformed JSON repair and extraction
            malformed_patterns = [
                r'"sql"\s*:\s*"([^"]*)"',                   # Extract SQL value from malformed JSON
                r'"query"\s*:\s*"([^"]*)"',                 # Extract query value from malformed JSON
                r"'sql'\s*:\s*'([^']*)'",                   # Single quotes variant
                r"'query'\s*:\s*'([^']*)'",                 # Single quotes query variant
            ]
            
            for i, pattern in enumerate(malformed_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip().replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                    if sql and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info(f"✅ PARSING - Repaired malformed JSON pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from malformed JSON'
                        }
            
            # STRATEGY 8: Content analysis for SQL-like patterns (last resort)
            content_upper = content.upper()
            if 'SELECT' in content_upper and 'FROM' in content_upper:
                # Try to extract the most complete SQL-looking segment
                lines = content.split('\n')
                sql_lines = []
                in_sql = False
                
                for line in lines:
                    line_upper = line.strip().upper()
                    if line_upper.startswith('SELECT') or line_upper.startswith('WITH'):
                        in_sql = True
                        sql_lines = [line.strip()]
                    elif in_sql:
                        if (line_upper.startswith(('SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER')) or 
                            line.strip().startswith(('AND', 'OR', ')', ',')) or
                            line.strip() == ''):
                            sql_lines.append(line.strip())
                        else:
                            break
                
                if sql_lines:
                    sql = '\n'.join(sql_lines).strip()
                    # Final validation
                    if len(sql) > 20 and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info("✅ PARSING - Extracted SQL via content analysis")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted via content analysis'
                        }
            
            # ALL STRATEGIES FAILED - Return clear error (NO FALLBACK SQL)
            logger.error("❌ PARSING - All parsing strategies failed")
            logger.error(f"❌ PARSING - Response preview: {content[:200]}...")
            
            return {
                'sql': '',
                'explanation': f'Unable to extract SQL from LLM response. Response format was unexpected. Please try rephrasing your question or check if the query is too complex. Response length: {len(content)} characters.'
            }
            
        except Exception as e:
            logger.error(f"❌ PARSING - Critical error in response parsing: {e}")
            return {
                'sql': '',
                'explanation': f'Error parsing LLM response: {str(e)}. Please try your question again.'
            }

    def _extract_sql_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract SQL query from various text formats with sophisticated pattern matching.
        
        Handles:
        - SQL in code blocks
        - SQL with explanation text
        - Malformed JSON with SQL
        - Plain SQL queries
        """
        try:
            # Pattern 1: SQL in code blocks
            sql_patterns = [
                r'```sql\s*(.*?)\s*```',
                r'```\s*(SELECT.*?(?:;|\Z))\s*```',
                r'SQL[:\s]*`(.*?)`',
                r'Query[:\s]*`(.*?)`',
            ]
            
            for pattern in sql_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip()
                    if sql and sql.upper().startswith('SELECT'):
                        return {
                            'sql': sql,
                            'explanation': 'SQL extracted from code block'
                        }
            
            # Pattern 2: Look for SELECT statements
            select_pattern = r'(SELECT\b.*?)(?:\n\n|\Z|;)'
            matches = re.findall(select_pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                sql = match.strip().rstrip(';')
                if len(sql) > 10:  # Ensure it's substantial
                    return {
                        'sql': sql,
                        'explanation': 'SQL extracted from text'
                    }
            
            # Pattern 3: JSON-like but malformed
            json_like_pattern = r'"sql"\s*:\s*"(.*?)"'
            matches = re.findall(json_like_pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                sql = match.strip().replace('\\n', '\n').replace('\\"', '"')
                if sql and sql.upper().startswith('SELECT'):
                    return {
                        'sql': sql,
                        'explanation': 'SQL extracted from JSON-like format'
                    }
            
            return {'sql': '', 'explanation': 'No SQL found in text'}
            
        except Exception as e:
            logger.error(f"Error extracting SQL from text: {e}")
            return {'sql': '', 'explanation': f'SQL extraction error: {str(e)}'}

    def _analyze_schema(self, schema: str) -> str:
        """
        Analyze the database schema to provide better context for SQL generation.
        
        Args:
            schema: Database schema information
            
        Returns:
            Schema analysis string with insights for SQL generation
        """
        try:
            analysis_parts = []
            
            # Extract table information
            tables = []
            lines = schema.split('\n')
            current_table = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('CREATE TABLE') or 'TABLE' in line.upper():
                    # Extract table name
                    match = re.search(r'CREATE TABLE\s+(\w+)|TABLE\s+(\w+)', line, re.IGNORECASE)
                    if match:
                        current_table = match.group(1) or match.group(2)
                        tables.append(current_table)
                elif current_table and ('PRIMARY KEY' in line.upper() or 'FOREIGN KEY' in line.upper() or 'id' in line.lower()):
                    # Capture key information
                    pass
            
            if tables:
                analysis_parts.append(f"Available tables: {', '.join(tables)}")
            
            # Add basic recommendations
            analysis_parts.append("Remember to use proper table joins and filtering where appropriate.")
            
            return "\n".join(analysis_parts) if analysis_parts else ""
            
        except Exception as e:
            logger.error(f"Error analyzing schema: {e}")
            return ""


class RuleBasedSQLGenTool(SQLGenTool):
    """
    Rule-based SQL generation tool.
    
    Uses pattern matching and templates to generate SQL from
    natural language queries. Useful for simple, predictable queries.
    """
    
    def __init__(self):
        """Initialize rule-based SQL generation tool."""
        self.patterns = {
            'show_all': {
                'keywords': ['show all', 'all records', 'list all', 'display all', 'get all', 'fetch all'],
                'template': 'SELECT * FROM {table}'
            },
            'count': {
                'keywords': ['count', 'how many', 'number of'],
                'template': 'SELECT COUNT(*) as count FROM {table}'
            },
            'sum': {
                'keywords': ['total', 'sum of', 'sum'],
                'template': 'SELECT SUM({column}) as total FROM {table}'
            },
            'average': {
                'keywords': ['average', 'avg', 'mean'],
                'template': 'SELECT AVG({column}) as average FROM {table}'
            },
            'top_by_amount': {
                'keywords': ['top', 'highest', 'largest', 'biggest', 'max', 'maximum'],
                'template': 'SELECT * FROM {table} ORDER BY {column} DESC LIMIT {limit}'
            },
            'bottom_by_amount': {
                'keywords': ['bottom', 'lowest', 'smallest', 'min', 'minimum'],
                'template': 'SELECT * FROM {table} ORDER BY {column} ASC LIMIT {limit}'
            },
            'group_by': {
                'keywords': ['by ', 'per ', 'each ', 'group by'],
                'template': 'SELECT {group_column}, {agg_func}({agg_column}) FROM {table} GROUP BY {group_column}'
            },
            'filter': {
                'keywords': ['where', 'filter', 'only', 'just'],
                'template': 'SELECT * FROM {table} WHERE {column} = \'{value}\''
            }
        }

    def generate_sql(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, str]:
        """
        Generate SQL using rule-based patterns.
        """
        try:
            question_lower = question.lower()
            
            # Extract table and column information from schema
            tables = self._extract_tables_from_schema(schema)
            
            if not tables:
                logger.error("❌ RULE-BASED - No tables found in schema")
                return {
                    "sql": "",
                    "explanation": "Unable to generate SQL: No table information found in database schema. Please ensure schema is properly formatted."
                }
            
            # Default to first table if not specified
            primary_table = list(tables.keys())[0]
            
            # Pattern matching - prioritize more specific patterns first
            # Sort patterns by keyword length (longer phrases first)
            sorted_patterns = sorted(
                self.patterns.items(),
                key=lambda x: max(len(keyword.split()) for keyword in x[1]['keywords']),
                reverse=True
            )
            
            for pattern_name, pattern_info in sorted_patterns:
                if any(keyword in question_lower for keyword in pattern_info['keywords']):
                    return self._generate_from_pattern(
                        pattern_name, 
                        pattern_info, 
                        question_lower, 
                        tables, 
                        primary_table
                    )
                    
            # Enhanced fallback for specific business questions
            if any(word in question_lower for word in ['percentage', 'percent', '%']) and 'alert' in question_lower and 'transaction' in question_lower:
                return self._generate_alert_percentage_sql(question)
            elif 'risk' in question_lower and any(word in question_lower for word in ['high', 'medium', 'low']):
                return self._generate_risk_analysis_sql(question)
            elif 'channel' in question_lower:
                return self._generate_channel_analysis_sql(question)
            else:
                logger.warning("❌ RULE-BASED - No pattern matched for question")
                return {
                    "sql": "",
                    "explanation": f"Unable to generate SQL: Question pattern not recognized by rule-based system. Question: '{question}'. Please try rephrasing with keywords like 'count', 'total', 'average', 'highest', 'lowest', etc."
                }
                
        except Exception as e:
            logger.error(f"Error in rule-based SQL generation: {e}")
            return {
                "sql": "",
                "explanation": f"Error generating SQL: {str(e)}"
            }

    def _extract_tables_from_schema(self, schema: str) -> Dict[str, List[str]]:
        """Extract table and column information from schema text."""
        tables = {}
        current_table = None
        
        for line in schema.split('\n'):
            line = line.strip()
            
            if line.startswith('Table:'):
                current_table = line.replace('Table:', '').strip()
                tables[current_table] = []
            elif current_table and line and ':' in line:
                column_name = line.split(':')[0].strip()
                tables[current_table].append(column_name)
        
        return tables
    
    def _generate_from_pattern(
        self, 
        pattern_name: str, 
        pattern_info: Dict, 
        question: str, 
        tables: Dict[str, List[str]], 
        primary_table: str
    ) -> Dict[str, str]:
        """Generate SQL from a matched pattern."""
        template = pattern_info['template']
        
        # Simple column matching
        numeric_columns = ['amount', 'price', 'revenue', 'sales', 'total', 'value', 'count']
        date_columns = ['date', 'created_at', 'updated_at', 'timestamp']
        
        table_columns = tables.get(primary_table, [])
        
        # Find appropriate columns
        agg_column = None
        group_column = None
        
        for col in table_columns:
            col_lower = col.lower()
            if any(nc in col_lower for nc in numeric_columns):
                agg_column = col
            if any(dc in col_lower for dc in date_columns):
                group_column = col
        
        # Fallback columns
        if not agg_column and table_columns:
            agg_column = table_columns[0]
        if not group_column and len(table_columns) > 1:
            group_column = table_columns[1]
        
        # Fill template based on pattern
        if pattern_name == 'top_by_amount' or pattern_name == 'bottom_by_amount':
            # Extract number from question (default to 5)
            numbers = re.findall(r'\d+', question)
            limit = numbers[0] if numbers else '5'
            
            # Find the best amount/numeric column
            amount_column = None
            for col in table_columns:
                col_lower = col.lower()
                if any(ac in col_lower for ac in ['amount', 'total', 'revenue', 'sales', 'price', 'value', 'score', 'rating']):
                    amount_column = col
                    break
            
            if not amount_column and agg_column:
                amount_column = agg_column
                
            sql = template.format(
                table=primary_table,
                column=amount_column or 'id',
                limit=limit
            )
            
            return {
                "sql": sql,
                "explanation": f"Finding {pattern_name.replace('_', ' ')} records by {amount_column or 'id'}"
            }
            
        elif pattern_name == 'group_by':
            # Detect aggregation function
            agg_func = 'COUNT'
            if any(word in question for word in ['sum', 'total']):
                agg_func = 'SUM'
            elif any(word in question for word in ['avg', 'average']):
                agg_func = 'AVG'
            
            sql = template.format(
                table=primary_table,
                group_column=group_column or table_columns[0],
                agg_func=agg_func,
                agg_column=agg_column or '*'
            )
            
            return {
                "sql": sql,
                "explanation": f"Grouping {primary_table} data by {group_column}"
            }
            
        else:
            # Simple template filling
            sql = template.format(
                table=primary_table,
                column=agg_column or table_columns[0] if table_columns else 'id'
            )
            
            return {
                "sql": sql,
                "explanation": f"Generated {pattern_name.replace('_', ' ')} query"
            }

    def _generate_alert_percentage_sql(self, question: str) -> Dict[str, str]:
        """Generate SQL for alert percentage queries."""
        # Determine date range from question
        date_filter = ""
        if "q1 2025" in question.lower() or "Q1 2025" in question:
            date_filter = "AND t.transaction_date BETWEEN '2025-01-01' AND '2025-03-31'"
        
        sql = f"""
        SELECT 
            ROUND(
                CAST(COUNT(DISTINCT a.alert_id) AS REAL) / 
                CAST(COUNT(DISTINCT t.transaction_id) AS REAL) * 100.0, 
                2
            ) as alert_percentage
        FROM fact_transactions t
        LEFT JOIN fact_alerts a ON t.transaction_id = a.transaction_id
        WHERE 1=1 {date_filter}
        """.strip()
        
        return {
            "sql": sql,
            "explanation": "Calculate percentage of transactions that resulted in alerts"
        }

    def _generate_risk_analysis_sql(self, question: str) -> Dict[str, str]:
        """Generate SQL for risk analysis queries."""
        sql = """
        SELECT 
            UPPER(risk_level) as risk_level,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) as percentage
        FROM fact_transactions
        WHERE risk_level IS NOT NULL
        GROUP BY UPPER(risk_level)
        ORDER BY count DESC
        """.strip()
        
        return {
            "sql": sql,
            "explanation": "Analyze distribution of transactions by risk level"
        }

    def _generate_channel_analysis_sql(self, question: str) -> Dict[str, str]:
        """Generate SQL for channel analysis queries."""
        sql = """
        SELECT 
            UPPER(channel) as channel,
            COUNT(*) as transaction_count,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM fact_transactions
        WHERE channel IS NOT NULL
        GROUP BY UPPER(channel)
        ORDER BY transaction_count DESC
        """.strip()
        
        return {
            "sql": sql,
            "explanation": "Analyze transaction distribution by channel"
        }


class VertexAISQLGenTool(SQLGenTool):
    """
    SQL generation using Google Vertex AI.
    """
    
    def __init__(self, project_id: str, model_name: str = "gemini-2.5-pro", temperature: float = 0.1):
        """Initialize Vertex AI SQL generation tool."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            self.project_id = project_id
            self.model_name = model_name
            self.temperature = temperature
            
            vertexai.init(project=project_id, location="europe-west1")
            self.model = GenerativeModel(model_name)
            
            logger.info(f"✅ Vertex AI initialized - Project: {project_id}, Model: {model_name}")
            
        except ImportError as e:
            logger.error(f"❌ Vertex AI dependencies not found: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI: {e}")
            raise

    def generate_sql(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, str]:
        """
        Generate SQL using Vertex AI.
        """
        try:
            # Build prompt with dynamic date handling and case sensitivity guidance
            prompt = self._build_sqlite_prompt(question, schema, history, kwargs.get('last_sql'))
            
            # Comprehensive logging for debugging
            logger.info("VERTEX AI REQUEST - Prompt length: %d characters", len(prompt))
            logger.info("VERTEX AI REQUEST - Full prompt:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            
            # Generate response with detailed logging
            generation_config = {
                "temperature": 0.1,
                "max_output_tokens": 8192,  # Increased from 4096 to handle complex CTEs
                "top_k": 20,
                "top_p": 0.7,
            }
            
            logger.info("VERTEX AI REQUEST - Generation config:")
            logger.info("  - Temperature: %s", generation_config["temperature"])
            logger.info("  - Max output tokens: %s", generation_config["max_output_tokens"])
            logger.info("  - Top K: %s", generation_config["top_k"])
            logger.info("  - Top P: %s", generation_config["top_p"])
            logger.info("  - Config: %s", generation_config)
            
            logger.info("VERTEX AI REQUEST - Sending request...")
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            logger.info("VERTEX AI RESPONSE - Raw response received")
            logger.info("VERTEX AI RESPONSE - Response object type: %s", type(response))
            logger.info("VERTEX AI RESPONSE - Has text attribute: %s", hasattr(response, 'text'))
            
            if response and hasattr(response, 'text') and response.text:
                logger.info(f"🔍 VERTEX AI RESPONSE - Text length: {len(response.text)} characters")
                logger.info(f"🔍 VERTEX AI RESPONSE - Text ends with: '{response.text[-20:]}'")
                
                # LOG FULL RESPONSE CONTENT (Critical for debugging)
                logger.info("🔍 VERTEX AI RESPONSE - Full response content:")
                logger.info("=" * 80)
                logger.info(response.text)
                logger.info("=" * 80)
                
                # Check if response appears complete
                if response.text.strip().endswith('}'):
                    logger.info("🔍 VERTEX AI RESPONSE - Response appears complete (ends with })")
                elif response.text.strip().endswith('"'):
                    logger.info("🔍 VERTEX AI RESPONSE - Response might be complete (ends with \")")
                else:
                    logger.warning(f"🔍 VERTEX AI RESPONSE - Response appears truncated, ends with: '{response.text[-50:]}'")
                
                # Parse response with sophisticated method
                return self._parse_response(response.text)
                
            else:
                logger.error("VERTEX AI RESPONSE - No text content in response")
                return {
                    "sql": "",
                    "explanation": "No response from Vertex AI"
                }
                
        except Exception as e:
            logger.error(f"Error generating SQL with Vertex AI: {e}")
            return {
                "sql": "",
                "explanation": f"Error generating SQL: {str(e)}"
            }

    def _parse_response(self, content: str) -> Dict[str, str]:
        """
        Bulletproof SQL extraction from Vertex AI responses with comprehensive parsing strategies.
        
        This method uses multiple sophisticated extraction strategies but NEVER generates
        fallback SQL. If parsing fails completely, it returns a clear error message.
        
        Parsing Strategies (in order):
        1. Direct JSON parsing
        2. JSON extraction from markdown code blocks
        3. Regex-based JSON extraction with SQL key detection
        4. Balanced brace matching for JSON objects
        5. SQL extraction from code blocks (```sql or ```)
        6. Raw SQL detection with SELECT statement patterns
        7. Malformed JSON repair and extraction
        8. Content analysis for SQL-like patterns
        
        NO FALLBACK SQL GENERATION - Always clear error messages on failure
        """
        try:
            logger.info(f"🔍 PARSING - Starting Vertex AI response parsing for {len(content)} character response")
            
            if not content or not content.strip():
                logger.error("❌ PARSING - Empty or whitespace-only response")
                return {
                    'sql': '',
                    'explanation': 'Vertex AI returned empty response - please try rephrasing your question'
                }
            
            # Clean up the response text
            cleaned_text = content.strip()
            
            # Remove common markdown artifacts that interfere with parsing
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_text = re.sub(r'^```\s*', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^\s*```json\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)
            
            logger.info(f"🧹 PARSING - Cleaned Vertex AI text length: {len(cleaned_text)} characters")
            
            # STRATEGY 1: Direct JSON parsing
            try:
                parsed = json.loads(cleaned_text)
                if isinstance(parsed, dict):
                    if 'sql' in parsed and parsed['sql'].strip():
                        logger.info("✅ PARSING - Successfully parsed Vertex AI response as direct JSON")
                        return {
                            'sql': parsed['sql'].strip(),
                            'explanation': parsed.get('explanation', 'SQL query generated successfully')
                        }
                    elif 'query' in parsed and parsed['query'].strip():
                        logger.info("✅ PARSING - Successfully parsed Vertex AI response as direct JSON (query key)")
                        return {
                            'sql': parsed['query'].strip(),
                            'explanation': parsed.get('explanation', 'SQL query generated successfully')
                        }
            except json.JSONDecodeError:
                logger.debug("⚠️ PARSING - Direct JSON parsing failed for Vertex AI response, trying extraction methods")
                pass
            
            # STRATEGY 2: JSON extraction from markdown code blocks
            markdown_patterns = [
                r'```json\s*(\{.*?\})\s*```',          # ```json {...} ```
                r'```\s*(\{.*?\})\s*```',              # ``` {...} ```
                r'```json\s*(\{[^`]*?\})\s*```',       # More permissive JSON in markdown
                r'```\s*(\{[^`]*?\})\s*```',           # More permissive generic markdown
            ]
            
            for i, pattern in enumerate(markdown_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    json_str = match.strip()
                    if json_str:
                        try:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict) and ('sql' in parsed or 'query' in parsed):
                                sql_key = 'sql' if 'sql' in parsed else 'query'
                                if parsed[sql_key].strip():
                                    logger.info(f"✅ PARSING - Extracted JSON from Vertex AI markdown pattern {i+1}")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted from markdown')
                                    }
                        except json.JSONDecodeError as e:
                            logger.debug(f"⚠️ PARSING - Failed to parse Vertex AI markdown JSON: {e}")
                            continue
            
            # STRATEGY 3: Regex-based JSON extraction with SQL key detection
            json_patterns = [
                r'(\{[^{}]*"sql"[^{}]*"[^"]*"[^{}]*\})',                    # Simple SQL key detection
                r'(\{[^{}]*"query"[^{}]*"[^"]*"[^{}]*\})',                  # Simple query key detection  
                r'(\{[^{}]*"sql"\s*:\s*"[^"]*SELECT[^"]*"[^{}]*\})',        # SQL with SELECT keyword
                r'(\{[^{}]*"query"\s*:\s*"[^"]*SELECT[^"]*"[^{}]*\})',      # Query with SELECT keyword
                r'(\{.*?"sql"\s*:\s*".*?".*?\})',                          # Flexible SQL key
                r'(\{.*?"query"\s*:\s*".*?".*?\})',                        # Flexible query key
            ]
            
            for i, pattern in enumerate(json_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if match.strip():
                        try:
                            parsed = json.loads(match)
                            if isinstance(parsed, dict):
                                sql_key = 'sql' if 'sql' in parsed else 'query' if 'query' in parsed else None
                                if sql_key and parsed[sql_key].strip():
                                    logger.info(f"✅ PARSING - Extracted JSON from Vertex AI using regex pattern {i+1}")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted via regex')
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # STRATEGY 4: Balanced brace matching for complex JSON
            brace_stack = []
            start_indices = []
            
            for i, char in enumerate(content):
                if char == '{':
                    if not brace_stack:
                        start_indices.append(i)
                    brace_stack.append(char)
                elif char == '}' and brace_stack:
                    brace_stack.pop()
                    if not brace_stack and start_indices:
                        start_idx = start_indices.pop()
                        json_candidate = content[start_idx:i+1]
                        try:
                            parsed = json.loads(json_candidate)
                            if isinstance(parsed, dict):
                                sql_key = 'sql' if 'sql' in parsed else 'query' if 'query' in parsed else None
                                if sql_key and parsed[sql_key].strip():
                                    logger.info("✅ PARSING - Extracted JSON from Vertex AI using balanced brace matching")
                                    return {
                                        'sql': parsed[sql_key].strip(),
                                        'explanation': parsed.get('explanation', 'SQL query extracted via brace matching')
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # STRATEGY 5: SQL extraction from code blocks
            sql_block_patterns = [
                r'```sql\s*(.*?)\s*```',                    # SQL code blocks
                r'```\s*(SELECT.*?)\s*```',                 # Generic SELECT blocks
                r'```sql\s*(SELECT.*?)```',                 # SQL with SELECT (no end whitespace)
                r'```\s*(WITH.*?SELECT.*?)\s*```',          # CTE queries
            ]
            
            for i, pattern in enumerate(sql_block_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip()
                    if sql and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info(f"✅ PARSING - Extracted SQL from Vertex AI code block pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from code block'
                        }
            
            # STRATEGY 6: Raw SQL detection with SELECT statement patterns
            raw_sql_patterns = [
                r'(SELECT\s+(?:[^;])+?)(?:\s*[;}]|\s*$)',               # Complete SELECT statements
                r'(WITH\s+.+?SELECT\s+(?:[^;])+?)(?:\s*[;}]|\s*$)',     # CTE queries
                r'(SELECT\s+.+?FROM\s+.+?)(?:\n\s*\n|\s*$|;)',          # SELECT...FROM with end detection
            ]
            
            for i, pattern in enumerate(raw_sql_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip().rstrip(';')
                    # Validate it's a substantial SQL query
                    if (len(sql) > 15 and 
                        sql.upper().startswith(('SELECT', 'WITH')) and 
                        'FROM' in sql.upper()):
                        logger.info(f"✅ PARSING - Extracted raw SQL from Vertex AI using pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from response text'
                        }
            
            # STRATEGY 7: Malformed JSON repair and extraction
            malformed_patterns = [
                r'"sql"\s*:\s*"([^"]*)"',                   # Extract SQL value from malformed JSON
                r'"query"\s*:\s*"([^"]*)"',                 # Extract query value from malformed JSON
                r"'sql'\s*:\s*'([^']*)'",                   # Single quotes variant
                r"'query'\s*:\s*'([^']*)'",                 # Single quotes query variant
            ]
            
            for i, pattern in enumerate(malformed_patterns):
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    sql = match.strip().replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                    if sql and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info(f"✅ PARSING - Repaired malformed JSON from Vertex AI pattern {i+1}")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted from malformed JSON'
                        }
            
            # STRATEGY 8: Content analysis for SQL-like patterns (last resort)
            content_upper = content.upper()
            if 'SELECT' in content_upper and 'FROM' in content_upper:
                # Try to extract the most complete SQL-looking segment
                lines = content.split('\n')
                sql_lines = []
                in_sql = False
                
                for line in lines:
                    line_upper = line.strip().upper()
                    if line_upper.startswith('SELECT') or line_upper.startswith('WITH'):
                        in_sql = True
                        sql_lines = [line.strip()]
                    elif in_sql:
                        if (line_upper.startswith(('SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER')) or 
                            line.strip().startswith(('AND', 'OR', ')', ',')) or
                            line.strip() == ''):
                            sql_lines.append(line.strip())
                        else:
                            break
                
                if sql_lines:
                    sql = '\n'.join(sql_lines).strip()
                    # Final validation
                    if len(sql) > 20 and sql.upper().startswith(('SELECT', 'WITH')):
                        logger.info("✅ PARSING - Extracted SQL from Vertex AI via content analysis")
                        return {
                            'sql': sql,
                            'explanation': 'SQL query extracted via content analysis'
                        }
            
            # ALL STRATEGIES FAILED - Return clear error (NO FALLBACK SQL)
            logger.error("❌ PARSING - All Vertex AI parsing strategies failed")
            logger.error(f"❌ PARSING - Vertex AI response preview: {content[:200]}...")
            
            return {
                'sql': '',
                'explanation': f'Unable to extract SQL from Vertex AI response. Response format was unexpected. Please try rephrasing your question or check if the query is too complex. Response length: {len(content)} characters.'
            }
            
        except Exception as e:
            logger.error(f"❌ PARSING - Critical error in Vertex AI response parsing: {e}")
            return {
                'sql': '',
                'explanation': f'Error parsing Vertex AI response: {str(e)}. Please try your question again.'
            }

    def _extract_json_simple(self, text: str) -> Optional[Dict]:
        """Extract JSON using simple brace matching."""
        try:
            # Find first { and last }
            start = text.find('{')
            if start == -1:
                return None
                
            # Find matching closing brace
            brace_count = 0
            end = start
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if brace_count != 0:
                return None
                
            json_str = text[start:end]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError, IndexError):
            # Multiple fallback strategies
            for pattern in [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{[^{}]*"sql"[^{}]*"explanation"[^{}]*\})',
                r'(\{.*?"sql".*?\})'
            ]:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        continue
            return None

    def _extract_sql_fallback(self, text: str) -> str:
        """Extract SQL when JSON parsing fails."""
        # Look for SQL patterns
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?;?)\s*```',
            r'(SELECT\s+(?:(?!SELECT)[^;])*)',
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if sql.upper().startswith('SELECT'):
                    return sql
                    
        return ""

    def _build_sqlite_prompt(self, question: str, schema: str, history: List[Dict[str, str]], last_sql: Optional[str] = None) -> str:
        """Build SQLite-specific prompt with all context and sophisticated guidance."""
        prompt_parts = []
        
        # Calculate current quarter information for dynamic examples
        quarter_info = self._calculate_quarter_info()
        
        # Dynamic schema-driven instructions for SQLite
        prompt_parts.append(f"""You are an expert SQLite SQL analyst. Convert natural language questions into accurate SQLite SQL queries using the provided database schema.

🚨 CRITICAL OUTPUT FORMAT (MANDATORY):
You MUST return ONLY a valid JSON object in this EXACT format:
{{"sql": "SELECT column FROM table WHERE condition", "explanation": "Brief description"}}

⚠️ RESPONSE REQUIREMENTS:
- Start response with {{ and end with }}
- No extra text before or after the JSON
- No markdown code blocks around the JSON  
- Use double quotes for JSON keys and string values
- Escape quotes in SQL as \"
- Keep explanation under 100 characters
- SQL must be complete and executable
- NEVER wrap response in ```json or ``` blocks
- NEVER add explanatory text outside the JSON

✅ CORRECT RESPONSE EXAMPLE:
{{"sql": "SELECT customer_id, SUM(amount) as total FROM fact_transactions WHERE UPPER(risk_level) = 'HIGH' GROUP BY customer_id ORDER BY total DESC LIMIT 10", "explanation": "Top 10 customers by high-risk transaction amounts"}}

❌ INCORRECT RESPONSE EXAMPLES:
- ```json {{"sql": "..."}} ```  (NO markdown blocks)
- Here is the SQL: {{"sql": "..."}}  (NO extra text)
- {{"query": "..."}}  (WRONG key name)
- {{"sql": "SELECT * FROM"}}  (INCOMPLETE SQL)
- Any response ending with ``` (NO markdown endings)

CORE SQL RULES:
1. Use SQLite syntax (no semicolons in JSON)
2. Use ONLY tables and columns from the schema
3. Generate COMPLETE SQL - never truncate WHERE clauses
4. For ratios: Use CAST(numerator AS REAL) / denominator 
5. For highest/lowest: Use ORDER BY DESC/ASC LIMIT 1
6. ALWAYS validate column names against schema

CASE SENSITIVITY HANDLING:
⚠️ CRITICAL: SQLite string comparisons are case-sensitive by default!
- For text filters, ALWAYS use UPPER() or LOWER() for case-insensitive matching
- Example: WHERE UPPER(risk_level) = 'HIGH' instead of WHERE risk_level = 'high'
- For LIKE patterns: WHERE UPPER(column) LIKE UPPER('%pattern%')
- Common case issues: 'high' vs 'HIGH', 'usa' vs 'USA', 'alert' vs 'Alert'
- When unsure of exact case, use: WHERE UPPER(column) IN ('VALUE1', 'VALUE2')

DYNAMIC DATE CONTEXT:
- Today's date is {quarter_info['current_date']}
- Current quarter is {quarter_info['current_quarter']} {quarter_info['current_quarter_year']} ({quarter_info['current_quarter_range']})
- Last completed quarter is {quarter_info['last_quarter']} {quarter_info['last_quarter_year']} ({quarter_info['last_quarter_range']})

BUSINESS TERMINOLOGY MAPPING:
- "quarter" / "last quarter" → Use dim_calendar table with quarter column, filter to {quarter_info['last_quarter']} {quarter_info['last_quarter_year']}
- "month" / "last month" → Use STRFTIME('%Y-%m', date_column) or dim_calendar 
- "year" / "last year" → Use dim_calendar.year column
- "high-risk" / "high risk" → Use UPPER(risk_level) = 'HIGH' (case-insensitive)
- "low-risk" / "low risk" → Use UPPER(risk_level) = 'LOW' (case-insensitive)
- "medium-risk" / "medium risk" → Use UPPER(risk_level) = 'MEDIUM' (case-insensitive)
- "revenue" / "sales" → Use amount or total_amount columns
- "customers" → Use dim_customer table
- "transactions" → Use fact_transactions table  
- "alerts" → Use fact_alerts table
- Geographic filters → Use UPPER(region) = UPPER('North America') for case-insensitive matching
- Alert types → Use UPPER(alert_type) = UPPER('Sanctions') for case-insensitive matching

🔥 RESPONSE FORMATTING RULES (CRITICAL):
1. Response must be valid JSON that can be parsed by json.loads()
2. SQL must be complete from SELECT to final clause (WHERE/ORDER BY/LIMIT)
3. No truncation - include ALL parts of the query
4. Test your JSON format before responding
5. If query is complex, break into subqueries or CTEs but keep complete""")
        
        # Add schema information with enhanced formatting
        prompt_parts.append(f"DATABASE SCHEMA:\n{schema}\n")
        prompt_parts.append("")
        
        # Add conversation history if available
        if len(history) > 1:
            prompt_parts.append("CONVERSATION CONTEXT:")
            for msg in history[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                # Include SQL if available for context
                if role == 'assistant' and msg.get('sql'):
                    content += f" (Generated SQL: {msg.get('sql')})"
                prompt_parts.append(f"  {role.capitalize()}: {content}")
            prompt_parts.append("")
        
        # Add previous SQL if available (for follow-ups)
        if last_sql:
            prompt_parts.append("⚠️  FOLLOW-UP DETECTED:")
            prompt_parts.append(f"Previous SQL: {last_sql}")
            prompt_parts.append("")
            prompt_parts.append("CRITICAL: This is a FOLLOW-UP question. You must:")
            prompt_parts.append("1. Analyze how the current question modifies the previous query")
            prompt_parts.append("2. If it's a filter (geographic, size, category), add WHERE clause to previous SQL")
            prompt_parts.append("3. If it's a ranking requirement, add ORDER BY and LIMIT to previous SQL")
            prompt_parts.append("4. If it's an aggregation change, modify the SELECT clause")
            prompt_parts.append("5. Do NOT generate a completely new query unless absolutely necessary")
            prompt_parts.append("")
            
            # Detect specific follow-up types
            question_lower = question.lower()
            if any(word in question_lower for word in ['america', 'usa', 'europe', 'asia', 'region']):
                prompt_parts.append("🌍 GEOGRAPHIC FILTER detected: Add appropriate WHERE clause for region/location")
            if any(word in question_lower for word in ['biggest', 'largest', 'highest', 'top', 'maximum']):
                prompt_parts.append("📊 RANKING REQUIREMENT detected: Add ORDER BY DESC LIMIT clause")
            if any(word in question_lower for word in ['smallest', 'lowest', 'minimum', 'bottom']):
                prompt_parts.append("📊 REVERSE RANKING detected: Add ORDER BY ASC LIMIT clause")
            
            prompt_parts.append("")
        
        # Add the current question with emphasis
        prompt_parts.append(f"USER QUESTION: {question}")
        prompt_parts.append("")
        
        # Add specific examples based on the question type
        question_lower = question.lower()
        if any(word in question_lower for word in ['biggest', 'largest', 'highest']):
            prompt_parts.append("EXAMPLE for 'biggest customer':")
            prompt_parts.append("  SELECT c.name, SUM(s.total_amount) as total_sales")
            prompt_parts.append("  FROM customers c JOIN sales s ON c.region = s.region") 
            prompt_parts.append("  GROUP BY c.name")
            prompt_parts.append("  ORDER BY total_sales DESC LIMIT 1")
            prompt_parts.append("")
        
        if any(word in question_lower for word in ['quarter', 'last quarter', 'q1', 'q2', 'q3', 'q4']):
            prompt_parts.append(f"DYNAMIC EXAMPLE for 'last quarter' analysis (based on current date {quarter_info['current_date']}):")
            prompt_parts.append("  SELECT fa.alert_type, COUNT(fa.alert_id) as count")
            prompt_parts.append("  FROM fact_alerts fa")
            prompt_parts.append("  JOIN dim_calendar dc ON fa.alert_dt = dc.dt") 
            prompt_parts.append(f"  WHERE dc.year = {quarter_info['last_quarter_year']} AND dc.quarter = '{quarter_info['last_quarter']}'")
            prompt_parts.append("  GROUP BY fa.alert_type ORDER BY count DESC")
            prompt_parts.append("")
            prompt_parts.append(f"⚠️  CRITICAL: 'Last quarter' means {quarter_info['last_quarter']} {quarter_info['last_quarter_year']} ({quarter_info['last_quarter_range']}), NOT rolling 3 months!")
            prompt_parts.append("")
            
        if any(word in question_lower for word in ['high-risk', 'high risk']):
            prompt_parts.append("EXAMPLE for 'high-risk' queries (case-insensitive):")
            prompt_parts.append("  Use WHERE UPPER(risk_level) = 'HIGH'")
            prompt_parts.append("  Alternative: WHERE risk_level COLLATE NOCASE = 'high'")
            prompt_parts.append("")
        
        if any(word in question_lower for word in ['america', 'usa', 'north america']) and last_sql:
            prompt_parts.append("EXAMPLE for geographic follow-up 'in america' (case-insensitive):")
            prompt_parts.append(f"  Previous: {last_sql}")
            prompt_parts.append("  Modified: Add WHERE UPPER(region) LIKE '%AMERICA%' OR UPPER(region) = 'USA'")
            prompt_parts.append("  Alternative: WHERE region COLLATE NOCASE LIKE '%america%'")
            prompt_parts.append("")
        
        prompt_parts.append("🎯 FINAL INSTRUCTIONS:")
        prompt_parts.append("1. Analyze the question carefully")
        prompt_parts.append("2. If this is a follow-up, MODIFY the previous SQL")
        prompt_parts.append("3. Map to appropriate columns from the schema")
        prompt_parts.append("4. Use JOINs when relating multiple tables")
        prompt_parts.append("5. Generate efficient SQLite query")
        prompt_parts.append("6. ⚠️  CRITICAL: Generate COMPLETE SQL - never truncate WHERE clauses")
        prompt_parts.append("7. Include ALL parts of the query: SELECT, FROM, WHERE, ORDER BY, LIMIT")
        prompt_parts.append("8. 🔤 CASE SENSITIVITY: Use UPPER() for all text comparisons")
        prompt_parts.append("9. 📝 RESPONSE FORMAT: Return ONLY the JSON object, nothing else")
        prompt_parts.append("")
        prompt_parts.append("CASE-INSENSITIVE EXAMPLES:")
        prompt_parts.append("✅ Good: WHERE UPPER(alert_type) = 'SANCTIONS'")
        prompt_parts.append("✅ Good: WHERE UPPER(region) LIKE '%AMERICA%'") 
        prompt_parts.append("✅ Good: WHERE UPPER(risk_level) IN ('HIGH', 'MEDIUM')")
        prompt_parts.append("❌ Bad: WHERE alert_type = 'sanctions' (might not match 'SANCTIONS' in data)")
        prompt_parts.append("❌ Bad: WHERE region = 'usa' (might not match 'USA' in data)")
        prompt_parts.append("")
        prompt_parts.append("🚨 MANDATORY JSON FORMAT:")
        prompt_parts.append('{"sql": "COMPLETE_SQL_QUERY_HERE", "explanation": "Brief description under 100 chars"}')
        prompt_parts.append("")
        prompt_parts.append("🚀 GENERATE RESPONSE NOW - JSON ONLY:")
        prompt_parts.append("")
        prompt_parts.append("FINAL REMINDER: Your response must be EXACTLY:")
        prompt_parts.append('{"sql": "YOUR_COMPLETE_SQL_HERE", "explanation": "YOUR_BRIEF_EXPLANATION_HERE"}')
        prompt_parts.append("")
        prompt_parts.append("NO markdown blocks, NO extra text, NO ```json or ```, JUST the JSON object:")
        
        return "\n".join(prompt_parts)
    
    def _calculate_quarter_info(self, current_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate current and last quarter information for dynamic date handling."""
        if current_date is None:
            current_date = datetime.now()
        
        # Current quarter calculation
        current_month = current_date.month
        current_year = current_date.year
        current_quarter_num = (current_month - 1) // 3 + 1
        current_quarter = f"Q{current_quarter_num}"
        
        # Last quarter calculation
        if current_quarter_num == 1:
            last_quarter_num = 4
            last_quarter_year = current_year - 1
        else:
            last_quarter_num = current_quarter_num - 1
            last_quarter_year = current_year
            
        last_quarter = f"Q{last_quarter_num}"
        
        # Quarter date ranges for reference
        quarter_ranges = {
            "Q1": ("January-March", "01-01", "03-31"),
            "Q2": ("April-June", "04-01", "06-30"), 
            "Q3": ("July-September", "07-01", "09-30"),
            "Q4": ("October-December", "10-01", "12-31")
        }
        
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "current_quarter": current_quarter,
            "current_quarter_year": current_year,
            "current_quarter_range": quarter_ranges[current_quarter][0],
            "last_quarter": last_quarter,
            "last_quarter_year": last_quarter_year,
            "last_quarter_range": quarter_ranges[last_quarter][0],
            "last_quarter_start": f"{last_quarter_year}-{quarter_ranges[last_quarter][1]}",
            "last_quarter_end": f"{last_quarter_year}-{quarter_ranges[last_quarter][2]}"
        }


def create_sql_gen_tool(
    tool_type: str = "vertex_ai",
    **kwargs
) -> SQLGenTool:
    """
    Factory function to create appropriate SQL generation tool.
    
    Args:
        tool_type: Type of tool ("vertex_ai" or "rule_based")
        **kwargs: Additional parameters for tool initialization
        
    Returns:
        Configured SQL generation tool instance
    """
    if tool_type == "vertex_ai":
        return VertexAISQLGenTool(**kwargs)
    elif tool_type == "rule_based":
        return RuleBasedSQLGenTool()
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")


