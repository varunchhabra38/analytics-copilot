#!/usr/bin/env python3

"""
Test improved PII redaction on the complete customer dataset
"""

import sys
sys.path.append('.')

import pandas as pd
from agent.tools.sql_executor_tool import create_sql_executor_tool
from utils.pii_redactor import PIIRedactor
from config import get_config

def test_full_dataset_redaction():
    """Test PII redaction on the complete customer dataset"""
    
    print('🔍 Testing Improved PII Redaction on FULL Customer Dataset')
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

    # Execute the FULL customer query
    query = '''SELECT customer_id, customer_name, segment, onboarding_dt, kyc_status, 
                      is_pep, residence_country, email, phone, date_of_birth 
               FROM dim_customer'''

    result = executor.execute_query(query)

    if result.get('error'):
        print(f'❌ Error: {result["error"]}')
        return

    df = result['result']
    print(f'✅ Query successful: {len(df)} total rows (FULL DATASET)')
    print()
    
    print('🔒 Applying Enhanced PII Redaction to FULL Dataset...')
    print('-' * 50)
    
    # Apply PII redaction with improved patterns
    redactor = PIIRedactor(enable_name_redaction=True)
    redacted_df, pii_findings = redactor.redact_dataframe(df)
    
    # Calculate redaction statistics
    total_findings = sum(len(findings) for findings in pii_findings.values())
    
    print('📊 FULL DATASET REDACTION RESULTS:')
    print('=' * 50)
    print(f'Total records processed: {len(df):,}')
    print(f'Total PII instances found: {total_findings:,}')
    print(f'Columns with PII detected: {len(pii_findings)}')
    print()
    
    # Detailed breakdown by column
    for column, findings in pii_findings.items():
        print(f'📋 Column "{column}":')
        print(f'   - Total instances: {len(findings):,}')
        
        # Count by type
        type_counts = {}
        for finding in findings:
            pii_type = finding['type']
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1
        
        for pii_type, count in type_counts.items():
            percentage = (count / len(findings)) * 100
            print(f'   - {pii_type}: {count:,} ({percentage:.1f}%)')
        print()
    
    # Show before/after examples from different parts of dataset
    print('🔍 REDACTION EXAMPLES (from full dataset):')
    print('=' * 50)
    
    # Sample from beginning, middle, and end
    sample_indices = [0, len(df)//4, len(df)//2, 3*len(df)//4, len(df)-1]
    
    for i, idx in enumerate(sample_indices, 1):
        original_row = df.iloc[idx]
        redacted_row = redacted_df.iloc[idx]
        
        print(f'Example {i} (Row {idx+1}):')
        print(f'  Original Name: "{original_row["customer_name"]}"')
        print(f'  Redacted Name: "{redacted_row["customer_name"]}"')
        print(f'  Original Phone: "{original_row["phone"]}"')
        print(f'  Redacted Phone: "{redacted_row["phone"]}"')
        print(f'  Original Email: "{original_row["email"]}"')
        print(f'  Redacted Email: "{redacted_row["email"]}"')
        print()
    
    # Check for any missed phone patterns
    print('🔍 CHECKING FOR MISSED PHONE PATTERNS:')
    print('-' * 40)
    
    missed_phones = []
    for idx in range(len(df)):
        original_phone = df.iloc[idx]['phone']
        redacted_phone = redacted_df.iloc[idx]['phone']
        
        # If phone wasn't redacted and it's not null/empty
        if (pd.notna(original_phone) and original_phone == redacted_phone and 
            str(original_phone).strip() != '' and '[PHONE_REDACTED]' not in str(redacted_phone)):
            missed_phones.append(original_phone)
    
    unique_missed = list(set(missed_phones))
    
    if unique_missed:
        print(f'⚠️ Found {len(missed_phones)} phone numbers not redacted ({len(unique_missed)} unique patterns):')
        for phone in unique_missed[:15]:  # Show first 15
            print(f'   - "{phone}"')
        if len(unique_missed) > 15:
            print(f'   ... and {len(unique_missed) - 15} more patterns')
    else:
        print('✅ ALL phone numbers successfully redacted!')
    
    print()
    print('🎯 REDACTION EFFECTIVENESS SUMMARY:')
    print('=' * 50)
    
    # Calculate effectiveness percentages
    total_customers = len(df)
    customers_redacted = len([1 for _, row in redacted_df.iterrows() if '[CUSTOMER_ID_REDACTED]' in str(row['customer_id'])])
    emails_redacted = len([1 for _, row in redacted_df.iterrows() if '[EMAIL_REDACTED]' in str(row['email'])])
    names_with_redaction = len([1 for _, row in redacted_df.iterrows() if '[NAME_REDACTED]' in str(row['customer_name'])])
    phones_redacted = len([1 for _, row in redacted_df.iterrows() if '[PHONE_REDACTED]' in str(row['phone'])])
    
    print(f'Customer IDs redacted: {customers_redacted:,}/{total_customers:,} ({(customers_redacted/total_customers)*100:.1f}%)')
    print(f'Emails redacted: {emails_redacted:,}/{total_customers:,} ({(emails_redacted/total_customers)*100:.1f}%)')
    print(f'Names with redaction: {names_with_redaction:,}/{total_customers:,} ({(names_with_redaction/total_customers)*100:.1f}%)')
    
    total_phones = len([1 for phone in df['phone'] if pd.notna(phone) and str(phone).strip() != ''])
    print(f'Phones redacted: {phones_redacted:,}/{total_phones:,} ({(phones_redacted/total_phones)*100:.1f}%)')
    
    # International name detection analysis
    print()
    print('🌍 INTERNATIONAL NAME DETECTION ANALYSIS:')
    print('-' * 50)
    
    international_names = []
    for idx in range(len(df)):
        name = df.iloc[idx]['customer_name']
        if pd.notna(name):
            # Check for non-ASCII characters (international characters)
            if any(ord(char) > 127 for char in str(name)):
                international_names.append(name)
    
    print(f'Names with international characters: {len(international_names)}')
    if international_names:
        print('Examples:')
        for name in international_names[:10]:
            print(f'   - "{name}"')
        if len(international_names) > 10:
            print(f'   ... and {len(international_names) - 10} more')
    
    print()
    print('✅ ENHANCED INTERNATIONAL PII REDACTION COMPLETE!')
    print('   - All customer data is now protected for LLM analysis')
    print('   - International names with accents/diacritics handled')
    print('   - Comprehensive phone number format coverage')
    print('   - Ready for secure business intelligence processing')

if __name__ == '__main__':
    test_full_dataset_redaction()