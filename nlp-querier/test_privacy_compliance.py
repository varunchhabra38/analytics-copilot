"""
Privacy-Compliant Summary System Demonstration

This script demonstrates how the enhanced summary system protects customer data
while still providing intelligent business insights through metadata analysis.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demonstrate_privacy_compliance():
    """Demonstrate privacy-compliant summary generation."""
    print("🔒 Privacy-Compliant Summary System Demo")
    print("=" * 60)
    
    # Create sample customer data (simulating real database results)
    customer_data = pd.DataFrame({
        'customer_id': [12345, 67890, 54321, 98765],
        'transaction_amount': [25000.50, 150000.75, 8500.25, 45000.00],
        'risk_score': [0.85, 0.92, 0.45, 0.78],
        'region': ['EMEA', 'AMERICAS', 'APAC', 'EMEA'],
        'alert_type': ['SANCTIONS', 'AML', 'SUSPICIOUS', 'AML'],
        'transaction_date': pd.date_range('2024-10-01', periods=4, freq='W')
    })
    
    print("📊 Sample Customer Data (NOT sent to LLM):")
    print(customer_data.to_string())
    print(f"\n💰 Actual total amount: ${customer_data['transaction_amount'].sum():,.2f}")
    print(f"🏦 Actual highest transaction: ${customer_data['transaction_amount'].max():,.2f}")
    
    # Test the privacy-compliant analysis system
    print("\n" + "=" * 60)
    print("🧠 PRIVACY-COMPLIANT ANALYSIS (Metadata Only)")
    print("=" * 60)
    
    try:
        from agent.nodes.summarize import _analyze_query_results, _audit_privacy_compliance
        
        # Analyze the data to extract privacy-safe insights
        question = "Show me high-risk financial transactions for compliance review"
        sql_query = "SELECT * FROM transactions WHERE risk_score > 0.7 AND amount > 10000"
        
        print("\n1️⃣ Extracting Privacy-Safe Metadata...")
        insights = _analyze_query_results(question, customer_data, sql_query)
        
        print("✅ Metadata extracted (no customer data exposed):")
        print(f"   • Business Context: {insights.get('business_context', 'N/A')}")
        print(f"   • Row Count: {insights.get('row_count', 0)}")
        print(f"   • Data Quality: {insights.get('data_quality', {})}")
        print(f"   • Patterns Detected: {len(insights.get('patterns', []))}")
        
        # Show what metadata is safe to use
        if 'key_metrics' in insights:
            print("\n📋 Privacy-Safe Statistical Metadata:")
            for col, stats in insights['key_metrics'].items():
                print(f"   • {col}:")
                for key, value in stats.items():
                    print(f"     - {key}: {value}")
        
        # Test privacy audit
        print("\n2️⃣ Privacy Compliance Audit...")
        from agent.nodes.summarize import _build_intelligent_summary_prompt
        
        # Generate prompt (should be privacy-safe)
        test_prompt = _build_intelligent_summary_prompt(question, sql_query, insights)
        
        # Audit the prompt
        is_compliant = _audit_privacy_compliance(insights, test_prompt)
        
        if is_compliant:
            print("✅ PRIVACY AUDIT PASSED - No customer data detected")
        else:
            print("❌ PRIVACY AUDIT FAILED - Customer data leak detected")
        
        print("\n3️⃣ Privacy-Safe Prompt Preview (First 300 chars):")
        print("─" * 50)
        print(test_prompt[:300] + "..." if len(test_prompt) > 300 else test_prompt)
        print("─" * 50)
        
        # Show what's NOT included
        print("\n🚫 What's NOT Sent to LLM (Customer Data Protected):")
        print("   ❌ Actual transaction amounts")
        print("   ❌ Customer IDs or identifiers") 
        print("   ❌ Specific dates or timestamps")
        print("   ❌ Individual risk scores")
        print("   ❌ Raw data values or records")
        
        print("\n✅ What IS Sent to LLM (Metadata Only):")
        print("   ✅ Statistical aggregates (count, variability)")
        print("   ✅ Data quality indicators")
        print("   ✅ Pattern classifications")
        print("   ✅ Business context categories")
        print("   ✅ Query structure metadata")
        
        # Generate privacy-safe summary
        print("\n4️⃣ Generating Privacy-Safe Summary...")
        from agent.nodes.summarize import _create_privacy_safe_summary
        
        safe_summary = _create_privacy_safe_summary(question, insights)
        print(f"\n💼 Executive Summary (Privacy Protected):")
        print(f"   {safe_summary}")
        
        print("\n" + "=" * 60)
        print("🔐 PRIVACY PROTECTION SUMMARY")
        print("=" * 60)
        print("✅ Customer data remains in secure environment")
        print("✅ Only statistical metadata sent to external AI")
        print("✅ Business insights generated without data exposure")
        print("✅ Compliance with data protection regulations")
        print("✅ Audit trail for privacy verification")
        
    except ImportError as e:
        print(f"⚠️ Module import error: {e}")
        print("This demo requires the enhanced summary modules.")
    except Exception as e:
        print(f"❌ Demo error: {e}")

def demonstrate_privacy_violations():
    """Show what would trigger privacy violations."""
    print("\n🚨 Privacy Violation Detection Demo")
    print("=" * 50)
    
    # Create example of what would be flagged as violations
    print("Example of DATA LEAKAGE that would be detected and blocked:")
    
    bad_insights = {
        "key_metrics": {
            "transaction_amount": {
                "total": 228501.50,  # VIOLATION: Actual total
                "average": 57125.38,  # VIOLATION: Actual average
                "max": 150000.75     # VIOLATION: Actual max value
            }
        },
        "time_context": {
            "transaction_date": {
                "date_range": "2024-10-01 to 2024-10-22",  # VIOLATION: Actual dates
                "most_recent": "2024-10-22"                # VIOLATION: Specific date
            }
        }
    }
    
    bad_prompt = """
    Analysis shows total transaction amount of $228,501.50 with individual 
    transactions ranging from $8,500.25 to $150,000.75. Customer 12345 had
    the highest risk score of 0.92 on 2024-10-15.
    """
    
    try:
        from agent.nodes.summarize import _audit_privacy_compliance
        
        print("🔍 Testing privacy audit on bad data...")
        is_safe = _audit_privacy_compliance(bad_insights, bad_prompt)
        
        if not is_safe:
            print("✅ GOOD: Privacy violations correctly detected and blocked!")
        else:
            print("❌ BAD: Privacy violations not detected (audit needs improvement)")
            
    except Exception as e:
        print(f"Audit test error: {e}")

if __name__ == "__main__":
    print("🔐 Starting Privacy-Compliant Analytics Demo\n")
    
    demonstrate_privacy_compliance()
    demonstrate_privacy_violations()
    
    print("\n" + "=" * 60)
    print("🎯 KEY PRIVACY PROTECTION FEATURES")
    print("=" * 60)
    print("🔒 Data Isolation: Customer data never leaves secure environment")
    print("🧮 Metadata Analysis: Only statistical summaries processed")
    print("🔍 Privacy Auditing: Automatic detection of potential data leaks")
    print("🚨 Fail-Safe Mode: Local summary generation if privacy violated")
    print("📝 Audit Logging: Complete trail of privacy protection actions")
    print("⚖️ Compliance Ready: Meets data protection regulation requirements")
    
    input("\n👋 Press Enter to exit...")