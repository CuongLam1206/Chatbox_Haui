"""
Multi-Format Document Parser
Supports: PDF, DOC, DOCX, MD, TXT
Uses Docling for DOC/PDF and EasyOCR for scanned PDFs
"""
from pathlib import Path
from typing import List
import os

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

from langchain_community.document_loaders import TextLoader


class MultiFormatLoader:
    """
    Load documents from multiple formats: PDF, DOCX, DOC, MD, TXT
    Uses Docling converter for DOC/PDF and LightOnOCR for scanned PDFs
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.md', '.txt'}
    
    def __init__(self):
        """Initialize multi-format loader"""
        print("✓ Multi-format document loader initialized (Docling + EasyOCR)")
        print(f"  Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}")
    
    def load_single_file(self, file_path: Path) -> List[Document]:
        """
        Load a single file based on its extension.
        For PDF/DOC/DOCX: Convert to .md first using Docling/LightOnOCR, then load the .md
        For MD/TXT: Load directly
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of Document objects
        """
        ext = file_path.suffix.lower()
        
        if ext not in self.SUPPORTED_EXTENSIONS:
            print(f"⚠ Unsupported file format: {ext} ({file_path.name})")
            return []
        
        try:
            print(f"  Loading {file_path.name} ({ext})...")
            
            # For MD/TXT files: Load directly
            if ext in ['.md', '.txt']:
                loader = TextLoader(str(file_path), encoding='utf-8', autodetect_encoding=True)
                documents = loader.load()
            
            # For PDF/DOC/DOCX: Convert to Markdown first
            elif ext in ['.pdf', '.docx', '.doc']:
                # Check if .md already exists
                md_path = file_path.with_suffix('.md')
                
                if not md_path.exists():
                    print(f"    Converting {file_path.name} to Markdown...")
                    
                    # For PDF: Check if scan or digital
                    if ext == '.pdf':
                        from src.utils import is_pdf_scan
                        
                        if is_pdf_scan(str(file_path)):
                            print(f"    🔍 Detected as SCAN. Using EasyOCR...")
                            from tools.ocr.easyocr_converter import convert_pdf_with_easyocr
                            md_path = convert_pdf_with_easyocr(str(file_path))
                        else:
                            print(f"    📄 Digital PDF. Using Docling...")
                            from tools.ocr.docling_converter import convert_to_md
                            md_path = convert_to_md(str(file_path))
                    
                    # For DOC/DOCX: Use Docling
                    else:
                        from tools.ocr.docling_converter import convert_to_md
                        md_path = convert_to_md(str(file_path))
                    
                    print(f"    ✓ Converted to {md_path.name}")
                else:
                    print(f"    ℹ Using existing {md_path.name}")
                
                # Load the markdown file
                loader = TextLoader(str(md_path), encoding='utf-8', autodetect_encoding=True)
                documents = loader.load()
            
            else:
                return []
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": ext[1:],  # Remove the dot
                    "doc_type": file_path.stem  # Filename without extension
                })
            
            print(f"    ✓ Loaded {len(documents)} pages/sections")
            return documents
            
        except Exception as e:
            print(f"    ✗ Error loading {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def load_directory(self, directory: Path) -> List[Document]:
        """
        Load all supported documents from a directory, prioritizing .md files
        to avoid duplicates if multiple versions exist.
        """
        all_documents = []
        print(f"\nScanning directory: {directory}")
        
        # Group files by their stem (filename without extension)
        files_by_stem = {}
        for ext in self.SUPPORTED_EXTENSIONS:
            for file_path in directory.glob(f"**/*{ext}"):
                stem = file_path.stem
                if stem not in files_by_stem:
                    files_by_stem[stem] = {}
                files_by_stem[stem][ext] = file_path
        
        # Process each stem, picking the best format
        for stem, formats in files_by_stem.items():
            # Priority: .md > .txt > .pdf > .docx > .doc
            priority = ['.md', '.txt', '.pdf', '.docx', '.doc']
            chosen_ext = None
            for ext in priority:
                if ext in formats:
                    chosen_ext = ext
                    break
            
            if chosen_ext:
                file_to_load = formats[chosen_ext]
                # Log if we are skipping other formats
                if len(formats) > 1:
                    others = [e for e in formats.keys() if e != chosen_ext]
                    print(f"\n[De-duplicate] Found multiple formats for '{stem}'. Loading '{chosen_ext}' and skipping {others}.")
                
                docs = self.load_single_file(file_to_load)
                all_documents.extend(docs)
        
        print(f"\n✓ Total documents loaded: {len(all_documents)}")
        return all_documents
