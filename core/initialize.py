"""
System Initialization Script
Loads documents, creates vector store, and prepares the system
"""
import sys
import shutil
from pathlib import Path

# Add project root to path (core/ → project root)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings import get_vietnamese_embeddings
from src.document_loader import DocumentLoader, DocumentMonitor
from src.vector_store import VectorStoreManager
from src.mongodb_handler import ConversationManager
from src.workflow import AgenticRAG
from core.config import DOCUMENT_DIR, VECTOR_DB_DIR


def initialize_system(force_rebuild: bool = False):
    """
    Initialize the chatbot system
    
    Args:
        force_rebuild: Force rebuild of vector store
        
    Returns:
        Tuple of (workflow, conversation_manager, vector_store)
    """
    print("=" * 60)
    print("INITIALIZING AGENTIC RAG CHATBOT SYSTEM")
    print("=" * 60)
    
    # Step 1: Initialize Vietnamese embeddings
    print("\n[1/5] Loading Vietnamese Embedding Model...")
    embedding = get_vietnamese_embeddings()
    
    # Step 2: Check for document updates
    print("\n[2/5] Checking for Document Updates...")
    doc_monitor = DocumentMonitor()
    updates = doc_monitor.check_updates()
    
    # Step 3: Load and process documents if needed
    needs_indexing = force_rebuild or len(updates) > 0
    
    if force_rebuild and VECTOR_DB_DIR.exists():
        print(f"\n[!] Cleaning existing vector database at {VECTOR_DB_DIR}...")
        shutil.rmtree(VECTOR_DB_DIR)
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    vector_store = VectorStoreManager()
    
    if needs_indexing:
        print("\n[3/5] Loading and Processing Documents...")
        doc_loader = DocumentLoader()
        chunks = doc_loader.load_and_split(DOCUMENT_DIR)
        
        print(f"\n[3/5] Building Vector Store...")
        vector_store.add_documents(chunks)
    else:
        print("\n[3/5] Vector Store Already Up-to-Date")
    
    # Display stats
    stats = vector_store.get_collection_stats()
    print(f"  → {stats['document_count']} documents indexed")
    
    # Step 4: Initialize MongoDB
    print("\n[4/5] Connecting to MongoDB...")
    conversation_manager = ConversationManager()
    
    # Step 5: Initialize Agentic RAG workflow
    print("\n[5/5] Initializing Agentic RAG Workflow...")
    workflow = AgenticRAG(vector_store)
    
    print("\n" + "=" * 60)
    print("✓ SYSTEM READY")
    print("=" * 60)
    
    return workflow, conversation_manager, vector_store


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Agentic RAG Chatbot")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild of vector store"
    )
    
    args = parser.parse_args()
    
    workflow, conv_manager, vector_store = initialize_system(force_rebuild=args.rebuild)
    
    # Test query
    print("\n" + "=" * 60)
    print("Testing with sample query...")
    print("=" * 60)
    
    test_question = "Điều kiện để được xét tốt nghiệp là gì?"
    result = workflow.run(test_question)
    
    print(f"\n📝 Question: {test_question}")
    print(f"\n✅ Answer: {result['answer']}")
    print(f"\n📚 Sources: {', '.join(result['sources']) if result['sources'] else 'None'}")
    print(f"\n📊 Relevance: {result['relevance_score']:.2%}")
    print(f"✓ Grounded: {result['is_grounded']}")
