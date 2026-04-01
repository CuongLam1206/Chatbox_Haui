"""
auto_update.py
Giám sát thư mục data/documents/ để tự động chuyển đổi tài liệu mới sang Markdown (Docling cho DOC/PDF, EasyOCR cho PDF scan) và embedding.
"""

import time
import hashlib
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Các module nội bộ
from tools.ocr.docling_converter import convert_to_md
from src.document_loader import DocumentLoader
from src.vector_store import VectorStoreManager
from src.document_parser import MultiFormatLoader
from core.config import DOCUMENT_DIR

STATE_FILE = Path(__file__).parent / "auto_update_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


class DocumentHandler(FileSystemEventHandler):
    def __init__(self):
        self.state = load_state()
        self.vector_store = VectorStoreManager()
        self.doc_loader = DocumentLoader()

    def process(self, src_path: Path):
        if not src_path.is_file():
            return
        if src_path.suffix.lower() not in {".pdf", ".docx", ".doc", ".md", ".txt"}:
            return
            
        # --- Tối ưu: Kiểm tra Metadata trước khi tính Hash ---
        mtime = src_path.stat().st_mtime
        size = src_path.stat().st_size
        
        cached = self.state.get(str(src_path))
        # Neu state kieu cu (chi co hash) hoac kieu moi (dict)
        if isinstance(cached, dict):
            if cached.get("mtime") == mtime and cached.get("size") == size:
                return  # Metadata khong doi -> Bo qua nhanh
        
        # Neu metadata doi hoac chua co, moi tinh Hash
        cur_hash = file_hash(src_path)
        if isinstance(cached, dict) and cached.get("hash") == cur_hash:
            # Metadata doi nhung noi dung khong doi (hiem gap nhung co the)
            self.state[str(src_path)]["mtime"] = mtime
            save_state(self.state)
            return

        if isinstance(cached, str) and cached == cur_hash:
            # Tuong thich voi state cu
            self.state[str(src_path)] = {"hash": cur_hash, "mtime": mtime, "size": size}
            save_state(self.state)
            return

        # --- Bắt đầu xử lý thực sự ---
        from src.utils import is_pdf_scan
        from tools.ocr.easyocr_converter import convert_pdf_with_easyocr

        # Convert to markdown if needed
        md_path = src_path
        if src_path.suffix.lower() != ".md":
            # Tự động chọn engine cho PDF
            if src_path.suffix.lower() == ".pdf" and is_pdf_scan(str(src_path)):
                print(f"🔍 Detected '{src_path.name}' as a SCAN. Using EasyOCR...")
                md_path = convert_pdf_with_easyocr(str(src_path))
            else:
                md_path = convert_to_md(str(src_path))
            
            print(f"✅ Converted {src_path.name} → {md_path.name}")
        
        # Check embedding
        doc_name = md_path.stem
        if self.vector_store.has_document(doc_name):
            print(f"🔎 {doc_name} already embedded – skip")
        else:
            loader = MultiFormatLoader()
            docs = loader.load_single_file(md_path)
            chunks = self.doc_loader.split_documents(docs)
            self.vector_store.add_documents(chunks)
            print(f"🚀 Embedded {doc_name}")
            
        # Update state (new format)
        self.state[str(src_path)] = {
            "hash": cur_hash,
            "mtime": mtime,
            "size": size
        }
        save_state(self.state)

    def on_created(self, event):
        self.process(Path(event.src_path))

    def on_modified(self, event):
        self.process(Path(event.src_path))


if __name__ == "__main__":
    folder = Path(DOCUMENT_DIR)
    print(f"🔎 Watching folder: {folder}")
    
    handler = DocumentHandler()
    
    # --- Bước 1: Quét toàn bộ thư mục khi khởi động ---
    print("⏳ Thực hiện quét thư mục ban đầu...")
    supported_ext = {".pdf", ".docx", ".doc", ".md", ".txt"}
    for file_path in folder.glob("**/*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_ext:
            handler.process(file_path)
    print("✅ Đã kiểm tra xong các file hiện có.")
    
    # --- Bước 2: Bắt đầu giám sát các thay đổi mới ---
    observer = Observer()
    observer.schedule(handler, str(folder), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
