#!/usr/bin/env python3

"""
Test improved phone number redaction patterns
"""

import sys
sys.path.append('.')

from utils.pii_redactor import PIIRedactor

def test_improved_phone_redaction():
    """Test the improved phone number redaction patterns"""
    
    print('🔍 Testing Improved Phone Number Redaction')
    print('=' * 70)

    # Phone patterns that were previously missed
    test_phones = [
        '+49(0) 890838637',        # German with space
        '+49(0)6475 255341',       # German without space
        '04 20 13 95 37',          # French local
        '+3132-8710122',           # Dutch
        '+1-357-901-5430x391',     # US with extension
        '334.373.8299x73763',      # US with dots and extension
        '361-855-9407',            # Basic US format
        '+49(0)6578 71331',        # German variation
        '0247462704',              # Local number
        '+33 (0)4 57 12 41 18',    # French with country code
        '(037) 5433036',           # Parentheses format
        '443-369-9577x7387',       # US with extension
    ]

    redactor = PIIRedactor(enable_name_redaction=True)

    print('📞 Testing Individual Phone Patterns:')
    print('-' * 50)
    
    for i, phone in enumerate(test_phones, 1):
        test_text = f'Contact customer at {phone} for verification'
        redacted, findings = redactor.redact_text(test_text)
        
        phone_redacted = phone not in redacted
        status = '✅ REDACTED' if phone_redacted else '❌ MISSED'
        
        print(f'{i:2d}. {status} "{phone}"')
        if phone_redacted and findings:
            detected_types = [f['type'] for f in findings if f['type'].startswith('phone')]
            print(f'     → Detected as: {", ".join(set(detected_types))}')
        elif not phone_redacted:
            print(f'     → Original: {test_text}')
            print(f'     → Result:   {redacted}')
    
    print()
    print('🧪 Testing Sample Customer Data:')
    print('-' * 50)
    
    # Sample customer data with problematic patterns
    sample_data = [
        {'name': 'Hans Mueller', 'phone': '+49(0) 890838637', 'email': 'hans@test.com'},
        {'name': 'Marie Dubois', 'phone': '04 20 13 95 37', 'email': 'marie@test.fr'},
        {'name': 'John Smith', 'phone': '+1-357-901-5430x391', 'email': 'john@test.us'},
        {'name': 'Maurizio Müller', 'phone': '334.373.8299x73763', 'email': 'maurizio@test.it'},
        {'name': 'Françoise Le Pen', 'phone': '+33 (0)4 57 12 41 18', 'email': 'francoise@test.fr'},
    ]
    
    for i, customer in enumerate(sample_data, 1):
        customer_text = f"Customer: {customer['name']}, Phone: {customer['phone']}, Email: {customer['email']}"
        redacted_text, findings = redactor.redact_text(customer_text)
        
        print(f'Customer {i}:')
        print(f'  Original: {customer_text}')
        print(f'  Redacted: {redacted_text}')
        
        # Count findings by type
        finding_types = {}
        for finding in findings:
            finding_types[finding['type']] = finding_types.get(finding['type'], 0) + 1
        
        print(f'  Findings: {dict(finding_types)}')
        print()
    
    print('📊 Redaction Effectiveness Summary:')
    print('-' * 50)
    
    total_tests = len(test_phones)
    successful = 0
    
    for phone in test_phones:
        test_text = f'Call {phone} now'
        redacted, _ = redactor.redact_text(test_text)
        if phone not in redacted:
            successful += 1
    
    effectiveness = (successful / total_tests) * 100
    print(f'Phone Redaction Success Rate: {successful}/{total_tests} ({effectiveness:.1f}%)')
    
    if effectiveness == 100:
        print('🎉 All phone patterns successfully redacted!')
    elif effectiveness >= 90:
        print('✅ Excellent redaction coverage!')
    elif effectiveness >= 80:
        print('⚠️ Good coverage, some patterns may need refinement')
    else:
        print('❌ Redaction gaps remain, patterns need improvement')

if __name__ == '__main__':
    test_improved_phone_redaction()