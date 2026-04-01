# Hướng dẫn Evaluation Framework

## Cấu trúc thư mục

```
tools/eval/
├── test_set.json         # 35 câu hỏi test (5 nhóm)
├── run_evaluation.py     # Chạy chatbot trên test set
├── compute_metrics.py    # Tính metrics + báo cáo
├── ablation_study.py     # So sánh B0 vs B1 vs B3
├── results.json          # (generated) Kết quả thô
├── results_metrics.json  # (generated) Kết quả đã tính metrics
└── README.md             # File này
```

---

## Workflow đầy đủ

### Bước 1 – Chạy evaluation trên Agentic RAG (B3)
```bash
# Tắt server trước, rồi:
python -m tools.eval.run_evaluation
# Hoặc chạy thử 10 câu đầu:
python -m tools.eval.run_evaluation --max 10
```

### Bước 2 – Tính metrics
```bash
python -m tools.eval.compute_metrics
# Không có Gemini API key:
python -m tools.eval.compute_metrics --no-llm
```

### Bước 3 – Ablation Study (so sánh B0 → B3)
```bash
python -m tools.eval.ablation_study --max 10
```

---

## Metrics được tính

| Metric | Mô tả |
|---|---|
| **Accuracy** | % câu trả lời đúng (LLM judge) |
| **Source Hit Rate** | % câu có tài liệu nguồn đúng |
| **Faithfulness** | Điểm 0-1, câu trả lời không bịa đặt |
| **Hallucination Rate** | 1 - Faithfulness |
| **Avg Latency** | Thời gian phản hồi trung bình (giây) |

---

## Thêm câu hỏi mới vào test set

Chỉnh sửa `test_set.json`, thêm theo format:
```json
{
  "id": "G1-011",
  "group": "G1_quy_che",
  "question": "...",
  "ground_truth": "...",
  "source_doc": "Tên tài liệu",
  "difficulty": "easy|medium|hard",
  "type": "factual|inference|list|calculation|boolean|multi_doc"
}
```

---

## Baselines cho Ablation Study

| Baseline | Mô tả |
|---|---|
| B0 | LLM thuần (Gemini, không RAG) |
| B1 | Naive RAG (vector search top-3, không grade) |
| B3 | **Agentic RAG** (hệ thống hiện tại) |
