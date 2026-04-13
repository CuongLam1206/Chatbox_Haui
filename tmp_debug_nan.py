import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('tools/eval/ragas_results.json', encoding='utf-8'))

print("=== NaN / None samples ===")
for s in d['per_sample']:
    ac = s.get('answer_correctness')
    ff = s.get('faithfulness')
    if ac is None or ff is None:
        print(f"[{s['_id']}] AC={ac} | FF={ff}")
        print(f"  Q  : {s['user_input']}")
        print(f"  Bot: {(s.get('response') or 'EMPTY')[:300]}")
        print(f"  GT : {s.get('reference','')[:200]}")
        print(f"  Contexts: {len(s.get('retrieved_contexts',[]))} docs")
        print()

print("=== G13 samples ===")
for s in d['per_sample']:
    if 'G13' in s.get('_group', ''):
        ff = s.get('faithfulness') or 0
        cr = s.get('context_recall') or 0
        print(f"[{s['_id']}] FF={ff:.3f} CR={cr:.3f}")
        print(f"  Bot: {(s.get('response') or '')[:200]}")
        # Check if contexts contain 'Turnitin'
        ctxs = s.get('retrieved_contexts', [])
        has_turnitin = any('turnitin' in c.lower() for c in ctxs)
        print(f"  Contexts({len(ctxs)}): has_turnitin={has_turnitin}")
        print()

print("=== G12 samples ===")
for s in d['per_sample']:
    if 'G12' in s.get('_group', ''):
        ac = s.get('answer_correctness') or 0
        print(f"[{s['_id']}] AC={ac:.3f}")
        print(f"  Bot: {(s.get('response') or '')[:200]}")
        print(f"  GT : {s.get('reference','')[:200]}")
        print()
