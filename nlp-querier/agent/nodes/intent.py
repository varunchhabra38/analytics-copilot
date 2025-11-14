"""
Intent detection node for the LangGraph Analytics Agent.

This node analyzes user input to detect ambiguities that require clarification
before proceeding with SQL generation and execution.
"""
from typing import Dict, Any, List
import logging
import re
from agent.state import AgentState

logger = logging.getLogger(__name__)


class IntentNode:
    """
    Node for detecting user intent and identifying ambiguities in natural language queries.
    
    Analyzes user input for common ambiguities like:
    - Multiple possible date/time columns
    - Unclear aggregation methods
    - Ambiguous entity references
    - Missing context for follow-up queries
    """
    
    def __init__(self):
        self.ambiguous_patterns = {
            'date_ambiguity': [
                r'\b(date|time|when|month|year|day)\b',
                r'\b(last|this|next)\s+(week|month|year|quarter)\b',
                r'\b(recent|latest|current)\b'
            ],
            'aggregation_ambiguity': [
                r'\b(total|sum|count|average|max|min|show|get)\b',
                r'\b(revenue|sales|profit|amount|value)\b'
            ],
            'entity_ambiguity': [
                r'\b(region|country|area|location)\b',
                r'\b(product|item|category|type)\b',
                r'\b(customer|client|user)\b'
            ],
            'reference_ambiguity': [
                r'\b(it|this|that|they|them)\b',
                r'\b(previous|last|above|earlier)\b'
            ]
        }
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Process user input to detect intent and potential ambiguities using LLM.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent analysis results
        """
        try:
            new_state = state.copy()
            question = new_state.get('question', '')
            history = new_state.get('history', [])
            
            logger.info(f"Intent detection for question: {question}")
            
            # Use LLM for intelligent intent detection instead of regex patterns
            ambiguities = self._llm_detect_ambiguities(question, history)
            
            if ambiguities:
                new_state['clarification_needed'] = True
                new_state['clarification_question'] = ambiguities['question']
                logger.info(f"LLM detected ambiguities: {ambiguities['reason']}")
            else:
                logger.info("LLM determined query is clear, proceeding")
                
            new_state['completed_nodes'] = new_state['completed_nodes'] + ['intent']
            return new_state
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            # Fail open - proceed without clarification if intent detection fails
            new_state = state.copy()
            new_state['clarification_needed'] = False
            new_state['completed_nodes'] = new_state['completed_nodes'] + ['intent']
            return new_state
    
    def _llm_detect_ambiguities(self, question: str, history: List[Dict[str, str]]) -> Dict[str, str] | None:
        """
        Use LLM (Vertex AI) to intelligently detect if a question is ambiguous.
        
        Args:
            question: User's natural language question
            history: Conversation history for context
            
        Returns:
            Dictionary with clarification question if ambiguous, None if clear
        """
        try:
            from agent.tools.sql_gen_tool import create_sql_gen_tool
            from config import get_config
            
            config = get_config()
            
            # Create a simple prompt for intent analysis
            context = ""
            if len(history) > 1:
                recent_history = history[-3:]  # Last 3 messages for context
                context = "Recent conversation:\n" + "\n".join([
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
                    for msg in recent_history
                ]) + "\n\n"
            
            intent_prompt = f"""{context}User question: "{question}"

CRITICAL: This system should be VERY PERMISSIVE and almost always return "clear" unless the question is genuinely impossible to understand.

Analyze this question for a business analytics database query. Determine if it's:

1. CLEAR - Can be answered directly with SQL (return "clear") - DEFAULT ASSUMPTION
2. AMBIGUOUS - Needs clarification ONLY if genuinely impossible to interpret

