"""
Docling Converter - Convert DOC/DOCX/PDF to Markdown

Uses Docling library to convert document formats to Markdown.
Handles digital PDFs and Word documents, NOT scanned PDFs.
"""

from pathlib import Path
from typing import Union
import logging

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    raise ImportError(
        "Docling is not installed. Install it with: pip install docling>=2.0.0"
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_to_md(file_path: Union[str, Path]) -> Path:
    """
    Convert DOC/DOCX/PDF to Markdown using Docling.
    
    Args:
        file_path: Path to the document file (.doc, .docx, .pdf)
        
    Returns:
        Path to the generated .md file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file format is not supported
        Exception: If conversion fails
    """
    file_path = Path(file_path)
    
    # Validate file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check supported formats
    supported_formats = {'.pdf', '.doc', '.docx'}
    if file_path.suffix.lower() not in supported_formats:
        raise ValueError(
            f"Unsupported format: {file_path.suffix}. "
            f"Supported: {', '.join(supported_formats)}"
        )
    
    logger.info(f"🔄 Converting {file_path.name} to Markdown using Docling...")
    
    try:
        # Initialize Docling converter
        converter = DocumentConverter()
        
        # Convert document
        result = converter.convert(str(file_path))
        
        # Generate output path (same directory, .md extension)
        md_path = file_path.with_suffix('.md')
        
        # Export to Markdown
        markdown_content = result.document.export_to_markdown()
        
        # Save to file
        md_path.write_text(markdown_content, encoding='utf-8')
        
        logger.info(f"✅ Conversion successful: {md_path.name}")
        logger.info(f"   Output size: {len(markdown_content)} characters")
        
        return md_path
        
    except Exception as e:
        logger.error(f"❌ Conversion failed for {file_path.name}: {e}")
        raise Exception(f"Docling conversion failed: {e}") from e


def is_docling_available() -> bool:
    """
    Check if Docling is properly installed and available.
    
    Returns:
        True if Docling can be imported, False otherwise
    """
    try:
        from docling.document_converter import DocumentConverter
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # Test conversion
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python docling_converter.py <file_path>")
        print("Example: python docling_converter.py document.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        output_file = convert_to_md(input_file)
        print(f"\n✅ Success! Markdown file created: {output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
