"""
ChromaDB Vector Store Management
"""
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    EnsembleRetriever = None

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

class SimpleEnsembleRetriever(BaseRetriever):
    """Fallback Ensemble Retriever if LangChain version is missing"""
    retrievers: List[BaseRetriever]
    weights: List[float]
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        # Track where each document comes from
        source_map = {} # (content_hash) -> [source_names]
        
        all_docs = []
        for i, retriever in enumerate(self.retrievers):
            name = "Vector" if i == 0 else "BM25"
            retrieved = retriever.invoke(query)
            for doc in retrieved:
                doc.metadata["retrieval_source"] = name
                all_docs.append(doc)
            
        # De-duplicate docs using page_content and metadata as key
        unique_docs = {}
        for doc in all_docs:
            key = (doc.page_content, str(sorted(doc.metadata.items())))
            if key not in unique_docs:
                unique_docs[key] = doc
            else:
                # If already exists, mark as joint source
                unique_docs[key].metadata["retrieval_source"] = "Hybrid (Vector+BM25)"
        
        return list(unique_docs.values())

from core.config import VECTOR_DB_DIR, RETRIEVAL_K
from src.embeddings import get_vietnamese_embeddings


class VectorStoreManager:
    """
    Manage ChromaDB vector store with persistence
    """
    
    def __init__(self, persist_dir: Path = VECTOR_DB_DIR):
        """
        Initialize vector store manager
        
        Args:
            persist_dir: Directory for persistent storage
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Get Vietnamese embedding function
        embedding_function = get_vietnamese_embeddings().get_embedding_function()
        
        print(f"Initializing ChromaDB at: {persist_dir}")
        
        self.vectorstore = Chroma(
            persist_directory=str(persist_dir),
            embedding_function=embedding_function,
            collection_name="haui_regulations"
        )
        
        self.bm25_retriever = None
        self._initialize_bm25()
        
        doc_count = self.vectorstore._collection.count()
        print(f"✓ Vector store ready ({doc_count} documents)")
        if self.bm25_retriever:
            print("✓ Hybrid search capability active (Vector + BM25)")
        else:
            print("⚠ BM25 index is empty. Hybrid search will be limited to Vector search.")
    
    def _initialize_bm25(self):
        """Initialize BM25 retriever from current documents in Chroma"""
        try:
            results = self.vectorstore._collection.get()
            if results and results.get("documents"):
                documents = []
                for i in range(len(results["documents"])):
                    doc = Document(
                        page_content=results["documents"][i],
                        metadata=results["metadatas"][i] if results.get("metadatas") else {}
                    )
                    documents.append(doc)
                
                if documents:
                    self.bm25_retriever = BM25Retriever.from_documents(documents)
                    self.bm25_retriever.k = RETRIEVAL_K
                    print("✓ BM25 Keyword Retriever initialized")
        except Exception as e:
            print(f"⚠ Could not initialize BM25: {e}")
    
    def add_documents(self, chunks: List[Document]) -> List[str]:
        """
        Add new document chunks to vector store
        
        Args:
            chunks: List of Document objects
            
        Returns:
            List of document IDs
        """
        if not chunks:
            return []
        
        print(f"Adding {len(chunks)} chunks to vector store...")
        ids = self.vectorstore.add_documents(chunks)
        # Re-initialize BM25 after adding new docs
        self._initialize_bm25()
        print(f"✓ Added {len(ids)} chunks")
        return ids
    
    def update_documents(self, doc_ids: List[str], new_chunks: List[Document]):
        """
        Update existing documents
        
        Args:
            doc_ids: List of document IDs to update
            new_chunks: New document chunks
        """
        if doc_ids:
            print(f"Updating {len(doc_ids)} documents...")
            self.vectorstore.delete(doc_ids)
        
        self.add_documents(new_chunks)
    
    def delete_documents(self, doc_ids: List[str]):
        """
        Remove documents from vector store
        
        Args:
            doc_ids: List of document IDs to delete
        """
        if not doc_ids:
            return
        
        print(f"Deleting {len(doc_ids)} documents...")
        self.vectorstore.delete(doc_ids)
        print(f"✓ Deleted {len(doc_ids)} documents")
    
    def get_retriever(self, k: int = RETRIEVAL_K):
        """
        Get Hybrid Retriever (Ensemble of Chroma and BM25)
        """
        chroma_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        if self.bm25_retriever:
            if EnsembleRetriever:
                print(f"✓ Using LangChain EnsembleRetriever (weights=[0.5, 0.5], k={k})")
                self.bm25_retriever.k = k
                return EnsembleRetriever(
                    retrievers=[chroma_retriever, self.bm25_retriever],
                    weights=[0.5, 0.5]
                )
            else:
                print(f"✓ Using SimpleEnsembleRetriever fallback (weights=[0.5, 0.5], k={k})")
                self.bm25_retriever.k = k
                return SimpleEnsembleRetriever(
                    retrievers=[chroma_retriever, self.bm25_retriever],
                    weights=[0.5, 0.5]
                )
        
        print("⚠ Using Vector Retriever only (BM25 not available)")
        return chroma_retriever
    
    def similarity_search(self, query: str, k: int = RETRIEVAL_K) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Query string
            k: Number of results
            
        Returns:
            List of relevant documents
        """
        return self.vectorstore.similarity_search(query, k=k)
    
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with collection stats
        """
        count = self.vectorstore._collection.count()
        return {
            "document_count": count,
            "persist_directory": str(self.persist_dir)
        }

    def has_document(self, doc_name: str) -> bool:
        """Check if a document exists in the vector store."""
        # Kiem tra ca filename (co duoi) va doc_type (khong duoi) de tranh trung lap
        results = self.vectorstore._collection.get(
            where={"$or": [
                {"filename": {"$eq": doc_name}},
                {"filename": {"$eq": f"{doc_name}.md"}},
                {"doc_type": {"$eq": doc_name}}
            ]},
            include=[],
        )
        return len(results.get("ids", [])) > 0
