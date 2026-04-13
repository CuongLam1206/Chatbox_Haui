# -*- coding: utf-8 -*-
"""
tools/eval/ragas_evaluation.py
Đánh giá hệ thống Agentic RAG Chatbot bằng framework RAGAS.

Metrics:
  - Faithfulness: Câu trả lời có bám sát context không
  - Answer Relevancy: Câu trả lời có trả đúng câu hỏi không  
  - Context Precision: Document liên quan có được xếp hạng cao không
  - Context Recall: Hệ thống có truy xuất đủ thông tin cần thiết không
  - Answer Correctness: Câu trả lời có đúng so với ground truth không

Cách dùng:
    pip install ragas datasets langchain-google-genai
    python -m tools.eval.ragas_evaluation
    python -m tools.eval.ragas_evaluation --max 5     # test nhanh 5 câu
"""
import sys
import io
import json
import time
import argparse
import traceback
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Fix UnicodeEncodeError and SSL Transport Error on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))


def collect_rag_data(test_cases: List[Dict], max_cases: int = None) -> List[Dict]:
    """
    Chạy chatbot trên test set và thu thập đầy đủ dữ liệu cho RAGAS:
    - user_input (question)
    - response (predicted answer)
    - retrieved_contexts (list of chunk contents)
    - reference (ground truth answer)
    """
    from core.initialize import initialize_system
    import core.config as _cfg

    # Force temperature=0 during evaluation for reproducible results
    _cfg.TEMPERATURE = 0.0
    print("⚙️  Initializing chatbot system (temperature=0 for eval)...")
    workflow, _, _ = initialize_system()

    if max_cases:
        test_cases = test_cases[:max_cases]

    ragas_data = []

    for i, case in enumerate(test_cases, 1):
        question = case["question"]
        print(f"\n[{i}/{len(test_cases)}] {case['id']}: {question[:60]}...")

        try:
            t0 = time.time()

            # --- Chạy từng bước của workflow để lấy cả documents ---
            from src.agents.router import QueryRouter
            history = []

            # Initialize state
            state = {
                "question": question,
                "chat_history": history,
                "documents": [],
                "generation": "",
                "sources": [],
                "relevance_score": 0.0,
                "is_grounded": True,
                "retry_count": 0,
            }

            # Route
            route = workflow.router.route(question, history)

            # Chỉ đánh giá các query đi qua RAG pipeline
            if route not in ("vectorstore", "document_generation"):
                print(f"   ⏩ Skipped (route={route})")
                continue

            if route == "document_generation":
                state["is_document_query"] = True

            # Retrieve
            state = workflow.retrieve(state)
            retrieved_docs = state["documents"]

            # Grade + Rerank (nếu không phải document query)
            is_doc_query = state.get("is_document_query", False)
            if not is_doc_query and retrieved_docs:
                state = workflow.grade_documents(state)
                state = workflow.rerank_documents(state)

            # Generate
            state = workflow.generate_answer(state)

            latency = round(time.time() - t0, 2)

            # Thu thập dữ liệu cho RAGAS
            contexts = [
                doc.page_content if hasattr(doc, "page_content") else str(doc)
                for doc in state["documents"]
            ]

            # Strip HTML tags from response for RAGAS evaluation
            import re as _re
            raw_response = state["generation"]
            clean_response = _re.sub(r'<[^>]+>', '', raw_response)  # remove HTML tags
            clean_response = _re.sub(r'\n{3,}', '\n\n', clean_response).strip()

            entry = {
                "user_input": question,
                "response": clean_response,
                "retrieved_contexts": contexts,
                "reference": case["ground_truth"],
                # Metadata phụ (không phải RAGAS columns)
                "_id": case["id"],
                "_group": case["group"],
                "_difficulty": case.get("difficulty", "unknown"),
                "_latency_sec": latency,
                "_route": route,
                "_num_contexts": len(contexts),
            }
            ragas_data.append(entry)
            print(f"   ✓ [{latency}s] contexts={len(contexts)} | {clean_response[:80]}...")

        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

    return ragas_data


