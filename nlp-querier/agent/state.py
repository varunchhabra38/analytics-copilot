"""
Agent state management for the LangGraph Analytics Agent.

This module defines the AgentState TypedDict that holds all conversation context,
processing state, and results throughout the analytics workflow.
"""
from typing import TypedDict, Optional, List, Dict, Any
import pandas as pd


class AgentState(TypedDict):
    """
    State container for the analytics agent workflow.
    
    Maintains conversation history, processing state, and results across
    all nodes in the LangGraph workflow. All updates should be immutable.
    """
    # User input and conversation context
    question: str
    history: List[Dict[str, str]]  # [{role: "user"|"assistant", content: str}]
    
    # Schema and SQL processing
    schema: Optional[str]
    generated_sql: Optional[str]
    validated_sql: Optional[str]
    last_sql: Optional[str]  # For follow-up queries
    
    # Execution results
    execution_result: Optional[pd.DataFrame]
    execution_error: Optional[str]
    
    # Security and privacy
    pii_findings: Optional[Dict[str, List[Dict[str, Any]]]]  # PII detection results
    
    # Output generation
    visualization_path: Optional[str]
    summary: Optional[str]
    business_interpretation: Optional[str]  # LLM-generated business insights
    
    # Clarification handling
    clarification_needed: bool
    clarification_question: Optional[str]
    user_clarification_response: Optional[str]
    
    # Retry and error handling
    retry_count: int
    max_retries: int
    
    # Node tracking
    current_node: Optional[str]
    completed_nodes: List[str]
    
    operation_not_permitted: bool
    operation_feedback: Optional[str]