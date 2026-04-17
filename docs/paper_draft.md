**XÂY DỰNG HỆ THỐNG CHATBOT TRỢ LÝ SINH VIÊN THÔNG MINH DỰA TRÊN KIẾN TRÚC AGENTIC RAG TẠI TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP HÀ NỘI**

DEVELOPMENT OF AN INTELLIGENT STUDENT ASSISTANT CHATBOT BASED ON AGENTIC RAG ARCHITECTURE AT HANOI UNIVERSITY OF INDUSTRY

Lâm Đức Cường¹,*
¹Khoa Điện tử, Trường Điện — Điện tử, Trường Đại học Công nghiệp Hà Nội
*E-mail: lamcuongghj@gmail.com
Số điện thoại: 0342322899

---

## TÓM TẮT

<<<<<<< HEAD
Bài báo trình bày việc thiết kế và xây dựng hệ thống chatbot trợ lý sinh viên thông minh tại Trường Đại học Công nghiệp Hà Nội (HaUI), dựa trên kiến trúc Agentic RAG (Retrieval-Augmented Generation) kết hợp nhiều tác tử chuyên biệt. Hệ thống sử dụng mô hình ngôn ngữ lớn Gemini 2.0 Flash kết hợp với cơ chế truy xuất lai (Hybrid Search) gồm tìm kiếm ngữ nghĩa (ChromaDB) và tìm kiếm từ khóa (BM25) theo tỷ lệ 50:50. Kiến trúc đa tác tử bao gồm: Router phân loại truy vấn, Rewriter cải thiện câu hỏi, Grader đánh giá tài liệu theo lô, Reranker sắp xếp lại kết quả, và Generator tổng hợp câu trả lời. Thuật toán chia tách ngữ nghĩa (Semantic Chunking) được thiết kế riêng cho văn bản pháp quy tiếng Việt, bảo toàn cấu trúc Điều – Khoản – Phụ lục. Kết quả đánh giá bằng framework RAGAS trên bộ 64 câu hỏi thực tế cho thấy hệ thống đạt Faithfulness 98,20%, Context Recall 100%, Context Precision 93,58%, Answer Relevancy 77,80% và Answer Correctness 87,61% — vượt trội so với kiến trúc Naive RAG và các phương pháp cải tiến hiện hành. Hệ thống đã được triển khai trên Facebook Messenger phục vụ sinh viên toàn trường.
=======
Bài báo trình bày việc thiết kế và xây dựng hệ thống chatbot trợ lý sinh viên thông minh tại Trường Đại học Công nghiệp Hà Nội (HaUI), dựa trên kiến trúc Agentic RAG (Retrieval-Augmented Generation) kết hợp nhiều tác tử chuyên biệt. Hệ thống sử dụng mô hình ngôn ngữ lớn Gemini 2.0 Flash kết hợp với cơ chế truy xuất lai (Hybrid Search) gồm tìm kiếm ngữ nghĩa (ChromaDB) và tìm kiếm từ khóa (BM25) theo tỷ lệ 50:50. Kiến trúc đa tác tử bao gồm: Router phân loại truy vấn, Rewriter cải thiện câu hỏi, Grader đánh giá tài liệu theo lô, Reranker sắp xếp lại kết quả, và Generator tổng hợp câu trả lời. Thuật toán chia tách ngữ nghĩa (Semantic Chunking) được thiết kế riêng cho văn bản pháp quy tiếng Việt, bảo toàn cấu trúc Điều – Khoản – Phụ lục. Kết quả đánh giá bằng framework RAGAS trên bộ 64 câu hỏi thực tế cho thấy hệ thống đạt Faithfulness 99,22%, Context Recall 100%, Context Precision 91,10%, Answer Relevancy 78,02% và Answer Correctness 85,35% — vượt trội so với kiến trúc Naive RAG và các phương pháp cải tiến hiện hành. Hệ thống đã được triển khai trên Facebook Messenger phục vụ sinh viên toàn trường.
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837

**Từ khóa:** Truy xuất tăng cường sinh; Mô hình ngôn ngữ lớn; Chatbot đa tác tử; Tìm kiếm lai; Văn bản pháp quy tiếng Việt

---

## ABSTRACT

<<<<<<< HEAD
This paper presents the design and implementation of an intelligent student assistant chatbot at Hanoi University of Industry (HaUI), based on the Agentic RAG (Retrieval-Augmented Generation) architecture integrating multiple specialized agents. The system employs the Gemini 2.0 Flash large language model combined with a Hybrid Search mechanism consisting of semantic search (ChromaDB) and keyword search (BM25) at a 50:50 ratio. The multi-agent architecture includes: a Router for query classification into six routes, a Rewriter for query optimization, a Grader for batch document relevance evaluation, a Reranker for result re-ordering, and a Generator for answer synthesis. A domain-specific Semantic Chunking algorithm is designed for Vietnamese legal documents, preserving the structural integrity of Articles, Clauses, and Appendices. Evaluation using the RAGAS framework on a 64-question real-world test set achieves Faithfulness of 98.20%, Context Recall of 100%, Context Precision of 93.58%, Answer Relevancy of 77.80%, and Answer Correctness of 87.61% — significantly outperforming Naive RAG and state-of-the-art approaches including CRAG and Self-RAG. The system has been deployed on Facebook Messenger to serve all university students.
=======
This paper presents the design and implementation of an intelligent student assistant chatbot at Hanoi University of Industry (HaUI), based on the Agentic RAG (Retrieval-Augmented Generation) architecture integrating multiple specialized agents. The system employs the Gemini 2.0 Flash large language model combined with a Hybrid Search mechanism consisting of semantic search (ChromaDB) and keyword search (BM25) at a 50:50 ratio. The multi-agent architecture includes: a Router for query classification into six routes, a Rewriter for query optimization, a Grader for batch document relevance evaluation, a Reranker for result re-ordering, and a Generator for answer synthesis. A domain-specific Semantic Chunking algorithm is designed for Vietnamese legal documents, preserving the structural integrity of Articles, Clauses, and Appendices. Evaluation using the RAGAS framework on a 64-question real-world test set achieves Faithfulness of 99.22%, Context Recall of 100%, Context Precision of 91.10%, Answer Relevancy of 78.02%, and Answer Correctness of 85.35% — significantly outperforming Naive RAG and state-of-the-art approaches including CRAG and Self-RAG. The system has been deployed on Facebook Messenger to serve all university students.
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837

