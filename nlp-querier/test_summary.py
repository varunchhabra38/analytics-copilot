#!/usr/bin/env python3
"""
Test summary generation directly
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_summary_generation():
    """Test the summary generation function directly."""
    try:
        from agent.nodes.summarize import _create_query_summary_fallback
        
        question = "What is the average transaction amount by channel for high-risk customers?"
        sql_query = """SELECT T1.channel, AVG(T1.amount) AS average_amount 
                      FROM fact_transactions AS T1 
                      WHERE T1.customer_id IN (SELECT DISTINCT customer_id FROM fact_alerts WHERE UPPER(risk_level) = 'HIGH') 
                      GROUP BY T1.channel"""
        execution_success = True
        
        logger.info("🧪 Testing fallback summary generation...")
        summary = _create_query_summary_fallback(question, sql_query, execution_success)
        
        logger.info("✅ Fallback summary generated:")
        logger.info("-" * 60)
        logger.info(summary)
        logger.info("-" * 60)
        logger.info(f"Summary length: {len(summary)} characters")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_summary_generation()