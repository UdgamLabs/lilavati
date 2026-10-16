"""Score Lilavati (one greedy try, code executed) on the robustness sets in the model card:
GSM-Plus testmini (the 7 answerable perturbation types), SVAMP (all 1,000), ASDiv (numeric answers) and GSM-Hard.

    python eval/robust.py --sets svamp asdiv            # any of: gsmplus svamp asdiv gsmhard
    python eval/robust.py --sets gsmplus --limit 200

Needs `pip install datasets` (for pyarrow and the downloads).
"""
import argparse, collections, json, os, re, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lilavati import Lilavati


def load(name):
    """[(question, gold answer as text, type)]"""
    from huggingface_hub import hf_hub_download
    dl = lambda repo, f: hf_hub_download(repo, f, repo_type="dataset")
    if name == "gsmplus":   # "critical thinking" items have no numeric answer, so the 7 answerable types are scored
        rows = map(json.loads, open(dl("qintongli/GSM-Plus", "data/testmini-00000-of-00001.jsonl")))
        return [(r["question"], str(r["answer"]).strip(), r["perturbation_type"]) for r in rows if r["perturbation_type"] != "critical thinking"]
    if name == "svamp":
        sv = json.load(open(dl("ChilleD/SVAMP", "train.json"))) + json.load(open(dl("ChilleD/SVAMP", "test.json")))
        return [(f"{r['Body'].strip()} {r['Question'].strip()}", str(r["Answer"]), r.get("Type", "")) for r in sv]
    if name == "asdiv":
        import pyarrow.parquet as pq
        out = []
        for r in pq.read_table(dl("EleutherAI/asdiv", "asdiv/validation-00000-of-00001.parquet")).to_pylist():
            m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(\(|$)", str(r["answer"]))
            if m:
                out.append((f"{r['body'].strip()} {r['question'].strip()}", m.group(1), r.get("solution_type", "")))
        return out
    if name == "gsmhard":
        return [(r["input"], str(r["target"]), "") for r in map(json.loads, open(dl("reasoning-machines/gsm-hard", "gsmhardv2.jsonl")))]
    raise ValueError(name)


def correct(v, gold):
    """Exact for whole-number golds; to the gold's precision otherwise (GSM-Plus golds are rounded, e.g. 4.33)."""
    if v is None or gold is None or str(gold).lower() == "none":
        return False
    try:
        g = float(str(gold).replace(",", ""))
    except ValueError:
        return False
    d = len(str(gold).split(".")[1].rstrip("0")) if "." in str(gold) else 0
    # whole numbers: exact; 1-3 decimals: to that precision; long decimals (GSM-Hard): relative 1e-6
    tol = 1e-4 if d == 0 else (0.5 * 10 ** -d + 1e-9 if d <= 3 else 1e-6 * max(1.0, abs(g)))
    return abs(float(v) - g) < tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="+", default=["gsmplus", "svamp", "asdiv", "gsmhard"])
    ap.add_argument("--model", default="UdgamLabs/Lilavati")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--device", default=None)
    a = ap.parse_args()
    lv = Lilavati(a.model, None, device=a.device)
    for name in a.sets:
        items = load(name)[:a.limit or None]
        right, by_type, t0 = 0, collections.defaultdict(lambda: [0, 0]), time.time()
        for q, g, typ in items:
            ok = correct(lv.solve(q, tries=1)["answer"], g)
            right += ok
            by_type[typ][0] += ok
            by_type[typ][1] += 1
        print(f"{name}: {right}/{len(items)} = {100 * right / len(items):.2f}%  ({time.time() - t0:.0f} s)")
        if name == "gsmplus":
            for typ, (r, n) in sorted(by_type.items()):
                print(f"   {typ:28s} {100 * r / n:5.1f}%  (n={n})")


if __name__ == "__main__":
    main()