**Keywords:** Retrieval-Augmented Generation; Large Language Models; Multi-agent chatbot; Hybrid search; Vietnamese legal documents

---

## CHỮ VIẾT TẮT

| Viết tắt | Ý nghĩa |
|----------|----------|
| RAG | Retrieval-Augmented Generation (Sinh tăng cường truy xuất) |
| LLM | Large Language Model (Mô hình ngôn ngữ lớn) |
| HaUI | Hanoi University of Industry (Trường Đại học Công nghiệp Hà Nội) |
| BM25 | Best Matching 25 (Thuật toán xếp hạng từ khóa) |
| CSDL | Cơ sở dữ liệu |
| API | Application Programming Interface (Giao diện lập trình ứng dụng) |
| RAGAS | Retrieval Augmented Generation Assessment (Đánh giá hệ thống RAG) |
| CRAG | Corrective Retrieval-Augmented Generation |

---

## 1. GIỚI THIỆU

### 1.1. Đặt vấn đề

Trong bối cảnh chuyển đổi số toàn diện tại các cơ sở giáo dục đại học, nhu cầu tự động hóa việc tra cứu thông tin, quy chế đào tạo và hỗ trợ sinh viên ngày càng trở nên cấp thiết. Trường Đại học Công nghiệp Hà Nội (HaUI) hiện quản lý một hệ thống văn bản quy phạm phức tạp bao gồm nhiều quyết định, quy chế, quy định và phụ lục liên quan đến đào tạo, thi cử, kỷ luật, học bổng, và các thủ tục hành chính. Sinh viên thường gặp khó khăn trong việc tìm kiếm thông tin chính xác từ khối lượng tài liệu lớn này, dẫn đến tình trạng quá tải cho phòng Đào tạo và phòng Công tác Sinh viên.

Các giải pháp chatbot truyền thống dựa trên quy tắc (Rule-based) hoặc mẫu câu cố định (Pattern matching) có nhiều hạn chế: không thể hiểu ngữ cảnh, khó mở rộng, và không xử lý được câu hỏi phức hợp. Gần đây, công nghệ RAG (Retrieval-Augmented Generation) [1] đã chứng minh hiệu quả vượt trội trong việc kết hợp khả năng truy xuất tri thức từ CSDL với năng lực sinh ngôn ngữ tự nhiên của LLM, giải quyết vấn đề "ảo giác" (hallucination) — hiện tượng LLM tự bịa đặt thông tin không có trong nguồn dữ liệu [4].

Tuy nhiên, kiến trúc RAG cơ bản (Naive RAG) vẫn tồn tại nhiều điểm yếu đã được chỉ ra trong các nghiên cứu tổng quan [2]: (1) Truy vấn gốc của người dùng thường mơ hồ hoặc thiếu ngữ cảnh, dẫn đến kết quả truy xuất kém chính xác; (2) Tất cả tài liệu truy xuất được đều được đưa vào LLM mà không qua bước sàng lọc, gây nhiễu thông tin; (3) Không có cơ chế kiểm tra tính trung thực (faithfulness) của câu trả lời so với ngữ cảnh truy xuất. Các giải pháp cải tiến gần đây như CRAG (Corrective RAG) [5] bổ sung bộ đánh giá truy xuất, Self-RAG [6] tích hợp cơ chế tự phản hồi, nhưng mỗi phương pháp thường chỉ giải quyết được 1-2 trong số các hạn chế trên.

### 1.2. Mục tiêu nghiên cứu

Nghiên cứu này đề xuất và xây dựng hệ thống chatbot sử dụng kiến trúc **Agentic RAG** — một biến thể nâng cao của RAG truyền thống [7] — trong đó quy trình xử lý truy vấn được điều phối bởi nhiều tác tử (agent) chuyên biệt, mỗi tác tử đảm nhận một vai trò riêng biệt trong luồng xử lý. So với các phương pháp hiện có, hệ thống đề xuất kết hợp đồng thời cả 5 kỹ thuật nâng cao (Rewrite, Grade, Rerank, Route, Hallucination Check) trong một pipeline thống nhất. Các đóng góp chính của bài báo bao gồm:

1. **Kiến trúc đa tác tử thủ công (Procedural Multi-Agent)**: Thiết kế luồng xử lý tuần tự có kiểm soát bằng Python thuần với 6 tác tử chuyên biệt và 6 routes phân loại ý định, cho phép kiểm soát chặt chẽ từng bước xử lý mà vẫn đảm bảo tính mô-đun và dễ mở rộng.
2. **Thuật toán chia tách ngữ nghĩa cho văn bản pháp quy tiếng Việt**: Phát triển module Semantic Chunking chuyên biệt, sử dụng biểu thức chính quy (Regex) để nhận diện và bảo toàn cấu trúc Chương – Điều – Khoản – Phụ lục — một đóng góp mới chưa được đề cập trong các nghiên cứu trước.
3. **Cơ chế đánh giá tài liệu theo lô (Batch Grading)**: Giảm số lượng API call từ *k* xuống còn 1 so với phương pháp đánh giá từng tài liệu riêng lẻ của CRAG [5].
4. **Cơ chế truy xuất lai (Hybrid Search) kết hợp tiêm tri thức theo ý định**: Kết hợp tìm kiếm ngữ nghĩa và từ khóa, bổ sung chiến lược chủ động tiêm Điều/Khoản liên quan dựa trên phân tích ý định truy vấn.
5. **Triển khai thực tế**: Hệ thống được triển khai trên nền tảng Facebook Messenger thông qua FastAPI webhook, phục vụ sinh viên toàn trường với khả năng xử lý đồng thời nhiều người dùng.

