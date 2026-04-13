"""
Answer Generation Agent
Generates answers based on retrieved context
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import TEMPERATURE
from src.llm_provider import get_llm


def detect_query_type(question: str) -> str:
    q = question.lower()

    # Synthesis: RÕ RÀNG hỏi 2 chủ đề riêng biệt cùng lúc
    if any(s in q for s in [" và bị ", " cùng lúc ", " đồng thời phải ", " ngoài ra còn bị "]):
        return "synthesis"

    # Conditional: điều kiện / tiêu chuẩn (check trước procedural)
    if any(s in q for s in ["điều kiện", "tiêu chuẩn", "đối tượng", "trường hợp nào", "bao gồm những", "được hưởng"]):
        return "conditional"

    # Procedural: quy trình / các bước
    if any(s in q for s in ["đăng ký", "thủ tục", "các bước", "quy trình", "hồ sơ", "làm thế nào", "làm như thế nào"]):
        return "procedural"

    return "factual"


QUERY_TYPE_SUFFIX = {
    "factual": "Trả lời ngắn gọn 1-3 câu, đưa kết luận/con số chính ngay dòng đầu.",
    "procedural": "Liệt kê các bước/thủ tục theo thứ tự, đánh số rõ ràng.",
    "conditional": "Liệt kê ĐẦY ĐỦ tất cả điều kiện/trường hợp trong ngữ cảnh, không bỏ sót.",
    "synthesis": "Tổng hợp thông tin từ nhiều nguồn, trình bày từng chủ đề riêng biệt, có tiêu đề phân chia.",
}


class AnswerGenerator:
    """
    Generate answers from retrieved context
    """
    
    def __init__(self):
        """Initialize answer generator"""
        
        llm = get_llm(temperature=TEMPERATURE)
        
        # RAG prompt
        system_prompt = """Bạn là trợ lý ảo thông minh của Trường Đại học Công nghiệp Hà Nội (HaUI).
        
Nhiệm vụ: Trả lời câu hỏi sinh viên dựa HOÀN TOÀN vào ngữ cảnh tài liệu bên dưới.

=== QUY TẮC VÀNG (LUÔN TUÂN THỦ) ===

R1. **CHỈ DÙNG THÔNG TIN TRONG NGỮ CẢNH.** TUYỆT ĐỐI KHÔNG bịa thêm, suy luận thêm, hay thêm kiến thức bên ngoài.
R2. **TRẢ LỜI NGẮN GỌN, ĐI THẲNG VÀO VẤN ĐỀ.** Đưa câu trả lời chính NGAY DÒNG ĐẦU. Không mở đầu lan man.
R3. **TRÍCH DẪN CHÍNH XÁC SỐ LIỆU:** Khi ngữ cảnh có con số (tiền, %, thời gian, điểm, số người...) → BẮT BUỘC ghi đúng con số đó. Ví dụ: "300.000 đồng", "06 tháng", "3.60 - 4.0".
R4. **KHÔNG hỏi ngược lại người dùng.** KHÔNG viết "Bạn muốn biết gì thêm?", "Bạn đang ở cấp học nào?". Luôn giả định người hỏi là sinh viên ĐH/CĐ HaUI.
R5. **TRẢ LỜI ĐÚNG VÀ ĐỦ:** Liệt kê TẤT CẢ các ý/điều kiện liên quan trong ngữ cảnh. Không được bỏ sót vế nào.

=== HƯỚNG DẪN CHI TIẾT ===

1. Trả lời bằng tiếng Việt, rõ ràng, chuyên nghiệp và thân thiện.

2. **NGỮ CẢNH NGƯỜI DÙNG:** Chatbot phục vụ SINH VIÊN HỆ ĐẠI HỌC/CAO ĐẲNG của HaUI. Khi tài liệu đề cập nhiều cấp học → CHỈ trả lời phần liên quan đến sinh viên ĐH/CĐ.

3. **ƯU TIÊN TRẢ LỜI TRỰC TIẾP:**
- Câu hỏi dạng xác nhận → đưa KẾT LUẬN (Có/Không/Được/Không được) ngay dòng đầu.
- Câu hỏi hỏi "bao nhiêu/mấy/gì" → đưa CON SỐ / TÊN CỤ THỂ ngay dòng đầu, rồi mới giải thích.
- Câu hỏi nhiều vế → đánh số 1, 2, 3... trả lời từng vế.

4. **TUYỆT ĐỐI KHÔNG nói "Tôi chưa có thông tin" nếu ngữ cảnh CÓ CHỨA câu trả lời.** Đọc kỹ TOÀN BỘ ngữ cảnh bao gồm bảng, danh sách, sơ đồ.

5. **XỬ LÝ MÂU THUẪN:** Ưu tiên văn bản có Ngày ban hành mới nhất hoặc QĐ có số hiệu lớn hơn.

6. **KHÔNG tự suy luận ngoài ngữ cảnh.** Nếu tài liệu chỉ nói năm 1, 2, 3 → CHỈ ghi năm 1, 2, 3. KHÔNG suy luận năm 4.

7. **XỬ LÝ THỜI KHÓA BIỂU:**
- Hỏi tiết cụ thể → trả lời ĐÚNG tiết đó cho TẤT CẢ cơ sở.
- Hỏi chung → liệt kê toàn bộ bảng giờ.
- KHÔNG nhầm giữa Lý thuyết và Thực hành.

