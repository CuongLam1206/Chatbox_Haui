# 🚀 Hướng Dẫn Deploy Chatbot HaUI lên Facebook Messenger

Tài liệu này hướng dẫn từng bước để kết nối chatbot với Facebook Messenger thông qua Facebook Webhooks và Ngrok tunnel.

---

## 📋 Yêu Cầu Trước Khi Bắt Đầu

| Yêu cầu | Ghi chú |
|---|---|
| Python ≥ 3.10 | Đã cài môi trường ảo |
| MongoDB Atlas | Lưu lịch sử hội thoại |
| Tài khoản Facebook Developer | [developers.facebook.com](https://developers.facebook.com) |
| Tài khoản Ngrok | [ngrok.com](https://ngrok.com) (Free tier đủ dùng) |
| Gemini API Key | Hoặc OpenAI / Groq |

---

## 🔑 Bước 1 – Cấu Hình File `.env`

Mở file `.env` ở thư mục gốc dự án và điền các giá trị sau:

```env
# ===== LLM (chọn 1 provider) =====
USE_GEMINI=true
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-2.0-flash

# ===== MongoDB =====
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxx.mongodb.net/
MONGODB_DATABASE=agentic_rag_db

# ===== Ngrok =====
NGROK_AUTHTOKEN=<your_ngrok_authtoken>
# Lấy tại: https://dashboard.ngrok.com/get-started/your-authtoken

# ===== Facebook Messenger =====
FB_PAGE_ACCESS_TOKEN=<your_page_access_token>
FB_VERIFY_TOKEN=haui_chatbot_2024
FB_APP_SECRET=<your_app_secret>
```

> **Lưu ý**: `FB_VERIFY_TOKEN` là chuỗi tự đặt, dùng để xác thực webhook với Facebook (bước 4).

---

## 🏗️ Bước 2 – Tạo Facebook App & Page

### 2.1. Tạo Facebook App

1. Truy cập [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Chọn **Tạo ứng dụng** → chọn loại **Business**
3. Đặt tên app (ví dụ: `HaUI Chatbot`) → Tạo

### 2.2. Thêm sản phẩm Messenger

1. Trong Dashboard của App → **Add Product** → chọn **Messenger** → **Set Up**

### 2.3. Tạo hoặc kết nối Facebook Page

1. Cuộn xuống mục **Access Tokens**
2. Chọn page muốn kết nối (hoặc tạo page mới)
3. Cấp quyền và lấy **Page Access Token** → dán vào `.env` (`FB_PAGE_ACCESS_TOKEN`)

### 2.4. Lấy App Secret

1. **Settings** → **Basic** → Copy **App Secret** → dán vào `.env` (`FB_APP_SECRET`)

---

## 📦 Bước 3 – Cài Đặt Dependencies

```bash
# Kích hoạt môi trường ảo
agentic_rag\Scripts\activate     # Windows
# hoặc
source agentic_rag/bin/activate  # Linux/Mac

# Cài packages (bao gồm fastapi, uvicorn, pyngrok)
pip install -r requirements.txt
pip install pyngrok
```

---

## 🔧 Bước 4 – Khởi Tạo Vector Database

> Chỉ cần chạy lần đầu hoặc khi thêm tài liệu mới.

```bash
cd e:\chatbot_Haui\agentic_chatbot
python -m core.initialize
```

Lệnh này sẽ:
- Load tài liệu từ `data/documents/`
- Chunk theo Điều/Phụ lục (semantic chunking)
- Build ChromaDB embeddings + BM25 index

---

## ▶️ Bước 5 – Chạy FastAPI Server

Mở **Terminal 1** và chạy:

```bash
cd e:\chatbot_Haui\agentic_chatbot
python api/main.py
```

Server khởi động tại: `http://localhost:8000`

Kiểm tra server đang chạy:

```bash
curl http://localhost:8000/docs
```

---

## 🌐 Bước 6 – Tạo Ngrok Tunnel

Mở **Terminal 2** và chạy:

```bash
cd e:\chatbot_Haui\agentic_chatbot
python api/start_tunnel.py
```

Kết quả mẫu:

```
[SUCCESS] Tunnel đã được tạo!
URL công khai của bạn là: https://xxxx-xxx-xxx.ngrok-free.app
Dán link này vào Facebook Webhook: https://xxxx-xxx-xxx.ngrok-free.app/webhook
```

> ⚠️ **Lưu ý**: URL ngrok thay đổi mỗi lần restart (Free tier). Cần cập nhật lại webhook Facebook mỗi lần.

---

## ⚙️ Bước 7 – Cấu Hình Webhook trên Facebook

1. Quay lại Facebook Developer Dashboard → **Messenger** → **Settings**
2. Tìm mục **Webhooks** → click **Add Callback URL**
3. Điền:
   - **Callback URL**: `https://xxxx-xxx-xxx.ngrok-free.app/webhook`
   - **Verify Token**: `haui_chatbot_2024` (giá trị `FB_VERIFY_TOKEN` trong `.env`)
4. Click **Verify and Save**
   - ✅ Facebook sẽ gọi `GET /webhook` để xác thực token
   - Nếu server đang chạy đúng, sẽ trả về `WEBHOOK_VERIFIED`

### 7.1. Subscribe Events

Sau khi verify thành công:
1. Trong mục **Webhooks** → **Add Subscriptions**
2. Chọn page muốn subscribe
3. Tick vào **`messages`** → Save

---

## ✅ Bước 8 – Test Chatbot

1. Mở Facebook và nhắn tin vào **Page** đã kết nối
2. Kiểm tra Terminal 1 (FastAPI) sẽ in ra log:

   ```
   Received message from <sender_id>: <nội dung tin nhắn>
   Initializing Chatbot System...  ← (chỉ lần đầu)
   Message chunk sent to <sender_id>
   ```

3. Chatbot sẽ trả lời trong Messenger

---

## 🔄 Quy Trình Luồng Dữ Liệu

```
Facebook Messenger
      ↓  (POST /webhook)
FastAPI Server (port 8000)
      ↓
Ngrok Tunnel (public URL)
      ↓
LangGraph Workflow
  ├── Router → classify intent
  ├── Rewriter → improve query
  ├── Retrieval → ChromaDB + BM25
  ├── Grader → filter docs
  ├── Reranker → sort by relevance
  └── Generator → craft answer
      ↓
Facebook Graph API → gửi reply
      ↓
Facebook Messenger (user nhận tin)
```

---

## 🐛 Troubleshooting

### ❌ Webhook Verification Failed (403)

- Kiểm tra `FB_VERIFY_TOKEN` trong `.env` phải khớp với giá trị nhập trên Facebook Dashboard
- Đảm bảo FastAPI server đang chạy trước khi verify

### ❌ Ngrok URL không hoạt động

- Restart `python api/start_tunnel.py` và cập nhật lại Callback URL trên Facebook
- Kiểm tra `NGROK_AUTHTOKEN` trong `.env` có đúng không

### ❌ Bot không trả lời tin nhắn

- Kiểm tra `FB_PAGE_ACCESS_TOKEN` còn hiệu lực (token có thể hết hạn)
- Đảm bảo subscription event **`messages`** đã được tick
- Xem log Terminal 1 để debug lỗi

### ❌ Lần đầu bot chậm (~30-60s)

- Bình thường – hệ thống đang khởi tạo embedding model và load ChromaDB
- Các tin nhắn tiếp theo sẽ nhanh hơn

### ❌ Tin nhắn bị cắt

- Bot tự động chia nhỏ câu trả lời nếu vượt 1900 ký tự (giới hạn Facebook là 2000)
- Người dùng sẽ nhận nhiều tin nhắn liên tiếp

---

## 📁 Cấu Trúc Files Liên Quan

```
agentic_chatbot/
├── api/
│   ├── main.py           # FastAPI server + webhook handler
│   └── start_tunnel.py   # Khởi động Ngrok tunnel
├── core/
│   └── initialize.py     # Khởi tạo vector DB + workflow
├── .env                  # Biến môi trường (FB token, Ngrok, LLM key)
└── requirements.txt      # Dependencies
```

---

## 🔁 Workflow Hàng Ngày (Sau Khi Setup Lần Đầu)

```bash
# Terminal 1: Chạy chatbot server
cd e:\chatbot_Haui\agentic_chatbot
agentic_rag\Scripts\activate
python api/main.py

# Terminal 2: Chạy tunnel (song song)
python api/start_tunnel.py
# → Copy URL mới → Cập nhật Callback URL trên Facebook Dashboard
```