ALWAYS CLEAR PATTERNS (never mark as ambiguous):
- ANY request with specific entities: "biggest customer", "top sales", "all products", "total revenue"
- ANY geographic qualifiers: "in america", "in USA", "in europe", "by region"
- ANY aggregation with clear intent: "highest", "lowest", "biggest", "smallest", "total", "count", "sum"
- ANY follow-up patterns: "in america", "for USA", "filter by...", "only show...", "just the ones..."
- ANY data display requests: "show all", "list", "display", "get"

ONLY MARK AS AMBIGUOUS IF:
- The question is literally just a single word like "data" or "help"
- The question makes no sense grammatically
- The question has NO actionable intent whatsoever

EXAMPLES OF CLEAR (not ambiguous):
- "biggest customer" → CLEAR (find customer with highest metric)
- "customers in america" → CLEAR (filter customers by region)
- "total sales" → CLEAR (sum sales amount)
- "show all products" → CLEAR (SELECT * FROM products)
- "in america" → CLEAR (follow-up filter)
- "top 5 sales" → CLEAR (ORDER BY sales DESC LIMIT 5)

EXAMPLES OF TRULY AMBIGUOUS (rare):
- "what" → AMBIGUOUS (no actionable intent)
- "help me" → AMBIGUOUS (no specific data request)

DEFAULT RESPONSE: {{"status": "clear"}}
ONLY use ambiguous if truly necessary.

