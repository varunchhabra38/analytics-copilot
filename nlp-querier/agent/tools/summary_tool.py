from typing import List, Dict, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class SummaryTool:
    """
    Enhanced summary tool with intelligent analysis capabilities.
    
    Provides both simple conversation summaries and intelligent data summaries
    with business context awareness.
    """
    
    def generate_summary(self, history: List[Dict[str, str]]) -> str:
        """
        Generate an intelligent summary of the conversation history.

        Args:
            history (List[Dict[str, str]]): The conversation history, where each entry is a dictionary
                                              containing 'role' and 'content'.

        Returns:
            str: An intelligent summary of the conversation.
        """
        if not history:
            return "No conversation history available."
        
        # Enhanced conversation analysis
        user_questions = [entry['content'] for entry in history if entry['role'] == 'user']
        assistant_responses = [entry['content'] for entry in history if entry['role'] == 'assistant']
        
        # Detect conversation patterns
        conversation_insights = self._analyze_conversation_patterns(user_questions, assistant_responses)
        
        # Build intelligent summary
        summary_parts = []
        
        if len(user_questions) == 1:
            summary_parts.append(f"Single query session: '{user_questions[0]}'")
        else:
            summary_parts.append(f"Multi-turn conversation with {len(user_questions)} user queries")
            
        # Add pattern insights
        if conversation_insights['domain']:
            summary_parts.append(f"Focus area: {conversation_insights['domain']}")
            
        if conversation_insights['query_progression']:
            summary_parts.append(conversation_insights['query_progression'])
        
        return ". ".join(summary_parts) + "."
    
    def generate_data_summary(self, data: Any, context: Dict[str, Any] = None) -> str:
        """
        Generate an intelligent summary of data results.
        
        Args:
            data: Data to summarize (DataFrame, list, dict, etc.)
            context: Additional context (question, metadata, etc.)
            
        Returns:
            str: Intelligent data summary
        """
        try:
            if data is None:
                return "No data available for analysis."
            
            # Convert to DataFrame if possible for consistent analysis
            df = self._normalize_data(data)
            if df is None:
                return f"Data summary: {type(data).__name__} with {len(data) if hasattr(data, '__len__') else 'unknown'} items."
            
            # Analyze data characteristics
            insights = self._analyze_data_insights(df, context or {})
            
            # Generate business-friendly summary
            return self._build_data_summary(insights, context or {})
            
        except Exception as e:
            logger.warning(f"Error generating data summary: {e}")
            return "Data analysis completed with basic summary."
    
    def _analyze_conversation_patterns(self, questions: List[str], responses: List[str]) -> Dict[str, Any]:
        """
        Analyze conversation patterns to understand user intent and progression.
        """
        insights = {
            'domain': None,
            'query_progression': None,
            'complexity': 'simple'
        }
        
        if not questions:
            return insights
        
        # Combine all text for domain detection
        all_text = " ".join(questions + responses).lower()
        
        # Detect business domain
        domain_keywords = {
            'financial compliance': ['alert', 'risk', 'sanctions', 'aml', 'compliance', 'suspicious'],
            'sales analytics': ['sales', 'revenue', 'customer', 'product', 'order', 'purchase'],
            'operational analytics': ['performance', 'efficiency', 'process', 'operation', 'metrics'],
            'data exploration': ['show', 'list', 'display', 'what', 'how many', 'count']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                insights['domain'] = domain
                break
        
        # Analyze query progression
        if len(questions) > 1:
            progression_patterns = []
            
            # Check for drill-down pattern
            if any(word in questions[-1].lower() for word in ['filter', 'where', 'only', 'specific']):
                progression_patterns.append("drill-down analysis")
            
            # Check for comparison pattern
            if any(word in questions[-1].lower() for word in ['compare', 'vs', 'versus', 'difference']):
                progression_patterns.append("comparative analysis")
            
            # Check for trend analysis
            if any(word in questions[-1].lower() for word in ['trend', 'over time', 'historical', 'change']):
                progression_patterns.append("trend analysis")
            
            if progression_patterns:
                insights['query_progression'] = f"Evolved to {', '.join(progression_patterns)}"
            
            insights['complexity'] = 'complex' if len(questions) > 3 else 'moderate'
        
        return insights
    
    def _normalize_data(self, data: Any) -> pd.DataFrame:
        """
        Normalize various data types to DataFrame for consistent analysis.
        """
        try:
            if isinstance(data, pd.DataFrame):
                return data
            elif isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    return pd.DataFrame(data)
                elif len(data) > 0:
                    return pd.DataFrame({'value': data})
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                return None
        except Exception:
            return None
    
    def _analyze_data_insights(self, df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze DataFrame to extract key insights.
        """
        insights = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'numeric_columns': [],
            'categorical_columns': [],
            'key_stats': {},
            'notable_patterns': [],
            'data_quality': 'good'
        }
        
        if len(df) == 0:
            insights['notable_patterns'].append("No data found")
            return insights
        
        # Analyze column types and content
        import numpy as np
        
        for col in df.columns:
            if df[col].dtype in [np.int64, np.float64, int, float]:
                insights['numeric_columns'].append(col)
                # Calculate key statistics
                insights['key_stats'][col] = {
                    'sum': float(df[col].sum()) if not df[col].isna().all() else 0,
                    'mean': float(df[col].mean()) if not df[col].isna().all() else 0,
                    'min': float(df[col].min()) if not df[col].isna().all() else 0,
                    'max': float(df[col].max()) if not df[col].isna().all() else 0
                }
            else:
                insights['categorical_columns'].append(col)
                # Analyze categorical patterns
                if len(df[col].unique()) < len(df) * 0.8:  # If less than 80% unique, it's categorical
                    top_values = df[col].value_counts().head(3)
                    insights['key_stats'][col] = top_values.to_dict()
        
        # Pattern detection
        if len(df) == 1:
            insights['notable_patterns'].append("Single record result")
        elif len(df) < 10:
            insights['notable_patterns'].append("Small result set - detailed analysis")
        elif len(df) > 1000:
            insights['notable_patterns'].append("Large dataset - statistical analysis")
        
        # Data quality assessment
        missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_percentage > 10:
            insights['data_quality'] = 'concerns'
            insights['notable_patterns'].append(f"{missing_percentage:.1f}% missing data")
        elif missing_percentage > 0:
            insights['notable_patterns'].append(f"{missing_percentage:.1f}% missing data")
        
        return insights
    
    def _build_data_summary(self, insights: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Build a business-friendly data summary from insights.
        """
        summary_parts = []
        
        # Start with basic data description
        row_count = insights['row_count']
        if row_count == 0:
            return "Query completed successfully but returned no matching records."
        elif row_count == 1:
            summary_parts.append("Found 1 matching record")
        else:
            summary_parts.append(f"Analysis of {row_count:,} records")
        
        # Add key insights from numeric data
        numeric_insights = []
        for col, stats in insights['key_stats'].items():
            if col in insights['numeric_columns'] and isinstance(stats, dict):
                if 'sum' in stats and stats['sum'] > 0:
                    numeric_insights.append(f"{col} totaling {stats['sum']:,.0f}")
                elif 'mean' in stats:
                    numeric_insights.append(f"average {col} of {stats['mean']:.2f}")
        
        if numeric_insights:
            summary_parts.append(f"shows {', '.join(numeric_insights[:2])}")
        
        # Add categorical insights
        categorical_insights = []
        for col, stats in insights['key_stats'].items():
            if col in insights['categorical_columns'] and isinstance(stats, dict):
                if stats:
                    top_value, top_count = next(iter(stats.items()))
                    if top_count > 1:
                        categorical_insights.append(f"most common {col}: {top_value} ({top_count} occurrences)")
        
        if categorical_insights and len(summary_parts) < 3:
            summary_parts.append(categorical_insights[0])
        
        # Add notable patterns
        if insights['notable_patterns'] and len(summary_parts) < 3:
            pattern = insights['notable_patterns'][0]
            if pattern not in ['Small result set - detailed analysis', 'Large dataset - statistical analysis']:
                summary_parts.append(pattern)
        
        # Combine into coherent summary
        if len(summary_parts) == 1:
            return summary_parts[0] + "."
        elif len(summary_parts) == 2:
            return f"{summary_parts[0]} {summary_parts[1]}."
        else:
            return f"{summary_parts[0]} {summary_parts[1]}, with {summary_parts[2]}."