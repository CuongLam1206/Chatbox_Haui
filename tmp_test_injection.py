"""Quick test: verify intent-based article injection works for thesis and plagiarism queries"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.initialize import initialize_system

workflow, _, _ = initialize_system()

# Test 1: Thesis query (G7-005)
print("\n" + "="*60)
print("TEST 1: Thesis query (G7-005)")
print("="*60)
state = {
    "question": "Sinh viên trình bày đồ án tốt nghiệp trước hội đồng trong bao nhiêu phút?",
    "chat_history": [],
    "documents": [],
    "generation": "",
    "sources": [],
    "relevance_score": 0.0,
    "is_grounded": False,
    "retry_count": 0
}
state = workflow.retrieve(state)
print(f"\nRetrieved {len(state['documents'])} docs")
for i, doc in enumerate(state['documents'][:5]):
    content_preview = doc.page_content[:200].replace('\n', ' ')
    has_15min = "15 phút" in doc.page_content or "10 đến 15" in doc.page_content
    print(f"  [{i}] {'✓ HAS 15 MIN' if has_15min else '✗'} | {content_preview}...")

# Test 2: Plagiarism query (G13-002)
print("\n" + "="*60)
print("TEST 2: Plagiarism query (G13-002)")
print("="*60)
state2 = {
    "question": "Nhà trường sử dụng phần mềm nào để kiểm tra đạo văn?",
    "chat_history": [],
    "documents": [],
    "generation": "",
    "sources": [],
    "relevance_score": 0.0,
    "is_grounded": False,
    "retry_count": 0
}
state2 = workflow.retrieve(state2)
print(f"\nRetrieved {len(state2['documents'])} docs")
for i, doc in enumerate(state2['documents'][:5]):
    content_preview = doc.page_content[:200].replace('\n', ' ')
    has_turnitin = "turnitin" in doc.page_content.lower()
    print(f"  [{i}] {'✓ HAS TURNITIN' if has_turnitin else '✗'} | {content_preview}...")
