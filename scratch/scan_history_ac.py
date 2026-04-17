import os
import json

history_dir = r"e:\chatbot_Haui\agentic_chatbot\tools\eval\results_history"
files = [f for f in os.listdir(history_dir) if f.endswith(".json")]

print(f"{'Filename':<35} | {'Faithfulness':<12} | {'AC (Correctness)':<15} | {'Recall':<10}")
print("-" * 80)

results = []
for f in files:
    try:
        with open(os.path.join(history_dir, f), "r", encoding="utf-8") as jf:
            data = json.load(jf)
            scores = data.get("aggregate_scores", {})
            faith = scores.get("faithfulness", 0)
            ac = scores.get("answer_correctness", 0)
            recall = scores.get("context_recall", 0)
            results.append((f, faith, ac, recall))
    except:
        pass

# Sắp xếp theo Answer Correctness giảm dần
results.sort(key=lambda x: x[2], reverse=True)

for r in results:
    print(f"{r[0]:<35} | {r[1]:<12.4f} | {r[2]:<15.4f} | {r[3]:<10.4f}")
