import json
import sys
from pathlib import Path

"""
Lightweight eval harness.
Reads qa_eval.jsonl and computes substring hit-rate based on predicted answers provided via stdin (jsonl with id, answer).
Usage:
  python eval/run_eval.py predictions.jsonl
The predictions file should contain lines: {"id": "q1", "answer": "..."}.
"""


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main(pred_path: str):
    gold = {row["id"]: row for row in load_jsonl(Path("eval/qa_eval.jsonl"))}
    preds = {row["id"]: row for row in load_jsonl(Path(pred_path))}

    total = len(gold)
    hits = 0
    missing = []

    for qid, g in gold.items():
        p = preds.get(qid, {})
        ans = p.get("answer", "").lower()
        if g["expected_substring"].lower() in ans:
            hits += 1
        else:
            missing.append(qid)

    score = hits / total if total else 0
    print(f"hit_rate: {score:.2f} ({hits}/{total})")
    if missing:
        print("missed:", ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval/run_eval.py predictions.jsonl")
        sys.exit(1)
    main(sys.argv[1])

