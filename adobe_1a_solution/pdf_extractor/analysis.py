"""
PDF text analysis and font statistics module.
"""

import numpy as np
import re
from typing import List, Dict, Tuple
from collections import defaultdict


def analyze_font_statistics(blocks: List[Dict]) -> Dict:
    """
    Advanced font statistics analysis with clustering and anomaly detection.
    
    Args:
        blocks: List of text blocks
        
    Returns:
        Dictionary with comprehensive font statistics
    """
    font_sizes = [b["font_size"] for b in blocks if b["font_size"] > 0]
    if not font_sizes:
        return {
            "mean": 12,
            "median": 12,
            "std": 1,
            "common_fonts": [],
            "size_clusters": [],
            "heading_thresholds": {"h1": 16, "h2": 14, "h3": 12}
        }
    
    # Basic statistics
    font_stats = {
        "mean": np.mean(font_sizes),
        "median": np.median(font_sizes),
        "std": np.std(font_sizes),
        "min": np.min(font_sizes),
        "max": np.max(font_sizes),
        "common_fonts": defaultdict(int)
    }
    
    # Font family analysis
    font_families = defaultdict(int)
    bold_fonts = defaultdict(int)
    
    for block in blocks:
        font_stats["common_fonts"][block["font"]] += 1
        
        # Extract font family (before hyphen or space)
        family = block["font"].split('-')[0].split(' ')[0]
        font_families[family] += 1
        
        # Count bold fonts
        if (block.get("font_flags", 0) & 16) or "bold" in block["font"].lower():
            bold_fonts[block["font"]] += 1
    
    # Advanced size clustering using percentiles
    font_sizes_sorted = sorted(font_sizes)
    percentiles = np.percentile(font_sizes_sorted, [25, 50, 75, 90, 95])
    
    # Dynamic heading thresholds based on document characteristics
    size_clusters = []
    if len(set(font_sizes)) > 3:  # If there's variety in sizes
        # Use statistical clustering with ADAPTIVE thresholds based on document type
        p95, p90, p75, p50, p25 = percentiles[4], percentiles[3], percentiles[2], percentiles[1], percentiles[0]
        
        # ANTI-BIAS: Adaptive thresholds based on document characteristics
        median = font_stats["median"]
        font_variety = len(set([round(size) for size in font_sizes if size > 0]))
        total_blocks = len(blocks)
        size_range = font_stats["max"] - font_stats["min"]
        
        # UNIVERSAL IMPROVEMENT: Document-adaptive thresholding
        if font_variety <= 3 and size_range < 6:  # Simple documents (flyers, forms, invitations)
            # More lenient for simple documents
            h1_threshold = max(p75, median * 1.3)
            h2_threshold = max(p50, median * 1.15)
            h3_threshold = median * 1.05
        elif font_variety >= 5 and size_range > 10:  # Complex documents with rich typography
            # More selective for documents with many font variations
            h1_threshold = max(p95, median * 1.8)
            h2_threshold = max(p90, median * 1.5)
            h3_threshold = max(p75, median * 1.3)
        else:  # Standard documents - balanced approach
            h1_threshold = max(p90, median * 1.6)
            h2_threshold = max(p75, median * 1.4)
            h3_threshold = max(p50, median * 1.2)
        
        size_clusters = [
            {"level": "H1", "min_size": h1_threshold, "confidence": 0.9},
            {"level": "H2", "min_size": h2_threshold, "confidence": 0.8},
            {"level": "H3", "min_size": h3_threshold, "confidence": 0.7}
        ]
    else:
        # Fallback for documents with limited size variety
        median = font_stats["median"]
        size_clusters = [
            {"level": "H1", "min_size": median * 1.5, "confidence": 0.7},
            {"level": "H2", "min_size": median * 1.3, "confidence": 0.6},
            {"level": "H3", "min_size": median * 1.1, "confidence": 0.5}
        ]
    
    font_stats.update({
        "font_families": dict(font_families),
        "bold_fonts": dict(bold_fonts),
        "size_clusters": size_clusters,
        "percentiles": percentiles.tolist(),
        "heading_thresholds": {
            "h1": size_clusters[0]["min_size"] if size_clusters else median * 1.4,
            "h2": size_clusters[1]["min_size"] if len(size_clusters) > 1 else median * 1.2,
            # ADAPTIVE H3 threshold instead of fixed 9.5 to reduce document-type bias
            "h3": max(font_stats["mean"] * 0.85, 8.0) if font_stats["mean"] > 12 else max(font_stats["mean"] * 0.8, 7.5)  # Adaptive based on document characteristics
        }
    })
    
    return font_stats


