# 🚀 Hướng Dẫn Kết Nối Chatbot với Fanpage Chính Thức (Production)

Tài liệu này hướng dẫn các bước để chuyển từ Fanpage thử nghiệm sang **Fanpage thật của HaUI** và chạy trên server **Render**.

---

## 🛠️ Bước 1 – Lấy Page Access Token mới

Để Server có thể trả lời tin nhắn trên Fanpage thật, bạn cần một Token riêng cho Page đó:

1. Truy cập [Facebook Developers](https://developers.facebook.com) và chọn App của bạn.
2. Tại menu bên trái, chọn **Messenger** → **Settings**.
3. Cuộn xuống mục **Access Tokens**.
4. Nhấp vào **Add or Remove Pages**.
5. Chọn đúng **Fanpage chính thức của trường**.
6. Sau khi chọn, nhấn nút **Generate Token** bên cạnh tên Fanpage đó.
7. **Copy Token này** và lưu vào một nơi an toàn. 

> [!CAUTION]
> Page Access Token này có quyền gửi tin nhắn thay mặt Fanpage. Tuyệt đối không chia sẻ hoặc up lên GitHub công khai.

---

## ☁️ Bước 2 – Cập nhật Webhook Callback URL

Nếu bạn đang dùng link Ngrok (cũ), hãy chuyển sang link Render để server chạy 24/7:

1. Copy URL service của bạn trên Render (Ví dụ: `https://haui-chatbot.onrender.com`).
2. Quay lại Facebook App → **Messenger** → **Settings** → **Webhooks**.
3. Nhấp **Edit** tại dòng Callback URL.
4. Điền URL mới: `https://your-app-name.onrender.com/webhook` (phải có `/webhook` ở cuối).
5. Verify Token: Điền `haui_chatbot_2024` (giống trong file `.env` hoặc Render Dashboard).
6. Nhấp **Verify and Save**.

---

## ⚙️ Bước 3 – Cấu hình Biến Môi Trường trên Render

1. Truy cập [Render Dashboard](https://dashboard.render.com).
2. Chọn Web Service `haui-chatbot`.
3. Vào mục **Environment** ở menu bên trái.
4. Tìm biến `FB_PAGE_ACCESS_TOKEN`.
5. Thay đổi giá trị cũ bằng **Page Access Token mới** bạn vừa lấy ở Bước 1.
6. Nhấp **Save Changes**.
7. Render sẽ tự động thực hiện **Deploy** lại một bản mới để cập nhật token.

---

## 📢 Bước 4 – Chế độ Live & App Review (QUAN TRỌNG)

Nếu bạn muốn bất kỳ ai cũng có thể nhắn tin cho bot (không chỉ Admin/Tester):

1. **Chuyển App sang Mode Live**: Ở thanh trên cùng của Facebook Developer, gạt nút **App Mode** từ *Development* sang *Live*.
2. **App Review**:
   - Vào mục **App Review** → **Permissions and Features**.
   - Tìm quyền `pages_messaging`.
   - Nhấp **Request Advanced Access**.
   - Facebook sẽ yêu cầu bạn mô tả cách bot hoạt động (Video quay cảnh nhắn tin với bot) để họ duyệt. 
   - *Lưu ý: Trong lúc chờ duyệt, bot vẫn hoạt động bình thường với những người có vai trò Admin, Developer, hoặc Tester trong App.*

---

## 🔍 Bước 5 – Kiểm tra kết quả

1. Dùng một tài khoản có quyền Admin/Tester nhắn tin vào Fanpage trường.
2. Kiểm tra phần **Logs** trên Render:
   - Nếu thấy dòng `Received message from <sender_id>...` là server đã nhận được tin.
   - Nếu bot trả lời trên Messenger là bạn đã kết nối thành công!

---

> [!TIP]
> Nếu bot không trả lời, hãy kiểm tra lại mục **Webhooks** → **Add Subscriptions** trên Facebook, đảm bảo fanpage mới đã được tick chọn sự kiện `messages`. 
