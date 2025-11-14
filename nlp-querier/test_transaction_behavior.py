#!/usr/bin/env python3
"""
Test Transaction Behavior Analysis Scenario.

Test Case: Q3. Transaction Behavior
- "What is the average transaction amount by channel for high-risk customers?"
- Follow-ups: 
  * "How does online transaction behavior differ from branch or ATM?"
  * "Which country shows the highest flagged transaction ratio?"
"""

import logging
import sys
import os
from datetime import datetime

# Setup logging to see detailed results
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'test_transaction_behavior_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_transaction_behavior_scenario():
    """Test the transaction behavior analysis scenario with detailed logging."""
    
    logger.info("🧪 TRANSACTION BEHAVIOR ANALYSIS TEST")
    logger.info("=" * 80)
    
    try:
        from agent.graph import run_agent_chat
        
        # Test queries
        queries = [
            "What is the average transaction amount by channel for high-risk customers?",
            "How does online transaction behavior differ from branch or ATM?", 
            "Which country shows the highest flagged transaction ratio?"
        ]
        
        conversation_history = []
        
        for i, query in enumerate(queries, 1):
            logger.info(f"\n🔍 TEST QUERY {i}: {query}")
            logger.info("-" * 60)
            
            try:
                # Run the agent
                result = run_agent_chat(query, conversation_history)
                
                logger.info("✅ QUERY COMPLETED SUCCESSFULLY")
                logger.info(f"📊 RESULTS SUMMARY:")
                logger.info(f"  - SQL Generated: {'✅' if result.get('sql') else '❌'}")
                logger.info(f"  - Execution Success: {'✅' if result.get('execution_result') else '❌'}")
                logger.info(f"  - Summary Created: {'✅' if result.get('summary') else '❌'}")
                
                if result.get('sql'):
                    logger.info(f"🔧 GENERATED SQL:")
                    sql_lines = result['sql'].strip().split('\n')
                    for line_num, line in enumerate(sql_lines, 1):
                        logger.info(f"    {line_num:2d}: {line}")
                
                if result.get('summary'):
                    logger.info(f"📝 SUMMARY:")
                    logger.info(f"    {result['summary']}")
                
                # Update conversation history for context
                conversation_history = result.get('history', [])
                
                logger.info(f"💬 Conversation History Length: {len(conversation_history)}")
                
            except Exception as e:
                logger.error(f"❌ QUERY {i} FAILED: {e}")
                logger.error(f"   Error Type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
        
        logger.info("\n🏁 TRANSACTION BEHAVIOR TEST COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ TEST SETUP FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    test_transaction_behavior_scenario()