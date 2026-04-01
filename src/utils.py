"""
Utility functions for the RAG system
"""
from pathlib import Path
from pypdf import PdfReader

def is_pdf_scan(file_path: str) -> bool:
    """
    Check if a PDF file is likely a scan (has no text layer).
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        True if the PDF is likely a scan, False otherwise
    """
    try:
        reader = PdfReader(file_path)
        
        # Check first 5 pages (or fewer if document is shorter)
        num_pages_to_check = min(len(reader.pages), 5)
        
        for i in range(num_pages_to_check):
            text = reader.pages[i].extract_text()
            # If any page has significant text, it's probably not a scan
            if text and len(text.strip()) > 50:
                return False
                
        # If no significant text found in first few pages
        return True
    except Exception as e:
        print(f"⚠ Error checking PDF scan status: {e}")
        # Default to False (assume digital) to avoid heavy SmolDocling overhead on error
        return False
