import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('tools/eval/ragas_results.json', encoding='utf-8'))
targets = ['G7-001', 'G1-002', 'G1-010', 'G2-002', 'G1-004']

for s in d['per_sample']:
    if s['_id'] in targets:
        ac = s.get('answer_correctness') or 0
        print(f"[{s['_id']}] AC={ac:.3f}")
        print(f"  Q  : {s['user_input']}")
        print(f"  Bot: {(s.get('response') or '')[:300]}")
        print(f"  GT : {s.get('reference','')[:200]}")
        print()
