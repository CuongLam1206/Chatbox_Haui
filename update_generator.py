import os

file_path = 'src/agents/generator.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '2.7. **TUYỆT ĐỐI KHÔNG nói "Tôi chưa có thông tin" nếu ngữ cảnh CÓ CHỨA câu trả lời.**\nHãy đọc kỹ TOÀN BỘ ngữ cảnh bao gồm bảng, danh sách, sơ đồ tổ chức, thông tin liên hệ.\n- Nếu tên người, chức danh, số điện thoại xuất hiện trong ngữ cảnh → PHẢI trích xuất và trả lời.\n- Chỉ nói "chưa có thông tin" khi THỰC SỰ không có dữ liệu nào liên quan trong ngữ cảnh.'

replacement = target + '\n\n2.8. **ƯU TIÊN TRẢ LỜI TRỰC TIẾP:**\n- Luôn đưa ra **KẾT LUẬN CHÍNH** (Có/Không/Được/Không được/Đúng/Sai...) ngay dòng đầu tiên nếu câu hỏi là dạng xác nhận.\n- Nếu câu hỏi gồm nhiều vế (do hệ thống tách truy vấn), hãy đánh số thứ tự (1, 2...) để trả lời rõ ràng từng vế.\n- Tuyệt đối không giải thích lan man về các hình thức xử lý nếu câu hỏi chỉ hỏi về "có được hưởng quyền lợi X không".\n\n2.9. **XỬ LÝ MÂU THUẪN:** Nếu các đoạn ngữ cảnh có thông tin mâu thuẫn nhau, hãy ưu tiên thông tin từ văn bản có Ngày ban hành mới nhất hoặc Quyết định có số hiệu lớn hơn.'

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated generator.py")
else:
    print("Target content not found in generator.py")
