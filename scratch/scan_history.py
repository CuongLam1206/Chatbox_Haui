import os
import json

history_dir = r"e:\chatbot_Haui\agentic_chatbot\tools\eval\results_history"
files = [f for f in os.listdir(history_dir) if f.endswith(".json")]

print(f"{'Filename':<35} | {'Faithfulness':<12} | {'Recall':<12}")
print("-" * 65)

for f in files:
    try:
        with open(os.path.join(history_dir, f), "r", encoding="utf-8") as jf:
            data = json.load(jf)
            scores = data.get("aggregate_scores", {})
            faith = scores.get("faithfulness", 0)
            recall = scores.get("context_recall", 0)
            print(f"{f:<35} | {faith:<12} | {recall:<12}")
    except:
        pass
