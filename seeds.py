"""
Tables the row-matched grid's paired simulatability gain (explanation minus decision-only) seed by seed for each test
and mix, then averages over test groups per seed, from evaluate.py JSON files. The CIs evaluate.py prints pool the 3
seeds and resample families only, so they treat the trained adapters as fixed. This shows the seed spread they leave
out: for each group, every mix's 3 per-seed averages and how many of the 9 seed pairs favor one mix over another.
It also prints each mix's explanation-run means over the 6 tests (accuracy, explanation correctness, raw gain, own
minus wrong-reason), which need no decision-only subtraction.
Usage: python seeds.py <dir with <file>-grid-<sim>.json> [--sim gemini opus]
"""
import argparse
import json
import re
import statistics as st
from pathlib import Path

PRIMARY = "slice=unseen_family_train_vocab view=prose"
# test name: (evaluate.py JSON prefix, domain inside it, or None for a 1-domain file)
TESTS = {"grant": ("v1", "grant"), "trial": ("v1", "trial"), "mortgage": ("mortgage-split", None),
         "snap": ("snap", None), "review": ("v1", "review"), "dependent": ("dependent", None)}
GROUPS = {"invented trained": ["grant", "trial"], "real trained": ["mortgage", "snap"],
          "held out": ["review", "dependent"], "all 6": list(TESTS)}
MIXES = ["inv", "real", "mix"]
# explanation-run metrics averaged over the 6 tests: metric: label
OWN = {"acc_maj": "accuracy", "expl_valid": "explanation correctness",
       "sim_delta": "raw gain (own - shuffled)", "sim_dwrong": "own - wrong-reason"}


def main():
    """
    Reads each simulator's 4 grid JSONs, checks they ran on 1 commit, prints per-seed gains per test, per-seed group
    averages and the seed-pair counts for mix - real and mix - inv.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--sim", nargs="+", default=["gemini", "opus"])
    ap.add_argument("--sft", metavar="DIR", help="also count each mix's training rows, families, policies, root "
                    "cases and explanation characters from DIR/rm-<mix>.sft.train.jsonl")
    a = ap.parse_args()
    if a.sft:
        recs = {r["id"]: r for f in ("data/v1.jsonl", "data/mortgage-split.jsonl", "data/snap.jsonl")
                for r in map(json.loads, Path(f).read_text().splitlines())}
        print("| mix | rows | families | policies | root cases | explanation characters |\n|---|---|---|---|---|---|")
        for x in MIXES:
            rows, roots = [json.loads(ln) for ln in (Path(a.sft) / f"rm-{x}.sft.train.jsonl").open()], set()
            for row in rows:
                r = recs[row["id"]]
                while r.get("parent"):
                    r = recs[r["parent"]]
                roots.add(r["id"].split(":")[0])
            rs = [recs[row["id"]] for row in rows]
            ch = sum(len(t) - len(t.split("\n")[0]) for t in (row["messages"][2]["content"] for row in rows))
            print(f"| {x} | {len(rows)} | {len({r['template_family'] for r in rs})} | "
                  f"{len({r['policy_id'] for r in rs})} | {len(roots)} | {ch:,} |")
        print()
    for sim in a.sim:
        g, commits, own = {}, set(), {}
        for t, (f, dom) in TESTS.items():
            j = json.loads((Path(a.dir) / f"{f}-grid-{sim}.json").read_text())
            commits.add(j["commit"])
            gk = PRIMARY + (f" domain={dom}" if dom else "")
            for x in MIXES:
                ms = j["seed_groups"][f"{f + '-' if f != 'v1' else ''}rm-{x}-account-e2"]["metrics"][gk]
                for k in OWN:
                    own.setdefault((x, k), []).append(100 * ms[k]["mean"] if k in ms else float("nan"))
            for k, v in j["paired"].items():
                if m := re.search(r"rm-(inv|real|mix)-account-e2-s(\d) - ", k):
                    g[t, m[1], int(m[2])] = 100 * v[gk]["sim_delta"]["mean"]
        assert len(commits) == 1, f"{sim} JSONs come from several commits: {commits}"
        print(f"## {sim}, commit {commits.pop()}: paired gain in points, seeds 0 / 1 / 2\n")
        print("| test | " + " | ".join(MIXES) + " |\n|---|---|---|---|")
        for t in TESTS:
            print(f"| {t} | " + " | ".join(" / ".join(f"{g[t, x, s]:.1f}" for s in range(3)) for x in MIXES) + " |")
        print("\n| group | " + " | ".join(MIXES) + " | mix > real, seed pairs | mix > inv, seed pairs |\n" +
              "|---|---|---|---|---|---|")
        for name, ts in GROUPS.items():
            av = {(x, s): st.mean(g[t, x, s] for t in ts) for x in MIXES for s in range(3)}
            win = [sum(av["mix", i] > av[y, k] for i in range(3) for k in range(3)) for y in ("real", "inv")]
            print(f"| {name} | " + " | ".join(" / ".join(f"{av[x, s]:.1f}" for s in range(3)) for x in MIXES) +
                  f" | {win[0]} of 9 | {win[1]} of 9 |")
        print("\n| explanation runs, mean of 6 tests | " + " | ".join(MIXES) + " |\n|---|---|---|---|")
        for k, lab in OWN.items():
            print(f"| {lab} | " + " | ".join(f"{st.mean(own[x, k]):.1f}" for x in MIXES) + " |")
        print()


if __name__ == "__main__":
    main()
