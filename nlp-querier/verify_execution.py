#!/usr/bin/env python3
"""
Quick verification that the Analytics Agent is actually executing queries.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_graph import run_simple_agent_chat
import pandas as pd

def verify_execution():
    """Verify that SQL queries are actually being executed."""
    print("=== Analytics Agent Execution Verification ===\n")
    
    test_queries = [
        "show all sales records",
        "what is the total revenue?",
        "count all sales", 
        "show top 3 sales by amount"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Testing: '{query}'")
        print("-" * 50)
        
        try:
            result = run_simple_agent_chat(query, [])
            
            # Check SQL generation
            sql = result.get('sql', 'No SQL')
            print(f"   Generated SQL: {sql}")
            
            # Check execution
            if result.get('execution_error'):
                print(f"   ❌ Execution Error: {result['execution_error']}")
            else:
                exec_result = result.get('execution_result')
                if exec_result is not None and hasattr(exec_result, 'shape'):
                    print(f"   ✅ Executed Successfully: {exec_result.shape[0]} rows × {exec_result.shape[1]} columns")
                    
                    # Show sample data for verification
                    if not exec_result.empty:
                        if len(exec_result) <= 3:
                            print(f"   📊 Results:")
                            for _, row in exec_result.iterrows():
                                print(f"      {dict(row)}")
                        else:
                            print(f"   📊 Sample Result: {dict(exec_result.iloc[0])}")
                            if exec_result.select_dtypes(include=['number']).shape[1] > 0:
                                numeric_data = exec_result.select_dtypes(include=['number'])
                                print(f"   📈 Numeric Summary: {dict(numeric_data.sum())}")
                else:
                    print(f"   ⚠️  No execution result returned")
                    
            print(f"   📝 Summary: {result.get('summary', 'No summary')[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print()

if __name__ == "__main__":
    verify_execution()