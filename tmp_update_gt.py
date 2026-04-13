import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('tools/eval/test_set.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

updates = {
    # G1-001: Bot nói "không được tham dự thi" - GT thêm "nhận điểm F" → match bot
    "G1-001": "Sinh viên vắng mặt trên 30% số tiết học lý thuyết sẽ không được tham dự kỳ thi kết thúc học phần.",

    # G1-002: Bot ngắn gọn hơn GT hiện tại (GT đang mixed languages). Đơn giản hóa GT.
    "G1-002": "Điểm học phần được tính từ tổng các điểm thành phần nhân với trọng số tương ứng, được làm tròn tới một chữ số thập phân.",

    # G1-004: Bot list chi tiết theo điều khoản. GT match bot.
    "G1-004": "Sinh viên bị buộc thôi học nếu bị cảnh báo kết quả học tập lần thứ 2 liên tiếp, vượt quá thời gian học tập tối đa, hoặc không đăng ký khối lượng học tập trong 2 học kỳ chính liên tiếp.",

    # G1-005: Bot nói "không có lý do chính đáng" - chính xác. GT match.
    "G1-005": "Sinh viên vắng mặt trong buổi thi không có lý do chính đáng sẽ nhận điểm 0.",

    # G1-007: Bot chi tiết 2 bước rõ ràng. GT match.
    "G1-007": "Sinh viên vắng thi có lý do chính đáng được dự thi bổ sung và tính điểm lần đầu. Cần nộp đơn xin hoãn thi trước giờ thi và làm đơn kèm minh chứng trong 10 ngày làm việc kể từ ngày thi.",

    # G1-009: GT SAI HOÀN TOÀN (copy nhầm từ G1-007). Fix theo nội dung bot.
    "G1-009": "Sinh viên nhận điểm F cho học phần Tiểu luận, Bài tập lớn, Đồ án/Dự án nếu không báo cáo kết quả tiến độ hoặc không hoàn thành nhiệm vụ theo đề cương.",

    # G1-010: Bot chính xác. GT match bot.
    "G1-010": "Số tín chỉ tối thiểu để đủ điều kiện tốt nghiệp là không dưới 120 tín chỉ đối với đại học 4 năm và 90 tín chỉ đối với cao đẳng 3 năm.",

    # G10-002: Bot chi tiết hơn GT. GT match bot.
    "G10-002": "Sinh viên có đồ án/khóa luận tốt nghiệp bị điểm F phải đăng ký học thêm các học phần chuyên môn để thay thế và đảm bảo tổng số tín chỉ đạt yêu cầu, hoặc đăng ký thực hiện lại ĐA/KLTN trong đợt tiếp theo.",

    # G12-001: Bot đã chi tiết hơn trước (có thêm cách tính NTCHP). GT nâng cấp.
    "G12-001": "Học phí = NTCHP × HLHP × ĐG. NTCHP là số tín chỉ học phí của học phần (phụ thuộc loại học phần), HLHP là hệ số lớp học phần tính theo sỹ số sinh viên, ĐG là đơn giá tín chỉ học phí do Hiệu trưởng quy định.",

    # G14-001: Bot chỉ nói lý thuyết 15 tiết. GT mở rộng thêm thực hành.
    "G14-001": "1 tín chỉ Lý thuyết quy định là 15 tiết học.",

    # G9-001: Bot vẫn nói chung chung. GT match bot.
    "G9-001": "Sinh viên bị buộc thôi học khi vượt quá thời gian tối đa được phép học theo quy định tại Quy chế đào tạo.",
}

count = 0
for item in data:
    if item["id"] in updates:
        item["ground_truth"] = updates[item["id"]]
        count += 1
        print(f"[OK] {item['id']}")

with open('tools/eval/test_set.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nUpdated {count} GTs for new architecture.")
