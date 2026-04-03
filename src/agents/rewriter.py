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


from typing import List

class QueryRewriter:
    """
    Rewrite student queries into formal academic language for better retrieval.
    Supports decomposing complex queries into multiple search terms.
    """
    
    def __init__(self):
        """Initialize query rewriter"""
        self.slang_manager = SlangManager()
        llm = get_llm(temperature=0)
        
        # Decomposition & Rewriting prompt
        system_prompt = """Bạn là chuyên gia phân tích và tối ưu hóa truy vấn cho hệ thống RAG của Đại học Công nghiệp Hà Nội (HaUI).

Nhiệm vụ: Phân tích câu hỏi của sinh viên và chuyển đổi thành một DANH SÁCH các chuỗi từ khóa tìm kiếm tối ưu.

Quy tắc:
1. Nếu câu hỏi đơn giản: Trả về một chuỗi từ khóa duy nhất.
2. Nếu câu hỏi PHỨC HỢP (chứa nhiều vế, nhiều ý hỏi khác nhau): TÁCH thành các chuỗi từ khóa riêng biệt hoàn chỉnh.
   Mỗi vế phải là một câu hỏi độc lập có đầy đủ chủ ngữ "sinh viên HaUI".
3. Sử dụng lịch sử hội thoại để giải mã các đại từ hoặc ý ẩn ý.
4. Ưu tiên thực thể chính thức: tên Điều, tên Phụ lục, tên Quy định.
5. Chỉ trả về danh sách các câu search, mỗi câu trên một dòng. Không đánh số, không giải thích.

Ví dụ:
Câu hỏi: "Sinh viên vi phạm đạo văn đồ án và bị cảnh báo học tập lần 2 liên tiếp thì sao?"
Output:
quy định xử lý kỷ luật sinh viên đạo văn đồ án tốt nghiệp HaUI
hệ quả sinh viên bị cảnh báo kết quả học tập lần thứ 2 liên tiếp buộc thôi học HaUI

Câu hỏi: "địa chỉ SEEE và số điện thoại hiệu trưởng"
Output:
địa chỉ văn phòng Trường Điện Điện tử SEEE HaUI
họ tên số điện thoại Hiệu trưởng Trường SEEE HaUI

Câu hỏi: "tiết 5 lý thuyết ở CS1 bắt đầu lúc nào" (Lịch sử: đang hỏi về giờ học)
Output:
giờ bắt đầu tiết 5 lý thuyết cơ sở 1 HaUI

Lịch sử hội thoại:
{chat_history}

Câu hỏi hiện tại: {question}
Output:"""
        
        prompt = ChatPromptTemplate.from_template(system_prompt)
        
        self.chain = prompt | llm | StrOutputParser()
    
    def rewrite(self, question: str, chat_history: list = None) -> List[str]:
        """
        Rewrite query to formal language and decompose if necessary
        """
        # Step 1: Replace slang if any
        refined_q = self.slang_manager.replace_slang(question)
        
        # Step 2: LLM Rewriting & Decomposition
        response = self.chain.invoke({
            "question": refined_q,
            "chat_history": chat_history or []
        })
        
        # Parse lines into list
        queries = [q.strip() for q in response.split('\n') if q.strip()]
        
        # Fallback if empty
        if not queries:
            queries = [refined_q]
            
        print(f"[Rewriter] Decomposed into {len(queries)} queries: {queries}")
        return queries