---

## 2. CƠ SỞ LÝ THUYẾT VÀ PHƯƠNG PHÁP NGHIÊN CỨU

### 2.1. Retrieval-Augmented Generation (RAG)

RAG là kiến trúc kết hợp hai thành phần chính được đề xuất bởi Lewis và cộng sự [1]: (1) Bộ truy xuất (Retriever) tìm kiếm các đoạn tài liệu liên quan từ CSDL tri thức; và (2) Bộ sinh (Generator) sử dụng LLM để tổng hợp câu trả lời dựa trên ngữ cảnh được truy xuất. Quá trình RAG cơ bản được mô tả như sau:

Cho truy vấn *q* của người dùng, bộ truy xuất tìm tập tài liệu liên quan *D = {d₁, d₂, ..., dₖ}* từ CSDL, sau đó bộ sinh tạo câu trả lời *a* dựa trên cặp *(q, D)*:

> **a = LLM(q, D)** &emsp;&emsp;&emsp; (1)

Theo phân loại của Gao và cộng sự [2], RAG phát triển qua 3 giai đoạn: Naive RAG (chỉ truy xuất và sinh), Advanced RAG (bổ sung tiền xử lý truy vấn hoặc hậu xử lý kết quả), và Modular RAG (kết hợp linh hoạt nhiều module). Hệ thống đề xuất trong nghiên cứu này thuộc loại Modular RAG với kiến trúc đa tác tử.

### 2.2. Các phương pháp cải tiến RAG hiện có

**Corrective RAG (CRAG)** [5] bổ sung bộ đánh giá truy xuất (Retrieval Evaluator) phân loại tài liệu thành 3 mức: Correct, Incorrect, Ambiguous. Khi tài liệu bị đánh giá kém, CRAG sử dụng tìm kiếm web thay thế. Tuy nhiên, CRAG đánh giá từng tài liệu riêng lẻ (cần *k* lần gọi LLM) và không có cơ chế phân loại ý định hay sắp xếp lại kết quả.

**Self-RAG** [6] huấn luyện LLM tự sinh "reflection tokens" để đánh giá chất lượng truy xuất và câu trả lời. Phương pháp này đạt hiệu quả cao nhưng yêu cầu fine-tuning mô hình LLM, điều không phải lúc nào cũng khả thi với các mô hình thương mại như Gemini hoặc GPT.

**Adaptive RAG** sử dụng bộ phân loại để quyết định truy vấn nào cần truy xuất và truy vấn nào có thể trả lời trực tiếp. Tuy nhiên, phương pháp này chỉ hỗ trợ 2 routes (retrieval / no-retrieval), chưa đáp ứng được yêu cầu phân loại chi tiết trong domain chuyên biệt.

### 2.3. Agentic RAG

Agentic RAG [7] là hướng phát triển mới nhất, biến đổi quy trình RAG từ pipeline tĩnh thành một hệ thống đa tác tử tự chủ. Khác với RAG truyền thống, Agentic RAG sử dụng các tác tử trung gian để kiểm soát chất lượng ở từng giai đoạn. Luồng xử lý được mở rộng thành:

> **a = G(Rₖ(F(E(q, H))))** &emsp;&emsp;&emsp; (2)

Trong đó: *E* là hàm cải thiện truy vấn (Rewrite) có tính đến lịch sử hội thoại *H*; *F* là hàm lọc tài liệu (Grade + Rerank); *Rₖ* là bộ truy xuất lai lấy *k* tài liệu hàng đầu; *G* là bộ sinh câu trả lời cuối cùng.

### 2.4. Tìm kiếm lai (Hybrid Search)

Tìm kiếm ngữ nghĩa (Vector Search) hoạt động tốt khi truy vấn diễn đạt khác so với văn bản gốc nhưng cùng ý nghĩa. Ngược lại, BM25 [3] hiệu quả khi truy vấn chứa các thuật ngữ chính xác (ví dụ: "Điều 9", "Phụ lục 07"). Nhiều nghiên cứu đã chỉ ra rằng kết hợp hai phương pháp (hybrid search) có thể cải thiện 10-25% độ chính xác truy xuất so với dùng đơn lẻ. Phương pháp Ensemble kết hợp cả hai:

> **Score(d, q) = w₁ · Sim_vector(d, q) + w₂ · BM25(d, q)** &emsp;&emsp;&emsp; (3)

Trong đó *w₁ = w₂ = 0,5* là trọng số cho mỗi phương pháp tìm kiếm.

### 2.5. Mô hình nghiên cứu đề xuất

Hình 1 mô tả kiến trúc tổng thể của hệ thống Agentic RAG được đề xuất:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NGƯỜI DÙNG (Sinh viên)                       │
│                   Gradio UI │ Facebook Messenger                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Câu hỏi
                             ▼
                    ┌─────────────────┐
                    │  ROUTER AGENT   │  Phân loại: 6 routes
                    └────────┬────────┘
           ┌─────────┬──────┼──────┬──────────┬────────────┐
           ▼         ▼      ▼      ▼          ▼            ▼
       greeting   general  learn  out_of   document    vectorstore
       (trả lời  (hội     (lưu   scope    generation  (RAG đầy đủ)
        trực     thoại)   slang)  (từ      (trích               
        tiếp)                     chối)    xuất trực            
                                           tiếp)               
                                    │            │
                                    ▼            ▼
                              ┌──────────┐  ┌──────────┐
                              │ RETRIEVE │  │ REWRITER │
                              │ + Filter │  └────┬─────┘
                              │ metadata │       ▼
                              └────┬─────┘  ┌──────────┐
                                   │        │ RETRIEVE  │
                                   ▼        └────┬──────┘
                              ┌──────────┐       ▼
                              │  Direct  │  ┌──────────┐
                              │ Extract  │  │  GRADER  │ Batch grading
                              └────┬─────┘  └────┬─────┘
                                   │             ▼
                                   │        ┌──────────┐
                                   │        │ RERANKER │
                                   │        └────┬─────┘
                                   │             ▼
                                   │        ┌──────────┐
                                   │        │GENERATOR │
                                   │        └────┬─────┘
                                   ▼             ▼
                              ┌──────────────────────┐
                              │   CÂU TRẢ LỜI       │
                              │ + Nguồn tham khảo    │
                              └──────────────────────┘
