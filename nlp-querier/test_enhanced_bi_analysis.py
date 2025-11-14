#!/usr/bin/env python3
"""
Test the enhanced business intelligence analysis with redaction-aware prompts.
"""

import sys
import pandas as pd
sys.path.append('.')
from agent.tools.results_interpreter_tool import ResultsInterpreterTool

def test_enhanced_bi_analysis():
    """Test the enhanced BI analysis that should ignore redacted data."""
    
    print("🧪 Testing Enhanced Business Intelligence Analysis")
    print("=" * 60)
    
    # Create sample data with both business metrics and redacted PII
    sample_data = [
        {
            'alert_id': 'ALERT-001',
            'customer_name': '[NAME_REDACTED]',
            'customer_email': '[EMAIL_REDACTED]',
            'alert_type': 'SANCTIONS',
            'risk_level': 'HIGH',
            'country': 'NL',
            'amount': 50000.0,
            'channel': 'WIRE_TRANSFER',
            'alert_dt': '2024-10-15',
            'status': 'OPEN'
        },
        {
            'alert_id': 'ALERT-002', 
            'customer_name': '[NAME_REDACTED]',
            'customer_email': '[EMAIL_REDACTED]',
            'alert_type': 'AML_SUSPICIOUS',
            'risk_level': 'HIGH',
            'country': 'DE',
            'amount': 75000.0,
            'channel': 'ONLINE',
            'alert_dt': '2024-10-16',
            'status': 'OPEN'
        },
        {
            'alert_id': 'ALERT-003',
            'customer_name': '[NAME_REDACTED]',
            'customer_email': '[EMAIL_REDACTED]', 
            'alert_type': 'FRAUD',
            'risk_level': 'MEDIUM',
            'country': 'FR',
            'amount': 25000.0,
            'channel': 'ATM',
            'alert_dt': '2024-10-17',
            'status': 'RESOLVED'
        },
        {
            'alert_id': 'ALERT-004',
            'customer_name': '[NAME_REDACTED]',
            'customer_email': '[EMAIL_REDACTED]',
            'alert_type': 'SANCTIONS',
            'risk_level': 'HIGH', 
            'country': 'IT',
            'amount': 100000.0,
            'channel': 'WIRE_TRANSFER',
            'alert_dt': '2024-10-18',
            'status': 'OPEN'
        },
        {
            'alert_id': 'ALERT-005',
            'customer_name': '[NAME_REDACTED]',
            'customer_email': '[EMAIL_REDACTED]',
            'alert_type': 'AML_SUSPICIOUS',
            'risk_level': 'LOW',
            'country': 'ES',
            'amount': 5000.0,
            'channel': 'ONLINE',
            'alert_dt': '2024-10-19',
            'status': 'RESOLVED'
        }
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(sample_data)
    
    print("📊 Sample Data (with PII redacted):")
    print(df.to_string(index=False))
    print("\n" + "=" * 60)
    
    # Test the interpreter
    interpreter = ResultsInterpreterTool()
    
    question = "Show me high-risk alerts from the past week"
    sql_query = "SELECT * FROM fact_alerts WHERE risk_level = 'HIGH' AND alert_dt >= '2024-10-15'"
    
    print(f"\n🤖 Testing Business Intelligence Analysis...")
    print(f"Question: {question}")
    print(f"SQL: {sql_query}")
    print("\n" + "-" * 60)
    
    try:
        # Generate interpretation
        interpretation = interpreter.interpret_results(
            question=question,
            sql_query=sql_query,
            execution_result=df
        )
        
        print("\n✅ ENHANCED BI ANALYSIS RESULT:")
        print("=" * 60)
        print(interpretation)
        print("=" * 60)
        
        # Check if the interpretation mentions redaction (it shouldn't)
        if "[NAME_REDACTED]" in interpretation or "[EMAIL_REDACTED]" in interpretation:
            print("⚠️  WARNING: Analysis mentions redacted data - prompt needs more refinement")
        else:
            print("✅ SUCCESS: Analysis focuses on business metrics, ignores redacted fields")
            
        if "data quality" in interpretation.lower() or "data integrity" in interpretation.lower():
            print("⚠️  WARNING: Analysis incorrectly interprets redaction as data quality issue")
        else:
            print("✅ SUCCESS: Analysis doesn't confuse redaction with data quality problems")
            
    except Exception as e:
        print(f"❌ Error in BI analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_bi_analysis()