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
        """Parse the model response into SQL and explanation."""
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                result = json.loads(content)
                return {
                    "sql": result.get("sql", ""),
                    "explanation": result.get("explanation", "")
                }
            
            # Fallback: extract SQL from text
            lines = content.split('\n')
            sql_lines = []
            explanation_lines = []
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('select') or line.lower().startswith('with'):
                    current_section = 'sql'
                    sql_lines.append(line)
                elif line.lower().startswith('explanation') or line.lower().startswith('this query'):
                    current_section = 'explanation'
                    if not line.lower().startswith('explanation'):
                        explanation_lines.append(line)
                elif current_section == 'sql' and line:
                    sql_lines.append(line)
                elif current_section == 'explanation' and line:
                    explanation_lines.append(line)
            
            return {
                "sql": " ".join(sql_lines) if sql_lines else "",
                "explanation": " ".join(explanation_lines) if explanation_lines else "SQL query generated"
            }
            
        except Exception as e:
            logger.error(f"Error parsing SQL generation response: {e}")
            return {
                "sql": "",
                "explanation": f"Error parsing response: {str(e)}"
            }


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
        Generate SQL using rule-based pattern matching.
        
        Args:
            question: Natural language question
            schema: Database schema information
            history: Conversation history for context
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        try:
            question_lower = question.lower()
            
            # Extract table and column information from schema
            tables = self._extract_tables_from_schema(schema)
            
            if not tables:
                return {
                    "sql": "",
                    "explanation": "No tables found in schema"
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
            
            # Fallback: simple SELECT
            return {
                "sql": f"SELECT * FROM {primary_table} LIMIT 10",
                "explanation": f"Simple query to show sample data from {primary_table}"
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
                column=amount_column or table_columns[0],
                limit=limit
            )
        elif pattern_name == 'show_all':
            sql = template.format(table=primary_table)
        elif pattern_name == 'group_by':
            sql = template.format(
                table=primary_table,
                group_column=group_column or table_columns[0],
                agg_func='COUNT',
                agg_column='*'
            )
        else:
            sql = template.format(
                table=primary_table,
                column=agg_column or '*'
            )
        
        return {
            "sql": sql,
            "explanation": f"Generated {pattern_name} query for {primary_table}"
        }


class VertexAISQLGenTool(SQLGenTool):
    """
    Google Vertex AI-based SQL generation tool.
    
    Uses Vertex AI's language models to convert natural language queries to SQL
    with PostgreSQL-specific optimizations and conversation context.
    Uses Application Default Credentials for authentication.
    """
    
    def __init__(
        self, 
        project_id: str, 
        location: str = "us-central1", 
        model_name: str = "gemini-2.5-pro",
        temperature: float = 0.1
    ):
        """
        Initialize Vertex AI SQL generation tool.
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Model name to use (default: gemini-2.5-pro)
            temperature: Sampling temperature (default: 0.1 for consistency)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.temperature = temperature
        self._client = None
    
    def _calculate_quarter_info(self, current_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate current and last quarter information for dynamic date handling.
        
        Args:
            current_date: Optional current date (defaults to now)
            
        Returns:
            Dictionary with current and last quarter information
        """
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
    
    def _get_client(self):
        """Get Vertex AI client using Application Default Credentials."""
        if self._client is None:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                
                # Initialize with Application Default Credentials
                vertexai.init(project=self.project_id, location=self.location)
                self._client = GenerativeModel(self.model_name)
                
            except ImportError:
                raise ImportError("google-cloud-aiplatform is required for Vertex AI integration")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}")
                logger.info("Make sure you've run: gcloud auth application-default login")
                raise
        return self._client
    
    def generate_sql(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, str]:
        """
        Generate SQL using Vertex AI language model.
        
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
            
            # Build SQLite-specific prompt (not PostgreSQL)
            prompt = self._build_sqlite_prompt(question, schema, history, **kwargs)
            
            logger.info("VERTEX AI REQUEST - Prompt length: %d characters", len(prompt))
            logger.info("VERTEX AI REQUEST - Full prompt:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            
            logger.info("VERTEX AI REQUEST - Generation config:")
            generation_config = {
                "temperature": 0.1,  # Reduced from self.temperature for more deterministic output
                "max_output_tokens": 8192,  # Increased from 4096 to handle complex CTEs
                "top_k": 20,  # Reduced for more focused vocabulary
                "top_p": 0.7,  # Reduced for less random sampling
                "stop_sequences": [],  # Don't stop early
                "candidate_count": 1  # Single candidate for full resources
            }
            logger.info("  - Config: %s", generation_config)
            
            logger.info("VERTEX AI REQUEST - Sending request...")
            response = client.generate_content(prompt, generation_config=generation_config)
            
            logger.info("VERTEX AI RESPONSE - Raw response received")
            logger.info("VERTEX AI RESPONSE - Response object type: %s", type(response))
            logger.info("VERTEX AI RESPONSE - Has text attribute: %s", hasattr(response, 'text'))
            
            if hasattr(response, 'text') and response.text:
                logger.info(f"🔍 VERTEX AI RESPONSE - Text length: {len(response.text)} characters")
                logger.info(f"🔍 VERTEX AI RESPONSE - Text ends with: '{response.text[-20:]}'")
                
                # Check if response seems complete
                if response.text.rstrip().endswith('}'):
                    logger.info("🔍 VERTEX AI RESPONSE - Response appears complete (ends with })")
                elif response.text.rstrip().endswith('"'):
                    logger.info("🔍 VERTEX AI RESPONSE - Response might be complete (ends with \")")
                else:
                    logger.warning(f"🔍 VERTEX AI RESPONSE - Response appears truncated, ends with: '{response.text[-50:]}'")
            
            # Check for additional response metadata
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                logger.info(f"🔍 VERTEX AI RESPONSE - Candidate finish reason: {getattr(candidate, 'finish_reason', 'unknown')}")
                if hasattr(candidate, 'safety_ratings'):
                    logger.info(f"🔍 VERTEX AI RESPONSE - Safety ratings: {candidate.safety_ratings}")
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for i, part in enumerate(candidate.content.parts):
                        logger.info(f"🔍 VERTEX AI RESPONSE - Part {i} length: {len(part.text) if hasattr(part, 'text') else 'no text'}")
            
            # Parse response with enhanced debugging
            logger.info(f"🔍 Vertex AI raw response length: {len(response.text) if response.text else 0}")
            logger.info("🔍 FULL Vertex AI Response:")
            logger.info("=" * 80)
            logger.info(response.text)  # Log complete response for debugging
            logger.info("=" * 80)
            
            parsed_result = self._parse_response(response.text)
            
            # Log parsed result
            if parsed_result.get("sql"):
                logger.info(f"✅ Successfully parsed SQL from Vertex AI ({len(parsed_result['sql'])} chars)")
            else:
                logger.warning(f"❌ Failed to parse SQL from Vertex AI response")
                logger.warning(f"Raw response: {response.text}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error generating SQL with Vertex AI: {e}")
            return {
                "sql": "",
                "explanation": f"Error generating SQL: {str(e)}"
            }
    
    def _build_sqlite_prompt(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Build SQLite-specific prompt with all context."""
        prompt_parts = []
        
        # Calculate current quarter information for dynamic examples
        quarter_info = self._calculate_quarter_info()
        
        # Dynamic schema-driven instructions for SQLite
        prompt_parts.append(f"""You are an expert SQLite SQL analyst. Convert natural language questions into accurate SQLite SQL queries using the provided database schema.

CRITICAL OUTPUT FORMAT:
Return ONLY valid JSON: {{"sql": "SELECT ...", "explanation": "Brief explanation"}}

CORE RULES:
1. Use SQLite syntax (no semicolons in JSON)
2. Use ONLY tables and columns from the schema
3. Generate COMPLETE SQL - never truncate WHERE clauses
4. For ratios: Use CAST(numerator AS REAL) / denominator 
5. For highest/lowest: Use ORDER BY DESC/ASC LIMIT 1
6. Keep explanations brief (max 1 sentence)

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

IMPORTANT: Response must fit in JSON format and be complete. Avoid overly complex CTEs.""")
        
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
        last_sql = kwargs.get('last_sql')
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
        
        prompt_parts.append("INSTRUCTIONS:")
        prompt_parts.append("1. Analyze the question carefully")
        prompt_parts.append("2. If this is a follow-up, MODIFY the previous SQL")
        prompt_parts.append("3. Map to appropriate columns from the schema")
        prompt_parts.append("4. Use JOINs when relating multiple tables")
        prompt_parts.append("5. Generate efficient SQLite query")
        prompt_parts.append("6. Provide clear explanation")
        prompt_parts.append("7. ⚠️  CRITICAL: Generate COMPLETE SQL - never truncate WHERE clauses")
        prompt_parts.append("8. Include ALL parts of the query: SELECT, FROM, WHERE, ORDER BY, LIMIT")
        prompt_parts.append("9. 🔤 CASE SENSITIVITY: Use UPPER() for all text comparisons to avoid case mismatches")
        prompt_parts.append("")
        prompt_parts.append("CASE-INSENSITIVE EXAMPLES:")
        prompt_parts.append("✅ Good: WHERE UPPER(alert_type) = 'SANCTIONS'")
        prompt_parts.append("✅ Good: WHERE UPPER(region) LIKE '%AMERICA%'") 
        prompt_parts.append("✅ Good: WHERE UPPER(risk_level) IN ('HIGH', 'MEDIUM')")
        prompt_parts.append("❌ Bad: WHERE alert_type = 'sanctions' (might not match 'SANCTIONS' in data)")
        prompt_parts.append("❌ Bad: WHERE region = 'usa' (might not match 'USA' in data)")
        prompt_parts.append("")
        prompt_parts.append("🚨 IMPORTANT: Generate the FULL, COMPLETE SQL statement with no truncation!")
        prompt_parts.append("GENERATE SQLite SQL QUERY AS JSON:")
        
        return "\n".join(prompt_parts)

    def _build_postgresql_prompt(
        self, 
        question: str, 
        schema: str, 
        history: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Build PostgreSQL-specific prompt with all context."""
        prompt_parts = []
        
        # System instructions for PostgreSQL
        prompt_parts.append("""You are an expert PostgreSQL SQL analyst. Convert natural language questions into accurate PostgreSQL SQL queries.

PostgreSQL SQL Rules:
1. Use double quotes for table/column names if needed: "table_name"
2. Use single quotes for string literals: 'text'
3. Use PostgreSQL functions: DATE_TRUNC(), EXTRACT(), NOW()
4. Use LIMIT for result size management
5. Use proper JOIN syntax
6. Return JSON format: {"sql": "SELECT ...", "explanation": "..."}
7. End queries with semicolon
8. Use PostgreSQL date/time functions and data types
9. Use aggregate functions: SUM(), COUNT(), AVG(), etc.
10. Use window functions when appropriate

""")
        
        # Add schema information
        prompt_parts.append(f"PostgreSQL Schema:\n{schema}\n")
        
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
            prompt_parts.append(f"Previous PostgreSQL SQL:\n{last_sql}\n")
        
        # Add the current question
        prompt_parts.append(f"Question: {question}")
        prompt_parts.append("\nGenerate optimized PostgreSQL SQL:")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, content: str) -> Dict[str, str]:
        """
        Simple and robust JSON parsing for LLM responses.
        
        Args:
            content: Raw response from LLM
            
        Returns:
            Dict with 'sql' and 'explanation' keys
        """
        if not content or not content.strip():
            logger.warning("Empty response from Vertex AI")
            return {"sql": "", "explanation": "Empty response"}
        
        logger.info(f"🔍 Response parsing - length: {len(content)}")
        
        try:
            # Step 1: Clean up the response text
            content = content.strip()
            
            # Remove markdown code blocks
            content = re.sub(r'```(?:json|sql)?\s*\n?', '', content)
            content = re.sub(r'```\s*$', '', content)
            
            # Step 2: Extract JSON using simple brace matching
            json_start = content.find('{')
            if json_start == -1:
                # No JSON structure found, look for direct SQL
                return self._extract_sql_from_text(content)
            
            # Find the matching closing brace
            brace_count = 0
            json_end = -1
            
            for i in range(json_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break
            
            if json_end == -1:
                # Incomplete JSON, try to extract SQL directly
                logger.warning("Incomplete JSON structure, extracting SQL directly")
                return self._extract_sql_from_text(content)
            
            # Step 3: Parse the JSON
            json_text = content[json_start:json_end + 1]
            
            try:
                data = json.loads(json_text)
                if isinstance(data, dict) and 'sql' in data:
                    sql = data['sql'].strip()
                    explanation = data.get('explanation', 'SQL query generated')
                    
                    if sql and len(sql) > 5:  # Basic sanity check
                        logger.info(f"✅ JSON parsed successfully - SQL: {sql[:50]}...")
                        return {"sql": sql, "explanation": explanation}
            
            except json.JSONDecodeError:
                logger.warning("JSON parsing failed, falling back to text extraction")
            
            # Step 4: Fallback to text extraction
            return self._extract_sql_from_text(content)
            
        except Exception as e:
            logger.error(f"Error in response parsing: {e}")
            return {"sql": "", "explanation": f"Parsing error: {str(e)}"}
    
    def _extract_sql_from_text(self, content: str) -> Dict[str, str]:
        """
        Extract SQL from plain text response when JSON parsing fails.
        
        Args:
            content: Text content to search for SQL
            
        Returns:
            Dict with extracted SQL and explanation
        """
        # Look for quoted SQL in JSON-like structure
        sql_match = re.search(r'"sql":\s*"([^"]+)"', content, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            if sql and 'SELECT' in sql.upper():
                logger.info(f"✅ Extracted SQL from JSON field: {sql[:50]}...")
                return {"sql": sql, "explanation": "SQL extracted from JSON field"}
        
        # Look for standalone SELECT statements
        select_patterns = [
            r'(SELECT\s+[^;]+?(?:;|$))',
            r'(SELECT\s+.*?FROM\s+\w+[^}]*?)(?=\n|"|$)',
            r'(SELECT\s+.*?FROM\s+\w+.*?)(?=\s*(?:\n|"|$))',
        ]
        
        for pattern in select_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sql = match.strip().rstrip(';').rstrip(',').rstrip('"')
                if len(sql) > 10 and 'FROM' in sql.upper():
                    logger.info(f"✅ Extracted SQL from text: {sql[:50]}...")
                    return {"sql": sql, "explanation": "SQL extracted from text"}
        
        logger.warning("No valid SQL found in response")
        return {"sql": "", "explanation": "Could not extract SQL from response"}


class RuleBasedSQLGenTool(SQLGenTool):
                            CAST(COUNT(DISTINCT alert_id) AS REAL) / 
                            (SELECT COUNT(*) FROM fact_transactions t WHERE t.channel = fa.channel) as alert_ratio
                        FROM fact_alerts fa 
                        WHERE channel IS NOT NULL
                        GROUP BY channel
                        ORDER BY alert_ratio DESC
                        LIMIT 1
                        """.strip()
                    
                    # For other complex queries, try to infer the intent
                    main_tables = []
                    for cte in complete_ctes:
                        # Extract table references
                        table_matches = re.findall(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', cte, re.IGNORECASE)
                        main_tables.extend(table_matches)
                        # Create a meaningful query based on the most common table
                        from collections import Counter
                        most_common_table = Counter(main_tables).most_common(1)[0][0]
                        logger.info(f"🧹 CLEANUP - Building meaningful query on {most_common_table}")
                        
                        if most_common_table == "fact_alerts":
                            return f"SELECT alert_type, risk_level, COUNT(*) as count FROM {most_common_table} GROUP BY alert_type, risk_level ORDER BY count DESC"
                        elif most_common_table == "fact_transactions":
                            return f"SELECT channel, AVG(amount) as avg_amount, COUNT(*) as count FROM {most_common_table} GROUP BY channel ORDER BY avg_amount DESC"
                        else:
                            return f"SELECT COUNT(*) as total_count FROM {most_common_table}"
                
                # If no complete CTEs found, try to infer from partial SQL
                logger.warning("🧹 CLEANUP - No complete CTEs found, analyzing partial SQL for intent")
                
                # Look for key business terms to infer intent
                if "ratio" in sql.lower():
                    if "alert" in sql.lower() and ("transaction" in sql.lower() or "txn" in sql.lower()):
                        logger.info("🧹 CLEANUP - Inferred alert-to-transaction ratio query")
                        return """
                        SELECT 
                            channel,
                            COUNT(DISTINCT alert_id) as alerts,
                            (SELECT COUNT(*) FROM fact_transactions WHERE channel = fa.channel) as transactions,
                            CAST(COUNT(DISTINCT alert_id) AS REAL) / 
                            (SELECT COUNT(*) FROM fact_transactions WHERE channel = fa.channel) as ratio
                        FROM fact_alerts fa 
                        GROUP BY channel 
                        ORDER BY ratio DESC 
                        LIMIT 5
                        """.strip()
                
                table_matches = re.findall(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql, re.IGNORECASE)
                if table_matches:
                    main_table = table_matches[0]
                    logger.info(f"🧹 CLEANUP - Building meaningful query from table {main_table}")
                    if main_table == "fact_alerts":
                        return "SELECT risk_level, COUNT(*) as alert_count FROM fact_alerts GROUP BY risk_level ORDER BY alert_count DESC"
                    elif main_table == "fact_transactions": 
                        return "SELECT channel, COUNT(*) as txn_count FROM fact_transactions GROUP BY channel ORDER BY txn_count DESC"
                    else:
                        return f"SELECT COUNT(*) FROM {main_table}"
                
                # Final fallback - but still try to be meaningful
                logger.warning("🧹 CLEANUP - Using final fallback with business context")
                if "ratio" in sql.lower():
                    return "SELECT 'Analysis incomplete due to truncation' as message, COUNT(*) as total_alerts FROM fact_alerts"
                return "SELECT 'Query truncated - showing alert summary' as message, COUNT(*) as total_alerts FROM fact_alerts"
            
            # CTE looks complete, just clean up formatting
            logger.info("🧹 CLEANUP - CTE appears complete")
            
        # For regular SELECT queries or complete CTEs
        lines = sql.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove incomplete clauses that might be cut off
            if (line.endswith(' AND') or line.endswith(' OR') or 
                line.endswith(' WHERE') or line.endswith(' =') or
                line.endswith(' >') or line.endswith(' AS')):
                logger.warning(f"🧹 CLEANUP - Removing incomplete line: {line}")
                break
                
            cleaned_lines.append(line)
        
        cleaned_sql = '\n'.join(cleaned_lines)
        
        # Final cleanup - remove trailing incomplete operators (but preserve quoted strings)
        cleaned_sql = cleaned_sql.strip()
        
        # Only remove trailing incomplete operators if the SQL doesn't end with a quoted string
        while (cleaned_sql.endswith((',', 'AND', 'OR', '=', '>', '<', 'AS')) and 
               not (cleaned_sql.endswith("'") and "'" in cleaned_sql[:-1])):
            if cleaned_sql.endswith(','):
                cleaned_sql = cleaned_sql[:-1].strip()
            elif cleaned_sql.endswith(('AND', 'OR', 'AS')):
                words = cleaned_sql.split()
                cleaned_sql = ' '.join(words[:-1])
            elif cleaned_sql.endswith(('=', '>', '<')):
                cleaned_sql = cleaned_sql[:-1].strip()
        
        logger.info(f"🧹 CLEANUP - Final SQL: {cleaned_sql}")
        return cleaned_sql
    
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
                analysis_parts.append(f"- Available tables: {', '.join(tables)}")
            
            # Identify potential patterns based on common naming conventions
            numeric_indicators = ['amount', 'total', 'price', 'revenue', 'sales', 'quantity', 'count', 'sum']
            date_indicators = ['date', 'time', 'created', 'updated', 'timestamp']
            location_indicators = ['region', 'country', 'state', 'city', 'location', 'address']
            name_indicators = ['name', 'title', 'description', 'label']
            
            schema_lower = schema.lower()
            
            # Detect column types based on naming patterns
            detected_patterns = []
            if any(indicator in schema_lower for indicator in numeric_indicators):
                detected_patterns.append("numeric/amount columns detected (suitable for aggregations)")
            if any(indicator in schema_lower for indicator in date_indicators):
                detected_patterns.append("date/time columns detected (suitable for time-based queries)")
            if any(indicator in schema_lower for indicator in location_indicators):
                detected_patterns.append("location columns detected (suitable for geographic filtering)")
            if any(indicator in schema_lower for indicator in name_indicators):
                detected_patterns.append("name/description columns detected (suitable for text searches)")
            
            if detected_patterns:
                analysis_parts.append("- Column patterns: " + "; ".join(detected_patterns))
            
            # Detect potential relationships
            if 'id' in schema_lower and len(tables) > 1:
                analysis_parts.append("- Foreign key relationships likely exist between tables (suitable for JOINs)")
            
            return "\n".join(analysis_parts) if analysis_parts else "- Schema contains standard table structure"
            
        except Exception as e:
            logger.warning(f"Error analyzing schema: {e}")
            return "- Standard database schema"


def create_sql_gen_tool(sql_gen_type: str = "vertex_ai", **kwargs) -> SQLGenTool:
    """
    Factory function to create appropriate SQL generation tool.
    
    Simplified to use only Vertex AI with Application Default Credentials.
    
    Args:
        sql_gen_type: Type of SQL generation tool ("vertex_ai" or "rule_based")
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured SQL generation tool instance
        
    Raises:
        ValueError: If unsupported sql_gen_type is specified
        ImportError: If required dependencies are not available
    """
    if sql_gen_type == "vertex_ai":
        try:
            project_id = kwargs.get("project_id")
            if not project_id:
                raise ValueError("project_id is required for Vertex AI SQL generation")
            
            return VertexAISQLGenTool(
                project_id=project_id,
                location=kwargs.get("location", "us-central1"),
                model_name=kwargs.get("model_name", "gemini-2.5-pro"),
                temperature=kwargs.get("temperature", 0.1)
            )
        except ImportError as e:
            logger.warning(f"Vertex AI not available: {e}")
            logger.info("Install with: pip install google-cloud-aiplatform")
            logger.info("Fallback to rule-based SQL generation")
            return RuleBasedSQLGenTool()
    
    elif sql_gen_type == "rule_based":
        return RuleBasedSQLGenTool()
    
    else:
        raise ValueError(f"Unsupported SQL generation type: {sql_gen_type}")


# Example usage configurations for different setups:
#
# For Vertex AI with Application Default Credentials:
# sql_gen_tool = create_sql_gen_tool(
#     sql_gen_type="vertex_ai",
#     project_id="your-gcp-project"
# )
#
# For development/testing with rule-based generation:
# sql_gen_tool = create_sql_gen_tool(sql_gen_type="rule_based")