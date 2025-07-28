# PDF Outline Extractor Package
"""
Advanced PDF Outline Extractor with Statistical Analysis and ML-like Features

This package provides a sophisticated PDF outline extraction system that uses
statistical analysis, confidence scoring, and multi-pass analysis to detect
document headings without bias toward specific document types.
"""

__version__ = "3.0.0"
__author__ = "Advanced PDF Extraction System"
__description__ = "Statistical ML-like PDF outline extractor with confidence scoring"

from .extractor import PDFOutlineExtractor
from .utils import setup_logging
from .processor import process_pdfs_advanced

__all__ = ['PDFOutlineExtractor', 'setup_logging', 'process_pdfs_advanced']
