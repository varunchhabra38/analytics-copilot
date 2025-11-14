#!/usr/bin/env python3
"""
Test the enhanced BI analysis with actual redacted customer data to verify
that the LLM no longer confuses redaction with data quality issues.
"""

import sys
import pandas as pd
import json
sys.path.append('.')
from agent.tools.results_interpreter_tool import ResultsInterpreterTool
from utils.enhanced_pii_redactor import EnhancedPIIRedactor, RedactionMode

def test_redaction_awareness():
    """Test that the enhanced BI prompt handles redacted data correctly."""
    
    print("🎯 TESTING REDACTION-AWARE BUSINESS INTELLIGENCE")
    print("=" * 80)
    
    # Create realistic customer data with PII
    original_data = [
        {
            'customer_id': 'CUST-12345',
            'customer_name': 'John van der Berg',
            'customer_email': 'j.vandenberg@hotmail.com',
            'phone': '+31-6-12345678',
            'account_type': 'CURRENT',
            'balance': 15000.50,
            'risk_score': 75,
            'country': 'Netherlands',
            'last_transaction_amount': 5000.0,
            'last_transaction_date': '2024-11-10',
            'status': 'ACTIVE'
        },
        {
            'customer_id': 'CUST-67890', 
            'customer_name': 'Maria Elena Rodriguez',
            'customer_email': 'maria.rodriguez@gmail.com',
            'phone': '+34-612-345-678',
            'account_type': 'SAVINGS',
            'balance': 25000.00,
            'risk_score': 35,
            'country': 'Spain',
            'last_transaction_amount': 1200.0,
            'last_transaction_date': '2024-11-12',
            'status': 'ACTIVE'
        },
        {
            'customer_id': 'CUST-54321',
            'customer_name': 'Thomas Mueller',
            'customer_email': 'thomas.mueller@web.de',
            'phone': '+49-151-23456789',
            'account_type': 'CURRENT',
            'balance': 8500.75,
            'risk_score': 85,
            'country': 'Germany', 
            'last_transaction_amount': 12000.0,
            'last_transaction_date': '2024-11-11',
            'status': 'FLAGGED'
        }
    ]
    
    # Convert to DataFrame
    df_original = pd.DataFrame(original_data)
    print("📊 ORIGINAL DATA (with PII):")
    print(df_original.to_string(index=False))
    print("\n" + "=" * 80)
    
    # Apply PII redaction
    redactor = EnhancedPIIRedactor(mode=RedactionMode.BUSINESS_INTELLIGENCE)
    df_redacted = redactor.redact_dataframe(df_original)
    
    print("🔒 REDACTED DATA (privacy-protected):")
    print(df_redacted.to_string(index=False))
    print("\n" + "=" * 80)
    
    # Test the interpreter with redacted data
    interpreter = ResultsInterpreterTool()
    
    question = "Show me high-risk customers and their account details"
    sql_query = "SELECT * FROM dim_customer WHERE risk_score > 70"
    
    print(f"\n🤖 Testing Enhanced BI Analysis with Redacted Data...")
    print(f"Question: {question}")
    print(f"SQL: {sql_query}")
    print("\n" + "-" * 80)
    
    try:
        # Generate interpretation with redacted data
        interpretation = interpreter.interpret_results(
            question=question,
            sql_query=sql_query,
            execution_result=df_redacted
        )
        
        print("\n✅ ENHANCED BI ANALYSIS RESULT:")
        print("=" * 80)
        print(interpretation)
        print("=" * 80)
        
        # Validate the results
        success_indicators = []
        warning_indicators = []
        
        # Check 1: Should NOT mention redacted fields as data problems
        if "[NAME_REDACTED]" in interpretation or "[EMAIL_REDACTED]" in interpretation:
            warning_indicators.append("❌ Analysis mentions redacted data fields")
        else:
            success_indicators.append("✅ Analysis ignores redacted fields")
            
        # Check 2: Should NOT treat redaction as data quality issue
        if "data quality" in interpretation.lower() or "data integrity" in interpretation.lower():
            warning_indicators.append("❌ Analysis treats redaction as data quality issue")
        else:
            success_indicators.append("✅ Analysis doesn't confuse redaction with data problems")
            
        # Check 3: Should focus on business metrics
        business_metrics = ['balance', 'risk_score', 'country', 'account_type', 'status']
        metrics_mentioned = sum(1 for metric in business_metrics if metric in interpretation.lower())
        if metrics_mentioned >= 3:
            success_indicators.append("✅ Analysis focuses on business metrics")
        else:
            warning_indicators.append("❌ Analysis doesn't emphasize business metrics enough")
            
        # Check 4: Should provide actionable insights
        insight_keywords = ['recommend', 'action', 'priority', 'insight', 'pattern']
        insights_present = any(keyword in interpretation.lower() for keyword in insight_keywords)
        if insights_present:
            success_indicators.append("✅ Analysis provides actionable insights")
        else:
            warning_indicators.append("❌ Analysis lacks actionable insights")
            
        # Display results
        print("\n📈 VALIDATION RESULTS:")
        print("-" * 40)
        for indicator in success_indicators:
            print(indicator)
        for indicator in warning_indicators:
            print(indicator)
            
        # Overall assessment
        total_checks = len(success_indicators) + len(warning_indicators)
        success_rate = len(success_indicators) / total_checks * 100 if total_checks > 0 else 0
        
        print(f"\n🎯 OVERALL ENHANCEMENT EFFECTIVENESS: {success_rate:.1f}%")
        if success_rate >= 80:
            print("🟢 EXCELLENT: Enhanced BI analysis is working properly")
        elif success_rate >= 60:
            print("🟡 GOOD: Enhanced BI analysis is mostly working, minor improvements needed")
        else:
            print("🔴 NEEDS WORK: Enhanced BI analysis requires further refinement")
            
    except Exception as e:
        print(f"❌ Error in enhanced BI analysis: {e}")
        import traceback
        traceback.print_exc()

def compare_redaction_modes():
    """Compare different redaction modes for BI analysis."""
    print("\n" + "=" * 80)
    print("🔬 COMPARING REDACTION MODES FOR BI ANALYSIS")
    print("=" * 80)
    
    # Sample data
    data = [{
        'customer_name': 'Sarah Johnson',
        'customer_email': 'sarah.j@corporate.com',
        'account_balance': 50000.0,
        'risk_level': 'HIGH'
    }]
    df = pd.DataFrame(data)
    
    modes = [
        (RedactionMode.STRICT, "Maximum Privacy"),
        (RedactionMode.BUSINESS_INTELLIGENCE, "BI-Optimized"), 
        (RedactionMode.DEVELOPMENT, "Development/Testing")
    ]
    
    for mode, description in modes:
        print(f"\n🔒 {description} Mode ({mode.value}):")
        print("-" * 40)
        
        redactor = EnhancedPIIRedactor(mode=mode)
        redacted = redactor.redact_dataframe(df)
        
        print(f"Original: {data[0]['customer_name']} | {data[0]['customer_email']}")
        print(f"Redacted: {redacted.iloc[0]['customer_name']} | {redacted.iloc[0]['customer_email']}")
        
        if mode == RedactionMode.BUSINESS_INTELLIGENCE:
            print("✅ Preserves patterns for business analysis while protecting identity")
        elif mode == RedactionMode.STRICT:
            print("⚠️  Maximum privacy but limits business intelligence")
        else:
            print("💡 Development-friendly but not for production")

if __name__ == "__main__":
    test_redaction_awareness()
    compare_redaction_modes()