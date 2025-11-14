#!/usr/bin/env python3
"""
Direct SQL Query Tool for Testing and Validation.
Run SQL queries directly against the SQLite database to validate LLM results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sqlite_db import SQLiteManager
import pandas as pd

def run_query_tool():
    """Interactive SQL query tool."""
    print("=== SQLite Direct Query Tool ===")
    print("Type SQL queries to test against the analytics database")
    print("Type 'schema' to see table structures")
    print("Type 'samples' to see sample data")
    print("Type 'exit' to quit\n")
    
    # Initialize database
    db = SQLiteManager()
    
    while True:
        try:
            query = input("SQL> ").strip()
            
            if query.lower() == 'exit':
                break
            elif query.lower() == 'schema':
                print("\n" + "="*50)
                print("DATABASE SCHEMA:")
                print("="*50)
                print(db.get_schema())
                print("="*50 + "\n")
                continue
            elif query.lower() == 'samples':
                print("\n" + "="*50)
                print("SAMPLE DATA:")
                print("="*50)
                
                # Show sample from each table
                for table in ['sales', 'customers']:
                    print(f"\n--- {table.upper()} (first 5 rows) ---")
                    result = db.execute_query(f"SELECT * FROM {table} LIMIT 5")
                    if result['success']:
                        df = pd.DataFrame(result['rows'])
                        print(df.to_string())
                    else:
                        print(f"Error: {result['error']}")
                print("="*50 + "\n")
                continue
            elif not query:
                continue
            
            # Execute the query
            print(f"\nExecuting: {query}")
            print("-" * 40)
            
            result = db.execute_query(query)
            
            if result['success']:
                df = pd.DataFrame(result['rows'])
                print(f"✅ Success! Returned {len(df)} rows")
                
                if not df.empty:
                    print("\nResults:")
                    print(df.to_string())
                    
                    # Show summary stats for numeric columns
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        print(f"\nSummary Statistics:")
                        for col in numeric_cols:
                            values = df[col]
                            print(f"  {col}: Sum={values.sum():,.0f}, Avg={values.mean():.2f}, Min={values.min()}, Max={values.max()}")
                else:
                    print("No rows returned")
            else:
                print(f"❌ Error: {result['error']}")
                
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    run_query_tool()