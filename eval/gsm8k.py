"""Score Lilavati on the GSM8K test set, end to end: the model writes programs, they run in the sandbox, and the
returned number is compared with the reference answer.

    python eval/gsm8k.py                          # one greedy try per problem (the 54.7% setting), all 1,319 problems
    python eval/gsm8k.py --tries 48               # 48 tries at temperature 0.7 + checker-weighted vote (the 72.3% setting)
    python eval/gsm8k.py --limit 300 --out r.jsonl

Needs `pip install datasets` for the test set. --tries 48 is slow on a CPU (48 programs per problem); use a GPU.
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lilavati import Lilavati


def gold(answer_text):
    return float(answer_text.split("####")[-1].strip().replace(",", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="udgamlabs/Lilavati")
    ap.add_argument("--checker", default="udgamlabs/Lilavati-Checker")
    ap.add_argument("--tries", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="score only this many problems (0 = all)")
    ap.add_argument("--device", default=None, help="cuda, mps or cpu (default: the fastest available)")
    ap.add_argument("--out", default=None, help="write one JSON line per problem")
    a = ap.parse_args()

    from datasets import load_dataset
    rows = list(load_dataset("openai/gsm8k", "main", split="test"))[a.start:]
    if a.limit:
        rows = rows[:a.limit]
    lv = Lilavati(a.model, a.checker if a.tries > 1 else None, device=a.device)
    out = open(a.out, "w") if a.out else None
    right, t0 = 0, time.time()
    for i, r in enumerate(rows, start=1):
        res = lv.solve(r["question"], tries=a.tries, temperature=a.temperature)
        g = gold(r["answer"])
        ok = res["answer"] is not None and abs(float(res["answer"]) - g) < 1e-4
        right += ok
        if out:
            out.write(json.dumps(dict(idx=a.start + i - 1, gold=g, answer=res["answer"], correct=ok, program=res["program"])) + "\n")
        if i % 25 == 0 or i == len(rows):
            print(f"[{i}/{len(rows)}] accuracy {100 * right / i:.2f}%  ({time.time() - t0:.0f} s)", flush=True)
    print(f"GSM8K test, problems {a.start}..{a.start + len(rows) - 1}, tries={a.tries}: {right}/{len(rows)} = {100 * right / len(rows):.2f}%")


if __name__ == "__main__":
    main()
