# -*- coding: utf-8 -*-
"""
FastAPI Server for Facebook Messenger Webhook
With Google Sheets logging and Facebook Profile integration
"""
import os
import sys
import asyncio
import re as _re
import html as _html
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.initialize import initialize_system

load_dotenv(root_dir / ".env")

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
FB_GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"

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
                merged.append(f"{line.rstrip(chr(58))} : {next_line}")
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


def get_drive_links_for_sources(sources):
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

# ======== Google Sheets Logging ========
from src.google_sheets_handler import GoogleSheetsLogger
gs_logger = GoogleSheetsLogger()

# ======== Facebook User Profile Cache ========
_user_names = {}


def fetch_fb_user_name(user_id):
    """Fetch user name from Facebook Graph API."""
    global _user_names
    if user_id in _user_names:
        return _user_names[user_id]
    try:
        url = f"https://graph.facebook.com/v19.0/{user_id}"
        params = {"fields": "first_name,last_name", "access_token": FB_PAGE_ACCESS_TOKEN}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            full_name = (data.get("last_name", "") + " " + data.get("first_name", "")).strip()
            if full_name:
                _user_names[user_id] = full_name
                print(f"[FB] Name for {user_id}: {full_name}")
                return full_name
    except Exception as e:
        print(f"[FB] Profile error: {e}")
    fallback = f"User_{user_id[-4:]}"
    _user_names[user_id] = fallback
    return fallback


@asynccontextmanager
async def lifespan(app_instance):
    from src.document_loader import DocumentMonitor
    monitor = DocumentMonitor()
    updates = monitor.check_updates()
    if updates:
        print(f"WARNING: {len(updates)} documents need re-indexing!")
    else:
        print("Vector store is up to date.")
    yield


app = FastAPI(title="HaUI Chatbot Facebook API", lifespan=lifespan)
workflow = None
conversation_manager = None
init_lock = asyncio.Lock()


async def get_chatbot():
    global workflow, conversation_manager
    async with init_lock:
        if workflow is None:
            print("Initializing Chatbot System...")
            from concurrent.futures import ThreadPoolExecutor
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                workflow, conversation_manager, _ = await loop.run_in_executor(pool, initialize_system)
    return workflow, conversation_manager


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_messages(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except Exception:
        return "EMPTY_BODY"
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                msg = event.get("message", {})
                if msg and "text" in msg:
                    sid = event["sender"]["id"]
                    txt = msg["text"]
                    print(f"Received from {sid}: {txt}")
                    background_tasks.add_task(process_and_reply, sid, txt)
        return "EVENT_RECEIVED"
    raise HTTPException(status_code=404)


async def process_and_reply(sender_id: str, message_text: str):
    """Process message via RAG and reply, with logging to MongoDB + Google Sheets."""
    user_name = fetch_fb_user_name(sender_id)
    wf, conv_mgr = await get_chatbot()
    try:
        session_id = f"fb_{sender_id}"
        chat_history = conv_mgr.get_history(session_id, limit=10)
        result = wf.run(message_text, session_id=session_id, chat_history=chat_history)
        answer = result["answer"]

        # Log to MongoDB
        conv_mgr.add_message(session_id, "user", message_text, metadata={"user_name": user_name})
        conv_mgr.add_message(session_id, "assistant", answer, sources=result.get("sources"))

        # Log to Google Sheets
        gs_logger.append_log(
            user_name=user_name,
            user_id=sender_id,
            question=message_text,
            answer=answer,
            sources=result.get("sources"),
            relevance=result.get("relevance_score", 0.0),
        )

        send_fb_message(sender_id, answer)

        if result.get("sources"):
            drive_links = get_drive_links_for_sources(result["sources"])
            lines = []
            for src in result["sources"]:
                if src in drive_links:
                    lines.append(f"- {src}\n  Link: {drive_links[src]}")
                else:
                    lines.append(f"- {src}")
            sources_text = "Nguon tham khao:\n" + "\n".join(lines)
            send_fb_message(sender_id, sources_text)
    except Exception as e:
        print(f"Error: {e}")
        send_fb_message(sender_id, "Xin loi, toi gap su co ky thuat. Vui long thu lai sau.")


def _html_to_plain(text):
    text = _html.unescape(text)
    text = _re.sub(r"<br\\s*/?>", "\n", text, flags=_re.IGNORECASE)
    text = _re.sub(r"</?p\\s*>", "\n", text, flags=_re.IGNORECASE)
    text = _re.sub(r"<li\\s*>", "\n- ", text, flags=_re.IGNORECASE)
    text = _re.sub(r"<[^>]+>", "", text)
    text = _re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send_fb_message(recipient_id, message_text):
    message_text = _html_to_plain(message_text)
    MAX_LEN = 1900
    chunks = [message_text[i:i + MAX_LEN] for i in range(0, len(message_text), MAX_LEN)]
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    for chunk in chunks:
        payload = {"recipient": {"id": recipient_id}, "message": {"text": chunk}}
        resp = requests.post(FB_GRAPH_API_URL, params=params, headers=headers, json=payload)
        if resp.status_code != 200:
            print(f"FB send error: {resp.status_code} - {resp.text}")
        else:
            print(f"Message sent to {recipient_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
