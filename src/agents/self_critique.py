"""
Self-Critique Agent (Reflexion Pattern)
Bot tự đánh giá câu trả lời của mình. Nếu không đủ chất lượng, regenerate.
"""
import json
import re
from typing import Optional

from src.llm_provider import get_llm


class SelfCritiqueAgent:
    """
    Đánh giá chất lượng câu trả lời theo 3 tiêu chí:
    1. Completeness: Có trả lời đủ câu hỏi không?
    2. Groundedness: Có căn cứ trên ngữ cảnh không?
    3. Specificity: Có cụ thể (số liệu, điều kiện rõ ràng)?
    """

    CRITIQUE_PROMPT = """Bạn là chuyên gia đánh giá chất lượng câu trả lời về quy định HaUI.

Đánh giá câu trả lời dưới đây theo 3 tiêu chí (0-10 điểm mỗi tiêu chí):

1. **Completeness**: Câu trả lời có trả lời ĐẦY ĐỦ câu hỏi không? (bỏ sót nội dung quan trọng = điểm thấp)
2. **Grounded**: Câu trả lời có căn cứ rõ ràng từ ngữ cảnh không? (cite điều khoản chung chung = điểm thấp)
3. **Specific**: Có nêu rõ số liệu, điều kiện cụ thể không? (câu trả lời mơ hồ = điểm thấp)

Câu hỏi: {question}

Ngữ cảnh (tài liệu): {context_snippet}

Câu trả lời cần đánh giá: {answer}

Trả về JSON hợp lệ duy nhất (không giải thích):
{{"completeness": <0-10>, "grounded": <0-10>, "specific": <0-10>, "avg": <avg>, "improve_hint": "<1 câu gợi ý cải thiện nếu avg < 7, else empty string>"}}"""

    REFINE_PROMPT = """Bạn là trợ lý ảo HaUI. Hãy CẢI THIỆN câu trả lời sau dựa trên gợi ý.

Câu hỏi: {question}
Ngữ cảnh: {context}
Câu trả lời cũ (cần cải thiện): {old_answer}
Gợi ý cải thiện: {hint}

Yêu cầu: Trả lời lại ngắn gọn, đầy đủ, cụ thể hơn. Chỉ dùng thông tin trong ngữ cảnh.
Câu trả lời mới:"""

    QUALITY_THRESHOLD = 7.0  # avg score dưới này sẽ kích hoạt regenerate

    def __init__(self):
        self.llm = get_llm(temperature=0)
        print("  [+] SelfCritiqueAgent initialized")

    def critique(self, question: str, answer: str, context: str) -> dict:
        """Đánh giá câu trả lời, trả về dict với scores và hint"""
        # Chỉ dùng 500 chars đầu của context để tránh token overflow
        context_snippet = context[:500] + "..." if len(context) > 500 else context
        try:
            prompt = self.CRITIQUE_PROMPT.format(
                question=question,
                context_snippet=context_snippet,
                answer=answer
            )
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                avg = result.get('avg', 0)
                print(f"[Critique] completeness={result.get('completeness'):.0f} | grounded={result.get('grounded'):.0f} | specific={result.get('specific'):.0f} | avg={avg:.1f}")
                return result
        except Exception as e:
            print(f"[Critique] Error: {e}")

        return {"completeness": 8, "grounded": 8, "specific": 8, "avg": 8.0, "improve_hint": ""}

    def refine(self, question: str, old_answer: str, context: str, hint: str) -> str:
        """Sinh câu trả lời cải thiện dựa trên hint"""
        try:
            prompt = self.REFINE_PROMPT.format(
                question=question,
                context=context[:1500],  # limit context size
                old_answer=old_answer,
                hint=hint
            )
            response = self.llm.invoke(prompt)
            refined = response.content if hasattr(response, 'content') else str(response)
            print(f"[Critique] Refined answer generated ({len(refined)} chars)")
            return refined.strip()
        except Exception as e:
            print(f"[Critique] Refine error: {e}, keeping original")
            return old_answer

    def evaluate_and_refine(self, question: str, answer: str, context: str) -> str:
        """
        Main method: đánh giá và refine nếu cần.
        Returns final answer (refined hoặc original).
        """
        scores = self.critique(question, answer, context)
        avg = scores.get('avg', 10.0)

        if avg < self.QUALITY_THRESHOLD:
            hint = scores.get('improve_hint', '')
            if hint:
                print(f"[Critique] Score {avg:.1f} < {self.QUALITY_THRESHOLD} → Refining...")
                return self.refine(question, answer, context, hint)
            else:
                print(f"[Critique] Score {avg:.1f} < threshold but no hint, keeping original")

        return answer
