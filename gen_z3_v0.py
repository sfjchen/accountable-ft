"""Counterfactual training/eval data for Accountable-Model-Training.

Toy domain: clinical-trial eligibility. A policy is a conjunction of rules over
typed patient facts. z3 computes the gold decision and, for each base case,
three solver-defined neighbours:
  flip       minimal set of fact edits that flips the decision (z3 Optimize,
             soft "keep fact" constraints -> minimal correction subset)
  invariant  an edit to a fact that leaves the decision unchanged
  missing    a fact removed; gold says whether the decision is still
             determined and which rule needs the fact if it is not
Every record is checkable by re-running the solver, so no labels are hand-written.

Usage: python gen.py --n-policies 20 --cases-per-policy 10 --seed 0 --out out.jsonl
"""
import argparse, json, random
from z3 import Int, Bool, Optimize, Solver, And, Or, Not, If, Implies, sat, is_true

# fact name -> (kind, low, high). Distractors are never referenced by any rule.
FACTS = {
    "age": ("int", 18, 90), "egfr": ("int", 10, 120), "hba1c_x10": ("int", 50, 130),
    "ecog": ("int", 0, 4), "pregnant": ("bool",), "prior_metformin": ("bool",),
    "on_insulin": ("bool",), "height_cm": ("int", 140, 200), "zip3": ("int", 100, 999),
    "prior_trial": ("bool",),
}
DISTRACTORS = {"height_cm", "zip3", "prior_trial"}


def sample_policy(rng):
    """Return (rules, text). rules: list of (rule_id, fn(facts)->z3 bool, used fact names)."""
    rules, text = [], []
    lo, hi = rng.choice([(18, 65), (18, 75), (21, 70), (40, 80)])
    rules.append(("R_age", lambda f: And(f["age"] >= lo, f["age"] <= hi), ["age"]))
    text.append(f"R_age: age between {lo} and {hi} inclusive.")
    t = rng.choice([30, 45, 60])
    rules.append(("R_egfr", lambda f: f["egfr"] >= t, ["egfr"]))
    text.append(f"R_egfr: eGFR at least {t} mL/min.")
    a, b = rng.choice([(65, 100), (70, 105), (75, 110)])
    rules.append(("R_hba1c", lambda f: And(f["hba1c_x10"] >= a, f["hba1c_x10"] <= b), ["hba1c_x10"]))
    text.append(f"R_hba1c: HbA1c between {a/10:.1f}% and {b/10:.1f}% inclusive.")
    if rng.random() < 0.7:
        e = rng.choice([1, 2])
        rules.append(("R_ecog", lambda f: f["ecog"] <= e, ["ecog"]))
        text.append(f"R_ecog: ECOG performance status {e} or lower.")
    if rng.random() < 0.7:
        rules.append(("R_preg", lambda f: Not(f["pregnant"]), ["pregnant"]))
        text.append("R_preg: not pregnant.")
    if rng.random() < 0.6:
        rules.append(("R_metformin", lambda f: f["prior_metformin"], ["prior_metformin"]))
        text.append("R_metformin: has taken metformin before.")
    if rng.random() < 0.6:
        x = rng.choice([90, 100])
        rules.append(("R_insulin", lambda f: Or(Not(f["on_insulin"]), f["hba1c_x10"] >= x),
                      ["on_insulin", "hba1c_x10"]))
        text.append(f"R_insulin: not on insulin, unless HbA1c is at least {x/10:.1f}%.")
    return rules, text


def z3_vars(suffix=""):
    return {n: (Int(n + suffix) if s[0] == "int" else Bool(n + suffix)) for n, s in FACTS.items()}


def domain(v):
    cs = []
    for n, s in FACTS.items():
        if s[0] == "int":
            cs += [v[n] >= s[1], v[n] <= s[2]]
    return And(cs)


def bind(v, facts):
    return And([v[n] == facts[n] for n in facts])


def eligible(rules, v):
    return And([fn(v) for _, fn, _ in rules])


def decide(rules, facts):
    s = Solver(); v = z3_vars()
    s.add(bind(v, facts), eligible(rules, v))
    return "eligible" if s.check() == sat else "ineligible"


def rule_status(rules, facts):
    out = {}
    for rid, fn, _ in rules:
        s = Solver(); v = z3_vars(); s.add(bind(v, facts), fn(v))
        out[rid] = s.check() == sat
    return out


def read_model(m, v):
    f = {}
    for n, s in FACTS.items():
        val = m.eval(v[n], model_completion=True)
        f[n] = val.as_long() if s[0] == "int" else is_true(val)
    return f


def minimal_flip(rules, facts, decision):
    """Fewest fact edits that flip the decision. Pivotal facts = the edited ones."""
    o = Optimize(); v = z3_vars("_cf")
    o.add(domain(v))
    o.add(eligible(rules, v) if decision == "ineligible" else Not(eligible(rules, v)))
    for n in FACTS:
        o.add_soft(v[n] == facts[n], 1)
    if o.check() != sat:
        return None
    new = read_model(o.model(), v)
    return {n: new[n] for n in FACTS if new[n] != facts[n]}, new


