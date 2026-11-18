"""
Samples failures for the error analysis and prints them compactly for reading. Reads the <run>.items.jsonl files that
evaluate.py --dump writes, the runs and the data file. Draws, with a fixed seed and at most 1 item per case:
- wrong decisions: cases (every variant) whose majority decision differs from the engine's, in proportion to the
  gold -> predicted pairs
- simulator misses: edits where the simulator, reading the model's own explanation, predicts the model's answer after
  the edit wrongly, in proportion to whether the answer changed and whether the simulator predicted a change
Each item prints the stated facts, the policy's rule conditions, the engine's rule trace, the model's 4 lines and, for
an edit, the edit, the
model's answer after it and the 3 simulator passes' predictions. The cause labels go in data/errors-<file>.jsonl.
--tally instead counts the 2 leading causes over every failure: wrong decisions that cite a rule an exception waives
or a rule that only covers the other claim type, and simulator misses where the edit changes a fact the model cited
yet its answer stays.
Usage: python errors.py --dump DIR --runs <run stem>... --data data/<file>.jsonl [--n 25] [--seed 0] [--tally]
"""
import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from evaluate import load


def main():
    """
    Draws the 2 proportional samples and prints each item with its facts, rule trace, model output and simulator
    predictions.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tally", action="store_true")
    a = ap.parse_args()
    recs = {r["id"]: r for r in load(a.data)}
    out = {rs: {r["id"]: r["output"] for r in load(f"runs/{rs}.jsonl")} for rs in a.runs}
    if a.tally:
        C = Counter()
        for rs in a.runs:
            for d in load(Path(a.dump, rs + ".items.jsonl")):
                cid = d.get("case_id", d["id"])
                if cid not in recs:
                    continue
                r, o = recs[cid], out[rs].get(cid, "")
                sup = (re.search(r"policy support:(.*)", o, re.I) or [None, ""])[1]
                cited, tr = set(re.findall(r"\((R\d+)\)", sup)), r["gold"]["rule_trace"]
                rules, ct = {q["id"]: q for q in r["policy_spec"]["rules"]}, r["facts"].get("claim_type")
                # a rule written "claim_type != 'X' or ..." only binds claim type X
                other = {q["id"] for q in rules.values() if (m := re.match(r"claim_type != '(\w+)'", q.get("cond", "")))
                        and m[1] != ct}
                if d["type"] == "case":
                    C["cases"] += 1
                    C["gold cannot determine"] += d["gold"] == "cannot determine"
                    C["gold cannot determine, model too"] += d["gold"] == d["pred"] == "cannot determine"
                    if d["pred"] != d["gold"]:
                        w, x = any(tr.get(c) == "waived" for c in cited), bool(cited & other)
                        C["wrong decisions"] += 1
                        C["wrong, cites a waived rule"] += w
                        C["wrong, cites an other-claim-type rule"] += x
                        C["wrong, either"] += w or x
                elif d["fresh"] == d["f0"]:
                    lab = {v.lower(): k for k, v in r.get("fact_labels", {}).items()}
                    cf = {lab[x.strip().lower()] for x in re.findall(r"(?:^|;)\s*([^=;]+?)=", sup) if
                            x.strip().lower() in lab}
                    C["edits the engine flips, model stays"] += d["oracle"] != d["f0"]
                    if d.get("simulate") != d["fresh"]:
                        C["simulator misses, answer stays"] += 1
                        C["... edit changes a cited fact"] += bool(cf & set(d["edits"]))
                else:
                    C["edits the engine flips, model changes"] += d["oracle"] != d["f0"]
        for k, v in C.items():
            print(f"{k}: {v}")
        return
    pools = {"decision": defaultdict(list), "simulator": defaultdict(list)}
    for rs in a.runs:
        for d in load(Path(a.dump, rs + ".items.jsonl")):
            if d["type"] == "case" and d["id"] in recs and d["pred"] != d["gold"]:
                pools["decision"][f"{d['gold']} -> {d['pred']}"].append((rs, d))
            elif d["type"] == "edit" and d.get("simulate") != d["fresh"]:
                k = f"answer {'stays' if d['fresh'] == d['f0'] else 'changes'}, simulator says it " \
                    f"{'stays' if d.get('simulate') == d['f0'] else 'changes'}"
                pools["simulator"][k].append((rs, d))
    rng = random.Random(a.seed)
    for name, pool in pools.items():
        tot, seen, picks = sum(map(len, pool.values())), set(), []
        # largest-remainder quotas, so the strata add up to n
        q = {k: a.n * len(v) / tot for k, v in pool.items()}
        n = {k: int(x) for k, x in q.items()}
        for k in sorted(q, key=lambda k: n[k] - q[k])[:a.n - sum(n.values())]:
            n[k] += 1
        for k, v in sorted(pool.items()):
            rng.shuffle(v)
            for rs, d in v:
                cid = d.get("case_id", d["id"])
                if sum(p[0] == k for p in picks) >= n[k] or cid in seen:
                    continue
                seen.add(cid)
                picks.append((k, rs, d))
        print(f"\n######## {name} failures: {len(picks)} of {tot}, strata " +
              ", ".join(f"{k} {len(v)} -> {n[k]}" for k, v in sorted(pool.items())))
        for i, (k, rs, d) in enumerate(picks, 1):
            cid = d.get("case_id", d["id"])
            r = recs[cid]
            print(f"\n=== {name[0].upper()}{i:02d} [{k}] {rs} {d['id']} ({r.get('variant')})")
            print("facts: " + ", ".join(f"{f}={v}" for f, v in r["facts"].items()
                    if f in r.get("stated_facts", r["facts"])))
            for q in r["policy_spec"]["rules"]:
                print(f"  {q['id']}: {q.get('cond', q.get('fact', ''))}" + (f" unless {q['unless']}" if q.get("unless")
                        else "") + (f" default {q['value']}" if q["kind"] == "default" else ""))
            print(f"gold {r['gold']['decision']}; trace " + json.dumps(r["gold"]["rule_trace"]))
            print("model: " + out[rs].get(cid, "").strip().replace("\n", " | ")[:700])
            if d["type"] == "edit":
                print(f"edit {d['kind']} {json.dumps(d['edits'])}: engine {d['oracle']}, model {d['f0']} -> "
                      f"{d['fresh']}; simulator own {d.get('simulate')}, shuffled {d.get('simulate_shuf')}, "
                      f"none {d.get('simulate_noacc')}; explanation valid {d['valid']}")


if __name__ == "__main__":
    main()
