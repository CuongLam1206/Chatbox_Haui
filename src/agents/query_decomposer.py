"""
Query Decomposition Agent
Tách câu hỏi phức (multi-domain) thành các sub-queries độc lập.
Giúp retrieve đúng tài liệu cho câu hỏi kết hợp nhiều chủ đề.
"""
import json
import re
from typing import List

from core.config import GEMINI_API_KEY, GEMINI_MODEL
from src.llm_provider import get_llm


class QueryDecomposer:
    """
    Phát hiện và tách câu hỏi multi-domain thành sub-queries.
    Ví dụ: "vi phạm đạo văn VÀ bị cảnh báo học tập" → 2 queries riêng.
    """

    DECOMPOSE_PROMPT = """Bạn là chuyên gia phân tích câu hỏi về quy định trường đại học HaUI.

Nhiệm vụ: Phân tích câu hỏi. Nếu câu hỏi hỏi về NHIỀU CHỦ ĐỀ/QUY ĐỊNH KHÁC NHAU cùng lúc,
hãy tách thành các sub-queries riêng biệt (mỗi sub-query về 1 chủ đề). 
Nếu câu hỏi chỉ có 1 chủ đề, trả về nguyên câu hỏi gốc.

Các dấu hiệu câu hỏi phức (nên tách):
- Có từ "VÀ", "và đồng thời", "kết hợp với"
- Hỏi về 2 quy định/văn bản khác nhau cùng lúc
- Ví dụ: "sinh viên vi phạm đạo văn TRONG ĐỒ ÁN và bị cảnh báo học tập lần 2"

Câu hỏi: {question}

Trả về JSON hợp lệ (không giải thích):
{{"sub_queries": ["query1", "query2"]}}

Ví dụ đầu ra cho câu hỏi đơn: {{"sub_queries": ["câu hỏi gốc"]}}
Ví dụ đầu ra cho câu hỏi phức: {{"sub_queries": ["vi phạm đạo văn trong đồ án bị xử lý thế nào", "bị cảnh báo học tập lần 2 liên tiếp bị xử lý thế nào"]}}"""

    # Keywords đơn giản để fast-path (không gọi LLM)
    MULTI_DOMAIN_SIGNALS = [
        " và bị ", " và đồng thời ", " kết hợp với ", " đồng thời ",
        " cùng lúc ", " cả hai ", " vừa ", " ngoài ra còn "
    ]

    def __init__(self):
        self.llm = get_llm(temperature=0)
        print("  [+] QueryDecomposer initialized")

    def _needs_decomposition(self, question: str) -> bool:
        """Fast check: có cần decompose không (dùng keywords)"""
        q_lower = question.lower()
        return any(signal in q_lower for signal in self.MULTI_DOMAIN_SIGNALS)

    def decompose(self, question: str) -> List[str]:
        """
        Tách câu hỏi thành sub-queries.
        Returns list gồm 1 phần tử (câu gốc) nếu không cần tách.
        """
        if not self._needs_decomposition(question):
            return [question]

        try:
            prompt = self.DECOMPOSE_PROMPT.format(question=question)
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                sub_queries = parsed.get("sub_queries", [question])
                if sub_queries and len(sub_queries) > 0:
                    print(f"[Decomposer] Tách thành {len(sub_queries)} sub-queries:")
                    for i, q in enumerate(sub_queries):
                        print(f"  {i+1}. {q}")
                    return sub_queries

        except Exception as e:
            print(f"[Decomposer] Lỗi decompose: {e}, dùng câu gốc")

        return [question]
