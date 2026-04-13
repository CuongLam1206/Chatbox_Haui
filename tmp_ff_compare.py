import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load V5 (current)
with open('tools/eval/ragas_results.json', encoding='utf-8') as f:
    v5 = json.load(f)

# Load V4 (previous)
with open('tools/eval/results_history/ragas_20260409_151649.json', encoding='utf-8') as f:
    v4 = json.load(f)

print("=== FAITHFULNESS DROPS (V4 → V5) ===\n")

v4_map = {s['_id']: s for s in v4['per_sample']}
v5_map = {s['_id']: s for s in v5['per_sample']}

drops = []
for sid in v5_map:
    if sid in v4_map:
        ff4 = v4_map[sid].get('faithfulness', 0) or 0
        ff5 = v5_map[sid].get('faithfulness', 0) or 0
        if ff5 < ff4:
            drops.append({
                'id': sid,
                'group': v5_map[sid].get('_group'),
                'q': v5_map[sid].get('user_input'),
                'ff4': ff4,
                'ff5': ff5,
                'delta': ff5 - ff4,
                'bot': v5_map[sid].get('response', '')[:200]
            })

drops.sort(key=lambda x: x['delta'])
print(f"Found {len(drops)} samples with FF drop:\n")
for d in drops:
    print(f"[{d['id']}] {d['q']}")
    print(f"  FF: {d['ff4']:.4f} → {d['ff5']:.4f} (Δ = {d['delta']:+.4f})")
    print(f"  Bot: {d['bot'][:150]}...")
    print()
