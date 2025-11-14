#!/usr/bin/env python3

"""
Debug the SQL validator issue
"""

from agent.graph import run_agent_chat

def debug_sql_validator():
    print("Debugging SQL validator issues...")
    
    # Test the problematic question
    question = "Which region or channel has the highest alert-to-transaction ratio?"
    print(f"Question: {question}")
    
    try:
        result = run_agent_chat(question, [])
        
        # Look at the generated SQL
        generated_sql = result.get('generated_sql', 'N/A')
        validated_sql = result.get('sql', 'N/A')
        validation_error = result.get('validation_error', 'None')
        
        print(f"\nGenerated SQL:")
        print("=" * 60)
        print(generated_sql)
        print("=" * 60)
        
        print(f"\nValidated SQL: {validated_sql}")
        print(f"Validation Error: {validation_error}")
        
        # Check what the SQL actually starts with
        if generated_sql and generated_sql != 'N/A':
            sql_lines = generated_sql.strip().split('\n')
            first_line = sql_lines[0].strip()
            print(f"\nFirst line: '{first_line}'")
            print(f"Starts with SELECT: {first_line.upper().startswith('SELECT')}")
            print(f"Starts with WITH: {first_line.upper().startswith('WITH')}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    debug_sql_validator()