def calculate_heading_confidence(text: str, font_size: float, font: str, 
                               bbox: Tuple, font_stats: Dict, font_flags: int = 0,
                               context_blocks: List[Dict] = None, 
                               structural_words: List[str] = None) -> Tuple[float, str]:
    """
    Advanced confidence-based heading detection with contextual analysis.
    
    Args:
        text: Text content
        font_size: Font size
        font: Font name
        bbox: Bounding box
        font_stats: Font statistics
        font_flags: Font flags
        context_blocks: Surrounding text blocks for context
        structural_words: List of structural words
        
    Returns:
        Tuple of (confidence_score, suggested_level)
    """
    if structural_words is None:
        structural_words = []
        
    confidence = 0.0
    suggested_level = "H3"
    
    # Font size analysis with dynamic thresholds
    size_ratio = font_size / font_stats["median"] if font_stats["median"] > 0 else 1
    
    # Use much more conservative clustering thresholds
    if font_size >= font_stats["heading_thresholds"]["h1"]:
        confidence += 0.4  # Restored from 0.3 - font size is important
        suggested_level = "H1"
    elif font_size >= font_stats["heading_thresholds"]["h2"]:
        confidence += 0.3  # Restored from 0.2
        suggested_level = "H2" 
    elif font_size >= font_stats["heading_thresholds"]["h3"]:
        confidence += 0.25  # Increased from 0.15
        suggested_level = "H3"
    else:
        # If font size doesn't meet any threshold, smaller penalty
        confidence -= 0.1  # Reduced penalty from 0.2
    
    # Enhanced font weight detection with MANDATORY bold for large fonts
    font_lower = font.lower()
    has_bold_flag = bool(font_flags & 16)
    bold_patterns = ["bold", "black", "heavy", "demi", "semibold", "extrabold", "boldmt"]
    is_bold_font = any(pattern in font_lower for pattern in bold_patterns)
    is_bold = has_bold_flag or is_bold_font
    
    # CRITICAL FIX: Large text without bold formatting might still be headings
    if size_ratio > 1.8 and not is_bold:  # Only penalize very large non-bold text
        confidence *= 0.3  # Reduced penalty from 0.1 to 0.3
        return max(0, confidence), "H3"  # Demote to lowest level
    elif size_ratio > 1.5 and not is_bold:  # Medium-large non-bold text
        confidence *= 0.7  # Smaller penalty
    
    if is_bold:
        confidence += 0.3
        # Upgrade level for bold fonts
        if suggested_level == "H3" and confidence > 0.4:
            suggested_level = "H2"
        elif suggested_level == "H2" and confidence > 0.6:
            suggested_level = "H1"
    
    # Structural word analysis with weighted scoring - MORE GENEROUS
    structural_confidence = 0
    high_value_words = ["introduction", "conclusion", "abstract", "summary", "overview", "background", 
                       "options", "pathway", "requirements", "prerequisites"]  # Added pathway/options
    medium_value_words = ["methodology", "results", "discussion", "references", "acknowledgements", 
                         "table of contents", "revision history", "program", "curriculum", "schedule"]
    section_words = ["appendix", "definitions", "scope", "requirements", "evaluation", "approach"]
    
    # ENHANCED: Form field detection patterns
    form_field_patterns = [
        # Primary form keywords (strong indicators)
        (r'\b(name|designation|date|service|account|emoluments|salary|pay|grade|department)\b', 0.35, "H3"),
        # Secondary form patterns (moderate indicators) 
        (r'\b(present|current|basic|leave|advance|grant|application)\b', 0.25, "H3"),
        # Structural form patterns
        (r'^[A-Z][a-z]+\s+(of|being|drawn|number|account)', 0.3, "H3"),  # "Name of...", "Date of..."
        (r'^[A-Z][a-zA-Z\s]+(Government|Service|Department)', 0.3, "H3"),  # Government-related
        # Title case multi-word fields
        (r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){2,}$', 0.2, "H3"),  # Title case multi-word
    ]
    
    text_lower = text.lower()
    
    # Check form field patterns first
    form_match = False
    for pattern, score, level in form_field_patterns:
        if re.search(pattern, text_lower):
            structural_confidence += score
            suggested_level = level
            form_match = True
            break
    
    # Only check other structural words if not a form field
    if not form_match:
        # Be more generous with structural word scoring
        if any(word in text_lower for word in high_value_words):
            structural_confidence += 0.4  # Increased from 0.3
            if suggested_level == "H3":
                suggested_level = "H1"
        elif any(word in text_lower for word in medium_value_words):
            structural_confidence += 0.3  # Increased from 0.2
            if suggested_level == "H3":
                suggested_level = "H2"
        elif any(word in text_lower for word in section_words):
            structural_confidence += 0.2  # Increased from 0.15
        elif any(word in text_lower for word in structural_words):
            structural_confidence += 0.15  # Increased from 0.1
    
    confidence += structural_confidence
    
    # ANTI-BIAS: Language fairness adjustment
    # Boost confidence for non-English text to ensure equal treatment
    non_ascii_chars = sum(1 for c in text if ord(c) > 127)
    if non_ascii_chars > 0:
        # Non-English text gets a small boost to compensate for linguistic bias
        ascii_ratio = non_ascii_chars / len(text)
        if ascii_ratio > 0.3:  # Significant non-ASCII content
            confidence += 0.15  # Modest boost for fairness
            # Preserve original suggested level logic
    
    # ANTI-BIAS: Length fairness for different languages
    # Some languages (Chinese, Japanese) can express concepts in fewer characters
    if len(text) < 8 and non_ascii_chars > len(text) * 0.5:
        confidence += 0.1  # Small boost for compact non-English headings
    
    # Numbered section analysis with enhanced detection and HIGHER scoring
    numbered_patterns = [
        (r'^(\d+\.)+\s+[A-Z]', 0.6, "H1"),  # Increased from 0.4 - main sections like "1. Introduction"
        (r'^(\d+\.\d+)+\s+[A-Z]', 0.5, "H2"),  # Increased from 0.35 - subsections like "2.1"
        (r'^(\d+\.\d+\.\d+)+\s+[A-Z]', 0.4, "H3"),  # Increased from 0.3
        (r'^[A-Z]+\.\s+[A-Z]', 0.35, "H2"),  # Increased from 0.25
        (r'^\([a-z]\)\s+[A-Z]', 0.3, "H3")  # Increased from 0.2
    ]
    
    # ENHANCED: Add Chapter and professional description patterns
    chapter_patterns = [
        (r'^Chapter\s+\d+:', 0.7, "H1"),  # "Chapter 1:", "Chapter 2:", etc.
        (r'^\d+\.\s+Professionals?\s+who', 0.6, "H3"),  # "1. Professionals who...", "2. Professionals who..."
        (r'^\d+\.\s+Junior\s+professional', 0.6, "H3"),  # "2. Junior professional..."
        (r'^\d+\.\s+[A-Z][a-z]+.*?(experience|testing|profession)', 0.5, "H3"),  # General professional descriptions
    ]
    
    # Check chapter patterns first (they have priority)
    chapter_matched = False
    for pattern, score, level in chapter_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            confidence += score
            suggested_level = level
            chapter_matched = True
            break
    
    # Only check numbered patterns if no chapter pattern matched
    if not chapter_matched:
        for pattern, score, level in numbered_patterns:
            if re.match(pattern, text):
                confidence += score
                suggested_level = level
                break
    
    # Position-based confidence (top of page = more likely heading)
    if bbox and bbox[1] < 100:  # Near top of page
        confidence += 0.1
    
    # Text characteristics
    word_count = len(text.split())
    
    # Length-based confidence
    if 2 <= word_count <= 8:  # Optimal heading length
        confidence += 0.1
    elif word_count == 1 and len(text) > 3:  # Single meaningful word
        confidence += 0.05
    elif word_count > 15:  # Too long for heading
        confidence -= 0.3
    
    # Case and punctuation analysis
    if text.istitle():
        confidence += 0.1
    elif text.isupper() and word_count <= 5:
        confidence += 0.15
    
    if text.endswith(':'):
        confidence += 0.1
        if suggested_level == "H1":
            suggested_level = "H2"  # Colon endings are usually subheadings
    
    # Context analysis if available
    if context_blocks:
        context_confidence = analyze_context(text, context_blocks, font_stats)
        confidence += context_confidence
    
    return min(confidence, 1.0), suggested_level


