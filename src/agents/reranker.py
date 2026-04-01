"""
Reranker Agent
Responsible for re-scoring and filtering retrieved documents based on precision relevance.
"""
from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from src.llm_provider import get_llm

class DocumentReranker:
    """
    Reranks documents using a precision LLM prompt to ensure the most 
    relevant context is prioritized for generation.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Bạn là chuyên gia thẩm định văn bản cấp cao của HaUI.
Nhiệm vụ: Chấm điểm độ liên quan (0-10) của các đoạn văn bản đối với câu hỏi.

Đặc biệt lưu ý: 
- Nếu câu hỏi yêu cầu "Mẫu", "Phụ lục", "Phiếu" hoặc "Danh sách" và tài liệu chứa TIÊU ĐỀ hoặc NỘI DUNG tương ứng (Ví dụ: "Phụ lục 03", "Danh sách giao đề tài..."), hãy chấm 10 ĐIỂM ngay lập tức.
- Tuyệt đối không được bỏ qua các biểu mẫu hành chính.

Định dạng trả về: CHỈ trả về dãy số điểm cách nhau bởi dấu phẩy, KHÔNG ghi chú, KHÔNG đánh số thứ tự.
Ví dụ: 10,8,0,5"""),
            ("human", "Câu hỏi: {question}\n\nCác tài liệu:\n{documents}")
        ])
        
        self.chain = self.prompt | self.llm

    def rerank(self, question: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        """
        Rerank a list of documents based on relevance to the question.
        """
        if not documents:
            return []
            
        doc_texts = []
        for i, doc in enumerate(documents):
            # Combine headers from metadata with content for better context
            headers = []
            if hasattr(doc, 'metadata'):
                for h in ["Header 1", "Header 2", "Header 3"]:
                    if h in doc.metadata:
                        headers.append(f"{h}: {doc.metadata[h]}")
            
            header_str = " | ".join(headers) if headers else "No headers"
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            doc_texts.append(f"--- Đoạn {i+1} (Tiêu đề: {header_str}) ---\n{content}")
            
        formatted_docs = "\n\n".join(doc_texts)
        
        response = self.chain.invoke({
            "question": question,
            "documents": formatted_docs
        })
        
        try:
            import re
            # Extract numbers using regex to be robust against "Điểm: 10, 8..."
            content = response.content.strip()
            score_matches = re.findall(r"(\d+(?:\.\d+)?)", content)
            scores = [float(s) for s in score_matches]
            
            # Map scores to documents
            doc_scores = []
            for i, doc in enumerate(documents):
                # If LLM didn't return enough scores, pad with 0
                score = scores[i] if i < len(scores) else 0.0
                doc_scores.append((doc, score))
            
            # Sort by score descending
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Keep only docs with score >= 2 (threshold 2 to avoid dropping valid chunks like timetable)
            reranked_docs = [doc for doc, score in doc_scores if score >= 2]
            
            # Safety net: never return empty list — keep at least the best doc
            if not reranked_docs and doc_scores:
                best_doc, best_score = doc_scores[0]
                print(f"[Reranking] All scores < 2, keeping top doc (score={best_score})")
                reranked_docs = [best_doc]
            
            print(f"[Reranking] Re-scored {len(documents)} docs. Best score: {max(scores) if scores else 0}")
            return reranked_docs[:top_k]
            
        except Exception as e:
            print(f"⚠ Error in reranking: {e}. Returning original order.")
            return documents[:top_k]
