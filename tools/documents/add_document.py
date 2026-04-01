"""
Utility script to add new documents to the RAG system
Supports: PDF, DOC, DOCX, MD, TXT
"""
import sys
from pathlib import Path
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.document_loader import DocumentLoader, DocumentMonitor
from src.vector_store import VectorStoreManager
from core.config import DOCUMENT_DIR
from tools.ocr.docling_converter import convert_to_md


def add_document(source_path: str):
    """
    Add a new document to the RAG system
    
    Args:
        source_path: Path to the document file (PDF, DOC, DOCX, MD, TXT)
    """
    source = Path(source_path)
    
    # Validate file exists
    if not source.exists():
        print(f"✗ Error: File not found: {source}")
        return False
    
    # Check supported format
    supported_exts = {'.pdf', '.docx', '.doc', '.md', '.txt'}
    if source.suffix.lower() not in supported_exts:
        print(f"✗ Error: Unsupported file format: {source.suffix}")
        print(f"  Supported formats: {', '.join(supported_exts)}")
        return False
    
    # Copy to documents directory
    dest_dir = Path(DOCUMENT_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / source.name
    
    print(f"\n{'='*60}")
    print(f"ADDING DOCUMENT TO RAG SYSTEM")
    print(f"{'='*60}")
    print(f"Source: {source}")
    print(f"Destination: {dest_path}")
    
    # Check if file already exists
    if dest_path.exists():
        response = input(f"\n⚠ File '{source.name}' already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return False
    
    # Copy file
    print(f"\n[1/3] Copying file...")
    shutil.copy2(source, dest_path)
    print(f"  ✓ Copied to {dest_path}")
        # Convert the copied file to Markdown using Docling
    md_path = convert_to_md(str(dest_path))
    print(f"✅ Markdown generated: {md_path.name}")

    # Check for updates
    print(f"\n[2/3] Detecting document updates...")
    monitor = DocumentMonitor()
    updates = monitor.check_updates()
    
    if not updates:
        print("  ℹ No new updates detected (file might be identical)")
    
    # Load and index document
    print(f"\n[3/3] Loading and indexing document...")
    try:
        doc_loader = DocumentLoader()
        
        # Load only the new file
        from src.document_parser import MultiFormatLoader
        parser = MultiFormatLoader()
        documents = parser.load_single_file(dest_path)
        
        if not documents:
            print("  ✗ Failed to load document")
            return False
        
        # Split into chunks
        chunks = doc_loader.split_documents(documents)
        
        # Add to vector store
        vector_store = VectorStoreManager()
        vector_store.add_documents(chunks)
        
        print(f"\n{'='*60}")
        print(f"✓ SUCCESS!")
        print(f"{'='*60}")
        print(f"📄 Document: {source.name}")
        print(f"📊 Pages/Sections: {len(documents)}")
        print(f"🔢 Chunks created: {len(chunks)}")
        print(f"✅ Ready for queries")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add documents to the RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python add_document.py "E:\\nckh\\Quy chế đào tạo HaUI.doc"
  python add_document.py document.pdf
  python add_document.py report.docx
  python add_document.py notes.md
        """
    )
    
    parser.add_argument(
        'file',
        help='Path to the document file (PDF, DOC, DOCX, MD, TXT)'
    )
    
    args = parser.parse_args()
    
    success = add_document(args.file)
    
    if success:
        print("\n💡 Next steps:")
        print("  1. The document is now indexed and ready")
        print("  2. You can query it immediately via demo.py")
        print("  3. Run 'python demo.py' to test\n")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
