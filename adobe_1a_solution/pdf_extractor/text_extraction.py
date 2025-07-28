"""
PDF text extraction and span processing module.
"""

import fitz
import unicodedata
import re
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from .analysis import analyze_font_statistics


def normalize_text(text: str, custom_filters: List[str] = None) -> str:
    """Normalize text by removing extra spaces and normalizing unicode."""
    if custom_filters is None:
        custom_filters = []
        
    text = unicodedata.normalize('NFKC', text.strip())
    text = re.sub(r'\s+', ' ', text)
    
    # Apply custom filters
    for filter_pattern in custom_filters:
        text = re.sub(filter_pattern, '', text, flags=re.IGNORECASE)
    
    return text


def extract_text_blocks(pdf_path: str, custom_filters: List[str] = None) -> List[Dict]:
    """
    Extract structured text blocks from PDF with enhanced grouping.
    
    Args:
        pdf_path: Path to the PDF file
        custom_filters: Custom regex patterns to filter text
        
    Returns:
        List of text blocks with metadata
    """
    try:
        doc = fitz.open(pdf_path)
        blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_dict = page.get_text("dict")
            
            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                # Group spans that belong to the same logical line
                full_text = []
                spans = []
                font_sizes = []
                fonts = []
                font_flags = []
                
                for line in block["lines"]:
                    line_text = []
                    for span in line["spans"]:
                        norm_text = normalize_text(span["text"], custom_filters)
                        if norm_text:
                            line_text.append(norm_text)
                            spans.append(span)
                            font_sizes.append(span["size"])
                            fonts.append(span["font"])
                            font_flags.append(span["flags"])  # Capture font flags
                    
                    if line_text:
                        full_text.append(" ".join(line_text))
                
                if not full_text:
                    continue
                    
                # Join multiline text blocks into single line for headings
                combined_text = " ".join(full_text).strip()
                avg_font_size = np.mean(font_sizes) if font_sizes else 0
                dominant_font = max(set(fonts), key=fonts.count) if fonts else ""
                
                # Get dominant font flags
                dominant_flags = max(set(font_flags), key=font_flags.count) if font_flags else 0
                
                blocks.append({
                    "text": combined_text,
                    "font_size": avg_font_size,
                    "font": dominant_font,
                    "font_flags": dominant_flags,  # Add font flags
                    "page": page_num,  # Changed to 0-indexed to match sample
                    "bbox": block["bbox"],  # Use block bbox for better grouping
                    "spans": spans  # Keep original spans for detailed analysis
                })
        
        doc.close()
        logging.info(f"Extracted {len(blocks)} text blocks from {pdf_path}")
        return blocks
        
    except Exception as e:
        logging.error(f"Error extracting text blocks from {pdf_path}: {str(e)}")
        raise


def extract_span_level_headings(pdf_path: str, font_stats: Dict, custom_filters: List[str] = None) -> List[Dict]:
    """
    Extract headings at span level for documents where block consolidation 
    misses individual word headings (like flyers/invitations).
    """
    try:
        doc = fitz.open(pdf_path)
        span_headings = []
        
        # Collect all spans first for potential consolidation
        all_spans = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_dict = page.get_text("dict")
            
            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = normalize_text(span["text"], custom_filters)
                        if text and len(text) >= 1:  # Keep even single characters for consolidation
                            all_spans.append({
                                "text": text,
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"],
                                "bbox": span["bbox"],
                                "page": page_num  # 0-indexed pages
                            })
        
        # Try to consolidate adjacent spans that might form complete headings
        consolidated_spans = consolidate_adjacent_spans(all_spans)
        
        # Apply heading detection to consolidated spans
        for span in consolidated_spans:
            is_heading, level = is_span_heading(
                span["text"], span["size"], span["font"], 
                span["bbox"], font_stats, span["flags"]
            )
            
            if is_heading:
                span_headings.append({
                    "text": span["text"],
                    "level": level,
                    "page": span["page"],
                    "font_size": span["size"],
                    "font": span["font"]
                })
        
        doc.close()
        return span_headings
        
    except Exception as e:
        logging.error(f"Error in span-level heading extraction: {str(e)}")
        return []


