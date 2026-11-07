"""Measures the intra-cluster correlation (ICC) of the v1 reference run and redoes the power statement from it.

Scores <run>.jsonl with its companions through evaluate.score, keeps the primary population (slice
unseen_family_train_vocab, view prose) and estimates the one-way ANOVA ICC by template_family for 3 unit
metrics: per-item decision correctness (acc_class units, every non-intervention item), per-bank-item simulator
correctness with the case's own account (sim_acct) and the per-bank-item own-minus-shuffled difference (sim_delta,
only where both passes exist). Each ICC is then applied to the v1 primary-slice design: the families and items per
family of the full data file (prose items for acc, bank items for the sim metrics). The design effect uses unequal
cluster sizes, DE = 1 + (m(1 + CV^2) - 1) * ICC with ICC floored at 0. From the effective n it reports the 95%
half-width of a paired accuracy difference at 20% discordance and a true difference near 0 (variance 0.20), and the
minimum detectable paired dSim difference at 80% power, taking Var(dSim_A - dSim_B) = 2 * Var(sim_delta unit)
(independent item noise across the 2 conditions, which is conservative). The ICC also gets a 95% percentile interval
from resampling families with replacement. Prints one markdown table.

Usage:
  python scripts/power.py runs/v1-lite.jsonl --data data/v1.jsonl runs/v1-lite.edits.jsonl --bank data/v1.bank.jsonl
"""
import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import evaluate  # noqa: E402

SL, VW, Z95, Z80, DISC = "unseen_family_train_vocab", "prose", 1.959964, 0.841621, 0.20


def icc(vals, clus):
    """
    Returns (ICC, k clusters, n units) from the one-way ANOVA estimator with unequal cluster sizes:
    (MSB - MSW) / (MSB + (n0 - 1) * MSW), n0 = (N - sum n_i^2 / N) / (k - 1).
    """
    g = defaultdict(list)
    for v, c in zip(vals, clus):
        g[c].append(v)
    ys, k, N = [np.asarray(x, float) for x in g.values()], len(g), len(vals)
    mu, ns = np.mean(vals), np.array([len(y) for y in ys])
    msb = sum(len(y) * (y.mean() - mu) ** 2 for y in ys) / (k - 1)
    msw = sum(((y - y.mean()) ** 2).sum() for y in ys) / (N - k)
    n0 = (N - (ns ** 2).sum() / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw), k, N


def main():
    """
    Parses the CLI, scores the run, estimates each ICC, applies it to the v1 primary design and prints the table.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--data", nargs="+", required=True, help="data file first, then any rendered edits")
    ap.add_argument("--bank", required=True)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rp, data = Path(a.run), evaluate.load(a.data[0])
    recs = {r["id"]: r for p in a.data for r in evaluate.load(p)}
    bank = evaluate.load(a.bank)
    recs |= evaluate.bank_recs(bank, recs)
    aux = {k: evaluate.load(cp) for k in evaluate.COMPANIONS if (cp := rp.with_name(f"{rp.stem}.{k}.jsonl")).exists()}
    U = evaluate.score(recs, evaluate.load(rp), aux, bank)[0]
    prim = lambda us: [u for u in us if u[2] == SL and u[3] == VW]
    fam = {r["id"]: r["template_family"] for r in data}
    sz = {"prose items": Counter(r["template_family"] for r in data if r.get("slice") == SL and r.get("view") == VW
            and not r.get("intervention")),
            "bank items": Counter(fam[b["case_id"]] for b in bank if b["slice"] == SL and b["view"] == VW)}
    us = {"decision correct (acc_class)": ([u for m, x in U.items() if m.startswith("acc_class[") for u in prim(x)],
            "prose items"),
            "sim correct, own account (sim_acct)": (prim(U["sim_acct"]), "bank items"),
            "sim own - shuf (sim_delta)": (prim(U["sim_delta"]), "bank items")}
    var_d = 2 * np.var([u[0] for u in us["sim own - shuf (sim_delta)"][0]], ddof=1)
    print(f"run={rp.stem} population=slice={SL} view={VW}; Var(dSim_A - dSim_B) = 2 * Var(sim_delta) = {var_d:.3f}\n")
    print("| metric | units / families (run) | mean | ICC [95% cluster boot] | design | m | CV | DE | n_eff | "
            "acc CI half-width (20% disc.) | MDE dSim (80%) |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for name, (uu, kind) in us.items():
        rho, k, N = icc([u[0] for u in uu], [u[1] for u in uu])
        byc = defaultdict(list)
        for u in uu:
            byc[u[1]].append(u[0])
        cs = list(byc.values())
        bs = [icc([v for c in d for v in cs[c]], [j for j, c in enumerate(d) for _ in cs[c]])[0]
                for d in rng.integers(0, k, (a.boot, k))]
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        ns = np.array(list(sz[kind].values()), float)
        m, cv = ns.mean(), ns.std() / ns.mean()
        de = 1 + (m * (1 + cv ** 2) - 1) * max(rho, 0)
        ne = ns.sum() / de
        print(f"| {name} | {N} / {k} | {np.mean([u[0] for u in uu]):.3f} | {rho:.3f} [{lo:.3f}, {hi:.3f}] | "
                f"{len(ns)} fam x {int(ns.sum())} {kind} | {m:.1f} | {cv:.2f} | {de:.2f} | {ne:.0f} | "
                f"{100 * Z95 * np.sqrt(DISC / ne):.1f} pts | {100 * (Z95 + Z80) * np.sqrt(var_d / ne):.1f} pts |")


if __name__ == "__main__":
    main()
