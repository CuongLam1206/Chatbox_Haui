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
from src.agents.query_decomposer import QueryDecomposer
from src.agents.hyde_retriever import HyDERetriever, estimate_query_complexity
from src.agents.self_critique import SelfCritiqueAgent
from core.config import RELEVANCE_THRESHOLD, MAX_RETRIES, ENABLE_HALLUCINATION_CHECK, ENABLE_HYDE, ENABLE_DECOMPOSER


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
        
        # New: Query Decomposer + HyDE Retriever (configurable)
        self.decomposer = QueryDecomposer() if ENABLE_DECOMPOSER else None
        self.hyde_retriever = HyDERetriever(vector_store) if ENABLE_HYDE else None
        self.self_critique = SelfCritiqueAgent()
        
        mode = []
        if ENABLE_DECOMPOSER: mode.append("QueryDecomposer")
        if ENABLE_HYDE: mode.append("HyDE")
        mode.append("SelfCritique")
        mode_str = "+".join(mode) if mode else "Standard"
        print(f"✓ Agentic RAG workflow initialized ({mode_str})")
    
    def retrieve(self, state: GraphState) -> GraphState:
        """
        Retrieve relevant documents
        """
        question = state["question"]
        chat_history = state["chat_history"]
        
        # For appendix queries, use original question for better precision
        is_appendix_query = "phụ lục" in question.lower()
        
        if is_appendix_query:
            search_queries = [question]
            print(f"[Retrieval] Appendix query detected, using original: {question}")
        else:
            if ENABLE_DECOMPOSER and self.decomposer:
                # Step 1: Decompose multi-domain queries
                decomposed = self.decomposer.decompose(question)
            else:
                decomposed = [question]
            # Step 2: Rewrite each sub-query
            search_queries = []
            for sub_q in decomposed:
                rewritten = self.rewriter.rewrite(sub_q, chat_history)
                search_queries.extend(rewritten)
            print(f"[Retrieval] Search queries: {search_queries}")
        
        # Adaptive k: adjust retrieval depth by query complexity
        complexity = estimate_query_complexity(question)
        k_map = {"simple": 4, "medium": 7, "complex": 10}
        k = k_map[complexity]
        print(f"[Retrieval] complexity={complexity} → k={k} | HyDE={'on' if ENABLE_HYDE else 'off'} | Decomp={'on' if ENABLE_DECOMPOSER else 'off'}")
        
        all_documents = []
        seen_contents = set()
        
        print(f"\n[Retrieval] Processing {len(search_queries)} search queries...")
        
        first_hypothesis = ""  # reserved for future use
        for q in search_queries:
            if ENABLE_HYDE and self.hyde_retriever:
                # Use HyDE retriever (hypothesis + standard combined)
                query_docs = self.hyde_retriever.retrieve(q, k=k)
            else:
                # Fallback: standard hybrid retriever
                query_docs = self.retriever.invoke(q)
            for doc in query_docs:
                content_hash = hash(doc.page_content)
                if content_hash not in seen_contents:
                    all_documents.append(doc)
                    seen_contents.add(content_hash)
        
        documents = all_documents
        
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
        
        # Limit total documents to 15 to stay within reasonable context
        documents = documents[:15]
        
        print(f"[Retrieval] Found {len(documents)} unique documents")
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
        # Case 3: "Học bổng" + "Kỷ luật" / "Điều kiện" → inject Article 4 from Quy định học bổng (725)
        is_scholarship_condition_query = (
            ("học bổng" in _q) and
            ("điều kiện" in _q or "kỷ luật" in _q or "xét" in _q)
        )

        def _inject_articles(search_text, article_filter, label, source_filter=None):
            try:
                if source_filter:
                    # ChromaDB requires $and for multiple conditions
                    filters = {
                        "$and": [
                            {"article": article_filter},
                            {"source": {"$contains": source_filter}}
                        ]
                    }
                else:
                    filters = {"article": article_filter}
                
                print(f"[Retrieval] {label} — searching with filter: {filters}")
                injected = self.vector_store.vectorstore.similarity_search(
                    search_text, k=4, filter=filters
                )
                if injected:
                    existing_hashes = {hash(d.page_content) for d in documents}
                    new_docs = [d for d in injected if hash(d.page_content) not in existing_hashes]
                    if new_docs:
                        print(f"[Retrieval] {label} — injected {len(new_docs)} targeted articles to front")
                        return new_docs + documents
                    else:
                        print(f"[Retrieval] {label} — all injected docs already in results")
                else:
                    print(f"[Retrieval] {label} — no docs found matching filter")
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
        if is_scholarship_condition_query:
            documents = _inject_articles(
                "điều kiện xét cấp học bổng khuyến khích học tập kỷ luật",
                {"$in": ["4"]},
                "Scholarship-condition query",
                source_filter="725"
            )

        # Case 4: "đồ án tốt nghiệp" / "khóa luận" / "bảo vệ" / "trình bày" → inject Đ14 from qd-1532
        is_thesis_query = any(kw in _q for kw in [
            "đồ án tốt nghiệp", "khóa luận", "bảo vệ đồ án", "trình bày đồ án",
            "hội đồng đánh giá", "đa/kltn", "kltn", "bảo vệ luận văn"
        ])
        if is_thesis_query:
            documents = _inject_articles(
                "trình bày đồ án tốt nghiệp hội đồng đánh giá thời gian phút",
                {"$in": ["14", "12", "11", "7"]},
                "Thesis/KLTN query",
                source_filter="1532"
            )

        # Case 5: "đạo văn" / "trùng lặp" / "kiểm tra đạo văn" / "Turnitin" → inject Đ4 from qd-197
        is_plagiarism_query = any(kw in _q for kw in [
            "đạo văn", "trùng lặp", "turnitin", "kiểm tra đạo văn", "sao chép"
        ])
        if is_plagiarism_query:
            documents = _inject_articles(
                "phần mềm kiểm tra đạo văn Turnitin tỷ lệ trùng lặp mức xử lý",
                {"$in": ["4", "5", "6"]},
                "Plagiarism query",
                source_filter="197"
            )
        # Case 6: "tổ chức giảng dạy" / "yêu cầu giảng dạy" → inject Điều 8 from Quy chế
        is_teaching_org_query = (
            ("giảng dạy" in _q or "dạy và học" in _q or "dạy học" in _q) and
            ("tổ chức" in _q or "yêu cầu" in _q or "quy định" in _q)
        )
        if is_teaching_org_query:
            documents = _inject_articles(
                "yêu cầu tổ chức giảng dạy học tập phát huy năng lực thanh tra giám sát",
                {"$in": ["8"]},
                "Teaching-org query"
            )

        # Case 7: "trực tuyến" / "online" → inject Điều 8 khoản 2 from Quy chế
        is_online_learning_query = (
            ("trực tuyến" in _q or "online" in _q) and
            ("dạy" in _q or "học" in _q or "giảng" in _q)
        )
        if is_online_learning_query:
            documents = _inject_articles(
                "dạy học trực tuyến phương thức trực tuyến 30% khối lượng",
                {"$in": ["8"]},
                "Online-learning query"
            )
        # ────────────────────────────────────────────────────────────────────────

        # ── Person name lookup injection ─────────────────────────────────────────
        # Khi query là "X là ai" / "X là gì" → tìm trực tiếp tên bằng BM25 keyword
        import re as _re2
        person_match = _re2.match(
            r'^(?:thầy|cô|ts\.|pgs\.|gs\.|ths\.)?\s*(.+?)\s+là\s+(?:ai|gì)\s*\??$',
            _q.strip(), _re2.IGNORECASE
        )
        if not person_match:
            # Also match: "X là ai" without prefix
            person_match = _re2.match(
                r'^(.+?)\s+là\s+(?:ai|gì)\s*\??$',
                _q.strip(), _re2.IGNORECASE
            )
        
        if person_match:
            person_name = person_match.group(1).strip()
            # Remove common prefixes
            for prefix in ["thầy ", "cô ", "ts. ", "pgs. ", "gs. ", "ths. "]:
                if person_name.lower().startswith(prefix):
                    person_name = person_name[len(prefix):].strip()
                    break
            
            if len(person_name) >= 3:  # Tên ít nhất 3 ký tự
                print(f"[Retrieval] Person lookup detected: '{person_name}'")
                try:
                    # BM25 keyword search for exact person name
                    if self.vector_store.bm25_retriever:
                        self.vector_store.bm25_retriever.k = 6
                        bm25_results = self.vector_store.bm25_retriever.invoke(person_name)
                        # Filter to only docs containing the person's name
                        name_docs = [d for d in bm25_results 
                                     if person_name.lower() in d.page_content.lower()]
                        if name_docs:
                            existing_hashes = {hash(d.page_content) for d in documents}
                            new_docs = [d for d in name_docs if hash(d.page_content) not in existing_hashes]
                            if new_docs:
                                print(f"[Retrieval] Person injection: found {len(new_docs)} new chunks containing '{person_name}'")
                                documents = new_docs + documents
                            else:
                                print(f"[Retrieval] Person injection: name already in existing results")
                        else:
                            print(f"[Retrieval] Person injection: BM25 found no match for '{person_name}'")
                    
                    # Also try vector search with the name directly
                    name_vector_results = self.vector_store.vectorstore.similarity_search(
                        f"{person_name} giảng viên điều phối chương trình cố vấn học tập SEEE",
                        k=4
                    )
                    name_vector_docs = [d for d in name_vector_results 
                                        if person_name.lower() in d.page_content.lower()]
                    if name_vector_docs:
                        existing_hashes = {hash(d.page_content) for d in documents}
                        new_docs = [d for d in name_vector_docs if hash(d.page_content) not in existing_hashes]
                        if new_docs:
                            print(f"[Retrieval] Person vector injection: added {len(new_docs)} chunks")
                            documents = new_docs + documents
                except Exception as _pe:
                    print(f"[Retrieval] Person injection failed: {_pe}")
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
        reranked_docs = self.reranker.rerank(question, documents, top_k=5)
        
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
