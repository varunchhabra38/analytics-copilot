#!/usr/bin/env python3
"""
Enhanced PII Redactor with Business Intelligence Mode

This module provides different levels of PII protection:
1. STRICT: Complete redaction for maximum privacy
2. BUSINESS_INTELLIGENCE: Pattern-preserving pseudonymization for BI analysis
3. DEVELOPMENT: Minimal redaction for testing

For BI mode, we preserve data patterns while protecting individual privacy:
- Names: Convert to consistent pseudonyms (e.g., "John Smith" -> "Customer_A001") 
- Emails: Domain analysis preserved (e.g., "john@gmail.com" -> "user001@gmail.com")
- Phones: Country/format preserved (e.g., "+49 123 456" -> "+49 xxx xxx")
- Customer IDs: Consistent pseudonymization
"""

import re
import logging
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum

class RedactionMode(Enum):
    """Redaction modes with different privacy/utility trade-offs."""
    STRICT = "strict"                    # Maximum privacy, minimal utility
    BUSINESS_INTELLIGENCE = "business_intelligence"  # Balanced privacy/utility for BI
    DEVELOPMENT = "development"          # Minimal privacy for testing

@dataclass
class PIIPattern:
    """Pattern definition for PII detection and redaction."""
    name: str
    pattern: re.Pattern
    replacement: str
    description: str
    strict_replacement: Optional[str] = None  # Override for strict mode
    bi_replacement: Optional[str] = None      # Override for BI mode

