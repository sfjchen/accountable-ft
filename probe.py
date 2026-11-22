"""Builds prior-conflict probe test files (E1): real-domain cases decided by one threshold moved off its real value.

The reused test cases give too few conflicts (other rules decide most of them, Nov 22 tally), so each test-slice prose
base case is edited until the target rule alone decides it: its threshold fact is set between the original and the
moved threshold, then other rules that would decide the case are repaired with as few fact changes as possible. Only
the sentences of changed facts are re-rendered (template prose), the rest of the case wording is kept.
Each edited case gives 2 records, both variant base:
  <id>-pc:prose   the moved rule in policy_spec and policy_text, prior_conflict true, orig_decision the decision
                  under the original rule
  <id>-pcc:prose  the original rule, the control (prior_conflict false, orig_decision its own gold)
The move alternates up and down by case (MOVES), so following the original threshold is not one decision bias.
gold comes from gen.gold_for. pc_role, pc_source, pc_move and pc_changed record the construction.
The edit bank (--bank, after the build) keeps only the kinds a base record alone gives, pivotal_replace 4/7 and
noncrossing_replace 3/7 (infer.build_bank scales every group to the scarcest, so the probe's missing remove, add and
invariant variants would empty it).
Entry point: main (writes data/<name>-pc.jsonl and prints counts); --identity rewrites nothing and checks that gold
recomputation reproduces each base record's decision; --bank <probe file> writes its .bank.jsonl and .bank.meta.json.
"""
import argparse
import itertools
import json
import random
import re
from collections import Counter
from pathlib import Path

import engine as E
import gen


def _mortgage(d):
    """Returns the mortgage move by d points of every min_score threshold, its reserves exception with it."""
    return lambda s, txt: re.sub(r"(credit_score >= |at least )(\d{3})\b", lambda m: m[1] + str(int(m[2]) + d), s)


def _snap(t):
    """Returns the SNAP move of the $3,000 resource limit (no elderly or disabled member) to t."""
    return lambda s, txt: s.replace("$3,000", f"${t:,}") if txt else s.replace("resources <= 3000", f"resources <= {t}")


def _dependent(t):
    """Returns the IRS move of the qualifying child age from under 19 to under t (student exception unchanged)."""
    return lambda s, txt: (s.replace("under age 19", f"under age {t}") if txt else
                           re.sub(r"age (<|>=) 19\b", rf"age \g<1> {t}", s))


# domain -> (rule key, threshold fact, {direction: rewrite fn(string, is_text)})
MOVES = {
    "mortgage": ("min_score", "credit_score", {"up": _mortgage(60), "down": _mortgage(-20)}),
    "snap": ("resource_limit", "resources", {"up": _snap(4500), "down": _snap(1500)}),
    "dependent": ("qc_age", "age", {"up": _dependent(23), "down": _dependent(17)}),
}


def move_spec(spec, domain, direction):
    """Returns (new policy_spec, moved rule id or None) with the domain's target rule rewritten."""
    key, _, fns = MOVES[domain]
    sp, rid = json.loads(json.dumps(spec)), None
    for r in sp["rules"]:
        if r.get("key") == key:
            rid = r["id"]
            for f in ("cond", "unless", "near"):
                if isinstance(r.get(f), str):
                    r[f] = fns[direction](r[f], False)
            r["text"] = fns[direction](r["text"], True)
    return sp, rid


def move_text(text, sp, rid):
    """Returns policy_text with the line of rule rid replaced by its text in sp."""
    rt = next(x for x in sp["rules"] if x["id"] == rid)["text"]
    return "\n".join(f"{rid}. {rt}" if ln.startswith(f"{rid}. ") else ln for ln in text.splitlines())


def valid(pol):
    """Returns True when approval is reachable and every require rule can both hold and fail (gen.instantiate)."""
    ok = "approve" in E.possible(pol, {})
    for r in pol.requires:
        ok &= E.sat(pol, ["+" + r.id], {}) and E.sat(pol, ["-" + r.id], {})
    return ok


def repair(pol, f, rid, locked, editable, rng):
    """
    Returns f with every require rule but rid holding and the facts valid, changing only editable facts outside
    locked (greedy, as gen.sample_case), or None.
    """
    def bad(g):
        return sum(not r.holds(g) for r in pol.requires if r.id != rid) + (not pol.ok(g))

    f = dict(f)
    vrefs = sorted({n for _, refs in pol.valid for n in refs})
    for _ in range(60):
        fails = [r for r in pol.requires if r.id != rid and not r.holds(f)]
        if not fails and pol.ok(f):
            return f
        refs = [n for r in fails for n in r.all_refs] if fails else vrefs
        refs = [n for n in refs if n in editable and n not in locked]
        if not refs:
            return None
        n = rng.choice(refs)
        vals = list(pol.dom[n])
        rng.shuffle(vals)
        f[n] = min(vals, key=lambda v: bad({**f, n: v}))
    return None


