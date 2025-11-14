#!/usr/bin/env python3

"""
Analyze customer data to identify redaction gaps and improve PII protection
"""

import sys
sys.path.append('.')

import pandas as pd
from agent.tools.sql_executor_tool import create_sql_executor_tool
from utils.pii_redactor import PIIRedactor
from config import get_config

def analyze_redaction_gaps():
    """Analyze customer data to identify where PII redaction is not working fully"""
    
    print('🔍 Executing full customer query to analyze redaction gaps...')
    print('=' * 70)

    # Get database configuration
    config = get_config()
    db_config = config['database']

    # Create SQL executor
    if db_config['type'] == 'sqlite':
        db_path = db_config['connection_string'].replace('sqlite:///./', '')
        executor = create_sql_executor_tool(db_type='sqlite', db_path=db_path)
    else:
        executor = create_sql_executor_tool(
            db_type='postgresql', 
            connection_string=db_config['connection_string']
        )

    # Execute the full customer query
    query = '''SELECT customer_id, customer_name, segment, onboarding_dt, kyc_status, 
                      is_pep, residence_country, email, phone, date_of_birth 
               FROM dim_customer'''

    result = executor.execute_query(query)

    if result.get('error'):
        print(f'❌ Error: {result["error"]}')
        return

    df = result['result']
    print(f'✅ Query successful: {len(df)} total rows')
    print()
    
    # Analyze patterns that might be missed by redaction
    print('🔍 ANALYZING REDACTION GAPS - Sample Data Analysis:')
    print('=' * 70)
    
    # Show diverse name patterns
    print('📛 CUSTOMER NAME PATTERNS (first 25):')
    print('-' * 40)
    unique_names = df['customer_name'].unique()[:25]
    for i, name in enumerate(unique_names, 1):
        print(f'{i:2d}. "{name}"')
    
    print()
    print('📞 PHONE NUMBER PATTERNS (first 20):') 
    print('-' * 40)
    unique_phones = df['phone'].dropna().unique()[:20]
    for i, phone in enumerate(unique_phones, 1):
        print(f'{i:2d}. "{phone}"')
    
    print()
    print('📧 EMAIL PATTERNS (first 15):')
    print('-' * 40)
    unique_emails = df['email'].dropna().unique()[:15]
    for i, email in enumerate(unique_emails, 1):
        print(f'{i:2d}. "{email}"')
    
    print()
    print('🆔 CUSTOMER ID PATTERNS (first 15):')
    print('-' * 40)
    unique_ids = df['customer_id'].unique()[:15]
    for i, cust_id in enumerate(unique_ids, 1):
        print(f'{i:2d}. "{cust_id}"')
    
    print()
    print('🔬 TESTING CURRENT REDACTION ON SAMPLE DATA:')
    print('=' * 70)
    
    # Test current redaction on a sample
    redactor = PIIRedactor(enable_name_redaction=True)
    sample_df = df.head(10)
    
    print('📋 Sample Original Data:')
    print('-' * 40)
    for i, row in sample_df.iterrows():
        print(f"Row {i+1}:")
        print(f"  ID: {row['customer_id']}")
        print(f"  Name: {row['customer_name']}")
        print(f"  Email: {row['email']}")
        print(f"  Phone: {row['phone']}")
        print()
    
    print('🔒 After Current Redaction:')
    print('-' * 40)
    redacted_df, findings = redactor.redact_dataframe(sample_df)
    
    for i, row in redacted_df.iterrows():
        print(f"Row {i+1}:")
        print(f"  ID: {row['customer_id']}")
        print(f"  Name: {row['customer_name']}")
        print(f"  Email: {row['email']}")
        print(f"  Phone: {row['phone']}")
        print()
    
    # Identify patterns not being redacted
    print('⚠️ REDACTION GAP ANALYSIS:')
    print('=' * 70)
    
    # Check for missed patterns
    missed_patterns = []
    
    # Check names that weren't redacted
    original_names = sample_df['customer_name'].values
    redacted_names = redacted_df['customer_name'].values
    
    for orig, redacted in zip(original_names, redacted_names):
        if orig == redacted:  # Not redacted
            missed_patterns.append(('name', orig))
    
    # Check phones that weren't redacted
    original_phones = sample_df['phone'].dropna().values
    redacted_phones = redacted_df['phone'].dropna().values
    
    for orig, redacted in zip(original_phones, redacted_phones):
        if orig == redacted:  # Not redacted
            missed_patterns.append(('phone', orig))
    
    if missed_patterns:
        print('🚨 MISSED PII PATTERNS:')
        for pattern_type, value in missed_patterns:
            print(f'  {pattern_type.upper()}: "{value}"')
    else:
        print('✅ All sample patterns properly redacted')
    
    print()
    print('📊 REDACTION STATISTICS:')
    print('-' * 40)
    total_findings = sum(len(f) for f in findings.values())
    print(f'Total PII instances found: {total_findings}')
    for column, column_findings in findings.items():
        print(f'  {column}: {len(column_findings)} instances')

if __name__ == '__main__':
    analyze_redaction_gaps()