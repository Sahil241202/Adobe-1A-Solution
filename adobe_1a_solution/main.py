import argparse
import sys
import logging
from pathlib import Path

from pdf_extractor import (
    PDFOutlineExtractor,
    process_pdfs_advanced,
    setup_logging,
    __version__
)


def create_progress_callback(verbose: bool = False):
    """Create a progress callback function for processing updates."""
    def progress_callback(message: str):
        if verbose:
            print(f"Progress: {message}")
        logging.info(message)
    
    return progress_callback


def main():
    """Main CLI function with simplified usage and hardcoded default path."""
    
    # HARDCODED DEFAULT PATH - Change this to your PDF folder
    DEFAULT_PDF_FOLDER = "input"  # <-- Change this path to your PDF folder
    
    parser = argparse.ArgumentParser(
        description="Advanced PDF Outline Extractor - Simple Usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Simple Usage Examples:
  %(prog)s                               # Process PDFs in default folder (docs/)
  %(prog)s docs/                         # Process all PDFs in specified folder
  %(prog)s C:/MyDocuments/PDFs/          # Process PDFs in any folder
  %(prog)s file.pdf                      # Process single PDF file
  %(prog)s --fast                        # Fast processing of default folder
        """
    )
    
    # Main input - optional now (uses default if not provided)
    parser.add_argument(
        'path',
        nargs='?',  # Make it optional
        default=DEFAULT_PDF_FOLDER,  # Use hardcoded default
        help=f'Path to PDF file or folder containing PDFs (default: {DEFAULT_PDF_FOLDER})'
    )
    
    # Simplified options
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Enable fast parallel processing'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output folder (default: output)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show processing details'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'PDF Outline Extractor {__version__}'
    )
    
    args = parser.parse_args()
    
    # Setup logging (simplified)
    setup_logging('INFO', 'pdf_extractor.log')
    logger = logging.getLogger(__name__)
    
    # Create progress callback if verbose
    progress_callback = create_progress_callback(args.verbose) if args.verbose else None
    
    try:
        # Auto-detect if path is file or directory
        input_path = Path(args.path)
        
        # Show which path is being used
        if args.path == DEFAULT_PDF_FOLDER:
            print(f"Using default PDF folder: {DEFAULT_PDF_FOLDER}")
        
        if not input_path.exists():
            print(f"Error: Path '{args.path}' does not exist")
            if args.path == DEFAULT_PDF_FOLDER:
                print(f"Please create the '{DEFAULT_PDF_FOLDER}' folder and add your PDF files, or specify a different path.")
            sys.exit(1)
        
        # Collect PDF files automatically
        if input_path.is_file():
            if input_path.suffix.lower() != '.pdf':
                print(f"Error: '{args.path}' is not a PDF file")
                sys.exit(1)
            pdf_files = [str(input_path)]
            print(f"Processing single file: {input_path.name}")
        else:
            # It's a directory - find all PDFs
            pdf_files = [str(p) for p in input_path.rglob('*.pdf')]
            if not pdf_files:
                print(f"No PDF files found in '{args.path}'")
                sys.exit(1)
            print(f"Found {len(pdf_files)} PDF files in folder")
        
        if args.verbose:
            print("Files to process:")
            for pdf_file in pdf_files:
                print(f"  - {Path(pdf_file).name}")
            print()
        
        # Simple configuration - optimized for ease of use
        extractor_config = {
            'min_heading_length': 3,
            'max_heading_length': 100,  # Increased to allow longer headings
            'enable_cache': True,
            'custom_filters': None,
            'noise_patterns': None,
            'structural_words': None
        }
        
        # Auto-enable parallel processing for multiple files or when --fast is used
        use_parallel = args.fast or len(pdf_files) > 2
        workers = 6 if args.fast else 4
        
        if use_parallel and len(pdf_files) > 1:
            print(f"Using parallel processing with {workers} workers")
        
        # Process PDFs with simplified settings
        print("Starting PDF processing...")
        results = process_pdfs_advanced(
            pdf_paths=pdf_files,
            output_dir=args.output,
            cache_file='cache.json',
            parallel=use_parallel,
            max_workers=workers,
            include_metadata=False,  # Simplified - no metadata by default
            output_formats=['json'],  # Only JSON output
            config=extractor_config,
            progress_callback=progress_callback
        )
        
        # Simple success summary
        stats = results['statistics']
        print(f"\nProcessing Complete!")
        print(f"   Processed: {stats['successful']}/{stats['total_files']} files")
        print(f"   Success Rate: {stats['success_rate']:.0f}%")
        print(f"   Headings Found: {stats['total_headings_extracted']}")
        print(f"   Output Folder: {args.output}/")
        
        # Show output files created
        output_path = Path(args.output)
        json_files = list(output_path.glob("file*.json"))
        if json_files:
            print(f"   JSON Files: {len(json_files)} files created")
        
        if stats['failed'] > 0:
            print(f"\n{stats['failed']} files failed to process:")
            for result in results['results']:
                if result['status'] == 'error':
                    print(f"   - {result['filename']}: {result['error']}")
        
        # Simple exit
        sys.exit(0 if stats['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\nProcessing interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
