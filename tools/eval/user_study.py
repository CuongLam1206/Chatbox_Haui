"""
tools/eval/user_study.py
Công cụ khảo sát User Study cho 30-50 sinh viên.
Chạy chatbot tương tác và thu thập đánh giá (1-5 sao).

Cách dùng:
    python -m tools.eval.user_study
    python -m tools.eval.user_study --output tools/eval/user_study_results.csv
"""
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))


# ─── Bộ câu hỏi gợi ý cho sinh viên thử nghiệm ──────────────────────────────
SUGGESTED_QUESTIONS = [
    "Sinh viên vắng quá bao nhiêu % giờ lý thuyết sẽ bị cấm thi?",
    "Điều kiện bị buộc thôi học là gì?",
    "Điểm F ảnh hưởng đến GPA như thế nào?",
    "Học bổng khuyến khích học tập điều kiện là gì?",
    "Phòng Công tác Sinh viên ở đâu?",
    "Tiết 1 học lúc mấy giờ?",
    "Ngành CNKT Máy tính cố vấn học tập là ai?",
    "Trưởng chương trình CNKT Điện tử - Viễn thông là ai?",
    "Trường SEEE có bao nhiêu sinh viên?",
    "Thủ tục xin hoãn thi như thế nào?",
]

RATING_LABELS = {
    1: "Rất tệ (sai hoàn toàn)",
    2: "Tệ (sai một phần)",
    3: "Trung bình (đúng nhưng thiếu)",
    4: "Tốt (đúng và đủ)",
    5: "Rất tốt (chính xác, có nguồn)",
}


def run_user_study(output_path: str, max_questions: int = 10):
    """Chạy phiên khảo sát tương tác."""
    print("=" * 60)
    print("🎓 HAUI CHATBOT - USER STUDY")
    print("=" * 60)
    print("Cảm ơn bạn đã tham gia khảo sát!")
    print("Bạn sẽ hỏi chatbot và đánh giá câu trả lời (1-5 sao).\n")

    # Lấy thông tin sinh viên
    user_id = input("Mã sinh viên (hoặc 'anonym'): ").strip() or "anonym"
    major = input("Ngành học: ").strip() or "Không biết"

    print("\n⚙️  Đang khởi động chatbot...")
    from core.initialize import initialize_system
    workflow, _, _ = initialize_system()
    print("✓ Chatbot sẵn sàng!\n")

    results = []
    session_history = []

    print("📋 Bạn có thể dùng câu hỏi gợi ý sau:")
    for i, q in enumerate(SUGGESTED_QUESTIONS, 1):
        print(f"  [{i:2}] {q}")

    print("\nNhập số để chọn câu hỏi gợi ý, hoặc gõ câu hỏi của riêng bạn.")
    print("Gõ 'xong' để kết thúc.\n")

    asked = 0
    while asked < max_questions:
        print(f"─── Câu {asked + 1}/{max_questions} {'─' * 40}")
        user_input = input("❓ Câu hỏi: ").strip()

        if user_input.lower() in ("xong", "exit", "quit", "q"):
            break
        if not user_input:
            continue

        # Nếu nhập số → dùng câu gợi ý
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(SUGGESTED_QUESTIONS):
                user_input = SUGGESTED_QUESTIONS[idx]
                print(f"   → {user_input}")
            else:
                print("   Số không hợp lệ, vui lòng nhập lại.")
                continue

        # Gọi chatbot
        t0 = time.time()
        try:
            result = workflow.run(user_input, session_id=f"study_{user_id}", chat_history=session_history)
            latency = round(time.time() - t0, 2)
            answer = result.get("answer", "")
            sources = result.get("sources", [])
        except Exception as e:
            answer = f"[LỖI] {e}"
            sources = []
            latency = 0

        # Hiển thị câu trả lời
        print(f"\n🤖 Chatbot:\n{answer}")
        if sources:
            print(f"\n📚 Nguồn: {', '.join(sources[:3])}")
        print(f"   [{latency}s]")

        # Thu thập đánh giá
        print("\n⭐ Đánh giá câu trả lời:")
        for k, v in RATING_LABELS.items():
            print(f"   {k} - {v}")

        while True:
            rating_str = input("   Đánh giá (1-5): ").strip()
            if rating_str.isdigit() and 1 <= int(rating_str) <= 5:
                rating = int(rating_str)
                break
            print("   Vui lòng nhập từ 1 đến 5.")

        comment = input("   Nhận xét (Enter để bỏ qua): ").strip()

        # Lưu kết quả
        results.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "major": major,
            "question": user_input,
            "answer": answer[:200],  # Trim for CSV
            "sources": "; ".join(sources),
            "rating": rating,
            "comment": comment,
            "latency_sec": latency,
        })

        # Cập nhật history
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": answer})

        asked += 1
        print()

    # ─── In tóm tắt ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ KHẢO SÁT")
    print("=" * 60)
    if results:
        avg_rating = sum(r["rating"] for r in results) / len(results)
        print(f"  Số câu hỏi       : {len(results)}")
        print(f"  Đánh giá TB      : {avg_rating:.2f}/5.0 ⭐")
        print(f"  Câu trả lời tốt  : {sum(1 for r in results if r['rating'] >= 4)}/{len(results)}")
        dist = {i: sum(1 for r in results if r['rating'] == i) for i in range(1, 6)}
        print(f"  Phân phối       : {dist}")

    # ─── Lưu file CSV ───────────────────────────────────────────────────────
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(output_path).exists()
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Kết quả lưu tại: {output_path}")
    print("Cảm ơn bạn đã tham gia khảo sát! 🙏")
    return results


def analyze_results(results_path: str):
    """Phân tích tổng hợp file CSV của nhiều sinh viên."""
    import pandas as pd  # Optional, graceful fallback
    try:
        df = pd.read_csv(results_path, encoding="utf-8")
    except ImportError:
        print("[Phân tích] Cần cài pandas: pip install pandas")
        # Fallback: đọc CSV thủ công
        with open(results_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        ratings = [int(r["rating"]) for r in rows]
        print(f"  Tổng phiếu      : {len(rows)}")
        print(f"  Đánh giá TB     : {sum(ratings)/len(ratings):.2f}/5.0")
        print(f"  Câu tốt (≥4⭐)  : {sum(1 for r in ratings if r >= 4)}/{len(ratings)}")
        return

    print("\n" + "=" * 60)
    print("📊 PHÂN TÍCH USER STUDY TỔNG HỢP")
    print("=" * 60)
    print(f"  Tổng phiếu            : {len(df)}")
    print(f"  Số sinh viên          : {df['user_id'].nunique()}")
    print(f"  Đánh giá trung bình   : {df['rating'].mean():.2f}/5.0 ⭐")
    print(f"  Tỷ lệ hài lòng (≥4⭐) : {(df['rating'] >= 4).mean():.1%}")
    print(f"  Avg Latency           : {df['latency_sec'].mean():.2f}s")
    print(f"\n  Phân phối rating:\n{df['rating'].value_counts().sort_index().to_string()}")
    if "major" in df.columns:
        print(f"\n  Theo ngành:\n{df.groupby('major')['rating'].mean().round(2).to_string()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HaUI Chatbot User Study")
    parser.add_argument("--output", default="tools/eval/user_study_results.csv")
    parser.add_argument("--max", type=int, default=10, help="Số câu hỏi tối đa/phiên")
    parser.add_argument("--analyze", action="store_true", help="Phân tích file CSV đã có")
    args = parser.parse_args()

    if args.analyze:
        analyze_results(args.output)
    else:
        run_user_study(args.output, args.max)
