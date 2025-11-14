"""
Clarification node for the LangGraph Analytics Agent.

This node handles ambiguous user queries by generating context-aware clarification
questions and managing the wait-for-user workflow pattern in LangGraph.
"""
from typing import Dict, Any
import logging
from agent.state import AgentState

logger = logging.getLogger(__name__)


class ClarificationNode:
    """
    Node for handling user clarification in the analytics workflow.
    
    This node generates context-aware clarification questions when ambiguities
    are detected and manages the LangGraph "wait for user" pattern.
    """
    
    def __init__(self):
        """Initialize the clarification node."""
        pass
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Process clarification request and generate appropriate questions.
        
        Args:
            state: Current agent state containing clarification requirements
            
        Returns:
            Updated state with clarification question and wait status
        """
        logger.info("Processing clarification request")
        
        # Create new state to maintain immutability
        new_state = state.copy()
        new_state['current_node'] = 'clarification'
        
        # If user has already provided clarification, process it
        if state.get("user_clarification_response"):
            return self._process_user_response(new_state)
        
        # Generate clarification question if needed
        if state.get("clarification_needed") and not state.get("clarification_question"):
            new_state['clarification_question'] = self._generate_clarification_question(state)
        
        # Add clarification question to conversation history
        if new_state.get('clarification_question'):
            new_state['history'] = new_state['history'] + [
                {"role": "assistant", "content": new_state['clarification_question']}
            ]
        
        new_state['completed_nodes'] = new_state['completed_nodes'] + ['clarification']
        logger.info(f"Generated clarification question: {new_state.get('clarification_question')}")
        
        return new_state
    
    def _process_user_response(self, state: AgentState) -> AgentState:
        """
        Process user's clarification response and update the question.
        
        Args:
            state: State containing user clarification response
            
        Returns:
            Updated state with refined question
        """
        user_response = state.get("user_clarification_response", "")
        original_question = state.get("question", "")
        
        # Combine original question with clarification
        refined_question = f"{original_question} {user_response}".strip()
        
        # Update state
        new_state = state.copy()
        new_state['question'] = refined_question
        new_state['clarification_needed'] = False
        new_state['clarification_question'] = None
        
        # Add user response to history
        new_state['history'] = new_state['history'] + [
            {"role": "user", "content": user_response}
        ]
        
        logger.info(f"Processed user clarification: {user_response}")
        logger.info(f"Refined question: {refined_question}")
        
        return new_state
    
    def _generate_clarification_question(self, state: AgentState) -> str:
        """
        Generate a context-aware clarification question.
        
        This method analyzes the current state and conversation history to
        generate specific, helpful clarification questions.
        
        Args:
            state: Current agent state
            
        Returns:
            Specific clarification question string
        """
        question = state.get("question", "").lower()
        history = state.get("history", [])
        
        # Check for specific types of ambiguity
        if self._has_date_ambiguity(question):
            return self._generate_date_clarification(question)
        
        if self._has_aggregation_ambiguity(question):
            return self._generate_aggregation_clarification(question)
        
        if self._has_entity_ambiguity(question):
            return self._generate_entity_clarification(question)
        
        if self._has_reference_ambiguity(question, history):
            return self._generate_reference_clarification(question, history)
        
        # Generic fallback
        return ("I need some clarification to better understand your request. "
               "Could you provide more specific details about:\n"
               "- The time period you're interested in\n"
               "- What type of calculation or grouping you want\n"
               "- Any specific filters or conditions?")
    
    def _has_date_ambiguity(self, question: str) -> bool:
        """Check if question has date/time ambiguity."""
        date_terms = ['date', 'time', 'when', 'month', 'year', 'day', 'recent', 'latest', 'last', 'this', 'current']
        return any(term in question for term in date_terms)
    
    def _has_aggregation_ambiguity(self, question: str) -> bool:
        """Check if question has aggregation ambiguity."""
        agg_terms = ['total', 'sum', 'count', 'average', 'max', 'min', 'revenue', 'sales', 'show', 'get']
        return any(term in question for term in agg_terms)
    
    def _has_entity_ambiguity(self, question: str) -> bool:
        """Check if question has entity reference ambiguity."""
        entity_terms = ['region', 'country', 'area', 'location', 'product', 'category', 'customer', 'client']
        return any(term in question for term in entity_terms)
    
    def _has_reference_ambiguity(self, question: str, history: list) -> bool:
        """Check if question has reference ambiguity."""
        ref_terms = ['it', 'this', 'that', 'they', 'them', 'previous', 'above', 'earlier']
        return len(history) > 1 and any(term in question for term in ref_terms)
    
    def _generate_date_clarification(self, question: str) -> str:
        """Generate date-specific clarification question."""
        return ("I notice you're asking about dates or time periods. Could you please specify:\n"
               "- What date range are you interested in? (e.g., 'last 6 months', '2023', 'Q1 2024')\n"
               "- How should the data be grouped? (daily, weekly, monthly, quarterly, yearly)\n"
               "- Are you looking for a specific time period or comparison?")
    
    def _generate_aggregation_clarification(self, question: str) -> str:
        """Generate aggregation-specific clarification question."""
        return ("I see you want data summarized. Could you clarify:\n"
               "- What calculation do you need? (sum, average, count, maximum, minimum)\n"
               "- How should I group the data? (by month, region, product, etc.)\n"
               "- Are there any filters or conditions to apply?")
    
    def _generate_entity_clarification(self, question: str) -> str:
        """Generate entity-specific clarification question."""
        return ("Your query mentions entities that could be interpreted different ways. Please specify:\n"
               "- Which specific regions, products, or categories are you interested in?\n"
               "- Should I include all available options or filter to specific values?\n"
               "- Are there any exclusions or special conditions?")
    
    def _generate_reference_clarification(self, question: str, history: list) -> str:
        """Generate reference-specific clarification question."""
        return ("I see you're referring to previous results or data. Could you clarify:\n"
               "- Which specific data from our previous analysis should I use?\n"
               "- How should I modify or filter that previous result?\n"
               "- What new dimension or calculation should I add?")


# Legacy function for backward compatibility
def clarification_node(state: AgentState) -> Dict[str, Any]:
    """
    Node function for handling user clarification.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with clarification handling
    """
    try:
        clarification_processor = ClarificationNode()
        result = clarification_processor(state)
        return result
        
    except Exception as e:
        logger.error(f"Clarification error: {e}")
        return {
            **state,
            "clarification_needed": False,
            "clarification_question": None
        }


def ask_for_clarification(state: AgentState) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with clarification question and updated state
    """
    clarification_processor = ClarificationNode()
    updated_state = clarification_processor(state)
    
    return {
        "clarification_question": updated_state.get('clarification_question'),
        "updated_state": updated_state
    }