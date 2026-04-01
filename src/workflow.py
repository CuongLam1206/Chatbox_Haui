"""
Agentic RAG Workflow using LangGraph
Orchestrates the multi-agent RAG pipeline
"""
from typing import TypedDict, List

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

from src.vector_store import VectorStoreManager
from src.agents.grader import DocumentGrader
from src.agents.generator import AnswerGenerator
from src.agents.hallucination_check import HallucinationChecker
from src.agents.router import QueryRouter
from src.agents.rewriter import QueryRewriter
from src.agents.document_generator import DocumentGenerator
from src.agents.reranker import DocumentReranker
from core.config import RELEVANCE_THRESHOLD, MAX_RETRIES, ENABLE_HALLUCINATION_CHECK


class GraphState(TypedDict):
    """
    Represents the state of the graph
    """
    question: str  # User question
    chat_history: List[dict]  # Conversation history
    documents: List[Document]  # Retrieved documents
    generation: str  # Generated answer
    sources: List[str]  # Source references
    relevance_score: float  # Document relevance score
    is_grounded: bool  # Hallucination check result
    retry_count: int  # Number of retries


class AgenticRAG:
    """
    Agentic RAG workflow with quality checks
    """
    
    def __init__(self, vector_store: VectorStoreManager):
        """
        Initialize Agentic RAG workflow
        
        Args:
            vector_store: Vector store manager instance
        """
        self.vector_store = vector_store
        self.retriever = vector_store.get_retriever()
        
        # Initialize agents
        self.router = QueryRouter()
        self.rewriter = QueryRewriter()
        self.grader = DocumentGrader()
        self.generator = AnswerGenerator()
        self.document_generator = DocumentGenerator()
        self.reranker = DocumentReranker()
        self.hallucination_checker = HallucinationChecker() if ENABLE_HALLUCINATION_CHECK else None
        
        print("✓ Agentic RAG workflow initialized")
    
    def retrieve(self, state: GraphState) -> GraphState:
        """
        Retrieve relevant documents
        """
        question = state["question"]
        chat_history = state["chat_history"]
        
        # For appendix queries, use original question for better precision
        is_appendix_query = "phụ lục" in question.lower()
        
        if is_appendix_query:
            # Use original question to search for specific appendix
            search_query = question
            print(f"[Retrieval] Appendix query detected, using original: {search_query}")
        else:
            # Rewrite query for better search results, using history to resolve pronouns
            search_query = self.rewriter.rewrite(question, chat_history)
            print(f"[Retrieval] Search query: {search_query}")
        
        # Default k
        k = 10
        
        print(f"\n[Retrieval] Searching for: {question[:100]}... (k={k})")
        # Use hybrid retriever (Vector + BM25) for better keyword matching
        documents = self.retriever.invoke(search_query)
        
        # For appendix queries, filter by exact article number in metadata
        if is_appendix_query:
            import re
            appendix_match = re.search(r'phụ lục\s*(\d+)', question.lower())
            if appendix_match:
                appendix_num_str = appendix_match.group(1)
                append_num_with_zero = appendix_num_str.zfill(2)  # "07"
                appendix_num_no_zero = str(int(appendix_num_str))  # "7"
                
                print(f"[Retrieval] Filtering for article='{append_num_with_zero}' or '{appendix_num_no_zero}'")
                
                # Filter documents by metadata article number (try both formats)
                filtered_docs = [
                    doc for doc in documents
                    if doc.metadata.get('article', '') in [append_num_with_zero, appendix_num_no_zero]
                ]
                
                if filtered_docs:
                    print(f"[Retrieval] Found {len(filtered_docs)} exact matches for Phụ lục {appendix_num_str}")
                    documents = filtered_docs
                else:
                    print(f"[Retrieval] No exact metadata match, using semantic results")
        
        
        print(f"[Retrieval] Found {len(documents)} documents")
        for i, doc in enumerate(documents):
            source = doc.metadata.get('source', 'Unknown')
            ret_type = doc.metadata.get('retrieval_source', 'Unknown')
            article = doc.metadata.get('article', 'N/A')
            print(f"  {i+1}. [{ret_type}] [{source}] Article: {article}")
        
        # ── Intent-based article injection ──────────────────────────────────────
        import re as _re
        _q = question.lower()
        
        # Case 1: "đối tượng miễn/giảm học phí" → inject Article 4/5 from 29.1148
        is_exemption_obj_query = (
            ("đối tượng" in _q or "ai được" in _q or "trường hợp nào" in _q) and
            ("miễn" in _q or "giảm" in _q) and "học phí" in _q
        )
        # Case 2: "đánh giá học phần" / "phương pháp đánh giá" → inject Article 9 Quy chế
        is_grading_method_query = (
            ("đánh giá" in _q) and
            ("học phần" in _q or "phương pháp" in _q or "hình thức" in _q) and
            "học phí" not in _q  # phân biệt với "đánh giá miễn học phí"
        )

        def _inject_articles(search_text, article_filter, label):
            try:
                injected = self.vector_store.vectorstore.similarity_search(
                    search_text, k=4, filter={"article": article_filter}
                )
                if injected:
                    existing_ids = {id(d) for d in documents}
                    new_docs = [d for d in injected if id(d) not in existing_ids]
                    if new_docs:
                        print(f"[Retrieval] {label} — injected {len(new_docs)} targeted articles to front")
                        return new_docs + documents
            except Exception as _e:
                print(f"[Retrieval] Article injection failed ({label}): {_e}")
            return documents

        if is_exemption_obj_query:
            documents = _inject_articles(
                "đối tượng được miễn học phí", {"$in": ["4", "5"]},
                "Exemption-obj query"
            )
        if is_grading_method_query:
            documents = _inject_articles(
                "điểm thành phần đánh giá học phần thường xuyên giữa kỳ kết thúc",
                {"$in": ["9"]},
                "Grading-method query"
            )
        # ────────────────────────────────────────────────────────────────────────

        # ── Location query boost ─────────────────────────────────────────────────
        # Khi query hỏi về địa chỉ/phòng ban → ưu tiên SEEE.md lên đầu
        location_keywords = ["ở đâu", "địa chỉ", "liên hệ", "tầng"]
        is_location_query = any(kw in question.lower() for kw in location_keywords)
        if is_location_query and documents:
            seee_docs = [d for d in documents if
                         "seee" in (d.metadata.get('source', '') + d.metadata.get('filename', '')).lower() or
                         "giới thiệu" in (d.metadata.get('source', '') + d.metadata.get('filename', '')).lower()]
            other_docs = [d for d in documents if d not in seee_docs]
            if seee_docs:
                documents = seee_docs + other_docs
                print(f"[Retrieval] Location query — boosted {len(seee_docs)} SEEE.md docs to front")
        # ────────────────────────────────────────────────────────────────────────

        state["documents"] = documents
        return state
    
    def grade_documents(self, state: GraphState) -> GraphState:
        """
        Grade retrieved documents for relevance
        """
        question = state["question"]
        documents = state["documents"]
        
        print(f"[Grading] Evaluating {len(documents)} documents...")
        
        relevant_docs, relevance_score = self.grader.grade_documents(question, documents)
        
        print(f"[Grading] Relevance: {relevance_score:.2%} ({len(relevant_docs)}/{len(documents)} relevant)")
        if len(relevant_docs) < len(documents):
            print(f"  - Rejected {len(documents) - len(relevant_docs)} documents as irrelevant")
        
        state["documents"] = relevant_docs
        state["relevance_score"] = relevance_score
        
        # Safety net: nếu grader reject toàn bộ → giữ top-1 original doc
        # Flag fallback để reranker biết bỏ qua → không tốn LLM call thêm
        if not relevant_docs and documents:
            print(f"[Grading Safety] All docs rejected! Keeping top 1 as fallback (skip rerank).")
            state["documents"] = documents[:1]
            state["relevance_score"] = 0.2
            state["is_grader_fallback"] = True  # flag để skip reranker
        else:
            state["is_grader_fallback"] = False
        
        return state
    
    def rerank_documents(self, state: GraphState) -> GraphState:
        """
        Rerank retrieved documents for precision.
        Bỏ qua nếu đị grader fallback (đã chọn top-1 tốt nhất) → tiết kiệm 1 LLM call.
        """
        question = state["question"]
        documents = state["documents"]
        
        # Skip reranker khi ở chế độ fallback → giữ tốc độ baseline
        if state.get("is_grader_fallback", False):
            print(f"[Reranking] Skipped (grader fallback mode) – using top-1 directly.")
            return state
        
        if not documents:
            return state
            
        print(f"[Reranking] Re-evaluating {len(documents)} relevant documents...")
        reranked_docs = self.reranker.rerank(question, documents)
        
        state["documents"] = reranked_docs
        return state
    
    def generate_answer(self, state: GraphState) -> GraphState:
        """
        Generate answer from relevant documents
        """
        question = state["question"]
        documents = state["documents"]
        chat_history = state["chat_history"]
        
        print(f"[Generation] Creating answer...")
        
        answer, sources = self.generator.generate_from_documents(question, documents, chat_history)
        
        state["generation"] = answer
        state["sources"] = sources
        
        print(f"[Generation] Answer: {answer[:100]}...")
        print(f"[Generation] Sources: {', '.join(sources) if sources else 'None'}")
        
        return state
    
    def check_hallucination(self, state: GraphState) -> GraphState:
        """
        Check if answer is grounded in documents
        """
        if not self.hallucination_checker:
            state["is_grounded"] = True
            return state
        
        generation = state["generation"]
        documents = state["documents"]
        
        print(f"[Hallucination Check] Verifying answer...")
        
        # Combine documents for checking
        doc_text = "\n\n".join([
            doc.page_content if hasattr(doc, 'page_content') else str(doc)
            for doc in documents
        ])
        
        is_grounded = self.hallucination_checker.check(generation, doc_text)
        
        state["is_grounded"] = is_grounded
        
        print(f"[Hallucination Check] {'✓ Grounded' if is_grounded else '✗ Hallucination detected'}")
        
        return state
    
    def run(self, question: str, session_id: str = None, chat_history: list = None) -> dict:
        """
        Run the complete Agentic RAG workflow
        
        Args:
            question: User question
            session_id: Session ID (for tracing/logging)
            chat_history: Optional history list (if provided externally)
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Initialize state
        history = chat_history or []
        state: GraphState = {
            "question": question,
            "chat_history": history,
            "documents": [],
            "generation": "",
            "sources": [],
            "relevance_score": 0.0,
            "is_grounded": True,
            "retry_count": 0
        }
        
        # Step 0: Route the query (considering history)
        route = self.router.route(question, history)
        print(f"\n[Router] Routing query to: {route}")
        
        if route == "greeting":
            return {
                "answer": "Xin chào! Tôi là Trợ lý Sinh viên Thông minh của HaUI. Tôi có thể hỗ trợ bạn các thông tin chuyên môn, quy trình thủ tục hoặc giải đáp các thắc mắc về nhà trường. Bạn cần tôi giúp gì hôm nay?",
                "sources": [],
                "relevance_score": 1.0,
                "is_grounded": True
            }
        elif route == "out_of_scope":
            return {
                "answer": "Xin lỗi, tôi là Trợ lý ảo chuyên biệt cho các vấn đề tại HaUI. Câu hỏi này nằm ngoài phạm vi hỗ trợ của tôi. Bạn vui lòng đặt câu hỏi liên quan đến học tập hoặc đời sống tại trường nhé.",
                "sources": [],
                "relevance_score": 0.0,
                "is_grounded": True
            }
        elif route == "learn":
            short, full = self.rewriter.extract_new_slang(question)
            self.rewriter.slang_manager.save_mapping(short, full)
            print(f"[Learn] Stored new abbreviation: {short} -> {full}")
            return {
                "answer": f"Đã hiểu! Tôi đã ghi nhớ: **{short}** là viết tắt của **{full}**. Từ nay tôi sẽ dùng thông tin này để hỗ trợ bạn tìm kiếm chính xác hơn.",
                "sources": [],
                "relevance_score": 1.0,
                "is_grounded": True
            }
        elif route == "general":
            print("[General] Generating conversational response...")
            answer = self.generator.generate_general_response(question, history)
            return {
                "answer": answer,
                "sources": [],
                "relevance_score": 1.0,
                "is_grounded": True
            }
        elif route == "document_generation":
            # Always use RAG-based generation for appendix queries
            print("[Document Generation] Using RAG-based generation...")
            # Mark as document query (not template) for normal RAG flow
            state["is_document_query"] = True
        
        # Step 1: Retrieve documents
        state = self.retrieve(state)
        
        # For document queries, skip grading/reranking since retrieval is already accurate
        is_document_query = state.get("is_document_query", False)
        
        if is_document_query:
            print("[Document Query] Skipping grading/reranking - using retrieved documents directly")
            # Set high relevance score since retrieval already found the right documents
            state["relevance_score"] = 1.0
        else:
            # Step 2: Grade documents (expensive - calls LLM for each doc)
            state = self.grade_documents(state)
            
            # Step 2.5: Rerank documents for precision (expensive - calls LLM again)
            state = self.rerank_documents(state)
        
        # Step 3: Check if we have relevant documents
        if not state["documents"]:
            print(f"\n[Decision] No relevant documents found (Score: {state['relevance_score']:.2%})")
            return {
                "answer": "Xin lỗi, tôi chưa có thông tin để trả lời câu hỏi này. Bạn vui lòng liên hệ trực tiếp Phòng Đào tạo hoặc Phòng Công tác Sinh viên của nhà trường để được hỗ trợ.",
                "sources": [],
                "relevance_score": state["relevance_score"],
                "is_grounded": True
            }
        
        # Step 4: Generate answer with retry logic
        max_retries = MAX_RETRIES
        
        while state["retry_count"] <= max_retries:
            state = self.generate_answer(state)
            
            # Step 5: Check for hallucinations (if enabled)
            if ENABLE_HALLUCINATION_CHECK:
                state = self.check_hallucination(state)
                
                if state["is_grounded"]:
                    break
                else:
                    state["retry_count"] += 1
                    if state["retry_count"] <= max_retries:
                        print(f"\n[Retry] Regenerating answer (attempt {state['retry_count']}/{max_retries})...")
            else:
                break
        
        # Return final result
        return {
            "answer": state["generation"],
            "sources": state["sources"],
            "relevance_score": state["relevance_score"],
            "is_grounded": state["is_grounded"],
            "retry_count": state["retry_count"]
        }
