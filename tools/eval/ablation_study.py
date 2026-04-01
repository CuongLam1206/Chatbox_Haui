"""
tools/eval/ablation_study.py
So sánh hiệu suất giữa các baseline: B0 (LLM thuần) → B3 (Agentic RAG hiện tại).

Cách dùng:
    python -m tools.eval.ablation_study
    python -m tools.eval.ablation_study --max 10
"""
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))


def run_b0_llm_only(question: str) -> dict:
    """B0: LLM thuần, không RAG."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        prompt = f"""Bạn là trợ lý sinh viên của Trường Đại học Công nghiệp Hà Nội (HaUI).
Hãy trả lời câu hỏi sau dựa trên kiến thức của bạn (không có tài liệu tham khảo):

{question}"""
        t0 = time.time()
        resp = model.invoke([HumanMessage(content=prompt)])
        return {"answer": resp.content.strip(), "sources": [], "latency": round(time.time() - t0, 2)}
    except Exception as e:
        return {"answer": f"[ERROR] {e}", "sources": [], "latency": 0}


def run_b1_naive_rag(question: str, retriever) -> dict:
    """B1: Naive RAG - vector search đơn, không grade/rerank."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        t0 = time.time()
        docs = retriever.invoke(question)[:3]  # Top-3 only
        context = "\n\n".join(d.page_content[:500] for d in docs)
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        prompt = f"Dựa vào ngữ cảnh sau, hãy trả lời câu hỏi:\n\nNgữ cảnh:\n{context}\n\nCâu hỏi: {question}\nTrả lời:"
        resp = model.invoke([HumanMessage(content=prompt)])
        sources = list({d.metadata.get('source', '') for d in docs})
        return {"answer": resp.content.strip(), "sources": sources, "latency": round(time.time() - t0, 2)}
    except Exception as e:
        return {"answer": f"[ERROR] {e}", "sources": [], "latency": 0}


def run_ablation(test_set_path: str, output_path: str, max_cases: int = None):
    """Chạy ablation study: B0, B1, B3 trên cùng test set."""
    print("=" * 60)
    print("🔬 HAUI CHATBOT ABLATION STUDY")
    print("=" * 60)

    test_cases = json.loads(Path(test_set_path).read_text(encoding="utf-8"))
    if max_cases:
        test_cases = test_cases[:max_cases]
    print(f"📋 Test cases: {len(test_cases)}")

    # Init systems
    print("\n⚙️  Initializing systems...")
    from core.initialize import initialize_system
    workflow_b3, _, _ = initialize_system()
    retriever = workflow_b3.retriever

    baselines = {
        "B0_LLM_only": [],
        "B1_NaiveRAG": [],
        "B3_AgenticRAG": [],
    }

    for i, case in enumerate(test_cases, 1):
        q = case["question"]
        gt = case["ground_truth"]
        print(f"\n[{i}/{len(test_cases)}] {case['id']}: {q[:55]}...")

        # B0
        b0 = run_b0_llm_only(q)
        baselines["B0_LLM_only"].append({"id": case["id"], "question": q, "ground_truth": gt, **b0})
        print(f"  B0 [{b0['latency']}s]: {b0['answer'][:60]}")

        # B1
        b1 = run_b1_naive_rag(q, retriever)
        baselines["B1_NaiveRAG"].append({"id": case["id"], "question": q, "ground_truth": gt, **b1})
        print(f"  B1 [{b1['latency']}s]: {b1['answer'][:60]}")

        # B3
        t0 = time.time()
        b3_result = workflow_b3.run(q, session_id="ablation_eval")
        b3_latency = round(time.time() - t0, 2)
        baselines["B3_AgenticRAG"].append({
            "id": case["id"], "question": q, "ground_truth": gt,
            "answer": b3_result.get("answer", ""),
            "sources": b3_result.get("sources", []),
            "latency": b3_latency
        })
        print(f"  B3 [{b3_latency}s]: {b3_result.get('answer','')[:60]}")

    # Save
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(test_cases),
        },
        "baselines": baselines
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # Quick latency summary
    print("\n" + "=" * 60)
    print("⏱️  Latency Summary:")
    for name, runs in baselines.items():
        avg_lat = sum(r["latency"] for r in runs) / len(runs) if runs else 0
        print(f"  {name:<20} avg={avg_lat:.2f}s")
    print(f"\n✅ Ablation results saved: {output_path}")
    print("➡️  Run compute_metrics.py on each baseline for full metrics.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-set", default="tools/eval/test_set.json")
    parser.add_argument("--output", default="tools/eval/ablation_results.json")
    parser.add_argument("--max", type=int, default=None)
    args = parser.parse_args()

    run_ablation(args.test_set, args.output, args.max)
