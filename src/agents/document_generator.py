"""
Document Generator Agent
Responsible for RAG-based document information synthesis.
"""
from typing import List

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document


class DocumentGenerator:
    """
    Handles RAG-based generation for document queries.
    Uses vector store retrieval to synthesize information about documents.
    """
    
    def __init__(self):
        # Import LLM for RAG-based generation
        from src.llm_provider import get_llm
        self.llm = get_llm(temperature=0.3)
    
    def generate_from_rag(self, query: str, documents: List[Document]) -> str:
        """
        Generate document information using RAG.
        
        For document/appendix queries, directly return the content without LLM summarization
        to preserve complete information.
        
        Args:
            query: User query
            documents: Retrieved documents from vector store
            
        Returns:
            Formatted response with document information
        """
        if not documents:
            return "Tôi không tìm thấy thông tin về câu hỏi này trong tài liệu."
        
        # Extract sources
        sources = list(set([
            doc.metadata.get('source', 'Unknown').replace('.md', '')
            for doc in documents[:5]
            if hasattr(doc, 'metadata')
        ]))
        
        # For appendix/form queries, return chunks directly without LLM summarization
        if any(keyword in query.lower() for keyword in ['phụ lục', 'biên bản', 'phiếu', 'mẫu']):
            print(f"[Document Generator] Appendix/form query - using direct chunk extraction")
            
            # Simply concatenate all retrieved chunks
            full_content = "\n\n".join([
                doc.page_content if hasattr(doc, 'page_content') else str(doc)
                for doc in documents
            ])
            
            # Add sources
            if sources:
                sources_text = ", ".join(sources)
                full_content += f"\n\n📚 **Nguồn tham khảo**: {sources_text}"
            
            return full_content
        
        # For other queries, use LLM synthesis
        context = "\n\n".join([
            doc.page_content if hasattr(doc, 'page_content') else str(doc)
            for doc in documents
        ])
        
        # LLM prompt for general information synthesis
        prompt = f"""Dựa vào thông tin sau đây, hãy trả lời câu hỏi của người dùng:

Câu hỏi: {query}

Thông tin từ tài liệu:
{context}

Yêu cầu:
1. Trả lời chính xác dựa trên nội dung tài liệu
2. Giữ nguyên format markdown (**, ##, tables, lists)
3. Trình bày rõ ràng, có cấu trúc
4. Chỉ  dùng thông tin có trong tài liệu

Trả lời bằng tiếng Việt, chi tiết và cụ thể."""
        
        try:
            answer = self.llm.invoke(prompt)
            if hasattr(answer, 'content'):
                answer = answer.content
            
            # Format with sources
            if sources:
                sources_text = ", ".join(sources)
                answer += f"\n\n📚 **Nguồn tham khảo**: {sources_text}"
            
            return answer
        except Exception as e:
            print(f"Error in RAG generation: {e}")
            return f"Đã tìm thấy thông tin liên quan. Vui lòng xem chi tiết tại: {sources[0] if sources else 'tài liệu HaUI'}."
