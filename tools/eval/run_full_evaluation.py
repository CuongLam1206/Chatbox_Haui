"""
tools/eval/run_full_evaluation.py
Script chạy đánh giá chính thức cho paper NCKH:
- 3 lần evaluation + LLM Judge compute_metrics
- 1 lần ablation study
- Tổng hợp kết quả trung bình 3 lần

Cách dùng:
    python -m tools.eval.run_full_evaluation
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from tools.eval.run_evaluation import run_evaluation
from tools.eval.compute_metrics import compute_metrics
from tools.eval.ablation_study import run_ablation


def run_full_evaluation(num_runs: int = 3):
    """Chạy đánh giá chính thức: N lần eval + ablation."""
    
    test_set = "tools/eval/test_set.json"
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    all_summaries = []
    
    print("=" * 70)
    print("🏆 ĐÁNH GIÁ CHÍNH THỨC CHO PAPER NCKH")
    print(f"   {num_runs} lần evaluation + 1 lần ablation study")
    print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHẦN 1: Chạy N lần evaluation + compute_metrics (LLM Judge)
    # ═══════════════════════════════════════════════════════════════════════
    for run_idx in range(1, num_runs + 1):
        print(f"\n{'='*70}")
        print(f"📊 LẦN CHẠY {run_idx}/{num_runs}")
        print(f"{'='*70}")
        
        results_path = f"tools/eval/results_run{run_idx}.json"
        metrics_path = f"tools/eval/results_run{run_idx}_metrics.json"
        
        # Bước 1: Run evaluation
        print(f"\n🔹 Bước 1/{2}: Chạy evaluation...")
        run_evaluation(test_set, results_path)
        
        # Bước 2: Compute metrics WITH LLM Judge (không dùng --no-llm)
        print(f"\n🔹 Bước 2/{2}: Compute metrics (LLM Judge)...")
        summary = compute_metrics(results_path, metrics_path, use_llm=True)
        all_summaries.append(summary["summary"])
        
        # Copy kết quả vào docs
        import shutil
        shutil.copy2(metrics_path, docs_dir / f"results_run{run_idx}_metrics.json")
        
        print(f"\n✅ Lần {run_idx} hoàn thành!")
        print(f"   Accuracy: {summary['summary']['accuracy']:.1%}")
        print(f"   Faithfulness: {summary['summary']['avg_faithfulness']:.2f}")
        print(f"   Source Hit: {summary['summary']['source_hit_rate']:.1%}")
        print(f"   Latency: {summary['summary']['avg_latency_sec']:.2f}s")
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHẦN 2: Tổng hợp trung bình 3 lần
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"📈 TỔNG HỢP KẾT QUẢ TRUNG BÌNH {num_runs} LẦN")
    print(f"{'='*70}")
    
    avg_summary = {}
    for key in all_summaries[0]:
        values = [s[key] for s in all_summaries]
        avg_summary[key] = {
            "mean": round(sum(values) / len(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "runs": [round(v, 4) for v in values],
        }
    
    print(f"\n  {'Metric':<25} {'Mean':>8} {'Min':>8} {'Max':>8}")
    print("  " + "-" * 55)
    for key, stats in avg_summary.items():
        if "rate" in key or "accuracy" in key:
            print(f"  {key:<25} {stats['mean']:>7.1%} {stats['min']:>7.1%} {stats['max']:>7.1%}")
        elif "latency" in key:
            print(f"  {key:<25} {stats['mean']:>7.2f}s {stats['min']:>7.2f}s {stats['max']:>7.2f}s")
        else:
            print(f"  {key:<25} {stats['mean']:>8.4f} {stats['min']:>8.4f} {stats['max']:>8.4f}")
    
    # Save trung bình
    avg_output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_runs": num_runs,
            "description": f"Kết quả trung bình {num_runs} lần chạy — đánh giá bằng LLM Judge (Gemini 2.0 Flash)",
        },
        "average": avg_summary,
        "per_run": all_summaries,
    }
    avg_path = docs_dir / "evaluation_average.json"
    avg_path.write_text(json.dumps(avg_output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Kết quả trung bình saved: {avg_path}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHẦN 3: Ablation Study (1 lần)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print("🔬 ABLATION STUDY (B0 vs B1 vs B3)")
    print(f"{'='*70}")
    
    ablation_path = "tools/eval/ablation_results.json"
    run_ablation(test_set, ablation_path)
    
    import shutil
    shutil.copy2(ablation_path, docs_dir / "ablation_results.json")
    
    # ═══════════════════════════════════════════════════════════════════════
    # KẾT THÚC
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print("🏆 HOÀN THÀNH ĐÁNH GIÁ CHÍNH THỨC")
    print(f"{'='*70}")
    print(f"\nKết quả đã copy vào docs/:")
    for f in sorted(docs_dir.glob("*.json")):
        print(f"  📄 {f.name}")
    print(f"\n📊 Accuracy trung bình: {avg_summary['accuracy']['mean']:.1%}")
    print(f"📊 Faithfulness trung bình: {avg_summary['avg_faithfulness']['mean']:.4f}")
    print(f"⏱️  Latency trung bình: {avg_summary['avg_latency_sec']['mean']:.2f}s")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chạy đánh giá chính thức cho paper NCKH")
    parser.add_argument("--runs", type=int, default=3, help="Số lần chạy eval (mặc định 3)")
    args = parser.parse_args()
    
    run_full_evaluation(num_runs=args.runs)
