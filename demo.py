"""
Gradio Demo Interface for Agentic RAG Chatbot
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import gradio as gr
from core.initialize import initialize_system


# Handle command line arguments
parser = argparse.ArgumentParser(description="Start HaUI Smart Assistant Gradio Demo")
parser.add_argument("--rebuild", action="store_true", help="Force rebuild of vector store")
args = parser.parse_args()

# Initialize system
print("🚀 Starting Agentic RAG Chatbot...")
workflow, conversation_manager, vector_store = initialize_system(force_rebuild=args.rebuild)


# Track session ID in a global or state variable
# For simplicity in this demo, we'll use a single session or create one per user
current_session_id = None

def chat_function(message: str, history: list) -> str:
    """
    Handle chat messages with persistent memory
    """
    global current_session_id
    
    if not message.strip():
        return "Vui lòng nhập câu hỏi của bạn."
    
    # Initialize session if not exists
    if current_session_id is None:
        current_session_id = conversation_manager.create_session()
    
    # Get chat history from MongoDB (increased to 100 to support summarizing the whole conversation)
    chat_history = conversation_manager.get_history(current_session_id, limit=100)
    
    # Run Agentic RAG workflow with history
    result = workflow.run(message, session_id=current_session_id, chat_history=chat_history)
    
    # Format response
    answer = result['answer']
    
    # Save to MongoDB
    conversation_manager.add_message(current_session_id, "user", message)
    conversation_manager.add_message(current_session_id, "assistant", answer, sources=result.get('sources'))
    
    if result.get('sources'):
        sources_text = ", ".join(result['sources'])
        answer += f"\n\n📚 **Nguồn tham khảo**: {sources_text}"
    
    if result.get('relevance_score', 0) > 0:
        answer += f"\n\n_Độ liên quan: {result['relevance_score']:.0%}_"
    
    return answer


# Sample questions for quick testing
examples = [
    "Điều kiện để được xét tốt nghiệp là gì?",
    "Cách tính điểm trung bình chung tích lũy?",
    "Quy định về rèn luyện và kỷ luật?",
    "Thông tin về ký túc xá HaUI?",
    "Tóm tắt các cuộc hội thoại vừa rồi?"
]


# Create Gradio interface
demo = gr.ChatInterface(
    fn=chat_function,
    title="🎓 HaUI Smart Assistant",
    description=(
        "### Trợ lý Sinh viên Thông minh - Trường Đại học Công nghiệp Hà Nội\n"
        "Chào mừng bạn! Tôi là trợ lý ảo được đào tạo để hỗ trợ sinh viên về:\n"
        "- 📁 **Quy chế & Thủ tục**: Đăng ký học phần, xét tốt nghiệp, đồ án...\n"
        "- 📝 **Thông báo & Quy định**: Các văn bản mới nhất từ phía nhà trường.\n"
        "- 💬 **Hỗ trợ 24/7**: Giải đáp mọi thắc mắc về đời sống sinh viên tại HaUI."
    ),
    examples=examples,
)


if __name__ == "__main__":
    # Display startup info
    stats = vector_store.get_collection_stats()
    
    print("\n" + "=" * 60)
    print("📊 SYSTEM STATUS")
    print("=" * 60)
    print(f"  Documents indexed: {stats['document_count']}")
    print(f"  Vector DB: {stats['persist_directory']}")
    print("  Agentic RAG: Active")
    print("  MongoDB: Connected" if conversation_manager.client else "Disconnected")
    print("=" * 60)
    print("\n🌐 Starting Gradio interface...")
    print("   Access at: http://localhost:7860")
    print("=" * 60 + "\n")
    
    # Launch interface
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )
