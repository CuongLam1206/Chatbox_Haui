import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

import core.config as cfg
# Disable HyDE and Decomposer for local test (optional)
cfg.ENABLE_HYDE = True 
cfg.ENABLE_DECOMPOSER = False

from core.initialize import initialize_system

def test_question(question):
    print(f"\n{'='*50}")
    print(f"Testing Question: {question}")
    print(f"{'='*50}")
    
    workflow, _, _ = initialize_system()
    result = workflow.run(question)
    
    print(f"\nRESPONSE:\n{result['answer']}")
    print(f"\nSOURCE DOCUMENTS:")
    for i, src in enumerate(result.get('sources', [])):
        print(f"  {i+1}. {src}")
    return result

if __name__ == "__main__":
    # Test cases identified as problematic
    questions = [
        "Danh hiệu khen thưởng cá nhân sinh viên gồm mấy loại?",
        "Hội đồng đánh giá đồ án tốt nghiệp gồm tối thiểu bao nhiêu thành viên?",
        "Sinh viên nghỉ học từ 46% đến 60% tổng số giờ trong học kỳ bị xử lý kỷ luật thế"
    ]
    
    for q in questions:
        test_question(q)
