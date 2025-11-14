"""
Quick test of the simplified SQL generation approach.
"""
import sys
import os

# Add the agent directory to Python path
sys.path.append('agent')

from agent.tools.sql_gen_tool import VertexAISQLGenTool

def test_simplified_parsing():
    """Test the simplified JSON parsing approach."""
    print("🧪 Testing Simplified SQL Generation Approach")
    print("=" * 60)
    
    # Test data - typical truncated response from Vertex AI
    test_response = '''```json
{
  "sql": "SELECT CAST(SUM(T1.is_flagged) AS REAL) * 100 / COUNT(T1.txn_id) AS percentage_of_transactions_with_alerts FROM fact_transactions AS T1 JOIN dim_calendar AS T2 ON T1.txn_dt = T2.dt WHERE T2.year = 2025 AND T2.quarter = 'Q1'",
  "explanation": "This query calculates the percentage of transactions that were flagged in the first quarter of 2025 by dividing the count of flagged transactions by the total transaction count for that period."
}
```'''
    
    # Initialize the tool (without actual Vertex AI connection)
    try:
        tool = VertexAISQLGenTool(project_id="test-project")
    except:
        # Create a mock tool for parsing testing
        class MockTool:
            def _parse_response(self, content):
                from agent.tools.sql_gen_tool import VertexAISQLGenTool
                # Use the class method directly
                return VertexAISQLGenTool._parse_response(None, content)
            
            def _extract_sql_from_text(self, content):
                from agent.tools.sql_gen_tool import VertexAISQLGenTool
                return VertexAISQLGenTool._extract_sql_from_text(None, content)
        
        tool = MockTool()
    
    # Test parsing
    result = tool._parse_response(test_response)
    
    print("📝 Test Response:")
    print(test_response)
    print("\n" + "=" * 60)
    print("📊 Parsing Result:")
    print(f"✅ SQL: {result['sql']}")
    print(f"✅ Explanation: {result['explanation']}")
    print(f"✅ SQL Length: {len(result['sql'])}")
    print(f"✅ Valid SQL: {'SELECT' in result['sql'] and 'FROM' in result['sql']}")
    
    # Test edge cases
    print("\n" + "=" * 60)
    print("🔬 Testing Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        # Truncated JSON
        '{"sql": "SELECT * FROM table WHERE col = ',
        
        # No JSON structure
        'SELECT * FROM customers WHERE name = "John"',
        
        # Malformed JSON
        '{"sql": "SELECT * FROM table", explanation": "test"}',
        
        # Empty response
        '',
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: {case[:50]}...")
        result = tool._parse_response(case)
        print(f"   Result SQL: {result['sql'][:50]}...")
        print(f"   Result Explanation: {result['explanation']}")
    
    print("\n" + "=" * 60)
    print("🎉 Simplified Parsing Test Complete!")
    print("💡 This approach is much more resilient than complex regex fixes!")

if __name__ == "__main__":
    test_simplified_parsing()