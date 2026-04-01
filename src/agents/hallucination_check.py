"""
Hallucination Detection Agent
Checks if generated answer is grounded in source documents
"""
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.llm_provider import get_llm


class GradeHallucination(BaseModel):
    """Binary score for hallucination check"""
    
    binary_score: Literal["yes", "no"] = Field(
        description="Answer is grounded in facts, 'yes' or 'no'"
    )


class HallucinationChecker:
    """
    Check if answer contains hallucinations (not grounded in source documents)
    """
    
    def __init__(self):
        """Initialize hallucination checker"""
        
        llm = get_llm(temperature=0)
        
        structured_llm = llm.with_structured_output(GradeHallucination)
        
        system_prompt = """Bạn là một chuyên gia kiểm tra xem câu trả lời có được dựa trên các sự kiện trong tài liệu nguồn hay không.

Nhiệm vụ: Xác định xem câu trả lời có chứa thông tin KHÔNG có trong tài liệu nguồn hay không.

Nếu tất cả thông tin trong câu trả lời đều có thể được xác minh từ tài liệu nguồn, trả lời 'yes'.
Nếu câu trả lời có thông tin không có trong tài liệu nguồn, trả lời 'no'.

Đưa ra đánh giá nhị phân 'yes' (grounded) hoặc 'no' (hallucination)."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Tài liệu nguồn:\n{documents}\n\nCâu trả lời được tạo:\n{generation}")
        ])
        
        self.checker = prompt | structured_llm
    
    def check(self, generation: str, documents: str) -> bool:
        """
        Check if generation is grounded in documents
        
        Args:
            generation: Generated answer
            documents: Source documents
            
        Returns:
            True if grounded, False if hallucination detected
        """
        result = self.checker.invoke({
            "generation": generation,
            "documents": documents
        })
        
        return result.binary_score == "yes"
