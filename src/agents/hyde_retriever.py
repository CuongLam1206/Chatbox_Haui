"""
HyDE Retriever - Hypothetical Document Embeddings
Sinh hypothetical answer để cải thiện embedding similarity với tài liệu thực tế.
Giúp retrieve đúng hơn cho các câu hỏi ngắn/mơ hồ.
"""
from typing import List

from langchain_core.documents import Document

from src.llm_provider import get_llm


class HyDERetriever:
    """
    Tạo hypothetical document, embed nó thay vì embed câu hỏi trực tiếp.
    Hypothesis: embedding của "đoạn văn quy định giả lập" gần hơn với
    embedding của tài liệu thực tế hơn là embedding của câu hỏi.
    """

    HYDE_PROMPT = """Viết 2-3 câu văn ngắn mô phỏng nội dung của một điều khoản 
trong quy định/quy chế của Trường Đại học Công nghiệp Hà Nội (HaUI) 
có thể trả lời câu hỏi sau. Viết theo văn phong quy định chính thức.
KHÔNG giải thích, KHÔNG hỏi ngược, chỉ viết đoạn văn mô phỏng.

Câu hỏi: {question}

Đoạn văn mô phỏng:"""

    def __init__(self, vector_store):
        """
        Args:
            vector_store: VectorStoreManager instance
        """
        self.vector_store = vector_store
        self.llm = get_llm(temperature=0)
        print("  [+] HyDERetriever initialized")

    def _generate_hypothesis(self, question: str) -> str:
        """Sinh hypothetical document từ câu hỏi"""
        try:
            prompt = self.HYDE_PROMPT.format(question=question)
            response = self.llm.invoke(prompt)
            hypo = response.content if hasattr(response, 'content') else str(response)
            hypo = hypo.strip()
            print(f"[HyDE] Hypothesis: {hypo[:100]}...")
            return hypo
        except Exception as e:
            print(f"[HyDE] Lỗi sinh hypothesis: {e}")
            return question  # fallback về câu gốc

    def retrieve(self, question: str, k: int = 4) -> List[Document]:
        """
        Retrieve bằng cách kết hợp:
        - Embedding của hypothetical document (HyDE)
        - Embedding của câu hỏi gốc (standard)
        Merge và de-duplicate kết quả.
        """
        # Bước 1: Sinh hypothetical document
        hypo_doc = self._generate_hypothesis(question)

        # Bước 2: Retrieve bằng hypothesis embedding
        try:
            docs_by_hypo = self.vector_store.vectorstore.similarity_search(
                hypo_doc, k=k
            )
            for doc in docs_by_hypo:
                doc.metadata["retrieval_source"] = "HyDE"
        except Exception as e:
            print(f"[HyDE] Retrieval by hypothesis failed: {e}")
            docs_by_hypo = []

        # Bước 3: Retrieve bằng query gốc
        try:
            docs_by_query = self.vector_store.vectorstore.similarity_search(
                question, k=k
            )
            for doc in docs_by_query:
                if doc.metadata.get("retrieval_source") != "HyDE":
                    doc.metadata["retrieval_source"] = "Vector"
        except Exception as e:
            print(f"[HyDE] Retrieval by query failed: {e}")
            docs_by_query = []

        # Bước 4: Merge + de-duplicate (HyDE docs ưu tiên trước)
        seen = set()
        merged = []
        for doc in docs_by_hypo + docs_by_query:
            h = hash(doc.page_content)
            if h not in seen:
                seen.add(h)
                merged.append(doc)

        print(f"[HyDE] Retrieved {len(docs_by_hypo)} HyDE + {len(docs_by_query)} standard = {len(merged)} unique")
        return merged


def estimate_query_complexity(question: str) -> str:
    """
    Ước tính độ phức tạp của câu hỏi để chọn k phù hợp.
    
    Returns:
        'simple' → k=3
        'medium' → k=6 (default)
        'complex' → k=10
    """
    q = question.lower()

    # Signals cho câu hỏi phức
    complex_signals = [
        "điều kiện", "các trường hợp", "tất cả", "đầy đủ",
        "toàn bộ", "liệt kê", "bao gồm những", "các loại",
        "quy trình", "các bước", "thủ tục", "hồ sơ",
        "những gì", "như thế nào", "ra sao", "thế nào",
        "các quy định", "đối tượng nào", "trường hợp nào"
    ]
    # Signals cho câu hỏi đơn
    simple_signals = [
        "có không", "có được không", "bao nhiêu", "ở đâu",
        "khi nào", "là gì", "bằng bao nhiêu", "mấy"
    ]

    complex_score = sum(1 for s in complex_signals if s in q)
    simple_score = sum(1 for s in simple_signals if s in q)

    if complex_score >= 2:
        return "complex"
    if simple_score >= 1 and complex_score == 0:
        return "simple"
    return "medium"