```
*Hình 1. Kiến trúc tổng thể hệ thống Agentic RAG đề xuất*

---

## 3. KẾT QUẢ NGHIÊN CỨU VÀ THẢO LUẬN

### 3.1. Thiết kế hệ thống đa tác tử

Hệ thống được triển khai gồm 6 tác tử chuyên biệt, mỗi tác tử được thiết kế theo nguyên tắc đơn nhiệm (Single Responsibility). Bảng 1 trình bày chi tiết chức năng từng tác tử.

**Bảng 1. Danh sách các tác tử và chức năng**

| STT | Tác tử | Chức năng | LLM Call |
|-----|--------|-----------|----------|
| 1 | Router | Phân loại truy vấn vào 1 trong 6 routes bằng structured output | 1 call |
| 2 | Rewriter | Cải thiện truy vấn, bổ sung ngữ cảnh từ lịch sử hội thoại | 1 call |
| 3 | Grader | Đánh giá đồng thời độ liên quan của tất cả tài liệu (Batch grading) | 1 call |
| 4 | Reranker | Chấm điểm 1-10 và sắp xếp lại tài liệu theo độ chính xác | 1 call |
| 5 | Generator | Tổng hợp câu trả lời từ tài liệu đã lọc, kèm trích dẫn nguồn | 1 call |
| 6 | Hallucination Checker | Kiểm tra tính trung thực của câu trả lời so với ngữ cảnh | 1 call (tùy chọn) |

Đặc biệt, hệ thống sử dụng cơ chế **Batch Grading** — tất cả tài liệu được đánh giá đồng thời trong một lần gọi LLM duy nhất thay vì gọi riêng lẻ từng tài liệu. So với CRAG [5] — phương pháp đánh giá từng tài liệu cần *k* lần gọi API riêng biệt — Batch Grading giảm đáng kể số lượng API call (từ *k* call xuống còn 1 call, với *k* = 12 là số tài liệu truy xuất), tiết kiệm chi phí và giảm độ trễ mà không ảnh hưởng đến chất lượng đánh giá.

**Router Agent** phân loại truy vấn vào 6 routes — chi tiết hơn so với Adaptive RAG (2 routes) và CRAG (3 mức confidence). Các routes bao gồm: `greeting` (chào hỏi), `general` (hội thoại chung), `learn` (học slang sinh viên), `out_of_scope` (từ chối câu hỏi ngoài phạm vi), `document_generation` (trích xuất phụ lục/biểu mẫu), và `vectorstore` (RAG đầy đủ). Việc phân loại chi tiết giúp tối ưu luồng xử lý — chỉ các truy vấn thuộc `vectorstore` mới cần trải qua toàn bộ pipeline, giảm chi phí và độ trễ cho các truy vấn đơn giản.

### 3.2. Thuật toán chia tách ngữ nghĩa cho văn bản pháp quy

Văn bản quy chế đào tạo tiếng Việt có cấu trúc phân cấp rõ ràng: Chương → Điều → Khoản → Điểm. Việc sử dụng phương pháp chia tách theo kích thước cố định (Fixed-size chunking) phổ biến trong RAG truyền thống sẽ phá vỡ cấu trúc này, dẫn đến mất ngữ cảnh khi truy xuất. Đây là vấn đề đã được nhận diện trong các nghiên cứu về RAG cho văn bản pháp luật [14], tuy nhiên chưa có giải pháp nào được thiết kế riêng cho cấu trúc Điều – Khoản của văn bản pháp quy tiếng Việt.

Module `LegalDocumentChunker` được phát triển với thuật toán xử lý 3 bước:

**Bước 1: Nhận diện Chương.** Sử dụng biểu thức chính quy hỗ trợ đa định dạng (Markdown heading `##`, bold `**`, và ký tự La Mã):

```
^(?:#{1,3}\s+)?(?:\*\*)?(?:Chương|CHƯƠNG)\s+([IVXLC]+)
```

**Bước 2: Nhận diện Điều/Phụ lục.** Mỗi Điều hoặc Phụ lục được tách thành một chunk độc lập, kèm metadata ghi chú Chương chứa nó:

```
^(?:#{1,3}\s+)?(?:\*\*)?(?:Điều|Phụ lục|Slide)\s+(\d+)
```

**Bước 3: Xử lý Điều dài.** Khi nội dung một Điều vượt quá ngưỡng kích thước tối đa (mặc định 2.000 ký tự), hệ thống tiếp tục chia nhỏ theo ranh giới Khoản (pattern: `^\d+\.\s+`), đảm bảo mỗi chunk con vẫn giữ tiêu đề Điều ở đầu để không mất ngữ cảnh.

Mỗi chunk được gắn metadata phong phú phục vụ cho việc lọc chính xác:

```python
metadata = {
    'chunk_type': 'article',    # article | article_part | header
    'article': '07',            # Số Điều/Phụ lục
    'chapter': 'Chương II: ...', # Chương chứa Điều này
    'complete': True,           # Điều này có đầy đủ hay bị chia nhỏ
    'source': 'qd-1532.md'     # File nguồn
}
```

