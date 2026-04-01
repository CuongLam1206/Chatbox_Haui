"""
Query Router Agent
Routes queries to appropriate handlers
"""
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.llm_provider import get_llm


class RouteQuery(BaseModel):
    """Route a user query to the most appropriate datasource"""
    
    datasource: Literal["greeting", "out_of_scope", "vectorstore", "learn", "general", "document_generation"] = Field(
        description="Path to route the user query to: greeting, out_of_scope, vectorstore, learn, general, or document_generation"
    )


class QueryRouter:
    """
    Classify the user query and route to the correct path
    """
    
    def __init__(self):
        """Initialize query router"""
        
        # LLM with function calling
        llm = get_llm(temperature=0)
        
        structured_llm_router = llm.with_structured_output(RouteQuery)
        
        # Routing prompt
        system_prompt = """Bạn là trợ lý ảo thông minh của Trường Đại học Công nghiệp Hà Nội (HaUI).
        
Dựa trên đầu vào của người dùng và lịch sử hội thoại, hãy xác định nó thuộc loại nào:
1. 'greeting': Các tin nhắn chào hỏi, làm quen đơn giản (VD: 'xin chào', 'hi').
2. 'general': Các câu hỏi về bản thân chatbot, lịch sử cuộc trò chuyện, hoặc các câu hỏi xã giao (VD: 'bạn là ai', 'tôi vừa hỏi gì').
3. 'out_of_scope': CHỈ dành cho các yêu cầu hoàn toàn không liên quan đến trường học, giảng dạy, nghiên cứu hoặc đời sống sinh viên (VD: 'cách nấu phở', 'kết quả bóng đá', 'giá vàng hôm nay').
4. 'vectorstore': MỌI câu hỏi về học tập, nghiên cứu, đào tạo, quy định, quy chế, chế độ, xử lý vi phạm, thủ tục, biểu mẫu... tại HaUI (VD: 'điểm A là mấy', 'quy trình làm đồ án', 'xử lý đạo văn thế nào', 'phụ lục 08 là gì', 'kiểm tra đạo văn như thế nào').
5. 'learn': Khi người dùng muốn định nghĩa một từ viết tắt mới.
6. 'document_generation': Khi người dùng yêu cầu xuất, tạo, hoặc cung cấp các mẫu biểu mẫu, biên bản, phụ lục, phiếu theo dõi (VD: 'xuất phụ lục 05', 'tạo biên bản họp', 'mẫu phiếu theo dõi').

LƯU Ý QUAN TRỌNG:
- Các câu hỏi về quy định, quy chế, chính sách, xử lý vi phạm của trường ĐỀU THUỘC 'vectorstore'
- Chỉ chọn 'out_of_scope' khi câu hỏi HOÀN TOÀN không liên quan đến giáo dục/trường học
- Ưu tiên 'document_generation' nếu người dùng nhắc đến biên bản, phụ lục hoặc biểu mẫu cụ thể"""

        route_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{question}")
        ])
        
        self.router = route_prompt | structured_llm_router
    
    def route(self, question: str, chat_history: list = None) -> str:
        """
        Route the query
        
        Args:
            question: User question
            chat_history: Optional chat history
            
        Returns:
            datasource: One of "greeting", "out_of_scope", "vectorstore", "general", "document_generation"
        """
        # Pre-routing: Hard-coded patterns for chat history queries
        q_lower = question.lower().strip()
        
        chat_history_patterns = [
            "tôi vừa hỏi", "tôi đã hỏi", "câu hỏi trước",
            "câu hỏi đầu tiên", "lịch sử chat", "nhắc lại câu hỏi",
            "tôi hỏi gì", "tôi đã nói gì"
        ]
        if any(pattern in q_lower for pattern in chat_history_patterns):
            return "general"
        
        # Pre-routing: Keyword-based fallback để tránh LLM classify nhầm
        # Các từ khóa liên quan giáo dục/quy chế tại HaUI → vectorstore
        education_keywords = [
            # Hoạt động thi cử / đánh giá
            "thi", "kiểm tra", "chấm thi", "phúc khảo", "điểm", "bài thi",
            "đề thi", "đáp án", "phách", "coi thi", "lịch thi", "ca thi",
            "phòng thi", "hội đồng thi", "trắc nghiệm", "tự luận", "vấn đáp",
            "thực hành", "tiểu luận", "đồ án", "bài tập lớn",
            # Học tập / đào tạo
            "học phần", "tín chỉ", "học kỳ", "giảng viên", "sinh viên",
            "đào tạo", "chương trình", "học bổng", "học phí", "miễn giảm",
            "cố vấn học tập", "lớp học phần", "ngân hàng câu hỏi",
            # Quy chế / quy định
            "quy chế", "quy định", "điều khoản", "điều ", "khoản ", "chương ",
            "vi phạm", "kỷ luật", "cảnh cáo", "đình chỉ", "khiển trách",
            "xét", "xử lý", "biên bản", "phụ lục", "biểu mẫu", "thủ tục",
            # Đơn vị / tổ chức
            "trung tâm khảo thí", "phòng đào tạo", "khoa", "bộ môn",
            "haui", "đhcnhn", "công nghiệp hà nội",
            # Kết quả học tập
            "điểm thành phần", "điểm tổng kết", "xếp loại", "tốt nghiệp",
            "chuẩn đầu ra", "học lực", "gpa", "tích lũy",
            # Thời gian học / tiết học
            "tiết", "tiết học", "thời khóa biểu", "lịch học", "thời gian học",
            "ca sáng", "ca chiều", "ca tối", "giờ học", "bắt đầu", "kết thúc",
            "cơ sở 1", "cơ sở 2", "cơ sở 3", "hà nội", "hà nam", "ninh bình",
            # Nhân sự / tổ chức SEEE
            "seee", "trường điện", "điện tử", "điều phối", "trưởng chương trình",
            "cố vấn", "phó hiệu trưởng", "hiệu trưởng", "ngành", "chương trình đào tạo",
            "phòng công tác", "phòng y tế", "phòng tổng hợp", "văn phòng",
            "thư viện", "liên chi đoàn",
        ]
        if any(kw in q_lower for kw in education_keywords):
            return "vectorstore"
        
        # LLM-based routing for all other queries
        result = self.router.invoke({
            "question": question,
            "chat_history": chat_history or []
        })
        return result.datasource
