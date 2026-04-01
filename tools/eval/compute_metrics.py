"""
tools/eval/compute_metrics.py
Tính toán metrics từ file results.json và in báo cáo.

Cách dùng:
    python -m tools.eval.compute_metrics
    python -m tools.eval.compute_metrics --results tools/eval/results.json
"""
import sys
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))


# ─── LLM Judge để tính Faithfulness & Correctness ───────────────────────────

def llm_judge_batch(cases: list[dict]) -> list[dict]:
    """
    Dùng Gemini để đánh giá từng cặp (question, ground_truth, predicted).
    Trả về list dict với is_correct và faithfulness (0.0 - 1.0).
    """
    try:
        import google.generativeai as genai
        from core.config import GEMINI_API_KEY
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        print(f"[LLM Judge] Không thể kết nối Gemini: {e}. Dùng rule-based fallback.")
        return _rule_based_judge(cases)

    results = []
    for case in cases:
        prompt = f"""Đánh giá chất lượng câu trả lời của chatbot.

Câu hỏi: {case['question']}
Đáp án chuẩn: {case['ground_truth']}
Câu trả lời chatbot: {case['predicted']}

Trả lời JSON với hai trường:
- "is_correct": true nếu câu trả lời đúng về mặt thực tế so với đáp án chuẩn, false nếu sai hoặc thiếu thông tin quan trọng
- "faithfulness": điểm 0.0-1.0 đánh giá câu trả lời có bịa thêm thông tin không có trong đáp án không (1.0 = không bịa, 0.0 = toàn bịa)
- "note": nhận xét ngắn (tiếng Việt)

Chỉ trả về JSON, không thêm gì khác."""
        try:
            resp = model.generate_content(prompt)
            text = resp.text.strip().strip("```json").strip("```").strip()
            data = json.loads(text)
            results.append({**case, **data})
        except Exception:
            results.append({**case, "is_correct": None, "faithfulness": None, "note": "parse_error"})

    return results


def _rule_based_judge(cases: list[dict]) -> list[dict]:
    """Fallback: đánh giá dựa trên keyword overlap đơn giản."""
    results = []
    for c in cases:
        gt_words = set(re.findall(r'\w+', c["ground_truth"].lower()))
        pred_words = set(re.findall(r'\w+', c["predicted"].lower()))
        overlap = len(gt_words & pred_words) / max(len(gt_words), 1)
        results.append({**c, "is_correct": overlap >= 0.4, "faithfulness": min(overlap * 1.5, 1.0), "note": f"keyword_overlap={overlap:.2f}"})
    return results


# ─── Source Hit Rate ──────────────────────────────────────────────────────────