def conflict_facts(pol0, pol1, rid, x, facts, rng):
    """
    Returns (facts, changed fact names) closest to facts on which pol0 and pol1 (equal but for rule rid) reach
    different approve / deny decisions, or None: the threshold fact x and the rule's other facts are searched, the
    other rules repaired.
    """
    rule = next(r for r in pol0.requires if r.id == rid)
    others = sorted(n for n in rule.all_refs if n != x and n in facts and n not in pol0.dfn)
    combos = list(itertools.product(*[pol0.dom[n] for n in others])) if others else [()]
    if len(combos) > 64:
        combos = rng.sample(combos, 64)
    best = None
    for v in sorted(pol0.dom[x], key=lambda v: abs(v - facts[x]) if isinstance(v, (int, float)) else 0):
        for c in combos:
            g = {**facts, x: v, **dict(zip(others, c))}
            g = repair(pol0, g, rid, {x, *others}, set(facts), rng)
            if g is None:
                continue
            d0, d1 = E.decide(pol0, g)["decision"], E.decide(pol1, g)["decision"]
            if d0 != d1 and {d0, d1} == {"approve", "deny"}:
                ch = sorted(n for n in facts if g[n] != facts[n])
                if best is None or len(ch) < len(best[1]):
                    best = (g, ch)
        if best and len(best[1]) <= 1:
            break
    return best


def record(r, pol, sp, text, facts, rid, role, orig, move, changed):
    """Returns the probe record for base record r with policy (pol, sp, text) and facts."""
    seed = r["id"]
    sents = gen.case_sentences(pol, facts, seed, view=r["view"], base=r["case_sentences"])
    stated = {**facts, **pol.derived_values(facts)}
    states = {n: ({**s, "value": stated[n]} if n in stated else s) for n, s in r["fact_states"].items()}
    nid = r["id"].replace(":", f"-{role}:")
    g = gen.gold_for(pol, facts, nid)
    return r | {"id": nid, "policy_spec": sp, "policy_text": text, "facts": facts, "fact_states": states,
                "case_sentences": sents, "case_text": " ".join(x["sentence"] for x in sents), "gold": g,
                "orig_decision": orig if orig is not None else g["decision"],
                "prior_conflict": orig is not None and g["decision"] != orig, "moved_rule": rid if orig else None,
                "pc_role": "conflict" if orig is not None else "control", "pc_source": r["id"], "pc_move": move,
                "pc_changed": changed}


def write_bank(path):
    """Writes the edit bank of probe file path (pivotal and noncrossing kinds only) next to it, as infer.py does."""
    import infer
    infer.GROUPS = {"pivotal_replace": ("pivotal_replace",), "invariant": ("noncrossing_replace",)}
    infer.PROPS = {"pivotal_replace": 4 / 7, "invariant": 3 / 7}
    recs = [json.loads(ln) for ln in Path(path).open()]
    bank, meta = infer.build_bank(recs, 0)
    bp = Path(path).with_suffix(".bank.jsonl")
    bp.write_text("".join(json.dumps(b) + "\n" for b in bank))
    meta = {"data": path, "slice": recs[0]["slice"], "view": recs[0]["view"], "seed": 0, "kinds_kept": infer.GROUPS} | meta
    bp.with_name(bp.stem + ".meta.json").write_text(json.dumps(meta, indent=1))
    print(f"bank={bp} items={meta['items']}", meta["kinds"], "dropped", len(meta["drops"]), meta["drop_reasons"])


def main():
    """Parses the CLI, edits every base case of the slice and view, and writes the probe file."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="original real-domain file, e.g. data/snap.jsonl")
    ap.add_argument("--out")
    ap.add_argument("--bank", help="probe file to write the edit bank of (no build)")
    ap.add_argument("--slice", default="unseen_family_train_vocab")
    ap.add_argument("--view", default="prose")
    ap.add_argument("--identity", action="store_true", help="no move: check gold recomputation reproduces originals")
    a = ap.parse_args()
    if a.bank:
        return write_bank(a.bank)
    if not a.data or not a.out:
        ap.error("--data and --out are required without --bank")
    recs = [r for r in map(json.loads, Path(a.data).open())
            if r.get("slice") == a.slice and r.get("view") == a.view and r.get("variant") == "base"]
    out, cnt = [], Counter()
    for i, r in enumerate(recs):
        pol0 = gen.policy_for(r)
        if a.identity:
            cnt["identity_decision_mismatch"] += gen.gold_for(pol0, r["facts"], r["id"])["decision"] != r["gold"]["decision"]
            cnt["checked"] += 1
            continue
        move = ("up", "down")[i % 2]
        sp, rid = move_spec(r["policy_spec"], r["domain"], move)
        if rid is None:
            cnt["no_rule"] += 1
            continue
        text = move_text(r["policy_text"], sp, rid)
        pol1 = gen.policy_for(r | {"policy_spec": sp, "policy_text": text})
        if not valid(pol1):
            cnt["invalid_move"] += 1
            continue
        hit = conflict_facts(pol0, pol1, rid, MOVES[r["domain"]][1], r["facts"], random.Random(r["id"]))
        if hit is None:
            cnt[f"no_conflict_{move}"] += 1
            continue
        f, ch = hit
        c = record(r, pol1, sp, text, f, rid, "pc", E.decide(pol0, f)["decision"], move, ch)
        k = record(r, pol0, r["policy_spec"], r["policy_text"], f, rid, "pcc", None, move, ch)
        if not c["prior_conflict"] or c["gold"]["decision"] == k["gold"]["decision"]:
            cnt["gold_disagrees_with_decide"] += 1
            continue
        out += [c, k]
        cnt[f"conflict_{move}"] += 1
        cnt[f"{k['gold']['decision']}->{c['gold']['decision']}"] += 1
        cnt[f"changed_{min(len(ch), 3)}{'+' if len(ch) >= 3 else ''}"] += 1
        cnt["uncertified"] += c["gold"]["uncertified"] + k["gold"]["uncertified"]
    if not a.identity:
        Path(a.out).write_text("".join(json.dumps(x) + "\n" for x in out))
    print(a.out, f"base {len(recs)}", dict(sorted(cnt.items())))


if __name__ == "__main__":
    main()
