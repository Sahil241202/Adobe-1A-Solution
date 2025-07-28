#!/usr/bin/env python3
"""
Docker entry point for Challenge 1A PDF processing
Automatically processes all PDFs from /app/input and outputs to /app/output
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

from pdf_extractor.extractor import PDFOutlineExtractor

def main():
    """Process all PDFs from /app/input to /app/output"""
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in /app/input directory")
        print("Please mount a volume with PDF files: -v /path/to/pdfs:/app/input")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Initialize extractor
    extractor = PDFOutlineExtractor()
    
    processed_count = 0
    total_start_time = time.time()
    
    for pdf_file in pdf_files:
        try:
            start_time = time.time()
            print(f"Processing: {pdf_file.name}")
            
            # Extract outline
            result = extractor.extract_outline(str(pdf_file))
            
            # Create output filename
            output_filename = pdf_file.stem + ".json"
            output_path = output_dir / output_filename
            
            # Create Challenge 1A compliant output
            output_data = {
                "title": result.get("title", ""),
                "outline": result.get("outline", [])
            }
            
            # Save JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            processing_time = time.time() - start_time
            print(f"✅ Completed: {pdf_file.name} -> {output_filename} ({processing_time:.2f}s)")
            processed_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")
            continue
    
    total_time = time.time() - total_start_time
    print(f"\n🎯 Processing Summary:")
    print(f"   Successfully processed: {processed_count}/{len(pdf_files)} files")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Output directory: /app/output")
    
    # List output files
    output_files = list(output_dir.glob("*.json"))
    if output_files:
        print(f"   Created files:")
        for file in output_files:
            print(f"     - {file.name}")

if __name__ == "__main__":
    main()