def compute_source_hit(sources_returned: list[str], expected_source: str) -> bool:
    """Kiểm tra tài liệu đúng có trong top-k returned sources không."""
    if not expected_source or not sources_returned:
        return False
    exp_lower = expected_source.lower()
    for src in sources_returned:
        # Partial match: nếu expected là substring hoặc ngược lại
        if exp_lower in src.lower() or src.lower() in exp_lower:
            return True
        # Khớp từ khóa chính
        exp_keywords = set(re.findall(r'\w{4,}', exp_lower))
        src_keywords = set(re.findall(r'\w{4,}', src.lower()))
        if exp_keywords & src_keywords:
            return True
    return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def compute_metrics(results_path: str, output_path: str = None, use_llm: bool = True):
    """Tính tất cả metrics và in báo cáo."""
    data = json.loads(Path(results_path).read_text(encoding="utf-8"))
    results = data["results"]
    meta = data["metadata"]

    print(f"\n📊 Computing metrics for {len(results)} results...")

    # 1. Source Hit Rate
    for r in results:
        r["source_hit"] = compute_source_hit(r["sources_returned"], r["expected_source"])

    # 2. LLM / rule-based judge
    print("🤖 Running LLM judge (Faithfulness + Correctness)...")
    judged = llm_judge_batch(results) if use_llm else _rule_based_judge(results)
    for j, r in zip(judged, results):
        r["is_correct"] = j.get("is_correct")
        r["faithfulness"] = j.get("faithfulness")
        r["note"] = j.get("note", "")

    # 3. Aggregate metrics
    n = len(results)
    correct = [r for r in results if r["is_correct"] is True]
    hit = [r for r in results if r["source_hit"]]
    faith_scores = [r["faithfulness"] for r in results if r["faithfulness"] is not None]
    latencies = [r["latency_sec"] for r in results]

    accuracy = len(correct) / n
    source_hit_rate = len(hit) / n
    avg_faithfulness = sum(faith_scores) / len(faith_scores) if faith_scores else 0
    avg_latency = sum(latencies) / len(latencies)
    hallucination_rate = 1 - avg_faithfulness

    # 4. Per-group breakdown
    groups = defaultdict(list)
    for r in results:
        groups[r["group"]].append(r)

    print("\n" + "=" * 60)
    print("📈 EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Total cases        : {n}")
    print(f"  Accuracy           : {accuracy:.1%}  ({len(correct)}/{n})")
    print(f"  Source Hit Rate    : {source_hit_rate:.1%}  ({len(hit)}/{n})")
    print(f"  Avg Faithfulness   : {avg_faithfulness:.2f}")
    print(f"  Hallucination Rate : {hallucination_rate:.1%}")
    print(f"  Avg Latency        : {avg_latency:.2f}s")

    print("\n📦 Per-Group Breakdown:")
    print(f"  {'Group':<30} {'Acc':>6} {'Hit':>6} {'Cases':>6}")
    print("  " + "-" * 50)
    for g, g_results in sorted(groups.items()):
        g_correct = sum(1 for r in g_results if r["is_correct"])
        g_hit = sum(1 for r in g_results if r["source_hit"])
        print(f"  {g:<30} {g_correct/len(g_results):>5.0%} {g_hit/len(g_results):>5.0%} {len(g_results):>6}")

    # 5. Per-difficulty breakdown
    diffs = defaultdict(list)
    for r in results:
        diffs[r.get("difficulty", "unknown")].append(r)

    print("\n🎯 Per-Difficulty Breakdown:")
    for d, d_results in sorted(diffs.items()):
        d_correct = sum(1 for r in d_results if r["is_correct"])
        print(f"  {d:<10} Accuracy={d_correct/len(d_results):.0%}  ({len(d_results)} cases)")

    # 6. Failed cases
    failed = [r for r in results if not r["is_correct"]]
    if failed:
        print(f"\n❌ Failed cases ({len(failed)}):")
        for r in failed[:5]:
            print(f"  [{r['id']}] Q: {r['question'][:60]}")
            print(f"         GT: {r['ground_truth'][:60]}")
            print(f"         Pred: {r['predicted'][:60]}")

    # 7. Save enriched results
    out_path = output_path or results_path.replace(".json", "_metrics.json")
    summary = {
        "metadata": {**meta, "metrics_computed_at": __import__("datetime").datetime.now().isoformat()},
        "summary": {
            "accuracy": round(accuracy, 4),
            "source_hit_rate": round(source_hit_rate, 4),
            "avg_faithfulness": round(avg_faithfulness, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "avg_latency_sec": round(avg_latency, 2),
        },
        "per_group": {
            g: {
                "accuracy": round(sum(1 for r in gr if r["is_correct"]) / len(gr), 4),
                "source_hit_rate": round(sum(1 for r in gr if r["source_hit"]) / len(gr), 4),
                "n": len(gr)
            }
            for g, gr in groups.items()
        },
        "results": results,
    }
    Path(out_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Full metrics saved to: {out_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="tools/eval/results.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--no-llm", action="store_true", help="Dùng rule-based thay vì LLM judge")
    args = parser.parse_args()

    compute_metrics(args.results, args.output, use_llm=not args.no_llm)
