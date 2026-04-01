"""
FastAPI Server for Facebook Messenger Webhook
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

# Thêm thư mục gốc vào path để import các module src
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.initialize import initialize_system

# Load biến môi trường
load_dotenv(root_dir / ".env")

# Cấu hình Facebook
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
FB_GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"

# Thư mục tài liệu
DOCUMENTS_DIR = root_dir / "data" / "documents"
LINK_FILE = DOCUMENTS_DIR / "Link_nguon.md"

# Cache map: tên file stem → drive url
_drive_links: dict = {}


def load_drive_links():
    """
    Đọc Link_nguon.md và tạo dict {stem_name: drive_url}.
    Hỗ trợ cả format: 'Tên TL: URL' (1 dòng) và 'Tên TL:\nURL' (2 dòng).
    """
    global _drive_links
    if not LINK_FILE.exists():
        print("[DriveLinks] Link_nguon.md not found")
        return

    text = LINK_FILE.read_text(encoding="utf-8")
    # Chuẩn hóa: join dòng URL bị tách xuống dòng với dòng tên trước nó
    lines = text.splitlines()
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if (line.endswith(":") or ":" not in line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("http"):
                merged.append(f"{line.rstrip(':')} : {next_line}")
                i += 2
                continue
        merged.append(line)
        i += 1

    for entry in merged:
        if " : " in entry:
            name_part, url_part = entry.split(" : ", 1)
        elif ": http" in entry:
            idx = entry.index(": http")
            name_part = entry[:idx]
            url_part = entry[idx + 2:]
        else:
            continue
        # Chuẩn hóa tên: bỏ extension, strip, lowercase
        stem = name_part.strip()
        for ext in (".pptm", ".pptx", ".pdf", ".docx", ".doc", ".md"):
            stem = stem.replace(ext, "")
        _drive_links[stem.strip().lower()] = url_part.strip()

    print(f"[DriveLinks] Loaded {len(_drive_links)} links from Link_nguon.md")


def get_drive_links_for_sources(sources: list[str]) -> dict[str, str]:
    """
    Thực hiện fuzzy match giữa tên source và _drive_links.
    Trả về dict {source: url} cho các source tìm được link.
    """
    if not _drive_links:
        load_drive_links()
    result = {}
    for src in sources:
        src_lower = src.strip().lower()
        # 1. Exact match
        if src_lower in _drive_links:
            result[src] = _drive_links[src_lower]
            continue
        # 2. Partial match: source là sub-string của key hoặc ngược lại
        for key, url in _drive_links.items():
            if src_lower in key or key in src_lower:
                result[src] = url
                break
    return result


# Load links ngay khi khởi động
load_drive_links()

import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app_instance):
    """Startup: kiểm tra document changes, in cảnh báo nếu cần rebuild."""
    from src.document_loader import DocumentMonitor
    monitor = DocumentMonitor()
    updates = monitor.check_updates()
    if updates:
        print("\n" + "⚠️ " * 20)
        print(f"⚠️  CẢNH BÁO: Phát hiện {len(updates)} tài liệu mới/thay đổi chưa được index!")
        for u in updates[:5]:
            print(f"   [+] {Path(u).name}")
        print("⚠️  Hãy chạy: python -m core.initialize --rebuild")
        print("⚠️ " * 20 + "\n")
    else:
        print("✓ Vector store đồng bộ với tài liệu mới nhất.")
    yield  # Server chạy bình thường
    # Shutdown: không cần dọn dẹp thêm

app = FastAPI(title="HaUI Chatbot Facebook API", lifespan=lifespan)

# Khởi tạo hệ thống chatbot (Lazy initialization)
workflow = None
conversation_manager = None
init_lock = asyncio.Lock()

async def get_chatbot():
    global workflow, conversation_manager
    async with init_lock:
        if workflow is None:
            print("Initializing Chatbot System...")
            # Chạy initialize_system trong thread riêng nếu nó là hàm đồng bộ nặng
            from concurrent.futures import ThreadPoolExecutor
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                workflow, conversation_manager, _ = await loop.run_in_executor(pool, initialize_system)
    return workflow, conversation_manager

class FBMessage(BaseModel):
    object: str
    entry: List[dict]

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Xác thực Webhook với Facebook
    """
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def handle_messages(request: Request, background_tasks: BackgroundTasks):
    """
    Xử lý tin nhắn từ Facebook Messenger
    """
    try:
        data = await request.json()
    except Exception:
        print("Received empty or invalid JSON request")
        return "EMPTY_BODY"
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    if "text" in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]
                        print(f"Received message from {sender_id}: {message_text}")
                        
                        # Xử lý tin nhắn trong background để trả lời Facebook ngay lập tức (200 OK)
                        background_tasks.add_task(process_and_reply, sender_id, message_text)
                        
        return "EVENT_RECEIVED"
    else:
        raise HTTPException(status_code=404)