Respond with JSON:
{{"status": "clear"}} or {{"status": "ambiguous", "reason": "brief reason", "question": "specific clarification needed"}}"""

            # Use Vertex AI for intent analysis
            sql_tool = create_sql_gen_tool(
                "vertex_ai",
                project_id=config["ai"]["project_id"],
                model_name=config["ai"]["model_name"],
                temperature=0.1
            )
            
            # Get LLM response
            response = sql_tool._get_client().generate_content(
                intent_prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 200}
            )
            
            result_text = response.text.strip()
            
            # Parse JSON response
            import json
            if '{' in result_text and '}' in result_text:
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                json_str = result_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                if result.get("status") == "ambiguous":
                    return {
                        "reason": result.get("reason", "Query needs clarification"),
                        "question": result.get("question", "Could you provide more details?")
                    }
            
            # Default to clear if we can't parse or if status is "clear"
            return None
            
        except Exception as e:
            logger.warning(f"LLM intent detection failed, proceeding: {e}")
            # Fail open - if LLM intent detection fails, proceed with query
            return None
    
    def _detect_ambiguities(self, question: str, history: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """
        Detect specific types of ambiguities in the user question.
        
        Args:
            question: User's natural language question
            history: Conversation history for context
            
        Returns:
            Dictionary mapping ambiguity types to detected instances
        """
        ambiguities = {}
        question_lower = question.lower()
        
        # First check if this is clearly a raw data request (should NOT trigger clarification)
        raw_data_patterns = [
            r'\b(all|entire|complete|full)\b.*\b(table|records|data|rows)\b',
            r'\b(show|display|list|get)\b.*\b(all|entire|complete|full)\b',
            r'\bselect\s*\*\b',
            r'\bselect\s+.+\s+from\b',
            r'\b(view|see|display)\b.*\b(table|records|data)\b'
        ]
        
        is_raw_data_request = any(re.search(pattern, question_lower) for pattern in raw_data_patterns)
        
        if is_raw_data_request:
            logger.info("Detected raw data request, skipping ambiguity detection")
            return {}
        
        # Check for specific aggregation terms that truly indicate ambiguity
        # But first check for EXPLICIT aggregation requests that are NOT ambiguous
        explicit_aggregation_patterns = [
            r'\b(total\s+sum|sum\s+of|total\s+amount|total\s+revenue)\b',
            r'\b(count\s+all|count\s+of|number\s+of\s+records)\b',
            r'\b(average\s+of|mean\s+of|avg\s+of)\b',
            r'\b(max|maximum|min|minimum)\s+of\b',
            r'\b(sum\s+all|total\s+all)\b'
        ]
        
        is_explicit_aggregation = any(re.search(pattern, question_lower) for pattern in explicit_aggregation_patterns)
        
        if is_explicit_aggregation:
            logger.info("Detected explicit aggregation request, skipping ambiguity detection")
            return {}
        
        true_aggregation_patterns = [
            r'\b(total|sum|average|mean|count)\b(?!\s+(table|records|data|rows|of|all))',
            r'\b(revenue|profit|amount)\b.*\b(by|per|for)\b',
            r'\b(group\s+by|grouped\s+by)\b',
            r'\b(how\s+much|how\s+many)\b',
            r'\b(statistics|stats|metrics)\b'
        ]
        
        # Only flag aggregation ambiguity for truly ambiguous aggregation requests
        aggregation_matches = []
        for pattern in true_aggregation_patterns:
            if re.search(pattern, question_lower):
                aggregation_matches.append(pattern)
        
        if aggregation_matches:
            ambiguities['aggregation_ambiguity'] = aggregation_matches
        
        # Check other ambiguity types (but be more selective)
        if re.search(r'\b(last|this|next)\s+(week|month|year|quarter)\b', question_lower):
            ambiguities['date_ambiguity'] = ['time_period_ambiguous']
        
        # Special case: reference ambiguity only matters if there's no previous context
        reference_patterns = [r'\b(it|this|that|they|them)\b', r'\b(previous|last|above|earlier)\b']
        if len(history) <= 1:
            for pattern in reference_patterns:
                if re.search(pattern, question_lower):
                    if 'reference_ambiguity' not in ambiguities:
                        ambiguities['reference_ambiguity'] = []
                    ambiguities['reference_ambiguity'].append(pattern)
        
        return ambiguities
    
    def _generate_clarification_question(self, ambiguities: Dict[str, List[str]]) -> str:
        """
        Generate a context-aware clarification question based on detected ambiguities.
        
        Args:
            ambiguities: Dictionary of detected ambiguity types and patterns
            
        Returns:
            Specific clarification question to ask the user
        """
        if 'date_ambiguity' in ambiguities:
            return ("I notice you're asking about dates/times. Could you please specify:\n"
                   "- Which date range you're interested in?\n"
                   "- What time period should I use for grouping (daily, monthly, yearly)?")
        
        if 'aggregation_ambiguity' in ambiguities:
            return ("I see you want data aggregated. Could you clarify:\n"
                   "- Do you want totals, averages, counts, or another calculation?\n"
                   "- Should I group by specific dimensions?")
        
        if 'entity_ambiguity' in ambiguities:
            return ("Your query mentions entities that could be ambiguous. Please specify:\n"
                   "- Which specific regions, products, or categories?\n"
                   "- Should I include all or filter to specific values?")
        
        if 'follow_up_context' in ambiguities:
            return ("I see you're referring to previous results. Could you clarify:\n"
                   "- Which specific data from our previous analysis?\n"
                   "- How should I modify or filter that data?")
        
        # Generic fallback
        return ("I need some clarification to better understand your request. "
               "Could you provide more specific details about what you're looking for?")


def intent_node(state: AgentState) -> AgentState:
    """
    Node function for detecting user intent and identifying ambiguities.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with intent analysis
    """
    try:
        intent_processor = IntentNode()
        result = intent_processor(state)
        return result
        
    except Exception as e:
        logger.error(f"Intent detection error: {e}")
        new_state = state.copy()
        new_state['clarification_needed'] = False
        new_state['clarification_question'] = None
        return new_state


def detect_intent(user_input: str, state: AgentState) -> None:
    """
    Legacy function for backward compatibility.
    
    Args:
        user_input: The input provided by the user
        state: The current state of the agent
    """
    # Update state with new question
    state['question'] = user_input
    
    # Use the IntentNode class for processing
    intent_node = IntentNode()
    updated_state = intent_node(state)
    
    # Update the original state
    state.update(updated_state)