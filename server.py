"""
FastAPI Server for Render Deployment
Backend only — Facebook Messenger webhook.
"""
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from typing import List

from core.initialize import initialize_system

# ══════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════
PORT = int(os.getenv("PORT", 10000))

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
FB_GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"

DOCUMENTS_DIR = Path(__file__).parent / "data" / "documents"
LINK_FILE = DOCUMENTS_DIR / "Link_nguon.md"

# ══════════════════════════════════════════════════════════════
# Drive Links
# ══════════════════════════════════════════════════════════════
_drive_links: dict = {}


def load_drive_links():
    global _drive_links
    if not LINK_FILE.exists():
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

# ══════════════════════════════════════════════════════════════
# Chatbot init (lazy)
# ══════════════════════════════════════════════════════════════
workflow = None
conversation_manager = None
init_lock = asyncio.Lock()


def _init_sync():
    print("🚀 Initializing Chatbot System...")
    return initialize_system()


async def get_chatbot():
    global workflow, conversation_manager
    async with init_lock:
        if workflow is None:
            from concurrent.futures import ThreadPoolExecutor
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                wf, cm, _ = await loop.run_in_executor(pool, _init_sync)
            workflow, conversation_manager = wf, cm
    return workflow, conversation_manager


# ══════════════════════════════════════════════════════════════
# FastAPI App
# ══════════════════════════════════════════════════════════════
app = FastAPI(title="HaUI Chatbot API")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "chatbot_loaded": workflow is not None}


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
                if event.get("message") and "text" in event["message"]:
                    sender_id = event["sender"]["id"]
                    message_text = event["message"]["text"]
                    print(f"FB Message from {sender_id}: {message_text}")
                    background_tasks.add_task(process_and_reply, sender_id, message_text)
        return "EVENT_RECEIVED"
    raise HTTPException(status_code=404)


async def process_and_reply(sender_id: str, message_text: str):
    import requests
    import re as _re
    import html as _html

    wf, conv_mgr = await get_chatbot()

    try:
        session_id = f"fb_{sender_id}"
        chat_history = conv_mgr.get_history(session_id, limit=10)
        result = wf.run(message_text, session_id=session_id, chat_history=chat_history)
        answer = result["answer"]

        conv_mgr.add_message(session_id, "user", message_text)
        conv_mgr.add_message(session_id, "assistant", answer, sources=result.get("sources"))

        # HTML → plain text
        plain = _html.unescape(answer)
        plain = _re.sub(r"<br\s*/?>", "\n", plain, flags=_re.IGNORECASE)
        plain = _re.sub(r"</?p\s*>", "\n", plain, flags=_re.IGNORECASE)
        plain = _re.sub(r"<li\s*>", "\n• ", plain, flags=_re.IGNORECASE)
        plain = _re.sub(r"<[^>]+>", "", plain)
        plain = _re.sub(r"\n{3,}", "\n\n", plain).strip()

        _send_fb(sender_id, plain)

        if result.get("sources"):
            drive_links = get_drive_links_for_sources(result["sources"])
            lines = []
            for src in result["sources"]:
                if src in drive_links:
                    lines.append(f"• {src}\n  🔗 {drive_links[src]}")
                else:
                    lines.append(f"• {src}")
            _send_fb(sender_id, "📚 Nguồn tham khảo:\n" + "\n".join(lines))

    except Exception as e:
        print(f"Error: {e}")
        _send_fb(sender_id, "Xin lỗi, tôi gặp sự cố. Vui lòng thử lại sau.")


def _send_fb(recipient_id: str, text: str):
    import requests as req

    MAX_LEN = 1900
    chunks = [text[i : i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for chunk in chunks:
        resp = req.post(
            FB_GRAPH_API_URL,
            params={"access_token": FB_PAGE_ACCESS_TOKEN},
            headers={"Content-Type": "application/json"},
            json={"recipient": {"id": recipient_id}, "message": {"text": chunk}},
        )
        if resp.status_code != 200:
            print(f"FB send failed: {resp.status_code} - {resp.text}")


# ══════════════════════════════════════════════════════════════
# Run
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    print(f"\n{'=' * 50}")
    print(f"🚀 HaUI Chatbot API — port {PORT}")
    print(f"   Webhook: http://0.0.0.0:{PORT}/webhook")
    print(f"   Health:  http://0.0.0.0:{PORT}/health")
    print(f"{'=' * 50}\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