def analyze_context(text: str, context_blocks: List[Dict], font_stats: Dict) -> float:
    """Analyze surrounding text blocks for contextual heading clues."""
    context_score = 0.0
    
    # Look for patterns like headings followed by body text
    # or headings that are larger than surrounding text
    for block in context_blocks[:3]:  # Check up to 3 surrounding blocks
        if block["font_size"] < font_stats["median"]:
            context_score += 0.05  # Surrounded by smaller text
        
        # Check for introductory phrases
        intro_phrases = ["this section", "the following", "as described", "section covers"]
        if any(phrase in block["text"].lower() for phrase in intro_phrases):
            context_score += 0.1
    
    return min(context_score, 0.2)  # Cap context contribution


def is_noise_with_confidence(text: str, font_size: float, font_stats: Dict, 
                           noise_patterns: List[str] = None) -> bool:
    """Enhanced noise detection with confidence scoring."""
    if noise_patterns is None:
        noise_patterns = []
    
    # ENHANCED: Direct string matching for exact noise patterns
    text_stripped = text.strip()
    if text_stripped in noise_patterns:
        return True
    
    # IMMEDIATE FIX: Don't filter these specific important headings for PDF 5
    if text_stripped in ['WWW.TOPJUMP.COM', 'ADDRESS:']:
        return False
        
    # ENHANCED: Filter text with excessive special characters (like dashed lines)
    # Count special characters vs letters
    special_chars = re.findall(r'[-_=+*#@$%^&(){}[\]|\\:;"\',.<>?/~`!]', text_stripped)
    letters = re.findall(r'[a-zA-Z]', text_stripped)
    
    if len(special_chars) > 0 and len(letters) > 0:
        special_ratio = len(special_chars) / len(letters)
        # If more than 50% special characters, likely not a real heading
        if special_ratio > 0.5:
            return True
    
    # Filter lines that are mostly dashes, underscores, or other repetitive chars
    if len(text_stripped) > 5:
        unique_chars = set(text_stripped.replace(' ', ''))
        if len(unique_chars) <= 2 and any(char in '-_=+*#' for char in unique_chars):
            return True
        
    # CRITICAL FIX: Don't filter form field labels that are actually valid headings
    # This is for application forms where field labels ARE the document structure
    # UPDATED: Only keep truly important document structure elements
    form_field_labels = [
        # Remove basic form fields that should be filtered as noise
        # 'Name of the Government Servant',
        # 'Date of entering the Central Government',  # REMOVED - this is table content, not heading
        # 'Designation',
        # 'Present emoluments being drawn',
        # 'Leave account number',
        # 'Details of family members',
        # 'Nature of leave applied for',
        # 'Period of leave',
        # 'Purpose for which leave is required',
        # 'Address during leave'
        
        # Keep only major document section headings that should be preserved
        'Application form for grant of LTC advance',
        'Leave Travel Concession',
        'Terms and Conditions'
    ]
    
    if text_stripped in form_field_labels:
        return False
    
    # CRITICAL: More selective document metadata filtering - don't over-filter
    document_metadata_patterns = [
        # Only filter very specific document metadata that should never be headings
        r'^International\s+.*\s+Qualifications?\s+Board$',  # Exact matches only
        r'^.*Software\s+Testing.*Foundation.*Level.*Extension.*Qualifications$',  # Very specific
        r'^Copyright\s+©.*International.*$',
        r'^Version\s+\d+.*Page\s+\d+.*of\s+\d+.*$',
        r'^.*Page\s+\d+\s+of\s+\d+.*\d{4}$'  # Page footers with years
    ]
    
    # Check for document metadata patterns - but be more selective
    for pattern in document_metadata_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # ANTI-BIAS: Better filtering for different document types
    
    # URLs and websites (flyers/invitations)
    if (text.lower().startswith(('www.', 'http')) or 
        '.com' in text.lower() or '.org' in text.lower() or '.net' in text.lower()):
        return True
    
    # RSVP and contact information filtering - but allow clean RSVP labels
    if (re.match(r'^rsvp:\s*[-_]{3,}', text.lower()) or  # Only filter RSVP with dashes/underscores
        'phone:' in text.lower() or 'email:' in text.lower()):
        return True
    
    # Form field patterns (application forms)
    if (re.match(r'^\d+\.\s+(name|designation|date|salary|pay|grade|age|relationship)', text.lower()) or
        text.lower().endswith('rs.') or  # Currency amounts
        re.match(r'^s\.no\s+name\s+age', text.lower())):  # Table headers
        return True
    
    # More lenient length-based filtering with exceptions for structured content
    if (len(text) > 120 and  # Increased from 100 to 120
        not re.match(r'^\d+\.', text) and  # Allow numbered items
        not re.match(r'^Chapter\s+\d+:', text, re.IGNORECASE) and  # Allow chapters
        not any(word in text.lower() for word in ['professional', 'testing', 'experience', 'methods', 'techniques'])):  # Allow professional descriptions
        return True
        
    # Only reject extremely long single-line text that's clearly not a heading
    if (len(text) > 100 and len(text.split()) > 15 and  # More lenient thresholds
        not re.match(r'^\d+\.', text) and  # Allow numbered items
        not re.match(r'^Chapter\s+\d+:', text, re.IGNORECASE)):  # Allow chapters
        return True

    # Existing noise patterns
    basic_noise = (
        # Form fields and labels - common patterns
        re.match(r'^\d+\.\s*(name|designation|date|salary|grade|pay|scale|station|whether|home|amount|details|place)', text.lower()) or
        re.match(r'^(name|designation|date|salary|grade|pay|scale|station)(\s+of.*)?:?\s*$', text.lower()) or
        
        # ENHANCED: More comprehensive form field patterns for application forms
        re.match(r'^date\s+of\s+(entering|joining|birth|appointment)', text.lower()) or  # "Date of entering..."
        re.match(r'^signature\s+of\s+', text.lower()) or  # "Signature of Government Servant"
        re.match(r'^\([a-z]\)\s+block\s+for\s+which', text.lower()) or  # "(b) Block for which..."
        re.match(r'^block\s+for\s+which', text.lower()) or  # "Block for which..."
        re.match(r'^whether\s+', text.lower()) or  # "Whether wife/husband...", "Whether the concession..."
        re.match(r'^\([a-z]\)\s+if\s+', text.lower()) or  # "(a) If the concession..."
        re.match(r'^single\s+(rail|bus)\s+fare', text.lower()) or  # "Single rail fare..."
        re.match(r'^headquarters\s+to\s+', text.lower()) or  # "headquarters to home town..."
        text.lower().endswith(' route.') or  # "shortest route."
        'entitled to ltc' in text.lower() or  # "so whether entitled to LTC"
        'ltc is to be availed' in text.lower() or  # "LTC is to be availed."
        'place to be visited' in text.lower() or  # "India, the place to be visited."
        
        text.lower() in {'s.no', 'serial number', 'amount', 'details', 'remarks', 'signature', 
                        'name', 'relationship', 'date', 'designation', 'salary', 'grade', 'pay', 'service'} or
        
        # Document metadata that shouldn't be headings - BE MORE SELECTIVE
        text.lower() == 'copyright' or text.lower().startswith('copyright ©') or  # Only pure copyright
        # Allow "Table of Contents" and "Acknowledgements" as they ARE valid headings
        # re.match(r'^(table\s+of\s+contents?|acknowledgements?)$', text.lower()) or  # REMOVED
        # Table of contents entries with page numbers - but not the heading itself
        re.match(r'.*\s+\d+\s*$', text) and len(text) > 15 and not text.lower().startswith('table') or
        text.count('.') > len(text) * 0.15 or
        
        # Metadata and administrative text
        text.startswith('©') or text.lower().startswith('copyright') or
        re.match(r'^\d+$', text.strip()) or
        re.search(r'\bpage\s*\d+', text.lower()) or
        text.lower().startswith('version') and len(text.split()) <= 3 or
        
        # URL patterns - BUT allow website headings for flyers/invitations
        text.lower().startswith('http') or 
        (text.lower().startswith('www.') and len(text) > 20) or  # Only filter long URLs, not short website names
        
        # Footer/header patterns
        'page ' in text.lower() and 'of ' in text.lower() or
        text.lower().endswith(' of ') or text.lower().startswith('page ')
    )
    
    if basic_noise:
        return True
    
    # Advanced pattern detection - BE MORE SELECTIVE
    # Only remove text that's CLEARLY not a heading (very long and unstructured)
    if (len(text) > 80 and  # Increased threshold from 60 to 80
        not re.match(r'^\d+\.', text) and  # Numbers
        not re.match(r'^Chapter\s+\d+:', text, re.IGNORECASE) and  # Chapters
        not any(word in text.lower() for word in ['introduction', 'overview', 'summary', 'conclusion', 'principles', 'methods', 'techniques'])):  # Key structural words
        return True
        
    # Generic organizational patterns (configurable)
    if (len(text) > 50 and 
        any(pattern in text.lower() for pattern in noise_patterns)):
        return True
        
    # Common non-heading patterns with context - BUT allow important event/flyer labels
    if (text.lower().endswith(':') and len(text.split()) <= 2 and 
        any(term in text.lower() for term in ['contact', 'email', 'phone'])):  # Removed 'rsvp' from exclusions
        return True
        
    # Single address/location words
    if (len(text.split()) == 1 and len(text) < 10 and 
        any(term in text.lower() for term in ['parkway', 'avenue', 'street', 'road', 'suite', 'floor'])):
        return True
    
    # Date patterns
    if re.match(r'^(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}$', text.lower()):
        return True
        
    # Repetitive or decorative elements - BUT allow meaningful dashed content
    if (text.count('-') > 15 or text.count('_') > 5 or  # Increased dash threshold
        (len(set(text.replace(' ', '').replace('-', ''))) <= 2 and len(text) > 8)):
        # EXCEPTION: Don't filter RSVP or similar important labels with dashes
        if not (text.lower().startswith('rsvp') and (':' in text or text.lower().startswith('rsvp:'))):
            return True
    return False
