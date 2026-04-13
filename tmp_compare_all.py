import json, sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load all history files
history_dir = 'tools/eval/results_history'
files = sorted(glob.glob(os.path.join(history_dir, 'ragas_*.json')))

print(f"Found {len(files)} evaluation runs:\n")
print(f"{'Version':<8} {'Timestamp':<20} {'Faithfulness':>13} {'AR':>8} {'CP':>8} {'CR':>8} {'AC':>8}")
print("-" * 85)

all_runs = []
for i, f in enumerate(files):
    with open(f, encoding='utf-8') as fp:
        d = json.load(fp)
    
    ts = os.path.basename(f).replace('ragas_','').replace('.json','')
    metrics = d.get('metrics', d)
    ff = metrics.get('faithfulness', 0) or 0
    ar = metrics.get('answer_relevancy', 0) or 0  
    cp = metrics.get('context_precision', 0) or 0
    cr = metrics.get('context_recall', 0) or 0
    ac = metrics.get('answer_correctness', 0) or 0
    
    version = f"V{i+1}"
    all_runs.append({'version': version, 'ts': ts, 'ff': ff, 'ar': ar, 'cp': cp, 'cr': cr, 'ac': ac, 'data': d})
    print(f"{version:<8} {ts:<20} {ff:>13.4f} {ar:>8.4f} {cp:>8.4f} {cr:>8.4f} {ac:>8.4f}")

# Best values
print("\n" + "=" * 85)
best_ff = max(r['ff'] for r in all_runs)
best_ac = max(r['ac'] for r in all_runs)
print(f"Best Faithfulness: {best_ff:.4f}")
print(f"Best Answer Correctness: {best_ac:.4f}")

# Current vs best comparison
curr = all_runs[-1]
print(f"\nCurrent run ({curr['version']}): FF={curr['ff']:.4f}, AC={curr['ac']:.4f}")

# Per-sample analysis of latest run
print("\n" + "=" * 85)
print("BAD SAMPLES IN LATEST RUN (AC<0.7 or FF<0.7):")
print("=" * 85)

latest = all_runs[-1]['data']
samples = latest.get('per_sample', [])
bad = []
for s in samples:
    ac = s.get('answer_correctness') or 0
    ff = s.get('faithfulness') or 0
    if ac < 0.7 or ff < 0.7:
        bad.append(s)

bad.sort(key=lambda x: (x.get('answer_correctness') or 0))
print(f"\n{len(bad)} bad samples:\n")
for s in bad:
    ac = s.get('answer_correctness') or 0
    ff = s.get('faithfulness') or 0
    ar = s.get('answer_relevancy') or 0
    cr = s.get('context_recall') or 0
    print(f"[{s['_id']}] AC={ac:.4f} | FF={ff:.4f} | AR={ar:.4f} | CR={cr:.4f}")
    print(f"  Q: {s['user_input'][:80]}")
    print(f"  Bot: {(s.get('response',''))[:120]}")
    print()
