#!/usr/bin/env python3

"""
Test international name detection with enhanced PII redactor
"""

import sys
sys.path.append('.')

from utils.pii_redactor import PIIRedactor

def test_international_names():
    """Test PII redactor with various international names"""
    
    print('Testing enhanced PII redactor with international names...')
    print('=' * 60)

    # Test with various international names
    test_cases = [
        'José García has email jose.garcia@test.com',           # Spanish with accent
        'François Müller works here',                           # French/German mix  
        'Contact Åse Björk for details',                        # Scandinavian
        'Client: Николай Петров',                               # Cyrillic (Russian)
        'Customer María José Fernández called',                 # Spanish with accents
        'Meet with Jean-Pierre Dubois tomorrow',               # Hyphenated French
        'Call Ümit Özkan at the office',                      # Turkish
        'Søren Kjær is the contact person',                    # Danish
        'Invoice for Péter Nagy',                              # Hungarian
        'Account holder: Łukasz Kowalski'                      # Polish
    ]

    redactor = PIIRedactor(enable_name_redaction=True)

    for i, test_text in enumerate(test_cases, 1):
        print(f'Test {i:2d}: {test_text}')
        redacted, findings = redactor.redact_text(test_text)
        print(f'Result:  {redacted}')
        if findings:
            print(f'Found:   {len(findings)} PII instances')
            for finding in findings:
                print(f'         - {finding["type"]}: "{finding["value"]}"')
        else:
            print(f'Found:   No PII detected')
        print()

if __name__ == '__main__':
    test_international_names()