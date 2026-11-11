"""Compares two simulators (e.g. Gemini in runs/ and Opus in runs/sim-opus/) on the same frozen runs: item-level
agreement per pass, and simulator accuracy split by whether the model's own post-edit decision is correct, which is
where a simulator that just solves the edited case stops tracking the model.
Usage: python3 compare_sims.py --data data/v1.jsonl --bank data/v1.bank.jsonl --sims runs runs/sim-opus
    --labels gemini opus --runs account-e2-s0 account-e2-s1 ...
"""
import argparse
import re
from collections import defaultdict

from evaluate import bank_recs, boot, failed, load, norm_dec, votes

PASSES = {"simulate": "acct", "simulate_shuf": "shuf", "simulate_noacc": "noacc"}


def preds(path):
    """Returns {bank id: predicted decision or None}, read the way evaluate.py reads simulator rows."""
    out = {}
    for r in load(path):
        o = "" if failed(r) else r.get("output") or ""
        pm = re.search(r"predicted\s+decision[^:\n]*:\s*(.*)", o, re.I)
        ids = [x.strip("*`. ") for x in re.findall(r"edit\s*id\s*[:\-]\s*(\S+)", o, re.I)]
        out[r["id"]] = norm_dec(pm[1]) if pm and ids[-1:] == [r["id"]] else None
    return out


def main():
    """Prints agreement and split accuracy tables, pooled over the seeds of each condition with family CIs."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--sims", nargs=2, required=True, help="2 dirs holding <run>.simulate*.jsonl")
    ap.add_argument("--labels", nargs=2, required=True)
    ap.add_argument("--runs", nargs="+", required=True, help="run stems; seeds of one condition pool by -sN")
    a = ap.parse_args()
    recs = {r["id"]: r for r in load(a.data)}
    bank = load(a.bank)
    recs |= bank_recs(bank, recs)
    fam = {b["bank_id"]: recs[b["case_id"]].get("template_family") or recs[b["case_id"]]["policy_id"] for b in bank
            if b["case_id"] in recs}
    orc = {b["bank_id"]: b["oracle"] for b in bank}
    agree, acc = defaultdict(lambda: ([], [])), defaultdict(lambda: ([], []))
    for run in a.runs:
        cond = re.sub(r"-s\d+$", "", run)
        _, maj = votes(load(f"{a.sims[0]}/{run}.jsonl"))
        fresh = {b["bank_id"]: maj.get(b["edited_id"]) for b in bank}
        P = {(lb, k): preds(f"{d}/{run}.{k}.jsonl") for d, lb in zip(a.sims, a.labels) for k in PASSES}
        for k, ps in PASSES.items():
            pa, pb = P[(a.labels[0], k)], P[(a.labels[1], k)]
            for i in sorted(set(pa) & set(pb)):
                v, c = agree[(cond, ps)]
                v.append(float(pa[i] == pb[i]))
                c.append(fam[i])
            for lb in a.labels:
                for i, p in P[(lb, k)].items():
                    if fresh.get(i) is None:
                        continue
                    sub = "post-edit correct" if fresh[i] == orc[i] else "post-edit wrong"
                    for s in ("all", sub):
                        v, c = acc[(cond, lb, ps, s)]
                        v.append(float(p == fresh[i]))
                        c.append(fam[i])
                    if sub == "post-edit wrong":
                        v, c = acc[(cond, lb, ps, "wrong: predicts engine label")]
                        v.append(float(p == orc[i]))
                        c.append(fam[i])
    fmt = lambda b: f"{b['mean']:.3f} [{b['lo']:.3f}, {b['hi']:.3f}] n={b['n']}" if b["n"] else "n=0"
    print(f"| condition | pass | {a.labels[0]} = {a.labels[1]} |\n|---|---|---|")
    for (cond, ps), (v, c) in sorted(agree.items()):
        print(f"| {cond} | {ps} | {fmt(boot(v, c))} |")
    print(f"\n| condition | subset | pass | {' | '.join(a.labels)} |\n|---|---|---|---|---|")
    keys = sorted({(cond, s, ps) for cond, _, ps, s in acc})
    for cond, s, ps in keys:
        print(f"| {cond} | {s} | {ps} | " + " | ".join(fmt(boot(*acc[(cond, lb, ps, s)])) if (cond, lb, ps, s) in acc
                else "" for lb in a.labels) + " |")


if __name__ == "__main__":
    main()