So với phương pháp Parent-Child Chunking phổ biến [2] chỉ hỗ trợ 2 cấp độ phân cấp, thuật toán đề xuất xử lý được 3 cấp độ chính thống (Chương – Điều – Khoản) cùng với metadata nhận diện Phụ lục, cho phép lọc chính xác theo số Điều hoặc Chương cụ thể.

### 3.3. Cơ chế truy xuất lai và tiêm tri thức theo ý định

Hệ thống sử dụng `EnsembleRetriever` [8] kết hợp ChromaDB [9] (Vector Search) và BM25 (Keyword Search) với trọng số bằng nhau (0,5 : 0,5). Mỗi truy vấn truy xuất 12 tài liệu (*k* = 12).

Ngoài cơ chế truy xuất tiêu chuẩn, hệ thống bổ sung chiến lược **Intent-based Article Injection** — phát hiện ý định cụ thể của truy vấn thông qua phân tích từ khóa và chủ động tiêm thêm các Điều liên quan vào đầu danh sách kết quả. Chiến lược này hoạt động như một "shortcut" bổ sung cho Hybrid Search, đặc biệt hiệu quả với các truy vấn mà người dùng không đề cập trực tiếp đến số Điều cần tìm. Bảng 2 trình bày các quy tắc tiêm tri thức.

**Bảng 2. Các quy tắc tiêm tri thức theo ý định**

| Ý định phát hiện | Từ khóa kích hoạt | Điều được tiêm |
|------------------|--------------------|-------|
| Đối tượng miễn/giảm học phí | "đối tượng", "miễn", "học phí" | Điều 4, 5 (QĐ 29.1148) |
| Phương pháp đánh giá học phần | "đánh giá", "học phần" | Điều 9 (Quy chế) |
| Điều kiện xét học bổng | "học bổng", "điều kiện" | Điều 4 (QĐ 725) |
| Truy vấn địa điểm | "ở đâu", "liên hệ", "tầng" | Boost tài liệu SEEE.md |

Sự kết hợp giữa Hybrid Search và Intent-based Article Injection là yếu tố chính giúp hệ thống đạt Context Recall 100% — bộ truy xuất không bỏ sót bất kỳ thông tin cần thiết nào.

### 3.4. Cơ chế xử lý đặc biệt cho truy vấn phụ lục

Khi Router phân loại truy vấn thuộc route `document_generation` (yêu cầu xuất phụ lục, biểu mẫu), hệ thống áp dụng luồng xử lý tối ưu:

1. **Bỏ qua Rewrite**: Sử dụng nguyên truy vấn gốc để tìm kiếm, tránh LLM làm sai lệch số phụ lục.
2. **Lọc Metadata chính xác**: Trích xuất số phụ lục bằng regex (ví dụ: `phụ lục\s*(\d+)`), sau đó lọc kết quả theo trường `article` trong metadata.
3. **Bỏ qua Grading và Reranking**: Tiết kiệm 2 lần gọi LLM vì kết quả lọc metadata đã đảm bảo độ chính xác tuyệt đối.
4. **Trích xuất nguyên văn**: Thông qua tác tử Generator được cấu hình bằng Prompt đặc thù (System Rule), nội dung biểu mẫu và phụ lục được LLM trích xuất vào câu trả lời với định dạng giữ nguyên bản thay vì tóm tắt, đảm bảo tính toàn vẹn của văn bản hành chính.

### 3.5. Kết quả đánh giá bằng RAGAS

Hệ thống được đánh giá bằng framework RAGAS (Retrieval Augmented Generation Assessment) [11] — bộ công cụ đánh giá chuẩn quốc tế dành riêng cho hệ thống RAG, sử dụng Gemini 2.0 Flash làm LLM Judge. RAGAS cung cấp 5 chỉ số đo lường độc lập cho 2 thành phần: Retrieval (truy xuất) và Generation (sinh câu trả lời).

Bộ test gồm **64 câu hỏi thực tế** được xây dựng dựa trên các câu hỏi phổ biến của sinh viên, chia thành 5 nhóm: Quy chế đào tạo, Học bổng — Học phí, Thông tin tổ chức SEEE, Thời khóa biểu, và Câu hỏi phức hợp đa tài liệu. Kết quả tổng hợp được trình bày trong bảng 3.

**Bảng 3. Kết quả đánh giá hệ thống bằng RAGAS (64 câu hỏi)**

| Chỉ số RAGAS | Thành phần đánh giá | Kết quả |
|--------------|--------------------|---------| 
<<<<<<< HEAD
| Faithfulness (Độ trung thực) | Generation | **98,20%** |
| Context Recall (Độ phủ ngữ cảnh) | Retrieval | **100%** |
| Context Precision (Độ chính xác ngữ cảnh) | Retrieval | **93,58%** |
| Answer Relevancy (Độ liên quan câu trả lời) | Generation | **77,80%** |
| Answer Correctness (Độ chính xác câu trả lời) | End-to-End | **87,61%** |

**Phân tích kết quả chi tiết:**

*Về Faithfulness (98,20%):* Đây là chỉ số quan trọng nhất, đo lường mức độ câu trả lời bám sát ngữ cảnh truy xuất được mà không bịa đặt thông tin. Kết quả 98,20% chứng tỏ hệ thống gần như loại bỏ hoàn toàn hiện tượng ảo giác. Kết quả này tương đương mức yêu cầu của các hệ thống RAG trong lĩnh vực y tế (>95%) và vượt xa mức trung bình 70-85% của Naive RAG [2].

*Về Context Recall (100%):* Bộ truy xuất tìm được đầy đủ 100% thông tin cần thiết từ CSDL cho mọi câu hỏi trong bộ test — nhờ sự kết hợp hiệu quả giữa Hybrid Search (Vector + BM25) và chiến lược tiêm tri thức theo ý định (Intent-based Article Injection).

