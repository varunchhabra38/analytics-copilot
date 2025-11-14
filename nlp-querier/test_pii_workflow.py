#!/usr/bin/env python3

"""
Test Script: Analytics Agent with PII Protection

This script adds test data with PII to the database and provides test queries
to verify that the PII protection system is working correctly.
"""

import sqlite3
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_pii_test_data():
    """Add test data with PII to the database for testing redaction."""
    
    # Connect to the database
    db_path = "output/fcfp_analytics.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Adding PII test data to database...")
    
    try:
        # Add test customer data with PII
        test_customers = [
            ('CUST-001', 'John Smith', 'PREMIUM', '2024-01-15', 'VERIFIED', 0, 'USA', 'john.smith@email.com', '555-123-4567', '1980-05-15'),
            ('CUST-002', 'Jane Doe', 'STANDARD', '2024-02-20', 'PENDING', 1, 'UK', 'jane.doe@company.org', '(555) 987-6543', '1975-12-10'),
            ('CUST-003', 'Bob Wilson', 'VIP', '2024-03-10', 'VERIFIED', 0, 'CANADA', 'bob.wilson@test.net', '555.111.2222', '1990-08-22')
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO dim_customer 
            (customer_id, customer_name, segment, onboarding_dt, kyc_status, is_pep, residence_country, email, phone, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_customers)
        
        # Add test account data with PII
        test_accounts = [
            ('ACC-123456', 'CUST-001', 'John Smith Checking', 'CHECKING', '2024-01-15', 'ACTIVE', 'LOW', 5000.50, 'USD'),
            ('ACC-789012', 'CUST-002', 'Jane Doe Savings', 'SAVINGS', '2024-02-20', 'ACTIVE', 'MEDIUM', 15000.75, 'GBP'),
            ('ACC-345678', 'CUST-003', 'Bob Wilson Investment', 'INVESTMENT', '2024-03-10', 'ACTIVE', 'HIGH', 50000.00, 'CAD')
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO dim_account 
            (account_id, customer_id, account_name, account_type, opened_dt, status, risk_segment, balance, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_accounts)
        
        # Add test transaction data with PII in descriptions
        test_transactions = [
            ('TXN-001', 'CUST-001', 'ACC-123456', '2024-11-01', '14:30:00', 1500.00, 'USD', 'USA', 'ONLINE', 'DEPOSIT', 'Transfer from john.smith@email.com account', 0, 0.1),
            ('TXN-002', 'CUST-002', 'ACC-789012', '2024-11-02', '09:15:00', -250.75, 'GBP', 'UK', 'ATM', 'WITHDRAWAL', 'ATM withdrawal - called 555-987-6543 for verification', 1, 0.3),
            ('TXN-003', 'CUST-003', 'ACC-345678', '2024-11-03', '16:45:00', -5000.00, 'CAD', 'CANADA', 'WIRE', 'TRANSFER', 'Wire to account ACC-999888 per Bob Wilson request', 1, 0.8)
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO fact_transactions 
            (txn_id, customer_id, account_id, txn_dt, txn_time, amount, currency, country, channel, transaction_type, merchant_name, is_flagged, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_transactions)
        
        # Add test alert data with PII in descriptions
        test_alerts = [
            ('ALERT-001', 'CUST-001', 'ACC-123456', '2024-11-01', '14:35:00', 'NORTH_AMERICA', 'USA', 'HIGH', 'SUSPICIOUS_ACTIVITY', 'OPEN', 1, 1500.00, 'ONLINE', 'Large deposit from john.smith@email.com flagged for review. Contact: 555-123-4567', None, None),
            ('ALERT-002', 'CUST-002', 'ACC-789012', '2024-11-02', '09:20:00', 'EUROPE', 'UK', 'MEDIUM', 'VELOCITY_CHECK', 'OPEN', 1, 250.75, 'ATM', 'Rapid ATM usage pattern detected. Customer Jane Doe (CUST-002) verification needed.', None, None),
            ('ALERT-003', 'CUST-003', 'ACC-345678', '2024-11-03', '16:50:00', 'NORTH_AMERICA', 'CANADA', 'CRITICAL', 'LARGE_TRANSFER', 'OPEN', 1, 5000.00, 'WIRE', 'High-risk wire transfer. Customer SSN: 123-45-6789 requires immediate verification.', None, None)
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO fact_alerts 
            (alert_id, customer_id, account_id, alert_dt, alert_time, region, country, risk_level, alert_type, alert_status, txn_count, amount, channel, description, assigned_to, resolved_dt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_alerts)
        
        conn.commit()
        print("✅ PII test data added successfully!")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM dim_customer WHERE customer_name LIKE '%Smith%'")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_alerts WHERE description LIKE '%email%'")
        alert_count = cursor.fetchone()[0]
        
        print(f"📊 Test data verification:")
        print(f"  • Customers with PII names: {customer_count}")
        print(f"  • Alerts with PII in descriptions: {alert_count}")
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_test_queries():
    """Generate test queries that should trigger PII redaction."""
    
    test_queries = [
        {
            "query": "Show me customer details with their email addresses",
            "description": "Should redact emails in customer table",
            "expected_pii": ["email", "phone", "customer_name"]
        },
        {
            "query": "List all alerts with their descriptions",
            "description": "Should redact PII in alert descriptions",
            "expected_pii": ["email", "phone", "ssn", "customer_name", "account_number"]
        },
        {
            "query": "Show transaction details with merchant information",
            "description": "Should redact PII in transaction descriptions",
            "expected_pii": ["email", "phone", "account_number"]
        },
        {
            "query": "Get account information with customer names and contact details",
            "description": "Should redact names, emails, phones across multiple columns",
            "expected_pii": ["customer_name", "email", "phone"]
        },
        {
            "query": "Show high-risk alerts with full details",
            "description": "Should redact sensitive information in alert descriptions",
            "expected_pii": ["ssn", "customer_name", "email", "phone"]
        }
    ]
    
    print("\n🧪 TEST QUERIES FOR PII PROTECTION:")
    print("=" * 60)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. {test['query']}")
        print(f"   📝 Description: {test['description']}")
        print(f"   🎯 Expected PII Types: {', '.join(test['expected_pii'])}")
    
    print(f"\n" + "=" * 60)
    print("🔒 TESTING INSTRUCTIONS:")
    print("1. Run each query in the Streamlit app")
    print("2. Check that PII is redacted in the results table")
    print("3. Verify that business interpretation doesn't contain raw PII")
    print("4. Look for PII protection status messages in the UI")
    print("5. Ensure query results are still meaningful despite redaction")

def main():
    """Main test setup function."""
    print("🧪 ANALYTICS AGENT PII PROTECTION - TEST SETUP")
    print("=" * 60)
    
    # Add test data
    add_pii_test_data()
    
    # Show test queries
    generate_test_queries()
    
    print(f"\n🚀 READY TO TEST!")
    print("📱 Open the Streamlit app at: http://localhost:8503")
    print("🔍 Try the test queries above to verify PII protection")
    print("✅ Look for '[EMAIL_REDACTED]', '[PHONE_REDACTED]', etc. in results")

if __name__ == "__main__":
    main()