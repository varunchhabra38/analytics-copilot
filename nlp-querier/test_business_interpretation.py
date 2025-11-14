#!/usr/bin/env python3

"""
Test script to debug business interpretation functionality.
This will help us identify whether the issue is in the tool or the UI display.
"""

import pandas as pd
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools.results_interpreter_tool import ResultsInterpreterTool

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

def test_business_interpretation():
    """Test the business interpretation tool with sample data."""
    
    # Create sample DataFrame
    sample_data = {
        'transaction_type': ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'DEPOSIT', 'WITHDRAWAL'],
        'amount': [1000.50, -250.75, -500.00, 2500.00, -100.25],
        'account_id': ['ACC001', 'ACC002', 'ACC001', 'ACC003', 'ACC002'],
        'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
    }
    df = pd.DataFrame(sample_data)
    
    print("📊 Sample Data:")
    print(df)
    print("\n" + "="*80 + "\n")
    
    # Initialize interpreter tool
    interpreter = ResultsInterpreterTool()
    
    # Test question and SQL
    question = "Show me transaction patterns by type"
    sql_query = "SELECT transaction_type, COUNT(*) as count, AVG(amount) as avg_amount FROM transactions GROUP BY transaction_type"
    
    # Get business interpretation
    print("🔍 Running business interpretation...")
    result = interpreter.interpret_results(
        question=question,
        sql_query=sql_query,
        execution_result=df,
        context="Financial transaction analysis for fraud detection"
    )
    
    print("\n📝 Business Interpretation Result:")
    print("="*80)
    print(result)
    print("="*80)
    
    # Check if result looks like JSON
    if result.strip().startswith('{') and result.strip().endswith('}'):
        print("\n❌ ISSUE DETECTED: Result looks like raw JSON!")
        print("This should be formatted markdown, not JSON.")
        
        # Try to parse the JSON manually
        try:
            import json
            parsed = json.loads(result)
            print(f"\n📋 JSON Content Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing also failed: {e}")
    else:
        print("\n✅ Result appears to be formatted text (not raw JSON)")
        
    print(f"\n📏 Result length: {len(result)} characters")
    print(f"🔤 Result type: {type(result)}")

if __name__ == "__main__":
    test_business_interpretation()