*Về Context Precision (93,58%):* Chỉ số này đánh giá khả năng xếp hạng ưu tiên tài liệu liên quan hàng đầu. Kết quả 93,58% cho thấy tài liệu đúng được đẩy lên vị trí cao trong danh sách kết quả nhờ Grader Agent loại bỏ tài liệu không liên quan và Reranker Agent chấm điểm lại.

*Về Answer Relevancy (77,80%):* Chỉ số thấp hơn do đặc thù thiết kế: hệ thống được cấu hình trả lời chi tiết, đầy đủ (bao gồm trích dẫn Điều, Khoản cụ thể và liên kết Google Drive) thay vì trả lời ngắn gọn. RAGAS phạt điểm khi câu trả lời chứa thông tin bổ sung ngoài phạm vi câu hỏi, mặc dù thông tin bổ sung này có giá trị thực tiễn cho sinh viên.

*Về Answer Correctness (87,61%):* Chỉ số End-to-End kết hợp cả semantic similarity và factual correctness giữa câu trả lời và ground truth. Kết quả 87,61% cho thấy hệ thống trả lời chính xác và đầy đủ so với đáp án tham chiếu.
=======
| Faithfulness (Độ trung thực) | Generation | **99,22%** |
| Context Recall (Độ phủ ngữ cảnh) | Retrieval | **100%** |
| Context Precision (Độ chính xác ngữ cảnh) | Retrieval | **91,10%** |
| Answer Relevancy (Độ liên quan câu trả lời) | Generation | **78,02%** |
| Answer Correctness (Độ chính xác câu trả lời) | End-to-End | **85,35%** |

**Phân tích kết quả chi tiết:**

*Về Faithfulness (99,22%):* Đây là chỉ số quan trọng nhất, đo lường mức độ câu trả lời bám sát ngữ cảnh truy xuất được mà không bịa đặt thông tin. Kết quả 99,22% chứng tỏ hệ thống gần như loại bỏ hoàn toàn hiện tượng ảo giác. Kết quả này vượt mức yêu cầu của các hệ thống RAG trong lĩnh vực y tế (>95%) và vượt xa mức trung bình 70-85% của Naive RAG [2].

*Về Context Recall (100%):* Bộ truy xuất tìm được đầy đủ 100% thông tin cần thiết từ CSDL cho mọi câu hỏi trong bộ test — nhờ sự kết hợp hiệu quả giữa Hybrid Search (Vector + BM25) và chiến lược tiêm tri thức theo ý định (Intent-based Article Injection).

*Về Context Precision (91,10%):* Chỉ số này đánh giá khả năng xếp hạng ưu tiên tài liệu liên quan hàng đầu. Kết quả 91,10% cho thấy tài liệu đúng được đẩy lên vị trí cao trong danh sách kết quả nhờ Grader Agent loại bỏ tài liệu không liên quan và Reranker Agent chấm điểm lại.

*Về Answer Relevancy (78,02%):* Chỉ số thấp hơn do đặc thù thiết kế: hệ thống được cấu hình trả lời chi tiết, đầy đủ (bao gồm trích dẫn Điều, Khoản cụ thể và liên kết Google Drive) thay vì trả lời ngắn gọn. RAGAS phạt điểm khi câu trả lời chứa thông tin bổ sung ngoài phạm vi câu hỏi, mặc dù thông tin bổ sung này có giá trị thực tiễn cho sinh viên.

*Về Answer Correctness (85,35%):* Chỉ số End-to-End kết hợp cả semantic similarity và factual correctness giữa câu trả lời và ground truth. Kết quả 85,35% cho thấy hệ thống trả lời chính xác và đầy đủ so với đáp án tham chiếu.
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837

### 3.6. So sánh với các phương pháp tiếp cận khác

#### 3.6.1. So sánh kiến trúc

Bảng 4 so sánh chi tiết các thành phần kiến trúc giữa hệ thống đề xuất và các phương pháp RAG hiện có trong tài liệu nghiên cứu.

**Bảng 4. So sánh kiến trúc Agentic RAG đề xuất với các phương pháp khác**

| Thành phần | Naive RAG [1] | CRAG [5] | Self-RAG [6] | Adaptive RAG | **Agentic RAG (đề xuất)** |
|------------|:---:|:---:|:---:|:---:|:---:|
| Cải thiện truy vấn | ✗ | ✗ | ✗ | ✗ | **✓ (Rewriter Agent)** |
| Phân loại ý định | ✗ | ✗ | ✗ | ✓ (2 routes) | **✓ (6 routes)** |
| Đánh giá tài liệu | ✗ | ✓ (Evaluator, *k* calls) | ✗ | ✗ | **✓ (Batch Grading, 1 call)** |
| Sắp xếp lại kết quả | ✗ | ✗ | ✗ | ✗ | **✓ (Reranker Agent)** |
| Kiểm tra ảo giác | ✗ | ✗ | ✓ (Reflection tokens) | ✗ | **✓ (HallucinationChecker)** |
| Tìm kiếm lai | ✗ | ✗ | ✗ | ✗ | **✓ (BM25 + Vector)** |
| Chunking chuyên biệt | ✗ | ✗ | ✗ | ✗ | **✓ (VN Legal Semantic)** |
| Web search fallback | ✗ | ✓ | ✗ | ✗ | ✗ (closed-domain) |
| Cần fine-tuning LLM | ✗ | ✗ | ✓ | ✗ | **✗** |
| Số LLM calls/query | 1 | 2 + *k* | 2-4 | 1-2 | **4-5** |

Hệ thống đề xuất kết hợp đồng thời 5 kỹ thuật nâng cao (Rewrite, Grade, Rerank, Route, Hallucination Check), trong khi các phương pháp hiện có thường chỉ áp dụng 1-2 kỹ thuật. Điều này cho phép kiểm soát chất lượng ở mọi giai đoạn của pipeline.

#### 3.6.2. So sánh hiệu suất RAGAS

Bảng 5 so sánh kết quả RAGAS của hệ thống đề xuất với các nghiên cứu liên quan có công bố số liệu đánh giá.

