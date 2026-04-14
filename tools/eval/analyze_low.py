import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('tools/eval/ragas_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

samples = data['per_sample']
samples_sorted = sorted(samples, key=lambda x: x.get('answer_correctness', 1))

print('=== TOP 10 LOWEST Answer Correctness ===\n')
for s in samples_sorted[:10]:
    sid = s.get('_id', '?')
    grp = s.get('_group', '?')
    ac = s.get('answer_correctness', 0)
    faith = s.get('faithfulness', 0)
    ar = s.get('answer_relevancy', 0)
    q = s.get('user_input', '')[:80]
    a = s.get('response', '')[:150]
    ref = s.get('reference', '')[:150]
    print(f"[{sid}] {grp} | AC={ac:.4f} | Faith={faith:.2f} | AR={ar:.4f}")
    print(f"  Q: {q}")
    print(f"  A: {a}...")
    print(f"  Ref: {ref}...")
    print()
