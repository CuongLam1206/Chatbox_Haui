"""
Query Rewriter Agent
Transforms user queries into optimized search queries for the vector store
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.llm_provider import get_llm
from src.slang_manager import SlangManager


class LearnSlang(BaseModel):
    """Extract abbreviation and definition from user text"""
    
    abbreviation: str = Field(description="The short term or abbreviation")
    definition: str = Field(description="The full formal definition")


class QueryRewriter:
    """
    Rewrite student queries into formal academic language for better retrieval
    """
    
    def __init__(self):
        """Initialize query rewriter"""
        self.slang_manager = SlangManager()
        llm = get_llm(temperature=0)
        
        # Rewriting prompt
        system_prompt = """Bạn là chuyên gia tối ưu hóa câu hỏi cho Trợ lý ảo thông minh HaUI.
        
Nhiệm vụ: Phân tích câu hỏi của sinh viên và chuyển đổi thành một chuỗi TỪ KHÓA TÌM KIẾMM TỐI ƯU. 

Yêu cầu:
1. Nếu có NHIỀU câu hỏi trong một lượt (VD: "A là gì? có những B nào?"), hãy KẾT HỢP thành một search query BAO QUÁT.
2. Ưu tiên các thực thể (Ví dụ: tên Phụ lục, tên mẫu phiếu, tên chương, tên điều).
3. Kết hợp các thuật ngữ chính thức của HaUI.
4. **GIẢI MÃ THAM CHIẾU TỪ LỊCH SỬ HỘI THOẠI:** Nếu câu hỏi hiện tại rất ngắn hoặc thiếu chủ đề, BUỘC PHẢI tra lịch sử để điền đầy đủ.
   **QUAN TRỌNG:** Nếu câu hỏi hiện tại có SỐ TIẾT MỚI (khác với lịch sử) → LUÔN dùng số tiết MỚI đó, không dùng số tiết cũ.
   VD1: Lịch sử="Tiết 5 lý thuyết bắt đầu lúc nào?", Câu hỏi="kết thúc lúc nào" → Output: "Tiết 5 lý thuyết kết thúc lúc nào CS1 CS3"
   VD2: Lịch sử="kết thúc lúc nào", Câu hỏi="tiết 1" → Output: "Tiết 1 lý thuyết kết thúc lúc nào CS1 CS3"
   VD3: Lịch sử="Học bổng loại giỏi điều kiện gì", Câu hỏi="xuất sắc" → Output: "Học bổng KKHT loại xuất sắc điều kiện GPA"
   VD4: Lịch sử="tiết 5 bắt đầu 10:35... kết thúc 11:25", Câu hỏi="còn tiết 2 thì sao" → Output: "Tiết 2 lý thuyết kết thúc lúc nào CS1 CS3"
5. GIỮ NGUYÊN cấu trúc quan hệ giữa các phần câu hỏi (định nghĩa, phân loại, liệt kê).
6. Chỉ trả về chuỗi từ khóa, không giải thích gì thêm.

Ví dụ:
Câu hỏi: "cho mình xin mẫu phụ lục 03"
Output: Phụ lục 03 Danh sách giao đề tài thực hiện ĐA/KLTN HaUI

Câu hỏi: "Học phần là gì? có những loại học phần nào"
Output: Học phần định nghĩa phân loại các loại học phần

Câu hỏi: "điều kiện tốt nghiệp và cách tính điểm"
Output: điều kiện tốt nghiệp cách tính điểm trung bình

Lịch sử hội thoại:
{chat_history}

Câu hỏi hiện tại: {question}
Output:"""

        prompt = ChatPromptTemplate.from_template(system_prompt)
        
        self.rewriter = prompt | llm | StrOutputParser()
    
    def rewrite(self, question: str, chat_history: list = None) -> str:
        """
        Rewrite the query
        """
        custom_slang = self.slang_manager.get_formatted_slang()
        return self.rewriter.invoke({
            "question": question,
            "custom_slang": custom_slang,
            "chat_history": chat_history or []
        })
    
    def extract_new_slang(self, question: str) -> tuple[str, str]:
        """
        Extract a new abbreviation definition from natural language
        """
        llm = get_llm(temperature=0)
        extractor = llm.with_structured_output(LearnSlang)
        
        prompt = ChatPromptTemplate.from_template(
            "Trích xuất từ viết tắt và định nghĩa đầy đủ từ câu sau: {question}"
        )
        
        chain = prompt | extractor
        result = chain.invoke({"question": question})
        return result.abbreviation, result.definition