def run_ragas_evaluation(ragas_data: List[Dict], output_path: str):
    """
    Chạy RAGAS evaluation trên dữ liệu đã thu thập.
    Sử dụng Gemini làm LLM Judge.
    """
    import os
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        Faithfulness,
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        AnswerCorrectness,
    )

    # Setup Gemini as evaluator LLM
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    from core.config import GEMINI_API_KEY, GEMINI_MODEL
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    evaluator_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0,
        )
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GEMINI_API_KEY,
        )
    )

    # Chuẩn bị dataset cho RAGAS
    eval_dataset = Dataset.from_list([
        {
            "user_input": d["user_input"],
            "response": d["response"],
            "retrieved_contexts": d["retrieved_contexts"],
            "reference": d["reference"],
        }
        for d in ragas_data
    ])

    print(f"\n{'='*60}")
    print(f"🔬 RAGAS EVALUATION — {len(ragas_data)} samples")
    print(f"{'='*60}")

    # Khởi tạo metrics
    metrics = [
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
        ContextRecall(),
        AnswerCorrectness(),
    ]

    # Chạy evaluation
    print("\n⏳ Running RAGAS evaluation (this may take a few minutes)...")
    t0 = time.time()

    results = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        batch_size=4,          # smaller batches → fewer rate limit errors
        raise_exceptions=False, # NaN instead of crash on individual failures
    )

    eval_time = round(time.time() - t0, 1)

    # Trích xuất aggregate scores từ EvaluationResult
    # RAGAS mới dùng attribute hoặc _repr_dict thay vì .items()
    try:
        scores_dict = dict(results)  # thử convert trực tiếp
    except Exception:
        try:
            scores_dict = results._repr_dict  # fallback nội bộ
        except Exception:
            scores_dict = {}

    # In kết quả tổng quan
    print(f"\n{'='*60}")
    print(f"📊 RAGAS RESULTS (evaluated in {eval_time}s)")
    print(f"{'='*60}")
    for metric_name, score in scores_dict.items():
        if isinstance(score, (int, float)):
            print(f"  {metric_name:30s}: {score:.4f}")

    # Lấy kết quả chi tiết từng câu
    df = results.to_pandas()

    # Gộp metadata vào kết quả
    per_sample = []
    for i, row in df.iterrows():
        sample_result = row.to_dict()
        # Thêm metadata
        if i < len(ragas_data):
            sample_result["_id"] = ragas_data[i]["_id"]
            sample_result["_group"] = ragas_data[i]["_group"]
            sample_result["_difficulty"] = ragas_data[i]["_difficulty"]
            sample_result["_latency_sec"] = ragas_data[i]["_latency_sec"]
            sample_result["_route"] = ragas_data[i]["_route"]

        # Convert numpy types to native Python
        for k, v in sample_result.items():
            if hasattr(v, "item"):
                sample_result[k] = v.item()
            elif isinstance(v, list):
                sample_result[k] = [
                    x.item() if hasattr(x, "item") else x for x in v
                ]

        per_sample.append(sample_result)

    # Tổng hợp output
    output = {
        "metadata": {
            "framework": "RAGAS",
            "timestamp": datetime.now().isoformat(),
            "total_samples": len(ragas_data),
            "evaluation_time_sec": eval_time,
            "evaluator_llm": GEMINI_MODEL,
        },
        "aggregate_scores": {
            k: round(v, 4) if isinstance(v, (int, float)) else v
            for k, v in scores_dict.items()
        },
        "per_sample": per_sample,
    }

    # Lưu kết quả (latest)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # Lưu bản timestamped vào results_history/ để so sánh thực nghiệm
    history_dir = Path(output_path).parent / "results_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_path = history_dir / f"ragas_{ts}.json"
    history_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"\n📄 Full results saved to: {output_path}")
    print(f"📁 History saved to: {history_path}")

    # Phân tích theo nhóm
    print(f"\n{'='*60}")
    print("📊 BREAKDOWN BY GROUP")
    print(f"{'='*60}")
    from collections import defaultdict

    groups = defaultdict(list)
    for s in per_sample:
        groups[s.get("_group", "unknown")].append(s)

    for group_name, samples in sorted(groups.items()):
        fc_scores = [s.get("faithfulness", 0) for s in samples if s.get("faithfulness") is not None]
        ar_scores = [s.get("answer_relevancy", 0) for s in samples if s.get("answer_relevancy") is not None]
        ac_scores = [s.get("answer_correctness", 0) for s in samples if s.get("answer_correctness") is not None]

        print(f"\n  {group_name} ({len(samples)} samples):")
        if fc_scores:
            print(f"    Faithfulness:       {sum(fc_scores)/len(fc_scores):.4f}")
        if ar_scores:
            print(f"    Answer Relevancy:   {sum(ar_scores)/len(ar_scores):.4f}")
        if ac_scores:
            print(f"    Answer Correctness: {sum(ac_scores)/len(ac_scores):.4f}")

    return output


def main():
    parser = argparse.ArgumentParser(description="RAGAS Evaluation for HaUI Chatbot")
    parser.add_argument("--test-set", default="tools/eval/test_set.json",
                        help="Path to test set JSON")
    parser.add_argument("--output", default="tools/eval/ragas_results.json",
                        help="Path to save RAGAS results")
    parser.add_argument("--max", type=int, default=None,
                        help="Max number of test cases (for quick testing)")
    parser.add_argument("--skip-collect", action="store_true",
                        help="Skip data collection, use existing ragas_raw.json")
    args = parser.parse_args()

    raw_data_path = "tools/eval/ragas_raw.json"

    if args.skip_collect and Path(raw_data_path).exists():
        print("📂 Loading cached RAG data from ragas_raw.json...")
        ragas_data = json.loads(Path(raw_data_path).read_text(encoding="utf-8"))
    else:
        # Bước 1: Thu thập dữ liệu từ chatbot
        print("=" * 60)
        print("🧪 STEP 1: Collecting RAG data from chatbot")
        print("=" * 60)
        test_cases = json.loads(Path(args.test_set).read_text(encoding="utf-8"))
        ragas_data = collect_rag_data(test_cases, max_cases=args.max)

        # Lưu raw data để có thể chạy lại RAGAS mà không cần chạy lại chatbot
        Path(raw_data_path).write_text(
            json.dumps(ragas_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n💾 Raw data saved to: {raw_data_path}")

    # Bước 2: Chạy RAGAS evaluation
    print(f"\n{'='*60}")
    print("🔬 STEP 2: Running RAGAS evaluation")
    print(f"{'='*60}")
    run_ragas_evaluation(ragas_data, args.output)


if __name__ == "__main__":
    main()
