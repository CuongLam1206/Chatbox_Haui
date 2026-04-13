import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    with open('tools/eval/ragas_results.json', encoding='utf-8') as f:
        data = json.load(f)
        
    results = data.get('per_sample', [])
    all_samples = []
    
    for r in results:
        ac = r.get('answer_correctness', 0.0) or 0.0
        ff = r.get('faithfulness', 0.0) or 0.0
        ar = r.get('answer_relevancy', 0.0) or 0.0
        cp = r.get('context_precision', 0.0) or 0.0
        cr = r.get('context_recall', 0.0) or 0.0
        
        all_samples.append({
            'id': r.get('_id'),
            'group': r.get('_group'),
            'q': r.get('user_input'),
            'ac': ac,
            'ff': ff,
            'ar': ar,
            'cp': cp,
            'cr': cr,
            'bot': r.get('response', ''),
            'gt': r.get('reference', ''),
            'bad': ac < 0.7 or ff < 0.7
        })

    bad = [s for s in all_samples if s['bad']]
    bad.sort(key=lambda x: x['ac'])
    
    print(f"Total samples: {len(all_samples)}")
    print(f"Bad samples (AC<0.7 or FF<0.7): {len(bad)}")
    print(f"\n{'='*100}")
    
    for i, b in enumerate(bad):
        print(f"\n--- #{i+1} [{b['id']}] (Group: {b['group']}) ---")
        print(f"  Q : {b['q']}")
        print(f"  AC: {b['ac']:.4f} | FF: {b['ff']:.4f} | AR: {b['ar']:.4f} | CP: {b['cp']:.4f} | CR: {b['cr']:.4f}")
        print(f"  Bot: {b['bot'][:300]}")
        print(f"  GT : {b['gt'][:300]}")
        
        # Diagnosis
        if b['ff'] == 0.0 and b['ac'] > 0.5:
            print(f"  >> DIAGNOSIS: Bot answer seems correct but Faithfulness=0 => Context doesn't contain the info, bot may be hallucinating from pre-training")
        elif b['ff'] < 0.5 and 'không có thông tin' in b['bot'].lower():
            print(f"  >> DIAGNOSIS: Retriever FAILED - bot couldn't find relevant docs")
        elif b['ff'] == 1.0 and b['ac'] < 0.6:
            print(f"  >> DIAGNOSIS: Ground Truth mismatch - bot is faithful but GT format differs")
        elif b['ff'] < 0.7:
            print(f"  >> DIAGNOSIS: Possible hallucination or retrieval issue")

if __name__ == "__main__":
    main()
