import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = json.loads(Path("tools/eval/ragas_results.json").read_text(encoding="utf-8"))
samples = data["per_sample"]

weak = [s for s in samples if s.get("answer_correctness", 1) < 0.5 or s.get("faithfulness", 1) < 0.9]
weak.sort(key=lambda x: x.get("answer_correctness", 0))

print(f"=== WEAK SAMPLES ({len(weak)} found) ===\n")
for s in weak:
    print(f"ID: {s['_id']} | Group: {s['_group']}")
    print(f"  Faith={s.get('faithfulness',0):.2f} | Rel={s.get('answer_relevancy',0):.2f} | Corr={s.get('answer_correctness',0):.2f}")
    print(f"  Q: {s['user_input'][:80]}")
    resp = s.get('response','').replace('\n',' ')[:150]
    ref = s.get('reference','').replace('\n',' ')[:150]
    print(f"  A: {resp}")
    print(f"  GT: {ref}")
    print()
