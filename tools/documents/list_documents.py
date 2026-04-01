"""
list_documents.py
Kiểm tra danh sách tài liệu trong thư mục và trạng thái embedding trong Vector DB.
"""
from pathlib import Path
from src.vector_store import VectorStoreManager
from core.config import DOCUMENT_DIR

def check_status():
    print("\n" + "="*60)
    print("📋 TRẠNG THÁI HỆ THỐNG TÀI LIỆU")
    print("="*60)
    
    # 1. Khởi tạo Vector Store
    v_store = VectorStoreManager()
    
    # Lay tat ca metadata tu ChromaDB
    # Chung ta truy van tat ca ids va lay metadata 'filename'
    results = v_store.vectorstore._collection.get(include=['metadatas'])
    
    indexed_files = set()
    if results and results['metadatas']:
        for meta in results['metadatas']:
            if 'filename' in meta:
                indexed_files.add(meta['filename'])
    
    # 2. Quét thư mục data/documents
    doc_path = Path(DOCUMENT_DIR)
    local_files = []
    for ext in ['.pdf', '.docx', '.doc', '.md', '.txt']:
        local_files.extend(list(doc_path.glob(f"*{ext}")))
    
    print(f"\n📂 Thư mục: {doc_path}")
    print(f"📊 Tổng số đoạn (chunks) trong DB: {len(results['ids']) if results['ids'] else 0}")
    print(f"📄 Số file duy nhất đã Index: {len(indexed_files)}")
    print("-" * 60)
    print(f"{'Tên File':<40} | {'Trạng thái':<15}")
    print("-" * 60)
    
    for f in local_files:
        status = "✅ Đã Index" if f.name in indexed_files else "⏳ Đang chờ/Lỗi"
        # Neu la file .docx ma da co file .md tuong ung da index thi cung coi la xong
        if f.suffix.lower() != '.md':
            md_version = f.with_suffix('.md').name
            if md_version in indexed_files:
                status = "✅ Đã Index (.md)"
        
        print(f"{f.name[:39]:<40} | {status:<15}")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    check_status()
