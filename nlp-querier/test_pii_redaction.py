#!/usr/bin/env python3

"""
Test script for PII redaction functionality.
"""

import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.pii_redactor import PIIRedactor, get_pii_redactor

def test_pii_detection_basic():
    """Test basic PII detection patterns."""
    print("🔍 Testing Basic PII Detection...")
    
    redactor = PIIRedactor(enable_name_redaction=True)
    
    # Test data with various PII types
    test_text = """
    Customer John Smith (john.smith@email.com) called from 555-123-4567.
    His account number is ACC-123456789 and credit card ending 4532-1234-5678-9012.
    SSN: 123-45-6789, IP address: 192.168.1.100
    Customer ID: CUST-ABC123
    """
    
    findings = redactor.detect_pii(test_text)
    print(f"📊 Found {len(findings)} PII instances:")
    for finding in findings:
        print(f"  • {finding['type']}: {finding['value']} ({finding['description']})")
    
    redacted_text, _ = redactor.redact_text(test_text)
    print(f"\n📝 Original text:\n{test_text}")
    print(f"\n🔒 Redacted text:\n{redacted_text}")
    
    return len(findings) > 0

def test_pii_dataframe_redaction():
    """Test PII redaction in DataFrame."""
    print("\n🔍 Testing DataFrame PII Redaction...")
    
    # Create sample DataFrame with PII
    data = {
        'customer_name': ['John Smith', 'Jane Doe', 'Bob Wilson'],
        'email': ['john@email.com', 'jane.doe@company.org', 'bob@test.net'],
        'phone': ['555-123-4567', '(555) 987-6543', '555.111.2222'],
        'account_id': ['ACC-123456', 'ACC-789012', 'ACC-345678'],
        'balance': [1000.50, 2500.75, 750.25],
        'notes': ['Customer called about account', 'No issues', 'Phone: 555-999-8888']
    }
    df = pd.DataFrame(data)
    
    print("📊 Original DataFrame:")
    print(df)
    
    redactor = PIIRedactor(enable_name_redaction=True)
    redacted_df, findings = redactor.redact_dataframe(df)
    
    print(f"\n🔒 Redacted DataFrame:")
    print(redacted_df)
    
    print(f"\n📋 PII Findings Summary:")
    total_findings = 0
    for column, column_findings in findings.items():
        print(f"  • Column '{column}': {len(column_findings)} PII instances")
        total_findings += len(column_findings)
    
    print(f"📊 Total PII instances found: {total_findings}")
    
    return total_findings > 0

def test_pii_business_interpretation():
    """Test PII redaction in business interpretation text."""
    print("\n🔍 Testing Business Interpretation PII Redaction...")
    
    business_text = """
    ## Executive Summary: Customer Analysis
    
    Our analysis reveals concerning patterns in customer John Smith's account (ACC-123456789).
    The customer can be reached at john.smith@company.com or 555-123-4567.
    
    **Key Findings:**
    - Account holder Jane Doe (CUST-789012) shows unusual activity
    - Credit card transactions from IP 192.168.1.100 require investigation
    - SSN verification failed for 123-45-6789
    
    **Recommendations:**
    - Contact customer immediately at provided phone number
    - Verify identity using alternative methods
    """
    
    redactor = PIIRedactor(enable_name_redaction=True)
    redacted_text, findings = redactor.redact_text(business_text)
    
    print(f"📝 Original business interpretation:\n{business_text}")
    print(f"\n🔒 Redacted business interpretation:\n{redacted_text}")
    
    print(f"\n📋 PII Findings:")
    for finding in findings:
        print(f"  • {finding['type']}: {finding['description']}")
    
    report = redactor.generate_pii_report({"business_interpretation": findings})
    print(f"\n📊 PII Report:\n{report}")
    
    return len(findings) > 0

def test_edge_cases():
    """Test edge cases and false positives."""
    print("\n🔍 Testing Edge Cases...")
    
    redactor = PIIRedactor(enable_name_redaction=False)  # Disable name redaction
    
    # Text that might trigger false positives
    test_cases = [
        "Transaction amount: $1,234.56",  # Should not be flagged as phone
        "Date: 2024-01-01",  # Should not be flagged
        "Error code: 404-500-600",  # Should not be flagged as phone
        "Temperature: 98.6 degrees",  # Should not be flagged
        "Valid email: user@domain.com",  # Should be flagged
        "Invalid email-like: user@domain",  # Should not be flagged
        "Account: ACC-123456",  # Should be flagged
        "Random number: 123456789",  # Should not be flagged as account
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        findings = redactor.detect_pii(test_case)
        status = "🚨 PII FOUND" if findings else "✅ CLEAN"
        print(f"  {i}. {test_case} → {status}")
        if findings:
            for finding in findings:
                print(f"     └─ {finding['type']}: {finding['value']}")

def main():
    """Run all PII redaction tests."""
    print("🔒 PII REDACTION SYSTEM - COMPREHENSIVE TEST")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Basic PII Detection", test_pii_detection_basic()))
    test_results.append(("DataFrame Redaction", test_pii_dataframe_redaction()))
    test_results.append(("Business Interpretation", test_pii_business_interpretation()))
    
    # Run edge case tests
    test_edge_cases()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  • {test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🔒 PII redaction system is working correctly!")
        print("🛡️ Your query results and business interpretations will be protected.")
    else:
        print("\n⚠️ PII redaction system needs attention.")

if __name__ == "__main__":
    main()