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

    # Synthesis: RÕ RÀNG hỏi 2 chủ đề/hậu quả riêng biệt cùng lúc
    if any(s in q for s in [" và bị ", " cùng lúc ", " đồng thời phải ", " ngoài ra còn bị ", " và cho biết "]):
        return "synthesis"

    # Procedural: quy trình / các bước / thủ tục
    if any(s in q for s in ["đăng ký", "thủ tục", "các bước", "quy trình", "hồ sơ", "làm thế nào", "làm như thế nào", "cách nào"]):
        return "procedural"

    # Conditional: điều kiện / tiêu chuẩn / đối tượng
    if any(s in q for s in ["điều kiện", "tiêu chuẩn", "đối tượng", "trường hợp nào", "bao gồm những", "được hưởng", "ai được"]):
        return "conditional"

    # Simple Fact: Các câu hỏi định danh ngắn gọn (là ai, là gì, bao nhiêu %)
    if any(s in q for s in ["là ai", "là gì", "phần mềm nào", "số điện thoại", "sđt", "địa chỉ", "đơn vị nào", "bao nhiêu %", "mấy loại"]):
        return "simple_fact"

    # Factual: Mặc định là thông tin chi tiết (lịch trình, hệ số, mức phạt)
    return "factual"


QUERY_TYPE_SUFFIX = {
    "simple_fact": "TRẢ LỜI CỰC KỲ NGẮN GỌN (1-2 câu). Chỉ đưa ra tên gọi hoặc con số chính xác. Không giải thích thêm.",
    "factual": "Trả lời đầy đủ chi tiết kỹ thuật (giờ giấc, hệ số, mức phạt). Không lược bỏ thông tin quan trọng trong ngữ cảnh.",
    "procedural": "Liệt kê các bước thực hiện ngắn gọn. Tập trung vào thứ tự và hồ sơ.",
    "conditional": "Liệt kê các điều kiện/đối tượng dưới dạng gạch đầu dòng. Mỗi dòng súc tích.",
    "synthesis": "Tổng hợp đầy đủ các vế câu hỏi. Phân đoạn rõ ràng nếu hỏi về nhiều vấn đề.",
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

R1. **CHỈ DÙNG THÔNG TIN TRONG NGỮ CẢNH.** Không bịa thêm, không dùng kiến thức ngoài.
R2. **ĐỘ DÀI LINH HOẠT:** Câu hỏi định danh (là gì, là ai, bao nhiêu %) cần sự súc tích tuyệt đối; câu hỏi về lịch trình/công thức/kỷ luật cần sự chi tiết đầy đủ.
R3. **CHÍNH XÁC SỐ LIỆU:** Giữ nguyên các con số, đơn vị, mốc thời gian (ví dụ: 'Tiết 13 (18:00-18:50)', 'Hệ số 3').
R4. **KHÔNG CHAT LAN MAN:** Tuyệt đối không thêm câu chào, câu kết, hay các lời khuyên không được yêu cầu. Dừng lại ngay khi đủ ý.
R5. **XỬ LÝ MÂU THUẪN:** Ưu tiên quy định mới nhất. Tuy nhiên, nếu văn bản cũ có định nghĩa chi tiết (ví dụ: tên danh hiệu) mà văn bản mới không có, hãy sử dụng thông tin chi tiết đó.
R6. **ĐỐI CHIẾU BẢNG:** Khi đọc bảng Markdown, luôn đối chiếu giá trị ô với tiêu đề cột ở dòng trên để tránh lệch dữ liệu.

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
        # Detect query type and use adaptive instruction
        query_type = detect_query_type(question)
        adaptive_suffix = QUERY_TYPE_SUFFIX.get(query_type, QUERY_TYPE_SUFFIX["factual"])
        adaptive_text = f"Loại câu hỏi: {query_type}. {adaptive_suffix}"
        
        raw_output = self.chain.invoke({
            "question": question,
            "context": context,
            "chat_history": chat_history or [],
            "adaptive_instruction": adaptive_text
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