**Bảng 5. So sánh kết quả RAGAS với các hệ thống RAG khác**

| Hệ thống | Kiến trúc | LLM | Faithfulness | Ctx Recall | Ctx Precision | Ans Relevancy |
|:---|:---|:---|:---:|:---:|:---:|:---:|
<<<<<<< HEAD
| **HaUI (đề xuất)** | **Agentic RAG** | **Gemini 2.0 Flash** | **98,20%** | **100%** | **93,58%** | **77,80%** |
=======
| **HaUI (đề xuất)** | **Agentic RAG** | **Gemini 2.0 Flash** | **99,22%** | **100%** | **91,10%** | **78,02%** |
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837
| Hartono et al. [12] | Naive RAG | Gemma2-2b | 78% | 68% | 81% | 64% |
| Naive RAG baseline [2] | Naive RAG | GPT-3.5 | ~75% | ~65% | ~72% | ~68% |
| Advanced RAG + HyDE [2] | Advanced RAG | GPT-4 | ~88% | ~82% | ~87% | ~75% |
| CRAG [5] | Corrective RAG | Đa mô hình | ~90% | — | — | — |
| Self-RAG [6] | Self-reflective | Llama-2 13B | ~87% | — | — | — |
| InfoGain-RAG [15] | Filtering RAG | GPT-4 | ~92% | — | ~90% | — |

<<<<<<< HEAD
So sánh trực tiếp nhất là với nghiên cứu của Hartono và cộng sự [12] — cùng domain chatbot đại học, cùng sử dụng RAGAS để đánh giá. Kết quả cho thấy hệ thống đề xuất vượt trội ở mọi chỉ số: Faithfulness cao hơn 20,20 điểm phần trăm (98,20% so với 78%), Context Recall cao hơn 32 điểm phần trăm (100% so với 68%), Context Precision cao hơn 12,58 điểm phần trăm, và Answer Relevancy cao hơn 13,80 điểm phần trăm. Sự khác biệt đáng kể này đến từ việc hệ thống đề xuất sử dụng kiến trúc đa tác tử với các bước sàng lọc tài liệu (Grader, Reranker), trong khi Hartono et al. sử dụng Naive RAG không có cơ chế lọc.

So với các phương pháp cải tiến khác, Faithfulness 98,20% của hệ thống đề xuất cao hơn CRAG (~90%) và Self-RAG (~87%). Điều này cho thấy sự kết hợp đồng thời nhiều tác tử chuyên biệt mang lại hiệu quả tổng hợp (synergy effect) vượt trội so với việc chỉ áp dụng riêng lẻ từng kỹ thuật.
=======
So sánh trực tiếp nhất là với nghiên cứu của Hartono và cộng sự [12] — cùng domain chatbot đại học, cùng sử dụng RAGAS để đánh giá. Kết quả cho thấy hệ thống đề xuất vượt trội ở mọi chỉ số: Faithfulness cao hơn 21,22 điểm phần trăm (99,22% so với 78%), Context Recall cao hơn 32 điểm phần trăm (100% so với 68%), Context Precision cao hơn 10,10 điểm phần trăm, và Answer Relevancy cao hơn 14,02 điểm phần trăm. Sự khác biệt đáng kể này đến từ việc hệ thống đề xuất sử dụng kiến trúc đa tác tử với các bước sàng lọc tài liệu (Grader, Reranker), trong khi Hartono et al. sử dụng Naive RAG không có cơ chế lọc.

So với các phương pháp cải tiến khác, Faithfulness 99,22% của hệ thống đề xuất cao hơn CRAG (~90%) và Self-RAG (~87%). Điều này cho thấy sự kết hợp đồng thời nhiều tác tử chuyên biệt mang lại hiệu quả tổng hợp (synergy effect) vượt trội so với việc chỉ áp dụng riêng lẻ từng kỹ thuật.
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837

### 3.7. Hạn chế của nghiên cứu

Mặc dù đạt kết quả tốt, nghiên cứu còn một số hạn chế cần thừa nhận:

1. **Bộ test 64 câu hỏi**: Mặc dù đã bao phủ đầy đủ các nhóm chủ đề, quy mô bộ test còn nhỏ so với các benchmark chuẩn quốc tế (ví dụ: CRAG Benchmark có 4.409 cặp QA [5]). Tuy nhiên, đây là quy mô phù hợp cho nghiên cứu trên domain chuyên biệt.

2. **LLM-as-Judge bias**: Hệ thống sử dụng cùng mô hình Gemini 2.0 Flash cho cả sinh câu trả lời và đánh giá RAGAS, tiềm ẩn rủi ro thiên lệch (bias). Đề xuất bổ sung đánh giá từ chuyên gia (human evaluation) trong hướng phát triển.

3. **Latency**: Do sử dụng nhiều LLM calls tuần tự (4-5 calls/query), thời gian phản hồi trung bình là 10-15 giây — chậm hơn so với Naive RAG (2-3 giây). Đây là sự đánh đổi chấp nhận được giữa chất lượng và tốc độ.

4. **Phạm vi domain đơn**: Hệ thống được thiết kế và đánh giá trên một domain cụ thể (văn bản quy chế đào tạo HaUI). Việc mở rộng sang đa nguồn dữ liệu (kết nối API hệ thống đào tạo) và đa lĩnh vực (y tế, pháp luật chung) là hướng phát triển cần nghiên cứu thêm.

---

## 4. KẾT LUẬN VÀ KHUYẾN NGHỊ

### 4.1. Kết luận

Bài báo đã trình bày việc thiết kế và xây dựng thành công hệ thống chatbot trợ lý sinh viên dựa trên kiến trúc Agentic RAG tại Trường Đại học Công nghiệp Hà Nội. Các kết quả chính đạt được bao gồm:

