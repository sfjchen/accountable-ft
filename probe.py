"""Builds prior-conflict probe test files (E1): real-domain records with one threshold moved off its real value.

The case text is kept, so every probe record pairs with its original. Per domain, one rule's numbers are rewritten
in policy_spec (cond, unless, near, text) and in policy_text; gold is recomputed with gen.gold_for (and
removed_effect for -miss records). Each record keeps orig_decision (the gold under the original rule, the real
value for SNAP and IRS dependents, the training-data value for mortgage) and gets prior_conflict = gold decision
differs from orig_decision. Policies the move would make invalid (a rule that can no longer hold or fail, or no
approval reachable, the gen.instantiate check) are dropped.
Entry point: main (writes data/<name>-pc.jsonl and prints counts); --identity rewrites nothing, as a check that the
gold recomputation reproduces every original record.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import engine as E
import gen

# rule key -> list of (regex on cond/unless/near, replacement fn) and the same for text; each move is one direction
MOVES = {
    # mortgage min score up by 60 (640 -> 700, 660 -> 720), its "score at least t - 20 with reserves" exception too
    "mortgage": ("min_score", lambda s, txt: re.sub(r"(credit_score >= |at least )(\d{3})\b",
                 lambda m: m[1] + str(int(m[2]) + 60), s)),
    # SNAP resource limit for households without an elderly or disabled member: $3,000 -> $4,500
    "snap": ("resource_limit", lambda s, txt: s.replace("$3,000", "$4,500") if txt else
             s.replace("resources <= 3000", "resources <= 4500")),
    # IRS qualifying child age: under 19 -> under 23 (the student exception, under 24, is unchanged)
    "dependent": ("qc_age", lambda s, txt: s.replace("under age 19", "under age 23") if txt else
                  re.sub(r"age (<|>=) 19\b", r"age \1 23", s)),
}


def move_spec(spec, domain, identity=False):
    """Returns (new policy_spec, moved rule id or None) with the domain's target rule rewritten."""
    key, fn = MOVES[domain]
    sp, rid = json.loads(json.dumps(spec)), None
    for r in sp["rules"]:
        if r.get("key") == key and not identity:
            rid = r["id"]
            for f in ("cond", "unless", "near"):
                if isinstance(r.get(f), str):
                    r[f] = fn(r[f], False)
            r["text"] = fn(r["text"], True)
    return sp, rid


def valid(pol):
    """Returns True when approval is reachable and every require rule can both hold and fail (gen.instantiate)."""
    ok = "approve" in E.possible(pol, {})
    for r in pol.requires:
        ok &= E.sat(pol, ["+" + r.id], {}) and E.sat(pol, ["-" + r.id], {})
    return ok


def main():
    """Parses the CLI, rewrites every record of the slice and view, and writes the probe file."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="original real-domain file, e.g. data/snap.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--slice", default="unseen_family_train_vocab")
    ap.add_argument("--view", default="prose")
    ap.add_argument("--identity", action="store_true", help="no move: check gold recomputation reproduces originals")
    a = ap.parse_args()
    recs = [r for r in map(json.loads, Path(a.data).open()) if r.get("slice") == a.slice and r.get("view") == a.view]
    by_pol, out, cnt, ids = {}, [], Counter(), {r["id"]: r for r in recs}
    for r in recs:
        if r["policy_id"] not in by_pol:
            sp, rid = move_spec(r["policy_spec"], r["domain"], a.identity)
            text = r["policy_text"]
            if rid:
                lines = text.splitlines()
                rt = next(x for x in sp["rules"] if x["id"] == rid)["text"]
                lines = [f"{rid}. {rt}" if ln.startswith(f"{rid}. ") else ln for ln in lines]
                text = "\n".join(lines)
            pol = gen.policy_for(r | {"policy_spec": sp, "policy_text": text})
            by_pol[r["policy_id"]] = (sp, text, pol, rid, a.identity or (rid is not None and valid(pol)))
        sp, text, pol, rid, ok = by_pol[r["policy_id"]]
        if not ok:
            cnt["dropped_no_rule" if rid is None else "dropped_invalid"] += 1
            continue
        g = gen.gold_for(pol, r["facts"], r["id"])
        n = r | {"policy_spec": sp, "policy_text": text, "gold": g, "orig_decision": r["gold"]["decision"],
                 "prior_conflict": g["decision"] != r["gold"]["decision"], "moved_rule": rid}
        if r.get("removed_fact"):
            base = ids.get(r.get("parent"))
            if base is not None:
                bg = E.decide(pol, base["facts"])["decision"]
                n["removed_effect"] = ("cannot determine" if g["decision"] == "cannot determine" else
                        "default applied" if r["removed_fact"] in g["defaults_applied"] else
                        "unchanged" if g["decision"] == bg else "changed")
        if a.identity:
            # decisions must match exactly; sets may differ only where the search now runs over budget (uncertified)
            cnt["identity_decision_mismatch"] += g["decision"] != r["gold"]["decision"]
            cnt["identity_sets_mismatch_certified"] += not g["uncertified"] and (
                    g["sufficient_sets"] != r["gold"]["sufficient_sets"])
        cnt["kept"] += 1
        cnt["uncertified"] += g["uncertified"]
        cnt[f"{r['variant']}_conflict"] += n["prior_conflict"]
        cnt[f"{r['variant']}"] += 1
        cnt["conflict_" + "->".join((r["gold"]["decision"], g["decision"]))] += n["prior_conflict"]
        out.append(n)
    Path(a.out).write_text("".join(json.dumps(x) + "\n" for x in out))
    print(a.out, dict(sorted(cnt.items())), f"policies {len(by_pol)}")


if __name__ == "__main__":
    main()
