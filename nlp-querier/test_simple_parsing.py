"""
Simple test of JSON parsing without Vertex AI dependency.
"""
import json
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_sql_from_text(content: str) -> dict:
    """
    Extract SQL from plain text response when JSON parsing fails.
    """
    # Look for quoted SQL in JSON-like structure
    sql_match = re.search(r'"sql":\s*"([^"]+)"', content, re.DOTALL)
    if sql_match:
        sql = sql_match.group(1).strip()
        if sql and 'SELECT' in sql.upper():
            logger.info(f"✅ Extracted SQL from JSON field: {sql[:50]}...")
            return {"sql": sql, "explanation": "SQL extracted from JSON field"}
    
    # Look for standalone SELECT statements
    select_patterns = [
        r'(SELECT\s+[^;]+?(?:;|$))',
        r'(SELECT\s+.*?FROM\s+\w+[^}]*?)(?=\n|"|$)',
        r'(SELECT\s+.*?FROM\s+\w+.*?)(?=\s*(?:\n|"|$))',
    ]
    
    for pattern in select_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            sql = match.strip().rstrip(';').rstrip(',').rstrip('"')
            if len(sql) > 10 and 'FROM' in sql.upper():
                logger.info(f"✅ Extracted SQL from text: {sql[:50]}...")
                return {"sql": sql, "explanation": "SQL extracted from text"}
    
    logger.warning("No valid SQL found in response")
    return {"sql": "", "explanation": "Could not extract SQL from response"}

def parse_response(content: str) -> dict:
    """
    Simple and robust JSON parsing for LLM responses.
    """
    if not content or not content.strip():
        logger.warning("Empty response")
        return {"sql": "", "explanation": "Empty response"}
    
    logger.info(f"🔍 Response parsing - length: {len(content)}")
    
    try:
        # Step 1: Clean up the response text
        content = content.strip()
        
        # Remove markdown code blocks
        content = re.sub(r'```(?:json|sql)?\s*\n?', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Step 2: Extract JSON using simple brace matching
        json_start = content.find('{')
        if json_start == -1:
            # No JSON structure found, look for direct SQL
            return extract_sql_from_text(content)
        
        # Find the matching closing brace
        brace_count = 0
        json_end = -1
        
        for i in range(json_start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break
        
        if json_end == -1:
            # Incomplete JSON, try to extract SQL directly
            logger.warning("Incomplete JSON structure, extracting SQL directly")
            return extract_sql_from_text(content)
        
        # Step 3: Parse the JSON
        json_text = content[json_start:json_end + 1]
        
        try:
            data = json.loads(json_text)
            if isinstance(data, dict) and 'sql' in data:
                sql = data['sql'].strip()
                explanation = data.get('explanation', 'SQL query generated')
                
                if sql and len(sql) > 5:  # Basic sanity check
                    logger.info(f"✅ JSON parsed successfully - SQL: {sql[:50]}...")
                    return {"sql": sql, "explanation": explanation}
        
        except json.JSONDecodeError:
            logger.warning("JSON parsing failed, falling back to text extraction")
        
        # Step 4: Fallback to text extraction
        return extract_sql_from_text(content)
        
    except Exception as e:
        logger.error(f"Error in response parsing: {e}")
        return {"sql": "", "explanation": f"Parsing error: {str(e)}"}

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
    
    # Test parsing
    result = parse_response(test_response)
    
    print("📝 Test Response:")
    print(test_response[:200] + "..." if len(test_response) > 200 else test_response)
    print("\n" + "=" * 60)
    print("📊 Parsing Result:")
    print(f"✅ SQL: {result['sql'][:100]}..." if len(result['sql']) > 100 else f"✅ SQL: {result['sql']}")
    print(f"✅ Explanation: {result['explanation']}")
    print(f"✅ SQL Length: {len(result['sql'])}")
    print(f"✅ Valid SQL: {'SELECT' in result['sql'] and 'FROM' in result['sql']}")
    
    # Test edge cases
    print("\n" + "=" * 60)
    print("🔬 Testing Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        # Truncated JSON (typical problem case)
        '{"sql": "SELECT * FROM table WHERE col = ',
        
        # No JSON structure
        'SELECT * FROM customers WHERE name = "John"',
        
        # Malformed JSON
        '{"sql": "SELECT * FROM table", explanation": "test"}',
        
        # Empty response
        '',
        
        # Your original failing case
        '''```json
{
  "sql": "SELECT CAST((SELECT COUNT(fa.alert_id) FROM fact_alerts AS fa JOIN dim_calendar AS dc ON fa.alert_dt = dc.dt WHERE dc.year = 2025 AND dc.quarter = 'Q1') AS REAL) * 100 / (SELECT COUNT(ft.txn_id) FROM fact_transactions AS ft JOIN dim_calendar AS dc ON ft.txn_dt = dc.dt WHERE dc.year = 2025 AND dc.quarter = 'Q1')",
  "explanation": "Calculates the percentage of alerts relative to total transactions in Q1 2025 by dividing the alert count by the transaction count for that period."
}
```'''
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: {case[:50]}...")
        result = parse_response(case)
        success = "✅" if result['sql'] else "❌"
        print(f"   {success} Result SQL: {result['sql'][:80]}..." if result['sql'] else f"   {success} No SQL extracted")
        print(f"   📝 Explanation: {result['explanation']}")
    
    print("\n" + "=" * 60)
    print("🎉 Simplified Parsing Test Complete!")
    print("💡 This approach is much more resilient than complex regex fixes!")
    print("🚀 Key Benefits:")
    print("   • Simple brace matching for JSON extraction")
    print("   • Multiple fallback strategies")
    print("   • No complex regex for string fixing")
    print("   • More maintainable and debuggable")

if __name__ == "__main__":
    test_simplified_parsing()