def invariant_edit(rules, facts, decision, rng):
    """Change exactly one fact (prefer a referenced one) and keep the decision."""
    used = {n for _, _, ns in rules for n in ns}
    order = sorted(used, key=lambda _: rng.random()) + sorted(DISTRACTORS, key=lambda _: rng.random())
    for n in order:
        s = Solver(); v = z3_vars("_inv")
        s.add(domain(v), v[n] != facts[n], And([v[m] == facts[m] for m in FACTS if m != n]))
        s.add(eligible(rules, v) if decision == "eligible" else Not(eligible(rules, v)))
        if s.check() == sat:
            new = read_model(s.model(), v)
            return n, new
    return None


def missing_variant(rules, facts, rng):
    """Drop one referenced fact. Decision determined? If not, name the rule that needs it."""
    used = [n for _, _, ns in rules for n in ns]
    n = rng.choice(sorted(set(used)))
    can = {}
    for target in ("eligible", "ineligible"):
        s = Solver(); v = z3_vars("_mis")
        s.add(domain(v), And([v[m] == facts[m] for m in FACTS if m != n]))
        s.add(eligible(rules, v) if target == "eligible" else Not(eligible(rules, v)))
        can[target] = s.check() == sat
    if can["eligible"] and can["ineligible"]:
        needs = [rid for rid, _, ns in rules if n in ns]
        return n, "undetermined", needs
    return n, ("eligible" if can["eligible"] else "ineligible"), []


def sample_facts(rng, rules):
    """Bias toward near-boundary cases: ~half eligible."""
    for _ in range(200):
        f = {}
        for n, s in FACTS.items():
            f[n] = rng.randint(s[1], s[2]) if s[0] == "int" else rng.random() < 0.5
        if rng.random() < 0.5:  # force eligible
            s = Solver(); v = z3_vars(); s.add(domain(v), eligible(rules, v))
            for n in DISTRACTORS:
                s.add(v[n] == f[n])
            if s.check() == sat:
                f = read_model(s.model(), v)
        yield f


def facts_text(facts, drop=None):
    names = {"age": "Age", "egfr": "eGFR (mL/min)", "hba1c_x10": "HbA1c (%)", "ecog": "ECOG",
             "pregnant": "Pregnant", "prior_metformin": "Prior metformin", "on_insulin": "On insulin",
             "height_cm": "Height (cm)", "zip3": "ZIP prefix", "prior_trial": "Prior trial participation"}
    lines = []
    for n, label in names.items():
        if n == drop:
            continue
        val = facts[n]
        if n == "hba1c_x10":
            val = f"{val/10:.1f}"
        elif isinstance(val, bool):
            val = "yes" if val else "no"
        lines.append(f"{label}: {val}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-policies", type=int, default=20)
    ap.add_argument("--cases-per-policy", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="out.jsonl")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    records = []
    for p in range(a.n_policies):
        rules, text = sample_policy(rng)
        gen = sample_facts(rng, rules)
        for c in range(a.cases_per_policy):
            facts = next(gen)
            dec = decide(rules, facts)
            base_id = f"p{p:03d}_c{c:03d}"
            common = {"policy_id": f"p{p:03d}", "policy_text": "\n".join(text)}
            records.append({**common, "id": base_id, "variant": "base", "parent": None,
                            "facts": facts, "facts_text": facts_text(facts),
                            "expected_decision": dec, "rule_status": rule_status(rules, facts),
                            "changed_facts": {}, "needs_fact_for": []})
            flip = minimal_flip(rules, facts, dec)
            if flip:
                changed, new = flip
                records.append({**common, "id": base_id + "_flip", "variant": "flip", "parent": base_id,
                                "facts": new, "facts_text": facts_text(new),
                                "expected_decision": decide(rules, new), "rule_status": rule_status(rules, new),
                                "changed_facts": changed, "needs_fact_for": []})
            inv = invariant_edit(rules, facts, dec, rng)
            if inv:
                n, new = inv
                records.append({**common, "id": base_id + "_inv", "variant": "invariant", "parent": base_id,
                                "facts": new, "facts_text": facts_text(new),
                                "expected_decision": dec, "rule_status": rule_status(rules, new),
                                "changed_facts": {n: new[n]}, "needs_fact_for": []})
            n, mdec, needs = missing_variant(rules, facts, rng)
            dropped = {k: v for k, v in facts.items() if k != n}
            records.append({**common, "id": base_id + "_mis", "variant": "missing", "parent": base_id,
                            "facts": dropped, "facts_text": facts_text(facts, drop=n),
                            "expected_decision": mdec, "rule_status": None,
                            "changed_facts": {n: None}, "needs_fact_for": needs})
    with open(a.out, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    from collections import Counter
    print(len(records), "records ->", a.out)
    print("variants:", dict(Counter(r["variant"] for r in records)))
    print("base decisions:", dict(Counter(r["expected_decision"] for r in records if r["variant"] == "base")))
    print("missing outcomes:", dict(Counter(r["expected_decision"] for r in records if r["variant"] == "missing")))
    print("flip edit sizes:", dict(Counter(len(r["changed_facts"]) for r in records if r["variant"] == "flip")))


if __name__ == "__main__":
    main()