class EnhancedPIIRedactor:
    """
    Enhanced PII redactor with configurable modes for different use cases.
    
    Key Features:
    - Multiple redaction modes (STRICT, BUSINESS_INTELLIGENCE, DEVELOPMENT)
    - Pattern-preserving pseudonymization for business intelligence
    - Consistent pseudonym generation using hashing
    - Domain/format preservation where business-relevant
    """
    
    def __init__(self, mode: RedactionMode = RedactionMode.BUSINESS_INTELLIGENCE, enable_name_redaction: bool = True):
        self.mode = mode
        self.enable_name_redaction = enable_name_redaction
        self.logger = logging.getLogger(__name__)
        
        # Caches for consistent pseudonymization
        self._name_cache: Dict[str, str] = {}
        self._email_cache: Dict[str, str] = {}
        self._customer_id_cache: Dict[str, str] = {}
        self._phone_cache: Dict[str, str] = {}
        
        self._initialize_patterns()
    
    def _generate_pseudonym(self, value: str, prefix: str, cache: Dict[str, str]) -> str:
        """Generate consistent pseudonym using hash-based approach."""
        if value in cache:
            return cache[value]
        
        # Use hash for consistency across sessions
        hash_val = hashlib.sha256(value.encode()).hexdigest()[:8]
        pseudonym = f"{prefix}_{hash_val}"
        cache[value] = pseudonym
        return pseudonym
    
    def _preserve_email_domain(self, email: str) -> str:
        """Preserve email domain for business intelligence while protecting identity."""
        if self.mode == RedactionMode.STRICT:
            return "[EMAIL_REDACTED]"
        elif self.mode == RedactionMode.DEVELOPMENT:
            return email  # Keep original for testing
        else:  # BUSINESS_INTELLIGENCE
            if email in self._email_cache:
                return self._email_cache[email]
            
            try:
                local, domain = email.split('@')
                pseudonym_local = self._generate_pseudonym(local, "user", {})
                result = f"{pseudonym_local}@{domain}"
                self._email_cache[email] = result
                return result
            except:
                return "[EMAIL_INVALID]"
    
    def _preserve_phone_pattern(self, phone: str) -> str:
        """Preserve phone format/country while protecting individual numbers."""
        if self.mode == RedactionMode.STRICT:
            return "[PHONE_REDACTED]"
        elif self.mode == RedactionMode.DEVELOPMENT:
            return phone  # Keep original for testing
        else:  # BUSINESS_INTELLIGENCE
            if phone in self._phone_cache:
                return self._phone_cache[phone]
            
            # Preserve country codes and format structure
            if phone.startswith('+'):
                # International format: +49 123 456789 -> +49 XXX XXXXXX
                country_match = re.match(r'(\+\d{1,4})(.+)', phone)
                if country_match:
                    country_code = country_match.group(1)
                    rest = country_match.group(2)
                    # Replace digits with X but keep formatting
                    masked = re.sub(r'\d', 'X', rest)
                    result = f"{country_code}{masked}"
                    self._phone_cache[phone] = result
                    return result
            
            # Default: replace digits with X
            result = re.sub(r'\d', 'X', phone)
            self._phone_cache[phone] = result
            return result
    
    def _preserve_name_pattern(self, name: str) -> str:
        """Preserve name structure for business intelligence (titles, particles, etc.)."""
        if self.mode == RedactionMode.STRICT:
            return "[NAME_REDACTED]"
        elif self.mode == RedactionMode.DEVELOPMENT:
            return name  # Keep original for testing
        else:  # BUSINESS_INTELLIGENCE
            if name in self._name_cache:
                return self._name_cache[name]
            
            # Extract and preserve titles and particles
            title_pattern = r'^(Dr\.|Prof\.|Dipl\.-Ing\.|Ing\.|Univ\.Prof\.|B\.Sc\.|M\.Sc\.|Ph\.D\.|Mr\.|Mrs\.|Ms\.)\s*'
            particle_pattern = r'\b(van\s+de|van\s+der|van\s+den|van\s+|de\s+la|de\s+|du\s+|von\s+der|von\s+|d\'|della\s+|del\s+|di\s+|da\s+)\b'
            
            # Extract title
            title_match = re.match(title_pattern, name, re.IGNORECASE)
            title = title_match.group(1) + " " if title_match else ""
            name_without_title = re.sub(title_pattern, "", name, flags=re.IGNORECASE).strip()
            
            # Generate pseudonym for the core name part
            core_pseudonym = self._generate_pseudonym(name_without_title, "Customer", {})
            
            # Preserve particles if present
            if re.search(particle_pattern, name_without_title, re.IGNORECASE):
                # Complex name with particles - preserve structure
                parts = re.split(r'\s+', name_without_title)
                preserved_parts = []
                for part in parts:
                    if re.match(particle_pattern, part, re.IGNORECASE):
                        preserved_parts.append(part)  # Keep particle
                    elif len(part) > 2 and part.isalpha():
                        preserved_parts.append("Surname")  # Replace name parts
                    else:
                        preserved_parts.append(part)  # Keep short/special parts
                
                result = f"{title}{' '.join(preserved_parts)}"
            else:
                result = f"{title}{core_pseudonym}"
            
            self._name_cache[name] = result
            return result
    
    def _preserve_customer_id(self, customer_id: str) -> str:
        """Generate consistent customer ID pseudonym."""
        if self.mode == RedactionMode.STRICT:
            return "[CUSTOMER_ID_REDACTED]"
        elif self.mode == RedactionMode.DEVELOPMENT:
            return customer_id  # Keep original for testing
        else:  # BUSINESS_INTELLIGENCE
            return self._generate_pseudonym(customer_id, "CUST", self._customer_id_cache)
    
    def _initialize_patterns(self) -> None:
        """Initialize PII detection patterns with mode-specific replacements."""
        self.patterns = [
            PIIPattern(
                name="email",
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement="[EMAIL_REDACTED]",
                description="Email addresses",
                bi_replacement="PRESERVE_DOMAIN"  # Special flag for custom processing
            ),
            PIIPattern(
                name="customer_id",
                pattern=re.compile(r'\bCUST-\d{5}\b'),
                replacement="[CUSTOMER_ID_REDACTED]",
                description="Customer ID patterns",
                bi_replacement="PRESERVE_PATTERN"
            ),
            PIIPattern(
                name="phone_international",
                pattern=re.compile(r'\+\d{1,4}\s?\(?\d+\)?[\s\-\.]?\d+[\s\-\.]?\d+(?:x\d+)?\b'),
                replacement="[PHONE_REDACTED]",
                description="International phone numbers",
                bi_replacement="PRESERVE_FORMAT"
            ),
            PIIPattern(
                name="phone_german",
                pattern=re.compile(r'\+49\(0\)[\s\d]+|\b0[1-9][\d\s]{7,}\b'),
                replacement="[PHONE_REDACTED]",
                description="German phone numbers",
                bi_replacement="PRESERVE_FORMAT"
            ),
            PIIPattern(
                name="phone_basic",
                pattern=re.compile(r'\b\d{3}[\-\.]\d{3}[\-\.]\d{4}\b'),
                replacement="[PHONE_REDACTED]",
                description="Basic phone format",
                bi_replacement="PRESERVE_FORMAT"
            ),
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
                    description="Dutch/European names with particles",
                    bi_replacement="PRESERVE_STRUCTURE"
                ),
                PIIPattern(
                    name="full_name_extended", 
                    pattern=re.compile(r'\b[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+(?:\s+[A-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zà-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)?\b', re.UNICODE),
                    replacement="[NAME_REDACTED]",
                    description="Full names with international characters",
                    bi_replacement="PRESERVE_STRUCTURE"
                ),
                PIIPattern(
                    name="basic_names",
                    pattern=re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'),
                    replacement="[NAME_REDACTED]",
                    description="Basic English names",
                    bi_replacement="PRESERVE_STRUCTURE"
                )
            ])
    
    def redact_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redact PII from text according to the configured mode.
        
        Args:
            text: Input text to redact
            
        Returns:
            Tuple of (redacted_text, findings)
        """
        findings = []
        redacted_text = text
        
        for pattern in self.patterns:
            matches = list(pattern.pattern.finditer(redacted_text))
            
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                original_value = match.group()
                start, end = match.span()
                
                # Determine replacement based on mode and pattern type
                if self.mode == RedactionMode.STRICT:
                    replacement = pattern.strict_replacement or pattern.replacement
                elif self.mode == RedactionMode.DEVELOPMENT:
                    replacement = original_value  # Keep original
                else:  # BUSINESS_INTELLIGENCE mode
                    if pattern.bi_replacement == "PRESERVE_DOMAIN":
                        replacement = self._preserve_email_domain(original_value)
                    elif pattern.bi_replacement == "PRESERVE_FORMAT":
                        replacement = self._preserve_phone_pattern(original_value)
                    elif pattern.bi_replacement == "PRESERVE_STRUCTURE":
                        replacement = self._preserve_name_pattern(original_value)
                    elif pattern.bi_replacement == "PRESERVE_PATTERN":
                        replacement = self._preserve_customer_id(original_value)
                    else:
                        replacement = pattern.replacement
                
                # Apply replacement
                redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
                
                # Record finding
                findings.append({
                    'type': pattern.name,
                    'value': original_value,
                    'replacement': replacement,
                    'start': start,
                    'end': end,
                    'description': pattern.description
                })
        
        return redacted_text, findings

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about cached pseudonyms."""
        return {
            "names_cached": len(self._name_cache),
            "emails_cached": len(self._email_cache),
            "customer_ids_cached": len(self._customer_id_cache),
            "phones_cached": len(self._phone_cache)
        }

# Backward compatibility
PIIRedactor = EnhancedPIIRedactor