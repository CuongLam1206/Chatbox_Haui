import os

content = r'''"""
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

# Path setup
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.initialize import initialize_system

# Load env variables
load_dotenv(root_dir / ".env")

# Facebook Config
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
FB_GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"

# Documents and Drive Links
DOCUMENTS_DIR = root_dir / "data" / "documents"
LINK_FILE = DOCUMENTS_DIR / "Link_nguon.md"
_drive_links: dict = {}

def load_drive_links():
    global _drive_links
    if not LINK_FILE.exists():
        print("[DriveLinks] Link_nguon.md not found")
        return
    text = LINK_FILE.read_text(encoding="utf-8")
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
        stem = name_part.strip()
        for ext in (".pptm", ".pptx", ".pdf", ".docx", ".doc", ".md"):
            stem = stem.replace(ext, "")
        _drive_links[stem.strip().lower()] = url_part.strip()
    print(f"[DriveLinks] Loaded {len(_drive_links)} links")

def get_drive_links_for_sources(sources: list[str]) -> dict[str, str]:
    if not _drive_links:
        load_drive_links()
    result = {}
    for src in sources:
        src_lower = src.strip().lower()
        if src_lower in _drive_links:
            result[src] = _drive_links[src_lower]
            continue
        for key, url in _drive_links.items():
            if src_lower in key or key in src_lower:
                result[src] = url
                break
    return result

load_drive_links()

# Initialize Logging (Google Sheets + FB Profile)
from src.google_sheets_handler import GoogleSheetsLogger
gs_logger = GoogleSheetsLogger()

_user_names = {}

async def get_fb_user_profile(user_id: str):
    global _user_names
    if user_id in _user_names:
        return _user_names[user_id]
    try:
        url = f"https://graph.facebook.com/v19.0/{user_id}"
        params = {
            "fields": "first_name,last_name",
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            full_name = f"{data.get('last_name', '')} {data.get('first_name', '')}".strip()
            if not full_name:
                full_name = f"User {user_id}"
            _user_names[user_id] = full_name
            print(f"[FacebookAPI] Fetched name for {user_id}: {full_name}")
            return full_name
    except Exception as e:
        print(f"[FacebookAPI] Error: {e}")
    return f"User {user_id}"

import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app_instance):
    from src.document_loader import DocumentMonitor
    monitor = DocumentMonitor()
    updates = monitor.check_updates()
    if updates:
        print(f"Cảnh báo: {len(updates)} tài liệu mới chưa được index!")
    else:
        print("✓ Vector store đồng bộ.")
    yield

app = FastAPI(title="HaUI Chatbot Facebook API", lifespan=lifespan)
workflow = None
conversation_manager = None
init_lock = asyncio.Lock()

async def get_chatbot():
    global workflow, conversation_manager
    async with init_lock:
        if workflow is None:
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
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403)

@app.post("/webhook")
async def handle_messages(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except:
        return "EMPTY"
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    if "text" in messaging_event["message"]:
                        background_tasks.add_task(process_and_reply, sender_id, messaging_event["message"]["text"])
        return "EVENT_RECEIVED"
    raise HTTPException(status_code=404)

async def process_and_reply(sender_id: str, message_text: str):
    # Fetch profile and chatbot in parallel
    p_task = asyncio.create_task(get_fb_user_profile(sender_id))
    wf_task = asyncio.create_task(get_chatbot())
    user_name = await p_task
    wf, conv_mgr = await wf_task
    try:
        session_id = f"fb_{sender_id}"
        chat_history = conv_mgr.get_history(session_id, limit=10)
        result = wf.run(message_text, session_id=session_id, chat_history=chat_history)
        answer = result['answer']
        # Log to Mongo
        conv_mgr.add_message(session_id, "user", message_text, metadata={"user_name": user_name})
        conv_mgr.add_message(session_id, "assistant", answer, sources=result.get('sources'))
        # Log to Sheets
        gs_logger.append_log(
            user_name=user_name,
            user_id=sender_id,
            question=message_text,
            answer=answer,
            sources=result.get('sources'),
            relevance=result.get('relevance_score', 0.0)
        )
        send_fb_message(sender_id, answer)
        if result.get('sources'):
            drive_links = get_drive_links_for_sources(result['sources'])
            sources_text = "📚 Nguồn tham khảo:\n" + "\n".join([f"• {src}\n  🔗 {drive_links[src]}" if src in drive_links else f"• {src}" for src in result['sources']])
            send_fb_message(sender_id, sources_text)
    except Exception as e:
        print(f"Error: {e}")
        send_fb_message(sender_id, "Sự cố kỹ thuật, vui lòng thử lại sau.")

import re as _re
import html as _html

def _html_to_plain(text: str) -> str:
    text = _html.unescape(text)
    text = _re.sub(r'<br\s*/?>', '\n', text, flags=_re.IGNORECASE)
    text = _re.sub(r'</?p\s*>', '\n', text, flags=_re.IGNORECASE)
    text = _re.sub(r'<li\s*>', '\n• ', text, flags=_re.IGNORECASE)
    text = _re.sub(r'<[^>]+>', '', text)
    text = _re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def send_fb_message(recipient_id: str, message_text: str):
    message_text = _html_to_plain(message_text)
    chunks = [message_text[i:i+1900] for i in range(0, len(message_text), 1900)]
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    for chunk in chunks:
        data = {"recipient": {"id": recipient_id}, "message": {"text": chunk}}
        requests.post(FB_GRAPH_API_URL, params=params, json=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

target_path = r"e:\chatbot_Haui\agentic_chatbot\api\main.py"
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully wrote to main.py")