8. **BIỂU MẪU/PHỤ LỤC:**
   A) Muốn XEM MẪU → trích xuất chính xác từ document, dừng sau dòng cuối.
   B) Muốn TÓM TẮT → tóm tắt ngắn gọn, KHÔNG trích toàn bộ.

9. **DỮ LIỆU CÓ CẤU TRÚC (danh sách, bảng):**
   - Hỏi đích danh cá nhân → CHỈ trả lời về cá nhân đó.
   - Hỏi chung → liệt kê ĐẦY ĐỦ.

10. Nếu KHÔNG TÌM THẤY thông tin → lịch sự đề nghị sinh viên liên hệ Khoa/Đơn vị đào tạo.

Lịch sử hội thoại:
{chat_history}

Ngữ cảnh (Tài liệu HaUI):
{context}

Câu hỏi hiện tại: {question}

{adaptive_instruction}
"""
        
        prompt = ChatPromptTemplate.from_template(system_prompt)
        
        self.chain = prompt | llm | StrOutputParser()
    
    def _clean_template_output(self, text: str) -> str:
        """
        Clean template output by removing unwanted elements using simple string operations
        """
        # Split by common separators to isolate the main content
        lines = text.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            # Skip lines containing unwanted patterns (including variants without accents)
            if any(pattern.lower() in line.lower() for pattern in [
                '📚',
                'Nguồn tham khảo',
                'Nguon tham khao',
                'Độ liên quan:',
                'Do lien quan:',
                'Đây là **Phụ lục',
                'Dưới đây là',
                'Hãy điền',
                'Hy vọng',
                'Nếu cần thêm'
            ]):
                continue
            
            # Remove HTML tags
            if any(tag in line for tag in ['<div', '</div', '<br', '<center', '</center', '&nbsp']):
                continue
            
            # Skip pure markdown separators
            if line.strip() == '---':
                continue
            
            # Skip lines that are just headers (###, ##, #)
            if line.strip().startswith('#') and not line.strip().startswith('##'):
                # Allow ## but remove single # headers
                if line.count('#') < 2:
                    continue
            
            cleaned_lines.append(line)
        
        # Join back and clean up whitespace
        result = '\n'.join(cleaned_lines)
        
        # Remove multiple empty lines
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        
        return result.strip()
    
    def generate(self, question: str, context: str, chat_history: list = None) -> str:
        """
        Generate answer from context
        """
        raw_output = self.chain.invoke({
            "question": question,
            "context": context,
            "chat_history": chat_history or [],
            "adaptive_instruction": "Hãy trả lời ngắn gọn, chính xác, đi thẳng vào vấn đề. Đặt kết luận/con số chính NGAY DÒNG ĐẦU:"
        })

        cleaned = self._clean_template_output(raw_output)
        return self._clean_markdown_format(cleaned)
    
    def _clean_markdown_format(self, text: str) -> str:
        """
        Convert markdown to clean formatted text (remove *, # but keep structure)
        """
        import re
        
        # Replace headers (## → <strong>, ### → bold)
        text = re.sub(r'###\s+(.+)', r'<strong>\1</strong>', text)
        text = re.sub(r'##\s+(.+)', r'<strong>\1</strong>', text)
        text = re.sub(r'#\s+(.+)', r'<strong>\1</strong>', text)
        
        # Replace bold (**text** → <strong>text</strong>)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Replace italic (*text* → <em>text</em>)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        
        # Replace bullet points (- item → • item)
        text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\*\s+', '• ', text, flags=re.MULTILINE)
        
        return text
    
    def generate_from_documents(self, question: str, documents: list, chat_history: list = None) -> tuple[str, list]:
        """
        Generate answer from document list
        """
        if not documents:
            return "Tôi không tìm thấy thông tin liên quan để trả lời câu hỏi này.", []
        
        # Combine documents into context
        context = "\n\n---\n\n".join([
            doc.page_content if hasattr(doc, 'page_content') else str(doc)
            for doc in documents
        ])
        
        # Extract source references
        sources = []
        for doc in documents:
            if hasattr(doc, 'metadata') and 'doc_type' in doc.metadata:
                source = doc.metadata['doc_type']
                if source not in sources:
                    sources.append(source)
        
        # Generate answer
        answer = self.generate(question, context, chat_history)
        
        return answer, sources

    def generate_general_response(self, question: str, chat_history: list) -> str:
        """
        Generate a general conversational response
        """
        llm = get_llm(temperature=TEMPERATURE)
        
        system_prompt = """Bạn là trợ lý ảo thông minh của Trường Đại học Công nghiệp Hà Nội (HaUI).
        
Bạn đang trò chuyện tự do hoặc trả lời các câu hỏi về bản thân bạn hoặc lịch sử cuộc trò chuyện.
Hãy trả lời một cách thông minh, hữu ích và thể hiện sự tự hào về HaUI.

Nếu người dùng hỏi 'tôi vừa hỏi gì', hãy tóm tắt ngắn gọn các ý chính họ đã quan tâm.
Nếu người dùng hỏi 'bạn là ai', hãy giới thiệu bạn là Trợ lý Sinh viên Thông minh của HaUI, sẵn sàng hỗ trợ mọi thắc mắc về trường.

Lịch sử hội thoại:
{chat_history}

Câu hỏi hiện tại: {question}
Câu trả lời:"""

        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | llm | StrOutputParser()
        
        return chain.invoke({
            "question": question,
            "chat_history": chat_history
        })
