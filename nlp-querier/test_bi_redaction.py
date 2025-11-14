#!/usr/bin/env python3
"""
Test script to compare old strict redaction vs new business intelligence redaction.
This demonstrates how the new approach preserves data patterns for better BI analysis.
"""

import sys
sys.path.append('.')
from utils.enhanced_pii_redactor import EnhancedPIIRedactor, RedactionMode
from utils.pii_redactor import PIIRedactor

def compare_redaction_approaches():
    """Compare different redaction approaches on sample customer data."""
    
    print("🔍 TESTING ENHANCED PII REDACTION FOR BUSINESS INTELLIGENCE")
    print("=" * 80)
    
    # Sample customer data that would typically be passed to LLM for analysis
    sample_data = [
        {
            'customer_id': 'CUST-00001',
            'customer_name': 'Tara van de Biesenbos',
            'email': 'tara.biesenbos@gmail.com',
            'phone': '+31-20-1234567',
            'residence_country': 'NL'
        },
        {
            'customer_id': 'CUST-00002', 
            'customer_name': 'Dr. Hans Mueller',
            'email': 'hans.mueller@corporate.de',
            'phone': '+49(0)89-12345',
            'residence_country': 'DE'
        },
        {
            'customer_id': 'CUST-00003',
            'customer_name': 'Marie de la Croix',
            'email': 'marie@example.fr',
            'phone': '+33 1 23 45 67 89',
            'residence_country': 'FR'
        }
    ]
    
    print("\n📊 ORIGINAL DATA (what LLM would ideally see for patterns):")
    print("-" * 60)
    for i, record in enumerate(sample_data, 1):
        print(f"Record {i}:")
        for key, value in record.items():
            print(f"  {key}: {value}")
        print()
    
    print("\n❌ OLD STRICT REDACTION (current problematic approach):")
    print("-" * 60)
    
    # Test old strict redaction
    old_redactor = PIIRedactor(enable_name_redaction=True)
    
    for i, record in enumerate(sample_data, 1):
        print(f"Record {i} (STRICT):")
        for key, value in record.items():
            if isinstance(value, str):
                redacted_value, _ = old_redactor.redact_text(value)
                print(f"  {key}: {redacted_value}")
            else:
                print(f"  {key}: {value}")
        print()
    
    print("\n✅ NEW BUSINESS INTELLIGENCE REDACTION (pattern-preserving):")
    print("-" * 60)
    
    # Test new BI redaction
    bi_redactor = EnhancedPIIRedactor(mode=RedactionMode.BUSINESS_INTELLIGENCE, enable_name_redaction=True)
    
    for i, record in enumerate(sample_data, 1):
        print(f"Record {i} (BI MODE):")
        for key, value in record.items():
            if isinstance(value, str):
                redacted_value, _ = bi_redactor.redact_text(value)
                print(f"  {key}: {redacted_value}")
            else:
                print(f"  {key}: {value}")
        print()
    
    print("\n🎯 ANALYSIS IMPACT COMPARISON:")
    print("-" * 60)
    
    print("❌ PROBLEMS WITH STRICT REDACTION:")
    print("   • LLM sees '[NAME_REDACTED]' everywhere - loses name pattern insights")
    print("   • Email domains lost - can't analyze corporate vs personal email usage") 
    print("   • Phone format analysis impossible - all become '[PHONE_REDACTED]'")
    print("   • Customer ID patterns hidden - can't identify data quality issues")
    print("   • Geographic/cultural name analysis impossible")
    print("")
    
    print("✅ BENEFITS OF BI REDACTION:")
    print("   • Preserves name structure (titles, particles) for data quality analysis")
    print("   • Maintains email domains for business pattern recognition")
    print("   • Keeps phone format/country codes for geographic insights")
    print("   • Consistent pseudonymization allows trend analysis")
    print("   • LLM can provide meaningful business intelligence")
    print("")
    
    print("🔐 PRIVACY PROTECTION:")
    print("   • Individual identity protected through pseudonymization")
    print("   • No real names, emails, or phone numbers exposed")
    print("   • Consistent hashing ensures same person = same pseudonym")
    print("   • Business patterns preserved for valid analysis")
    
    # Show redaction statistics
    print(f"\n📊 REDACTION CACHE STATISTICS:")
    stats = bi_redactor.get_stats()
    for stat_name, count in stats.items():
        print(f"   • {stat_name}: {count}")

if __name__ == "__main__":
    compare_redaction_approaches()