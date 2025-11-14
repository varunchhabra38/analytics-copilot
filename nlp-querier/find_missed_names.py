#!/usr/bin/env python3
"""Find the specific names that are still not being redacted"""

import sys
sys.path.append('.')
from utils.pii_redactor import PIIRedactor
from utils.db import DatabaseManager

def find_missed_names():
    """Find which specific names are not being redacted."""
    
    # Get all customer data
    db = DatabaseManager()
    query = "SELECT customer_name FROM dim_customer"
    result = db.execute_query(query)
    
    redactor = PIIRedactor(enable_name_redaction=True)
    
    print("🔍 Finding names that are still not being redacted...")
    print("=" * 60)
    
    missed_names = []
    total_names = 0
    
    for row in result:
        if row and row[0]:
            name = row[0]
            total_names += 1
            
            # Test if this name gets redacted
            test_text = f"Customer: {name}"
            redacted_text, findings = redactor.redact_text(test_text)
            
            # Check if name is still in the redacted text (not caught)
            if name in redacted_text:
                missed_names.append(name)
                print(f"❌ MISSED: '{name}'")
                print(f"   Result: {redacted_text}")
                
                # Show what patterns DID match
                if findings:
                    print("   Findings found:")
                    for finding in findings:
                        print(f"     - {finding['type']}: '{finding['value']}'")
                else:
                    print("   No patterns matched this name")
                print()
    
    print(f"\n📊 SUMMARY:")
    print(f"Total names tested: {total_names}")
    print(f"Names successfully redacted: {total_names - len(missed_names)}")
    print(f"Names missed: {len(missed_names)}")
    print(f"Redaction rate: {((total_names - len(missed_names)) / total_names * 100):.1f}%")
    
    return missed_names

if __name__ == "__main__":
    find_missed_names()