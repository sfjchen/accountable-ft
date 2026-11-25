"""
Reads the registered real vs invented readout (DECISIONS, "Real vs invented for real-rule use") from evaluate.py JSON
files, 1 per held-out domain: each seed's score is the mean of the domains' rates for the arm's explanation run, and
R4 - M is a Welch t 95% CI over the 2 arms' per-seed scores, read as better, equivalent (CI within the margin) or
inconclusive, with the accuracy guardrail. It prints the same per domain, and every metric's per-seed values.
Usage: python arms.py <json>... [--arms rm-r4 rm-mix] [--margin 3] [--guard 5]
"""
import argparse
import json
import re
import statistics as st
from pathlib import Path

from scipy import stats

PRIMARY = "slice=unseen_family_train_vocab view=prose"
METRICS = {"joint": "joint success", "acc_maj": "accuracy", "expl_valid": "explanation correctness"}


def welch(x, y):
    """Returns (mean difference, lo, hi) of x - y in points with a Welch t 95% CI."""
    vx, vy = st.variance(x) / len(x), st.variance(y) / len(y)
    df = (vx + vy) ** 2 / (vx ** 2 / (len(x) - 1) + vy ** 2 / (len(y) - 1))
    d, h = st.mean(x) - st.mean(y), stats.t.ppf(0.975, df) * (vx + vy) ** 0.5
    return d, d - h, d + h


def main():
    """Collects per-seed rates by arm and domain, prints the per-seed table, the contrasts and the readout."""
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="+")
    ap.add_argument("--arms", nargs=2, default=["rm-r4", "rm-mix"], help="arm prefixes, the first minus the second")
    ap.add_argument("--margin", type=float, default=3.0, help="equivalence margin, points")
    ap.add_argument("--guard", type=float, default=5.0, help="largest accuracy loss the winner may not include")
    a = ap.parse_args()
    v, doms, commits = {}, [], set()
    for f in a.json:
        j = json.loads(Path(f).read_text())
        commits.add(j["commit"])
        dom = Path(f).name.split("-")[0]
        doms.append(dom)
        for c, g in j["conditions"].items():
            m = re.search(rf"({'|'.join(map(re.escape, a.arms))})-account-e2-s(\d+)$", c)
            if m and PRIMARY in g:
                for k in METRICS:
                    v[k, m[1], dom, int(m[2])] = 100 * g[PRIMARY][k]["mean"]
    assert len(commits) == 1, f"JSONs come from several commits: {commits}"
    print(f"commit {commits.pop()}, arms {a.arms[0]} - {a.arms[1]}, held-out domains {', '.join(doms)}\n")
    seeds = {x: sorted({s for (k, y, _, s) in v if y == x and k == "joint"}) for x in a.arms}
    res = {}
    for k, lab in METRICS.items():
        print(f"## {lab}, per seed\n\n| arm | domain | " + " | ".join(f"s{s}" for s in range(5)) + " |\n|---|---|" +
              "---|" * 5)
        per = {}
        for x in a.arms:
            for d in doms:
                print(f"| {x} | {d} | " + " | ".join(f"{v[k, x, d, s]:.1f}" if (k, x, d, s) in v else "" for s in
                                                    range(5)) + " |")
            per[x] = [st.mean(v[k, x, d, s] for d in doms) for s in seeds[x]]
        for d in doms + ["equal-weight mean"]:
            xs = [per[x] if d not in doms else [v[k, x, d, s] for s in seeds[x]] for x in a.arms]
            res[k, d] = welch(*xs)
            print(f"\n{a.arms[0]} - {a.arms[1]}, {d}: {res[k, d][0]:+.1f} [{res[k, d][1]:+.1f}, {res[k, d][2]:+.1f}]"
                  f" ({len(xs[0])} vs {len(xs[1])} seeds)", end="")
        print("\n")
    d, lo, hi = res["joint", "equal-weight mean"]
    win = a.arms[0] if lo > 0 else a.arms[1] if hi < 0 else None
    read = (f"{win} better" if win else f"equivalent within {a.margin:g} points" if -a.margin < lo and hi < a.margin
            else "inconclusive")
    _, alo, ahi = res["acc_maj", "equal-weight mean"]
    guard = "" if not win else (" (accuracy guardrail holds)" if (alo if win == a.arms[0] else -ahi) > -a.guard
                                else " (accuracy guardrail FAILS)")
    print(f"readout, joint success: {read}{guard}")


if __name__ == "__main__":
    main()