async def process_and_reply(sender_id: str, message_text: str):
    """
    Xử lý câu hỏi qua RAG và gửi câu trả lời
    """
    wf, conv_mgr = await get_chatbot()
    
    try:
        # Lấy hoặc tạo session based trên sender_id của Facebook
        # Ở đây ta giả định sender_id là duy nhất và có thể dùng làm session_id
        session_id = f"fb_{sender_id}"
        
        # Lấy lịch sử trò chuyện
        chat_history = conv_mgr.get_history(session_id, limit=10)
        
        # Chạy workflow
        result = wf.run(message_text, session_id=session_id, chat_history=chat_history)
        answer = result['answer']
        
        # Lưu vào MongoDB
        conv_mgr.add_message(session_id, "user", message_text)
        conv_mgr.add_message(session_id, "assistant", answer, sources=result.get('sources'))
        
        # Gửi tin nhắn phản hồi qua Facebook Graph API
        send_fb_message(sender_id, answer)
        
        # Nếu có nguồn tham khảo, gửi thêm một tin nhắn phụ kèm link Drive
        if result.get('sources'):
            drive_links = get_drive_links_for_sources(result['sources'])
            sources_lines = []
            for src in result['sources']:
                if src in drive_links:
                    sources_lines.append(f"• {src}\n  🔗 {drive_links[src]}")
                else:
                    sources_lines.append(f"• {src}")
            sources_text = "📚 Nguồn tham khảo:\n" + "\n".join(sources_lines)
            send_fb_message(sender_id, sources_text)
            
    except Exception as e:
        print(f"Error processing message: {e}")
        send_fb_message(sender_id, "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.")

import re as _re
import html as _html

def _html_to_plain(text: str) -> str:
    """
    Chuyển HTML sang plain text cho Facebook Messenger (chỉ hỗ trợ text thuần).
    - <strong>, <b>  → **text** (hoặc bỏ tag)
    - <em>, <i>      → bỏ tag
    - <br>, <br/>    → xuống dòng
    - <p>            → xuống dòng
    - <li>           → bullet •
    - còn lại        → bỏ tag
    """
    # Unescape HTML entities (&amp; &lt; &gt; v.v.)
    text = _html.unescape(text)
    # <br> → newline
    text = _re.sub(r'<br\s*/?>', '\n', text, flags=_re.IGNORECASE)
    # <p> / </p> → newline
    text = _re.sub(r'</?p\s*>', '\n', text, flags=_re.IGNORECASE)
    # <li> → bullet
    text = _re.sub(r'<li\s*>', '\n• ', text, flags=_re.IGNORECASE)
    # Strip tất cả HTML tags còn lại
    text = _re.sub(r'<[^>]+>', '', text)
    # Gộp nhiều dòng trắng liên tiếp thành tối đa 2 dòng
    text = _re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def send_fb_message(recipient_id: str, message_text: str):
    """
    Gửi tin nhắn qua Facebook Graph API. 
    Tự động strip HTML tags và chia nhỏ tin nhắn nếu vượt quá giới hạn 2000 ký tự.
    """
    # Convert HTML → plain text (Facebook Messenger không render HTML)
    message_text = _html_to_plain(message_text)

    # Giới hạn của Facebook là 2000 ký tự, ta chọn 1900 cho an toàn
    MAX_LENGTH = 1900
    
    # Chia nhỏ tin nhắn
    chunks = [message_text[i:i+MAX_LENGTH] for i in range(0, len(message_text), MAX_LENGTH)]
    
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    
    for chunk in chunks:
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk}
        }
        
        response = requests.post(FB_GRAPH_API_URL, params=params, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to send message chunk: {response.status_code} - {response.text}")
        else:
            print(f"Message chunk sent to {recipient_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
