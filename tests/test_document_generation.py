"""
Test script for Document Generation feature
"""
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.agents.router import QueryRouter
from src.agents.document_generator import DocumentGenerator
from src.vector_store import VectorStoreManager
from src.workflow import AgenticRAG

def test_routing():
    print("\n--- Testing Router ---")
    router = QueryRouter()
    
    questions = [
        "Xuất cho tôi Phụ lục 05",
        "Bạn có mẫu bản nhận xét đánh giá KLTN không?",
        "Tạo phiếu theo dõi tiến độ",
        "Quy trình bảo vệ đồ án như thế nào?",
        "Điểm A là bao nhiêu?"
    ]
    
    for q in questions:
        route = router.route(q)
        print(f"Question: {q} -> Route: {route}")

def test_generation():
    print("\n--- Testing Generation ---")
    gen = DocumentGenerator()
    
    questions = [
        "Xuất phụ lục 05",
        "Cho mình xin bản nhận xét đánh giá phụ lục 6",
        "Xuất Phụ lục 09: Biên bản giải trình tiếp thu sửa chữa",
        "Mẫu biên bản họp"
    ]
    
    for q in questions:
        answer, doc = gen.generate(q)
        print(f"\nQuestion: {q}")
        print(f"Answer: {answer}")
        if doc:
            print(f"Document Length: {len(doc)} characters")
            print(f"Document Preview: {doc[:100]}...")
        else:
            print("No document generated.")

def test_workflow():
    print("\n--- Testing Full Workflow (RAG Fallback) ---")
    vstore = VectorStoreManager()
    rag = AgenticRAG(vstore)
    
    # This should trigger document_generation route, then RAG fallback because Phụ lục 09 is not hardcoded
    question = "Hãy xuất cho tôi nội dung của Phụ lục 09: Biên bản giải trình tiếp thu sửa chữa"
    
    print(f"\nQuestion: {question}")
    result = rag.run(question)
    print(f"Answer Preview: {result['answer'][:500]}...")
    print(f"Sources: {result['sources']}")

if __name__ == "__main__":
    # Ensure environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env")
        sys.exit(1)
        
    test_routing()
    test_generation()
    test_workflow()
