"""
tools/eval/run_evaluation.py
Chạy toàn bộ test set và ghi kết quả ra file JSON.

Cách dùng:
    python -m tools.eval.run_evaluation
    python -m tools.eval.run_evaluation --test-set tools/eval/test_set.json --output tools/eval/results.json
"""
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from core.initialize import initialize_system


def run_evaluation(test_set_path: str, output_path: str, max_cases: int = None):
    """
    Chạy evaluation trên toàn bộ test set.
    
    Args:
        test_set_path: Đường dẫn tới file test_set.json
        output_path: Đường dẫn ghi kết quả
        max_cases: Số câu hỏi tối đa (None = chạy hết)
    """
    print("=" * 60)
    print("🧪 HAUI CHATBOT EVALUATION")
    print("=" * 60)

    # Load test set
    test_cases = json.loads(Path(test_set_path).read_text(encoding="utf-8"))
    if max_cases:
        test_cases = test_cases[:max_cases]
    print(f"📋 Test cases: {len(test_cases)}")

    # Init chatbot system
    print("\n⚙️  Initializing chatbot system...")
    workflow, _, _ = initialize_system()

    results = []
    errors = []
    start_time = time.time()

    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {case['id']}: {case['question'][:60]}...")
        try:
            t0 = time.time()
            result = workflow.run(case["question"], session_id=f"eval_{case['id']}")
            latency = round(time.time() - t0, 2)

            entry = {
                "id": case["id"],
                "group": case["group"],
                "difficulty": case.get("difficulty", "unknown"),
                "type": case.get("type", "unknown"),
                "question": case["question"],
                "ground_truth": case["ground_truth"],
                "predicted": result.get("answer", ""),
                "sources_returned": result.get("sources", []),
                "expected_source": case.get("source_doc", ""),
                "relevance_score": result.get("relevance_score", 0.0),
                "latency_sec": latency,
                # To be filled by compute_metrics.py
                "is_correct": None,
                "source_hit": None,
                "faithfulness": None,
            }
            results.append(entry)
            print(f"   ✓  [{latency}s] {result.get('answer','')[:80]}...")

        except Exception as e:
            print(f"   ✗  ERROR: {e}")
            errors.append({"id": case["id"], "error": str(e)})

    total_time = round(time.time() - start_time, 1)

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "test_set": test_set_path,
            "total_cases": len(test_cases),
            "completed": len(results),
            "errors": len(errors),
            "total_time_sec": total_time,
            "avg_latency_sec": round(sum(r["latency_sec"] for r in results) / len(results), 2) if results else 0,
        },
        "results": results,
        "errors": errors,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"✅ Done! {len(results)}/{len(test_cases)} completed in {total_time}s")
    print(f"📄 Results saved to: {output_path}")
    print("=" * 60)
    print("\n➡️  Next step: python -m tools.eval.compute_metrics")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run chatbot evaluation")
    parser.add_argument("--test-set", default="tools/eval/test_set.json")
    parser.add_argument("--output", default="tools/eval/results.json")
    parser.add_argument("--max", type=int, default=None, help="Số câu tối đa (để test nhanh)")
    args = parser.parse_args()

    run_evaluation(args.test_set, args.output, args.max)
