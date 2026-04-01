"""
Document Loading and Auto-Update Detection
Supports: PDF, DOC, DOCX, MD, TXT
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

from core.config import DOCUMENT_DIR, TRACKER_FILE, CHUNK_SIZE, CHUNK_OVERLAP
from src.document_parser import MultiFormatLoader


class DocumentMonitor:
    """
    Monitor documents for changes and track update status
    """
    
    def __init__(self, doc_dir: Path = DOCUMENT_DIR, tracker_file: Path = TRACKER_FILE):
        """
        Initialize document monitor
        
        Args:
            doc_dir: Directory containing documents
            tracker_file: JSON file to track document states
        """
        self.doc_dir = Path(doc_dir)
        self.tracker_file = Path(tracker_file)
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self.tracked_files = self._load_tracker()
    
    def _compute_hash(self, filepath: Path) -> str:
        """
        Compute MD5 hash of file content
        
        Args:
            filepath: Path to file
            
        Returns:
            MD5 hash string
        """
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _load_tracker(self) -> Dict:
        """
        Load tracked file states from JSON
        
        Returns:
            Dictionary of tracked files
        """
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_tracker(self):
        """Save current tracked states to JSON"""
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.tracked_files, f, indent=2, ensure_ascii=False)
    
    def check_updates(self) -> List[Tuple[str, Path]]:
        """
        Check for document updates across all supported formats
        
        Returns:
            List of (action, filepath) tuples where action is 'added', 'modified', or 'deleted'
        """
        updates = []
        current_files = {}
        
        # Supported file extensions
        supported_exts = ['.pdf', '.docx', '.doc', '.md', '.txt']
        
        # Scan current files
        for ext in supported_exts:
            for file_path in self.doc_dir.glob(f"**/*{ext}"):
                rel_path = str(file_path.relative_to(self.doc_dir))
                file_hash = self._compute_hash(file_path)
                mtime = file_path.stat().st_mtime
                
                current_files[rel_path] = {
                    "hash": file_hash,
                    "mtime": mtime,
                    "file_type": ext[1:],
                    "updated_at": datetime.now().isoformat()
                }
                
                # Check if new or modified
                if rel_path not in self.tracked_files:
                    updates.append(("added", file_path))
                    print(f"[+] New document: {rel_path}")
                elif self.tracked_files[rel_path]["hash"] != file_hash:
                    updates.append(("modified", file_path))
                    print(f"[~] Modified document: {rel_path}")
        
        # Check for deleted files
        for old_file in set(self.tracked_files.keys()) - set(current_files.keys()):
            updates.append(("deleted", old_file))
            print(f"[-] Deleted document: {old_file}")
        
        # Update tracker
        self.tracked_files = current_files
        self._save_tracker()
        
        if not updates:
            print("✓ No document updates detected")
        
        return updates


class DocumentLoader:
    """
    Load and process documents with text splitting
    """
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize document loader
        
        Args:
            chunk_size: Size of text chunks (used for non-legal documents)
            chunk_overlap: Overlap between chunks
        """
         # Semantic chunker for legal documents (.md files)
        from src.legal_chunker import LegalDocumentChunker
        self.legal_chunker = LegalDocumentChunker(max_chunk_size=chunk_size)  # Use config value
        
        # Fallback splitter for non-markdown documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        print(f"✓ Semantic Legal Chunker initialized for .md files (max {chunk_size} chars)")
        print(f"✓ Fallback Text Splitter for other formats (chunk_size={chunk_size})")

    
    def load_documents(self, doc_dir: Path = DOCUMENT_DIR) -> List[Document]:
        """
        Load all documents from directory (supports PDF, DOC, DOCX, MD, TXT)
        
        Args:
            doc_dir: Directory containing documents
            
        Returns:
            List of Document objects
        """
        print(f"Loading documents from: {doc_dir}")
        
        # Use multi-format loader
        multi_loader = MultiFormatLoader()
        documents = multi_loader.load_directory(doc_dir)
        
        # Add timestamp to metadata
        for doc in documents:
            doc.metadata["loaded_at"] = datetime.now().isoformat()
        
        print(f"✓ Loaded {len(documents)} documents from various formats")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks using Semantic Chunking for .md files (legal docs)
        and fallback RecursiveTextSplitter for other formats.
        """
        final_chunks = []
        md_count = 0
        other_count = 0
        
        for doc in documents:
            if doc.metadata.get("file_type") == "md":
                # Use semantic chunker for legal documents
                semantic_chunks = self.legal_chunker.chunk_document(
                    text=doc.page_content,
                    metadata=doc.metadata
                )
                final_chunks.extend(semantic_chunks)
                md_count += len(semantic_chunks)
            else:
                # Fallback for non-markdown (PDF, DOC, etc.)
                sub_chunks = self.text_splitter.split_documents([doc])
                final_chunks.extend(sub_chunks)
                other_count += len(sub_chunks)
        
        print(f"✓ Created {len(final_chunks)} chunks total:")
        print(f"  - {md_count} chunks from .md files (semantic by Article)")
        print(f"  - {other_count} chunks from other formats (recursive)")
        return final_chunks
    
    def load_and_split(self, doc_dir: Path = DOCUMENT_DIR) -> List[Document]:
        """
        Load documents and split into chunks
        
        Args:
            doc_dir: Directory containing documents
            
        Returns:
            List of chunked documents
        """
        documents = self.load_documents(doc_dir)
        return self.split_documents(documents)
