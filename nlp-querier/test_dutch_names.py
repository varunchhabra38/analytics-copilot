#!/usr/bin/env python3
"""Test script for Dutch/European names with particles"""

import sys
sys.path.append('.')
from utils.pii_redactor import PIIRedactor

def test_dutch_names():
    """Test Dutch and European names with particles like van de, van der, etc."""
    
    # Test the specific name that's not being redacted
    test_name = 'Tara van de Biesenbos'
    print(f'Testing specific name: "{test_name}"')

    redactor = PIIRedactor(enable_name_redaction=True)
    redacted_text, findings = redactor.redact_text(f'Customer: {test_name}')

    print(f'Original: Customer: {test_name}')
    print(f'Redacted: {redacted_text}')
    print(f'Findings: {len(findings)}')

    for finding in findings:
        print(f'  - {finding["type"]}: "{finding["value"]}"')

    # Test other Dutch names with particles
    dutch_names = [
        'Tara van de Biesenbos',
        'Rosa van der Veen', 
        'Jan van der Berg',
        'Marie de la Croix',
        'Pierre du Pont',
        'Anna von Schmidt',
        'Jean-Claude van Damme',
        'Vincent van Gogh',
        'Willem-Alexander van Oranje'
    ]

    print()
    print('Testing Dutch/European name particles:')
    print('-' * 50)
    
    missed_names = []
    for name in dutch_names:
        test_text = f'Contact {name} today'
        redacted, findings = redactor.redact_text(test_text)
        
        name_redacted = name not in redacted
        status = '✅ REDACTED' if name_redacted else '❌ MISSED'
        print(f'{status} "{name}"')
        
        if not name_redacted:
            missed_names.append(name)
            print(f'   Result: {redacted}')
    
    print()
    print(f'Summary: {len(missed_names)} out of {len(dutch_names)} names were missed')
    
    if missed_names:
        print('Missed names:')
        for name in missed_names:
            print(f'  - {name}')
    
    return missed_names

if __name__ == "__main__":
    test_dutch_names()