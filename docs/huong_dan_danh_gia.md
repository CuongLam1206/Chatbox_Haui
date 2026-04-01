# Hướng dẫn Đánh giá Hệ thống Chatbot HaUI — Chuẩn bị Paper NCKH

## 1. Tổng quan Pipeline Đánh giá

```
test_set.json (33 câu)
        │
        ▼
run_evaluation.py ──► results.json (predicted + latency)
        │
        ▼
compute_metrics.py ──► results_metrics.json (+ accuracy, faithfulness, source hit)
        │
        ▼
ablation_study.py ──► ablation_results.json (B0 vs B1 vs B3)
```

### Các Metric đánh giá

| Metric | Ý nghĩa | Cách tính |
|---|---|---|
| **Accuracy** | Tỷ lệ câu trả lời đúng | LLM Judge (Gemini) so sánh predicted vs ground_truth |
| **Source Hit Rate** | Tỷ lệ trích đúng nguồn | Keyword match giữa returned sources và expected source |
| **Faithfulness** | Độ trung thực (0-1) | LLM Judge: câu trả lời có bịa thêm không? |
| **Hallucination Rate** | Tỷ lệ bịa đặt | `1 - Faithfulness` |
| **Avg Latency** | Thời gian trung bình | `time(end) - time(start)` cho mỗi câu |

### Hai chế độ đánh giá

| Chế độ | Flag | Đánh giá bởi | Ưu / nhược |
|---|---|---|---|
| **LLM Judge** | (mặc định) | Gemini 2.0 Flash | Chính xác hơn, tốn API, chậm hơn |
| **Rule-based** | `--no-llm` | Keyword overlap | Nhanh, miễn phí, kém chính xác |

> [!IMPORTANT]
> **Cho paper NCKH:** Phải dùng **LLM Judge** (không có `--no-llm`) để kết quả có giá trị khoa học.

---

## 2. Quy trình Chạy Đánh giá Chính thức

### Bước 0: Đảm bảo server chưa chạy (tránh conflict)
```bash
# Đóng hết server đang chạy (nếu có)
```

### Bước 1: Chạy Evaluation chính (33 câu)
```bash
cd E:\chatbot_Haui\agentic_chatbot
conda activate agentic_rag

python -m tools.eval.run_evaluation
```
- Kết quả: `tools/eval/results.json`
- Thời gian: ~150-180s

### Bước 2: Đánh giá bằng LLM Judge
```bash
python -m tools.eval.compute_metrics
```
- **KHÔNG thêm `--no-llm`** — dùng Gemini để đánh giá chất lượng
- Kết quả: `tools/eval/results_metrics.json`

### Bước 3: Ablation Study (B0 vs B1 vs B3)
```bash
python -m tools.eval.ablation_study
```
- Kết quả: `tools/eval/ablation_results.json`
- Thời gian: ~10-15 phút (chạy 33 câu × 3 baselines)
- Có thể chạy nhanh với `--max 10` để test trước

### Bước 4: Copy kết quả vào docs
```bash
copy tools\eval\results_metrics.json docs\results_metrics.json
copy tools\eval\ablation_results.json docs\ablation_results.json
copy tools\eval\test_set.json docs\test_set.json
```

---

## 3. Bộ Test Set (33 câu / 5 nhóm)

| Nhóm | Chủ đề | Số câu | Nguồn tài liệu |
|---|---|---|---|
| G1 | Quy chế đào tạo | 10 | Quy chế QĐ 744 + 666 |
| G2 | Học bổng, học phí, chính sách | 7 | NĐ 81-2021, QĐ 1148 |
| G3 | Thông tin nhân sự SEEE | 8 | Giới thiệu SEEE 2025 |
| G4 | Thời khóa biểu, giờ học | 6 | Giới thiệu SEEE 2025 |
| G5 | Câu hỏi phức hợp đa tài liệu | 2 | Nhiều nguồn |

### Phân bố độ khó

| Mức | Số câu | Mô tả |
|---|---|---|
| Easy | 19 | Hỏi thẳng 1 thông tin cụ thể |
| Medium | 11 | Cần tổng hợp/so sánh |
| Hard | 3 | Liên kết đa tài liệu |

---

## 4. Ablation Study — 3 Baselines

| Baseline | Cấu hình | Mục đích so sánh |
|---|---|---|
| **B0 – LLM thuần** | Gemini 2.0 Flash, không RAG | Đánh giá hallucination khi không có tài liệu |
| **B1 – Naive RAG** | Vector search top-3, không grading | So sánh hiệu quả của grading + reranking |
| **B3 – Agentic RAG** | Full pipeline (routing, grading, reranking) | Hệ thống hoàn chỉnh |

---

## 5. Cấu hình Hệ thống (ghi vào paper)

| Thành phần | Cấu hình |
|---|---|
| Mô hình sinh (Generator) | Gemini 2.0 Flash |
| Router / Grader / Reranker | Gemini 2.0 Flash |
| Embedding | `dangvantuan/vietnamese-embedding` (768d) |
| Retrieval | Hybrid Vector (0.5) + BM25 (0.5), k=12 |
| Vector DB | ChromaDB |
| Corpus | 30+ tài liệu nội bộ HaUI |

---

## 6. Checklist Trước khi Chạy Đánh giá Chính thức

- [ ] Đã rebuild vector store: `python -m core.initialize --rebuild`
- [ ] Server KHÔNG đang chạy (tránh conflict port)
- [ ] Kết nối internet ổn định (LLM Judge cần Gemini API)
- [ ] API key Gemini còn quota
- [ ] `test_set.json` đã là bản final (33 câu)
- [ ] Chạy `run_evaluation` (Bước 1)
- [ ] Chạy `compute_metrics` KHÔNG có `--no-llm` (Bước 2)
- [ ] Chạy `ablation_study` (Bước 3)
- [ ] Copy kết quả vào `docs/` (Bước 4)

---

## 7. Lưu ý Quan trọng cho Paper

> [!WARNING]
> **Trước đây dùng `--no-llm`** (rule-based) để đánh giá nhanh trong lúc debug.
> Kết quả `--no-llm` **KHÔNG phù hợp** cho paper vì chỉ dùng keyword overlap đơn giản.

> [!TIP]
> Nên chạy evaluation **3 lần** và lấy trung bình để kết quả ổn định hơn (do LLM có tính non-deterministic).
