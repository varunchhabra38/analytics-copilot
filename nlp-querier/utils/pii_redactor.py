#!/usr/bin/env python3

"""
PII Redaction Utility for Analytics Agent

This module provides comprehensive PII detection and redaction capabilities
to protect sensitive information in query results and business interpretations.
"""

import re
import pandas as pd
import logging
from typing import Dict, List, Any, Union, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PIIPattern:
    """Represents a PII pattern with detection regex and replacement."""
    name: str
    pattern: re.Pattern
    replacement: str
    description: str

class PIIRedactor:
    """
    Comprehensive PII detection and redaction system.
    
    Detects and redacts common PII types including:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - Account numbers
    - Customer IDs
    - Names (configurable)
    - Social Security Numbers
    - IP addresses
    """
    
    def __init__(self, enable_name_redaction: bool = False):
        self.enable_name_redaction = enable_name_redaction
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize PII detection patterns."""
        self.patterns = [
            PIIPattern(
                name="email",
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement="[EMAIL_REDACTED]",
                description="Email addresses"
            ),
            PIIPattern(
                name="phone_international",
                pattern=re.compile(r'\+\d{1,4}\s?\(?\d+\)?[\s\-\.]?\d+[\s\-\.]?\d+(?:x\d+)?\b'),
                replacement="[PHONE_REDACTED]",
                description="International phone numbers with country codes"
            ),
            PIIPattern(
                name="phone_german",
                pattern=re.compile(r'\+49\(0\)[\s\d]+|\b0[1-9][\d\s]{7,}\b'),
                replacement="[PHONE_REDACTED]",
                description="German phone number formats"
            ),
            PIIPattern(
                name="phone_us_extensions",
                pattern=re.compile(r'\b\d{3}[\-\.]\d{3}[\-\.]\d{4}x\d+\b'),
                replacement="[PHONE_REDACTED]",
                description="US phone numbers with extensions"
            ),
            PIIPattern(
                name="phone_french",
                pattern=re.compile(r'\+33\s?\(0\)\d+\s?\d+\s?\d+\s?\d+\s?\d+'),
                replacement="[PHONE_REDACTED]",
                description="French phone number formats"
            ),
            PIIPattern(
                name="phone_german_area_codes",
                pattern=re.compile(r'\(\d{4,6}\)\s?\d{6,8}|\b0\d{4,5}[\s\-]?\d{5,7}\b'),
                replacement="[PHONE_REDACTED]",
                description="German area codes with parentheses and local numbers"
            ),
            PIIPattern(
                name="phone_european",
                pattern=re.compile(r'\(\d{3,5}\)\s?\d{6,8}\b'),
                replacement="[PHONE_REDACTED]",
                description="European phone number formats with parentheses"
            ),
            PIIPattern(
                name="phone_basic",
                pattern=re.compile(r'\b(?:\+?1[-\.\s]?)?\(?[0-9]{3}\)?[-\.\s]?[0-9]{3}[-\.\s]?[0-9]{4}\b'),
                replacement="[PHONE_REDACTED]",
                description="Basic phone numbers (fallback)"
            ),
            PIIPattern(
                name="credit_card",
                pattern=re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
                replacement="[CARD_REDACTED]",
                description="Credit card numbers"
            ),
            PIIPattern(
                name="ssn",
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                replacement="[SSN_REDACTED]",
                description="Social Security Numbers"
            ),
            PIIPattern(
                name="account_number",
                pattern=re.compile(r'\b(?:ACC|ACCT|ACCOUNT)[\s\-_]?[0-9]{3,12}\b', re.IGNORECASE),
                replacement="[ACCOUNT_REDACTED]",
                description="Account numbers"
            ),
            PIIPattern(
                name="standalone_account_id",
                pattern=re.compile(r'\bACC[\-_][0-9]{3,6}\b', re.IGNORECASE), 
                replacement="[ACCOUNT_REDACTED]",
                description="Standalone account IDs"
            ),
            PIIPattern(
                name="customer_id",
                pattern=re.compile(r'\b(?:CUST|CID|CUSTOMER)[\s\-_]?[0-9A-Z]{3,12}\b', re.IGNORECASE),
                replacement="[CUSTOMER_ID_REDACTED]",
                description="Customer IDs"
            ),
            PIIPattern(
                name="standalone_customer_id", 
                pattern=re.compile(r'\bCUST[\-_][0-9]{3,6}\b', re.IGNORECASE),
                replacement="[CUSTOMER_ID_REDACTED]",
                description="Standalone customer IDs"
            ),
            PIIPattern(
                name="ip_address",
                pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
                replacement="[IP_REDACTED]",
                description="IP addresses"
            )
        ]
        
        # Add name patterns if enabled
        if self.enable_name_redaction:
            self.patterns.extend([
                PIIPattern(
                    name="dutch_particle_names",
                    pattern=re.compile(r'\b[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+'
                                      r'(?:[-\s]?[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)*\s+'
                                      r'(?:van\s+de|van\s+der|van\s+den|van\s+|de\s+la|de\s+|du\s+|von\s+der|von\s+|d\'|della\s+|del\s+|di\s+|da\s+)\s*'
                                      r'[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+'
                                      r'(?:\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)*\b', re.UNICODE | re.IGNORECASE),
                    replacement="[NAME_REDACTED]",
                    description="Dutch/European names with particles (van de, van der, de la, du, von, etc.)"
                ),
                PIIPattern(
                    name="hyphenated_names",
                    pattern=re.compile(r'\b[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+-[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+\b', re.UNICODE),
                    replacement="[NAME_REDACTED]",
                    description="Hyphenated first names with last names (e.g., Jean-Pierre Dubois)"
                ),
                PIIPattern(
                    name="full_name_extended", 
                    pattern=re.compile(r'\b[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+(?:\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)?\b', re.UNICODE),
                    replacement="[NAME_REDACTED]",
                    description="Full names with international characters (Latin Extended, diacritics)"
                ),
                PIIPattern(
                    name="cyrillic_names",
                    pattern=re.compile(r'\b[\u0410-\u042F][\u0430-\u044F]+\s+[\u0410-\u042F][\u0430-\u044F]+(?:\s+[\u0410-\u042F][\u0430-\u044F]+)?\b', re.UNICODE),
                    replacement="[NAME_REDACTED]",
                    description="Cyrillic names (Russian, Bulgarian, etc.)"
                ),
                PIIPattern(
                    name="basic_names",
                    pattern=re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'),
                    replacement="[NAME_REDACTED]",
                    description="Basic English names (fallback)"
                )
            ])
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text and return findings.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of PII findings with type, value, and position
        """
        findings = []
        
        for pattern in self.patterns:
            matches = pattern.pattern.finditer(text)
            for match in matches:
                findings.append({
                    "type": pattern.name,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "description": pattern.description
                })
        
        return findings
    
    def _is_business_term(self, finding: Dict[str, Any]) -> bool:
        """
        Check if a detected name is actually a business term that should not be redacted.
        
        Args:
            finding: PII finding to check
            
        Returns:
            True if this is a business term, False if it's a real name
        """
        value = finding.get('value', '').lower()
        
        # Business terms that commonly get mistaken for names
        business_terms = {
            'customer', 'client', 'contact', 'account', 'invoice', 
            'payment', 'transfer', 'transaction', 'holder', 'user',
            'person', 'individual', 'entity', 'company', 'business',
            'call', 'meet', 'contact'
        }
        
        # Check if any word in the finding matches business terms
        words = value.split()
        for word in words:
            if word.strip().lower() in business_terms:
                return True
                
        return False
    
    def _remove_overlapping_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove overlapping PII findings, keeping the most specific/longest match.
        
        Args:
            findings: List of PII findings
            
        Returns:
            Filtered list without overlaps
        """
        if not findings:
            return findings
            
        # Sort by start position, then by length (longest first)
        findings.sort(key=lambda x: (x['start'], -(x['end'] - x['start'])))
        
        non_overlapping = []
        for finding in findings:
            # Check if this finding overlaps with any already accepted finding
            overlaps = False
            for accepted in non_overlapping:
                # Check for overlap
                if (finding['start'] < accepted['end'] and finding['end'] > accepted['start']):
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(finding)
        
        return non_overlapping

    def redact_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact PII from
            
        Returns:
            Tuple of (redacted_text, pii_findings)
        """
        if not isinstance(text, str):
            return str(text), []
        
        findings = self.detect_pii(text)
        
        # Filter out business terms for name patterns
        filtered_findings = []
        for finding in findings:
            if finding['type'] in ['full_name_extended', 'basic_names', 'hyphenated_names']:
                if not self._is_business_term(finding):
                    filtered_findings.append(finding)
            elif finding['type'].startswith('phone_'):
                # Only keep phone findings that look like actual phone numbers
                value = finding.get('value', '')
                # Skip if it's obviously not a phone number (need at least 7 digits)
                digit_count = len([c for c in value if c.isdigit()])
                if digit_count >= 7:
                    filtered_findings.append(finding)
            else:
                # Keep all other non-name findings
                filtered_findings.append(finding)
        
        # Remove overlapping findings to avoid double redaction
        filtered_findings = self._remove_overlapping_findings(filtered_findings)
        
        redacted_text = text
        
        # Sort findings by position (reverse order to avoid index shifting)
        filtered_findings.sort(key=lambda x: x['start'], reverse=True)
        
        for finding in filtered_findings:
            pattern = next(p for p in self.patterns if p.name == finding['type'])
            redacted_text = redacted_text[:finding['start']] + pattern.replacement + redacted_text[finding['end']:]
        
        return redacted_text, filtered_findings
    
    def redact_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[Dict[str, Any]]]]:
        """
        Redact PII from DataFrame.
        
        Args:
            df: DataFrame to redact PII from
            
        Returns:
            Tuple of (redacted_dataframe, pii_findings_by_column)
        """
        if df.empty:
            return df.copy(), {}
        
        redacted_df = df.copy()
        all_findings = {}
        
        for column in df.columns:
            if df[column].dtype == 'object':  # String columns
                column_findings = []
                
                for idx, value in df[column].items():
                    if pd.notna(value) and isinstance(value, str):
                        redacted_value, findings = self.redact_text(str(value))
                        if findings:
                            redacted_df.at[idx, column] = redacted_value
                            column_findings.extend([
                                {**finding, "row_index": idx, "original_value": value}
                                for finding in findings
                            ])
                
                if column_findings:
                    all_findings[column] = column_findings
        
        return redacted_df, all_findings
    
    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        """
        Redact PII from dictionary.
        
        Args:
            data: Dictionary to redact PII from
            
        Returns:
            Tuple of (redacted_dict, pii_findings_by_key)
        """
        redacted_data = {}
        all_findings = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_value, findings = self.redact_text(value)
                redacted_data[key] = redacted_value
                if findings:
                    all_findings[key] = findings
            elif isinstance(value, dict):
                redacted_value, nested_findings = self.redact_dict(value)
                redacted_data[key] = redacted_value
                if nested_findings:
                    all_findings[f"{key}_nested"] = nested_findings
            elif isinstance(value, list):
                redacted_value, list_findings = self.redact_list(value)
                redacted_data[key] = redacted_value
                if list_findings:
                    all_findings[f"{key}_list"] = list_findings
            else:
                redacted_data[key] = value
        
        return redacted_data, all_findings
    
    def redact_list(self, data: List[Any]) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """
        Redact PII from list.
        
        Args:
            data: List to redact PII from
            
        Returns:
            Tuple of (redacted_list, pii_findings)
        """
        redacted_data = []
        all_findings = []
        
        for idx, item in enumerate(data):
            if isinstance(item, str):
                redacted_item, findings = self.redact_text(item)
                redacted_data.append(redacted_item)
                for finding in findings:
                    finding["list_index"] = idx
                    all_findings.append(finding)
            elif isinstance(item, dict):
                redacted_item, dict_findings = self.redact_dict(item)
                redacted_data.append(redacted_item)
                for key, findings in dict_findings.items():
                    for finding in findings:
                        finding["list_index"] = idx
                        finding["dict_key"] = key
                        all_findings.append(finding)
            else:
                redacted_data.append(item)
        
        return redacted_data, all_findings
    
    def generate_pii_report(self, findings: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate a summary report of PII findings.
        
        Args:
            findings: PII findings dictionary
            
        Returns:
            Formatted PII report string
        """
        if not findings:
            return "✅ No PII detected in the data."
        
        report = "🔒 PII DETECTION REPORT\n"
        report += "=" * 50 + "\n\n"
        
        total_findings = sum(len(finding_list) for finding_list in findings.values())
        report += f"🚨 Total PII instances found: {total_findings}\n\n"
        
        for location, finding_list in findings.items():
            report += f"📍 Location: {location}\n"
            pii_types = {}
            for finding in finding_list:
                pii_type = finding['type']
                if pii_type not in pii_types:
                    pii_types[pii_type] = 0
                pii_types[pii_type] += 1
            
            for pii_type, count in pii_types.items():
                report += f"  - {pii_type}: {count} instance(s)\n"
            report += "\n"
        
        report += "🔒 All detected PII has been redacted for security.\n"
        return report

# Global PII redactor instance
_global_redactor = None

def get_pii_redactor(enable_name_redaction: bool = False) -> PIIRedactor:
    """Get global PII redactor instance."""
    global _global_redactor
    if _global_redactor is None or _global_redactor.enable_name_redaction != enable_name_redaction:
        _global_redactor = PIIRedactor(enable_name_redaction=enable_name_redaction)
    return _global_redactor

def redact_pii_from_text(text: str, enable_name_redaction: bool = False) -> str:
    """Quick function to redact PII from text."""
    redactor = get_pii_redactor(enable_name_redaction)
    redacted_text, _ = redactor.redact_text(text)
    return redacted_text

def redact_pii_from_dataframe(df: pd.DataFrame, enable_name_redaction: bool = False) -> pd.DataFrame:
    """Quick function to redact PII from DataFrame."""
    redactor = get_pii_redactor(enable_name_redaction)
    redacted_df, _ = redactor.redact_dataframe(df)
    return redacted_df