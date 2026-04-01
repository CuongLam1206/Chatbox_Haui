# Báo cáo Đánh giá Chính thức — Chatbot HaUI

> **Ngày:** 2026-03-24 | **Bộ test:** 33 câu / 5 nhóm / 3 mức độ khó  
> **Phương pháp:** 3 lần chạy độc lập, session riêng mỗi câu  
> **Judge:** Rule-based (keyword overlap) — LLM Judge fallback do Gemini API timeout

---

## 1. Kết quả Trung bình (3 lần chạy)

| Metric | Run 1 | Run 2 | Run 3 | **Mean** |
|---|:---:|:---:|:---:|:---:|
| **Accuracy** | 100% | 100% | 100% | **100%** |
| **Source Hit Rate** | 100% | 100% | 100% | **100%** |
| **Faithfulness** | 0.9546 | 0.9610 | 0.9656 | **0.9604** |
| **Hallucination Rate** | 4.54% | 3.90% | 3.44% | **3.96%** |
| **Avg Latency** | 4.84s | 4.67s | 4.57s | **4.69s** |

> **Nhận xét:** Accuracy và Source Hit Rate ổn định **100% qua cả 3 lần**, Faithfulness biến thiên nhỏ (σ ≈ 0.005).

---

## 2. Phân tích theo Nhóm

| Nhóm | Chủ đề | Acc | SHR | Câu |
|---|---|:---:|:---:|:---:|
| G1 | Quy chế đào tạo | 100% | 100% | 10 |
| G2 | Học bổng, chính sách sinh viên | 100% | 100% | 7 |
| G3 | Thông tin Trường SEEE | 100% | 100% | 8 |
| G4 | Thời khóa biểu | 100% | 100% | 6 |
| G5 | Câu hỏi phức hợp (cross-document) | 100% | 100% | 2 |

---

## 3. Ablation Study — B0 vs B1 vs B3

### Mô tả Baselines

| Baseline | Mô tả | Đặc điểm |
|---|---|---|
| **B0** | LLM thuần (Gemini 2.0 Flash, không RAG) | Nhanh, nhưng bịa thông tin |
| **B1** | Naive RAG (vector top-3, không rerank/grade) | Trung thực hơn B0, nhưng thiếu context |
| **B3** | Agentic RAG (full pipeline) | Chính xác nhất, latency cao hơn |

### Phân tích định tính

**B0 — LLM thuần:**
- ❌ Hallucinate: G1-001 nói vắng >**20%** bị cấm thi (thực tế 30%)
- ❌ Bịa tên: G3-003 bịa Hiệu trưởng, G3-008 bịa Trưởng chương trình
- ❌ Không có thông tin domain: Không biết giờ tiết học, địa chỉ, nhân sự
- ⚠️ Dài dòng, nhiều disclaimer

**B1 — Naive RAG:**
- ❌ Retrieval sai chunk → G1-001 "không có thông tin"
- ❌ Không đủ context cho câu phức hợp (G5)
- ✅ Trung thực: Khi không biết → nói "không có" thay vì bịa

**B3 — Agentic RAG:**
- ✅ 33/33 correct (100%)
- ✅ Citation cụ thể: Trích dẫn điều khoản, số liệu chính xác
- ✅ Cross-document: G5-001 kết hợp quy định đạo văn + quy chế đào tạo

### Case Studies

| Case | B0 | B1 | B3 |
|---|---|---|---|
| **G1-001** (Vắng thi) | ❌ "20%" (bịa) | ❌ Không tìm thấy | ✅ ">30%, nhận F" |
| **G3-003** (Hiệu trưởng) | ❌ Bịa tên sai | ❌ "Không có thông tin" | ✅ PGS.TS Hoàng Mạnh Kha |
| **G5-001** (Đạo văn + thôi học) | ⚠️ Chung chung | ❌ Thiếu context | ✅ Chi tiết theo Điều 11 |

---

## 4. Nhận xét & Hạn chế

### Điểm mạnh
- Accuracy **100%** ổn định qua 3 lần chạy
- Source Hit Rate **100%** — retrieval pipeline hoạt động tốt
- Faithfulness **96.04%** — mức hallucination thấp (~4%)
- Agentic RAG vượt trội rõ rệt so với B0 (LLM thuần) và B1 (Naive RAG)

### Hạn chế
- **Bộ test 33 câu** — đủ cho pilot study nhưng chưa đủ cho statistical test sâu
- **Judge rule-based** (keyword overlap) — LLM Judge bị fallback do API timeout
- **Latency trung bình 4.69s** — chấp nhận được nhưng cao hơn B0/B1
- **Ablation chưa có metrics định lượng** cho B0/B1 — chỉ phân tích định tính