def consolidate_adjacent_spans(spans: List[Dict]) -> List[Dict]:
    """
    Consolidate adjacent spans that might form complete headings.
    This handles cases where text is split into individual words or characters.
    """
    if not spans:
        return spans
    
    # Sort spans by page, then by Y position, then by X position
    sorted_spans = sorted(spans, key=lambda s: (s["page"], s["bbox"][1], s["bbox"][0]))
    
    consolidated = []
    i = 0
    
    while i < len(sorted_spans):
        current_span = sorted_spans[i]
        
        # Look for spans that might belong together
        potential_group = [current_span]
        j = i + 1
        
        # Group spans that are:
        # 1. On the same page
        # 2. Have similar font properties (bold flag is most important)
        # 3. Are positioned close to each other (same line)
        while j < len(sorted_spans):
            next_span = sorted_spans[j]
            
            # Same page check
            if next_span["page"] != current_span["page"]:
                break
            
            # Vertical proximity check (same line) - adaptive for font size
            y_diff = abs(next_span["bbox"][1] - current_span["bbox"][1])
            # Adaptive Y difference based on font size
            max_y_diff = max(2, min(5, current_span["size"] / 8))
            if y_diff > max_y_diff:
                break
            
            # Horizontal proximity check - adaptive for font size
            current_right = potential_group[-1]["bbox"][2]  # Right edge of last span in group
            next_left = next_span["bbox"][0]  # Left edge of next span
            x_gap = next_left - current_right
            # Adaptive gap based on font size
            max_x_gap = max(20, min(50, current_span["size"] * 2))
            if x_gap > max_x_gap:
                break
            
            # Font properties check - must have same bold flag
            same_bold = (current_span["flags"] & 16) == (next_span["flags"] & 16)
            similar_size = abs(next_span["size"] - current_span["size"]) < 8  # More lenient for variable fonts
            same_font_family = (current_span["font"].split('-')[0] == 
                              next_span["font"].split('-')[0])  # Same base font
            
            if not (same_bold and similar_size and same_font_family):
                break
            
            # Add to group
            potential_group.append(next_span)
            j += 1
        
        # Create consolidated span if we have multiple spans
        if len(potential_group) > 1:
            # Combine text with spaces, handling punctuation properly
            combined_text = ""
            for k, span in enumerate(potential_group):
                if k == 0:
                    combined_text = span["text"]
                else:
                    # Don't add space before punctuation
                    if span["text"] in "!?.,;:":
                        combined_text += span["text"]
                    else:
                        combined_text += " " + span["text"]
            
            # Use properties from first span but average the size
            first_span = potential_group[0]
            avg_size = sum(s["size"] for s in potential_group) / len(potential_group)
            
            consolidated_span = {
                "text": combined_text,
                "font": first_span["font"],
                "size": avg_size,
                "flags": first_span["flags"],
                "bbox": (
                    first_span["bbox"][0],  # leftmost x
                    first_span["bbox"][1],  # top y
                    potential_group[-1]["bbox"][2],  # rightmost x
                    first_span["bbox"][3]   # bottom y
                ),
                "page": first_span["page"]
            }
            consolidated.append(consolidated_span)
            i = j  # Skip all processed spans
        else:
            # Single span, add as-is
            consolidated.append(current_span)
            i += 1
    
    return consolidated


def is_span_heading(text: str, font_size: float, font: str, bbox: Tuple,
                   font_stats: Dict, font_flags: int = 0) -> Tuple[bool, Optional[str]]:
    """
    Enhanced span-level heading detection for various document types.
    Handles consolidated text from multiple spans.
    """
    if not text or len(text) < 3:
        return False, None
    
    # ENHANCED: Apply noise filtering at span level too
    from .analysis import is_noise_with_confidence
    noise_patterns = [
        'qualifications board', 'testing board', 'international board', 
        'copyright notice', 'document may be copied', 'source is acknowledged',
        '. *', '.*', '..', '• *', '- *', '* *'  # Enhanced: catch various bullet/dot patterns
    ]
    
    if is_noise_with_confidence(text, font_size, font_stats, noise_patterns):
        return False, None
        
    word_count = len(text.split())
    
    # Flexible word count for consolidated spans
    if word_count > 10:  # Allow reasonable consolidated headings
        return False, None
    
    # Font analysis
    font_lower = font.lower()
    has_bold_flag = bool(font_flags & 16)
    is_bold_font = "bold" in font_lower or "black" in font_lower
    is_bold = has_bold_flag or is_bold_font
    
    # Size analysis
    size_ratio = font_size / font_stats["median"] if font_stats["median"] > 0 else 1
    is_large = size_ratio > 1.4  # More lenient for spans
    is_very_large = size_ratio > 1.8
    
    # Text characteristics
    is_upper_case = text.isupper()
    is_title_case = text.istitle()
    
    # Enhanced detection for consolidated text
    mixed_case_pattern = bool(re.search(r'[A-Z][a-z]+.*[A-Z]', text))
    has_exclamation = text.endswith('!')
    
    # Generic filtering - avoid common non-headings
    if (word_count <= 3 and not has_exclamation and 
        any(pattern in text.lower() for pattern in ['com', 'www', 'http', '.org', '.net',
                                                   'parkway', 'avenue', 'street', 'rsvp:'])):
        return False, None
    
    # Detect clear headings
    if is_bold and is_large:
        if word_count <= 8:  # Consolidated phrases
            return True, "H1"
    
    if is_very_large and (is_upper_case or mixed_case_pattern):
        if word_count <= 8:
            return True, "H1"
    
    # Special pattern for announcements/flyers with mixed case and punctuation
    if (mixed_case_pattern and (has_exclamation or text.endswith('?')) and 
        word_count >= 3 and word_count <= 10):
        return True, "H1"
    
    # Conservative fallback
    if is_bold and word_count <= 4:
        return True, "H3"
        
    return False, None
