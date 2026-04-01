from typing import List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.llm_provider import get_llm


class BatchGradeResults(BaseModel):
    """List of binary scores for relevance check"""
    # Trả về danh sách chỉ số các tài liệu có liên quan
    relevant_indices: List[int] = Field(
        description="Indices of documents that are relevant to the question (0-indexed)"
    )


class DocumentGrader:
    """
    Grade the relevance of retrieved documents to a user question
    """
    
    def __init__(self):
        """Initialize document grader"""
        
        # LLM with function calling
        llm = get_llm(temperature=0)
        
        structured_llm_grader = llm.with_structured_output(BatchGradeResults)
        
        system_prompt = """Bạn là chuyên gia đánh giá tính liên quan của tài liệu đối với câu hỏi của sinh viên HaUI.
Nhiệm vụ: Duyệt qua DANH SÁCH tài liệu và xác định tài liệu nào có thể giúp trả lời câu hỏi.

Tiêu chí đánh giá 'có liên quan':
1. Chứa trực tiếp câu trả lời cho câu hỏi.
2. Chứa từ khóa/khái niệm gần với câu hỏi (VD: "Mẫu"="Phụ lục", "Phiếu"="Biểu mẫu").
3. Cùng Điều/Chương với nội dung được hỏi → relevant dù không chứa chính xác câu trả lời.
4. Chứa quy trình, thủ tục, biểu mẫu liên quan đến chủ đề hỏi.
5. Chứa thông tin về giảng viên, cố vấn học tập, điều phối chương trình, trưởng chương trình.
6. Chứa thông tin về cơ cấu tổ chức, ngành đào tạo, chương trình học của trường SEEE/HaUI.
7. Chứa thông tin liên hệ (SĐT, địa chỉ phòng) của các đơn vị/cá nhân trong trường.
8. Chứa thông tin về thời khóa biểu, lịch học, giờ học.

QUAN TRỌNG:
- Chấp nhận tài liệu từ BẤT KỲ quyết định/quy định/slide giới thiệu nào của HaUI/SEEE.
- Ưu tiên CHẤP NHẬN: thà nhận thừa còn hơn bỏ sót thông tin quan trọng.
- Nếu không chắc → chọn relevant.

Hãy trả về danh sách CÁC CHỈ SỐ (index, bắt đầu từ 0) của những tài liệu có liên quan.
Nếu không có tài liệu nào liên quan, hãy trả về danh sách trống []."""


        grade_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Câu hỏi: {question}\n\nDANH SÁCH TÀI LIỆU:\n{documents}")
        ])
        
        self.grader = grade_prompt | structured_llm_grader
    
    def grade_documents(self, question: str, documents: list) -> tuple[list, float]:
        """
        Grade multiple documents in ONE batch call to save tokens and avoid rate limits
        """
        if not documents:
            return [], 0.0
        
        formatted_docs = ""
        for i, doc in enumerate(documents):
            # Lấy thông tin tiêu đề từ metadata nếu có
            headers = []
            if hasattr(doc, 'metadata'):
                for h in ["Header 1", "Header 2", "Header 3"]:
                    if h in doc.metadata: headers.append(f"{h}: {doc.metadata[h]}")
            
            header_str = " | ".join(headers) if headers else "Không có tiêu đề"
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            
            formatted_docs += f"--- TÀI LIỆU {i} ---\nTiêu đề: {header_str}\nNội dung: {content[:1000]}\n\n"

        print(f"[Grading] Evaluating {len(documents)} documents in batch...")
        
        try:
            result = self.grader.invoke({"question": question, "documents": formatted_docs})
            relevant_indices = result.relevant_indices
            
            relevant_docs = [documents[i] for i in relevant_indices if 0 <= i < len(documents)]
            
            relevance_score = len(relevant_docs) / len(documents) if documents else 0.0
            print(f"[Grading] Relevance: {relevance_score:.2%} ({len(relevant_docs)}/{len(documents)} relevant)")
            
            return relevant_docs, relevance_score
            
        except Exception as e:
            print(f"Error in batch grading: {e}. Falling back to all documents.")
            return documents, 1.0