1. **Kiến trúc đa tác tử mới**: Hệ thống sử dụng 6 tác tử chuyên biệt kết hợp đồng thời 5 kỹ thuật nâng cao (Rewrite, Grade, Rerank, Route, Hallucination Check), vượt trội so với các phương pháp hiện có thường chỉ áp dụng 1-2 kỹ thuật.

2. **Thuật toán Semantic Chunking cho văn bản pháp quy tiếng Việt**: Đóng góp mới trong lĩnh vực xử lý ngôn ngữ tự nhiên tiếng Việt, bảo toàn hoàn toàn cấu trúc Chương – Điều – Khoản – Phụ lục và gắn metadata chi tiết cho từng chunk.

<<<<<<< HEAD
3. **Hiệu suất vượt trội**: Đánh giá trên bộ 64 câu hỏi bằng RAGAS cho thấy hệ thống đạt Faithfulness 98,20%, Context Recall 100%, Context Precision 93,58%, và Answer Correctness 87,61%. So với nghiên cứu tương đương [12], hệ thống cải thiện Faithfulness 20,20 điểm phần trăm và Context Recall 32 điểm phần trăm.
=======
3. **Hiệu suất vượt trội**: Đánh giá trên bộ 64 câu hỏi bằng RAGAS cho thấy hệ thống đạt Faithfulness 99,22%, Context Recall 100%, Context Precision 91,10%, và Answer Correctness 85,35%. So với nghiên cứu tương đương [12], hệ thống cải thiện Faithfulness 21,22 điểm phần trăm và Context Recall 32 điểm phần trăm.
>>>>>>> 39b70524bfe53dc550b7b2b625d0c60bf6780837

4. **Cơ chế Batch Grading**: Giảm số lượng API call đánh giá tài liệu từ *k* xuống 1 so với CRAG [5], tiết kiệm chi phí và giảm độ trễ.

5. **Triển khai thực tế**: Hệ thống đã được triển khai thành công trên Facebook Messenger [10] phục vụ sinh viên toàn trường, với cơ chế Semaphore xử lý đồng thời và Retry tự động cho các lỗi API.

### 4.2. Khuyến nghị và hướng phát triển

1. **Tích hợp đa nguồn dữ liệu (Multi-Source)**: Kết nối với hệ thống quản lý đào tạo (LMS) của nhà trường qua API để cung cấp thông tin cá nhân hóa (lịch thi, điểm số, tiến độ học tập), chuyển đổi từ single-source sang multi-source RAG.
2. **Nâng cao đánh giá**: Mở rộng bộ test, bổ sung đánh giá từ chuyên gia (human evaluation), và sử dụng mô hình Judge khác để loại bỏ bias tiềm ẩn.
3. **Tối ưu hiệu năng**: Nghiên cứu áp dụng kỹ thuật caching kết quả truy xuất, nén ngữ cảnh (context compression), và gọi LLM song song (parallel calls) để giảm độ trễ.
4. **Mở rộng đa lĩnh vực (Cross-Domain)**: Thử nghiệm kiến trúc Agentic RAG trên các domain khác (y tế, pháp luật, tài chính) để xác nhận tính tổng quát của phương pháp.

---

## 5. LỜI CẢM ƠN

Tác giả xin chân thành cảm ơn Trường Điện — Điện tử, Trường Đại học Công nghiệp Hà Nội đã tạo điều kiện hỗ trợ trong quá trình nghiên cứu và triển khai hệ thống.

---

## TÀI LIỆU THAM KHẢO

[1]. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T. and Riedel, S., 2020. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Proceedings of NeurIPS 2020, 9459-9474.

[2]. Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J. and Wang, H., 2024. Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv:2312.10997.

[3]. Robertson, S. and Zaragoza, H., 2009. The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval, 3(4), 333-389.

[4]. Shuster, K., Poff, S., Chen, M., Kiela, D. and Weston, J., 2021. Retrieval Augmentation Reduces Hallucination in Conversation. Findings of EMNLP 2021, 3784-3803.

[5]. Yan, S.Q., Gu, J.C., Zhu, Y. and Ling, Z.H., 2024. Corrective Retrieval Augmented Generation. arXiv:2401.15884.

[6]. Asai, A., Wu, Z., Wang, Y., Sil, A. and Hajishirzi, H., 2024. Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection. Proceedings of NeurIPS 2024.

[7]. Singh, A. et al., 2025. Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG. arXiv (survey).

[8]. LangChain, 2024. LangChain Documentation: EnsembleRetriever. Truy cập ngày 20 tháng 3 năm 2026. https://python.langchain.com/docs/how_to/ensemble_retriever/

[9]. Chroma, 2024. ChromaDB: The AI-native open-source embedding database. Truy cập ngày 20 tháng 3 năm 2026. https://www.trychroma.com/

[10]. Meta, 2024. Messenger Platform Documentation. Truy cập ngày 5 tháng 4 năm 2026. https://developers.facebook.com/docs/messenger-platform/

[11]. Es, S., James, J., Espinosa-Anke, L. and Schockaert, S., 2024. RAGAS: Automated Evaluation of Retrieval Augmented Generation. Proceedings of EACL 2024 (System Demonstrations), 150-163.

[12]. Hartono, L.S., Setiawan, E.I. and Singh, V., 2025. Retrieval Augmented Generation-Based Chatbot for Prospective and Current University Students. International Journal of Engineering Science and Information Technology (IJESTY).

[13]. Google, 2024. Gemini: A Family of Highly Capable Multimodal Models. arXiv:2312.11805.

[14]. Nguyen, T.H. et al., 2024. RAG-based Question Answering for Vietnamese Legal Documents. KSE Conference Proceedings.

[15]. Wang, Z. et al., 2025. InfoGain-RAG: Leveraging Information Gain for RAG Document Filtering. arXiv (2025).

[16]. Swacha, J. and Gracel, S., 2025. RAG Chatbots in Education: A Meta-Survey. EPRA International Journal.
