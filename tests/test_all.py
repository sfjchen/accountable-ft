"""Tests the engine on hand-written policies and against brute force, the generator, the parser and every metric of
evaluate.py on the hand-made tests/mini.jsonl, the bank, prompts, cache key and shuffled control of infer.py on
data/smoke.jsonl, and the SFT export, masking and loss weights of train.py with the Qwen2.5-0.5B-Instruct tokenizer.
Run: python -m pytest -q
"""
import hashlib
import itertools
import json
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine as E  # noqa: E402
import evaluate  # noqa: E402
import gen  # noqa: E402
import infer  # noqa: E402
from evaluate import aggregate, boot, explore_ckpt, norm_dec, parse, score, select_ckpt  # noqa: E402
from infer import CHANGE, PROPS, Runner, build_bank, build_prompt, format_target, root, select_recs  # noqa: E402

V5, BOOL = {"type": "int", "values": [0, 2, 4, 6, 8]}, {"type": "bool"}
SMOKE = [json.loads(ln) for ln in (ROOT / "data/smoke.jsonl").read_text().splitlines()]
BY = {r["id"]: r for r in SMOKE}
PRIM = select_recs(SMOKE, "unseen_family_train_vocab", "prose")
RECS = {r["id"]: r for r in map(json.loads, (ROOT / "tests/mini.jsonl").read_text().splitlines())}


def pol(facts, *rules, valid=()):
    """Returns a Policy over facts with require rules given as cond or (cond, unless) and defaults as (fact, value)."""
    rs = []
    for i, r in enumerate(rules):
        rid = f"R{i + 1}"
        rs.append({"id": rid, "kind": "require", "cond": r} if isinstance(r, str) else
                  {"id": rid, "kind": "default", "fact": r[0], "value": r[1]} if r[0] in facts else
                  {"id": rid, "kind": "require", "cond": r[0], "unless": r[1]})
    return E.Policy("p", facts, rs, valid)


def brute(p, known):
    """Returns the decisions over every possible completion of known, by full enumeration."""
    free = [n for n in p.order if n not in known]
    return {"approve" if all(r.holds(z) for r in p.requires) else "deny"
            for vals in itertools.product(*(p.dom[n] for n in free)) if p.ok(z := {**known, **dict(zip(free, vals))})}


def brute_sets(p, f):
    """Returns all subset-minimal sufficient sets of a complete record by enumerating subsets and completions."""
    dec, suff = brute(p, f), []
    for k in range(len(f) + 1):
        suff += [set(s) for s in itertools.combinations(f, k) if brute(p, {n: f[n] for n in s}) == dec]
    return sorted(sorted(s, key=p.order.index) for s in suff if not any(t < s for t in suff))


def test_decide_states_and_sets():
    """Checks exceptions, defaults, cannot determine, derived arithmetic and admissibility-aware sufficient sets."""
    p = pol({"a": V5, "flag": BOOL}, ("a <= 4", "flag"))
    assert E.decide(p, {"a": 6, "flag": True})["rule_trace"] == {"R1": "waived"}
    assert E.decide(p, {"a": 6, "flag": False})["decision"] == "deny"
    assert E.decide(p, {"a": 2, "flag": True})["rule_trace"] == {"R1": "pass"}
    p = pol({"notice": BOOL, "a": V5}, "notice", ("notice", False))
    d = E.decide(p, {"a": 2})
    assert d["decision"] == "deny" and d["defaults_applied"] == {"notice": False} and d["needs_fact_for"] == []
    assert E.fact_states(p, {"a": 2})["notice"] == {"state": "default", "value": False, "rule": "R2"}
    p = pol({"a": V5, "b": BOOL}, "a <= 4", "b")
    d = E.decide(p, {"b": True})
    assert d["decision"] == "cannot determine" and d["rule_trace"] == {"R1": "unknown", "R2": "pass"}
    assert E.decide(p, {"b": False})["needs_fact_for"] == [] and E.fact_states(p, {})["a"] == {"state": "missing"}
    se = {"start": {"type": "int", "values": [0, 7, 14]}, "end": {"type": "int", "values": [14, 21, 28]}}
    p = E.Policy("p", se, [{"id": "R1", "kind": "require", "cond": "dur <= 14"}], derived={"dur": "end - start"})
    assert E.decide(p, {"start": 7, "end": 28})["decision"] == "deny"
    assert E.fact_states(p, {"start": 7, "end": 21})["dur"] == {"state": "derived", "value": 14,
                                                                "sources": ["end", "start"]}
    assert E.sufficient_sets(p, {"start": 7, "end": 21}) == [["start", "end"]]
    se = {"start": {"type": "int", "values": [10, 20]}, "end": {"type": "int", "values": [5, 15, 25]}}
    p = pol(se, "end >= 20", valid=["end > start"])
    assert E.sufficient_sets(p, {"start": 20, "end": 25}) == [["start"], ["end"]]
    assert E.sufficient_sets(p, {"start": 10, "end": 15}) == [["end"]]
    p = pol(se, "end >= 25", valid=["end > start"])  # an edit with no possible completion is skipped, not raised
    assert E.min_flip(p, {"end": 15})["edits"] == {"end": 25}
    p = pol({"a": V5, "b": BOOL, "c": BOOL, "d": V5}, ("a <= 4", "b"), "c or d >= 6")
    assert E.sufficient_sets(p, {"a": 2, "b": True, "c": True, "d": 8}) == [["a", "c"], ["a", "d"], ["b", "c"],
                                                                            ["b", "d"]]


def test_min_flip_and_coerce():
    """Checks minimal flips, certified absence, exclude and prefer_disjoint, and bool coercion of text."""
    p = pol({"a": V5, "b": V5, "c": BOOL}, "a <= 2", "b >= 6")
    f = {"a": 6, "b": 2, "c": True}
    assert E.min_flip(p, f) == {"kind": "replace", "edits": {"a": 2, "b": 6}, "radius": 2, "certified_minimum": True,
                                "target": "approve"}
    assert all(E.decide(p, {**f, n: v})["decision"] == "deny" for n in p.order for v in p.dom[n])
    f = {"a": 2, "b": 6, "c": True}
    assert E.min_flip(p, f)["edits"] == {"a": 4} and E.min_flip(p, f, exclude={"a"})["edits"] == {"b": 4}
    assert E.min_flip(p, f, exclude={"a": 4})["edits"] == {"b": 4}
    mf = E.min_flip(p, f, prefer_disjoint={"a": 4})
    assert mf["edits"] == {"b": 4} and mf["disjoint"] is True
    one = pol({"a": V5}, "a <= 2")
    mf = E.min_flip(one, {"a": 2}, prefer_disjoint={"a": 4})
    assert mf["edits"] == {"a": 4} and mf["disjoint"] is False and mf["radius"] == 1
    assert E.min_flip(one, {"a": 2}, exclude={"a": 4})["edits"] is None
    assert E.min_flip(pol({"a": V5}, "a <= 8"), {"a": 2}) == {"kind": "replace", "edits": None, "exhausted_radius": 4,
                                                             "target": "deny"}
    mf = E.min_flip(pol({"a": V5, "b": V5, "c": BOOL}, "a <= 2 or b >= 6 and c"), {"a": 6, "b": 2, "c": False},
                    prefer_disjoint={"a": 2})
    assert mf["edits"] == {"b": 6, "c": True} and mf["radius"] == 2 and mf["disjoint"] is True
    b = pol({"c": BOOL}, "c")
    assert [E.coerce(b, "c", t) for t in ("Yes", "'no'", "true", "0", "unknown", "")] == [True, False, True, False,
                                                                                         "unknown", ""]


def test_random_policies_match_brute_force():
    """Checks possible(), sufficient_sets() and min_flip minimality against brute force on 60 random policies."""
    rng = random.Random(7)
    for _ in range(60):
        facts = {"a": {"type": "int", "values": [0, 1, 2, 3]}, "b": {"type": "int", "values": [0, 1, 2]}, "c": BOOL,
                 "d": {"type": "enum", "values": ["x", "y", "z"]}}
        p = pol(facts, (f"a + b <= {rng.randint(1, 4)}", rng.choice([None, "c", "d == 'z'"])),
                rng.choice(["not c or b >= 1", "d != 'x'", "a >= 1"]),
                rng.choice(["d in ['x', 'y'] or a == 3", "c or b == 0"]), valid=rng.choice([(), ("a >= b",)]))
        for _ in range(4):
            f = {n: rng.choice(p.dom[n]) for n in p.order if rng.random() < 0.8}
            want = brute(p, f)
            try:
                assert E.possible(p, f) == want
            except E.InvalidRecord:
                assert want == set()
                continue
            if len(f) == 4 and p.ok(f):
                assert sorted(E.sufficient_sets(p, f)) == brute_sets(p, f)
                for k in range(1, E.min_flip(p, f).get("radius", 5)):
                    for combo in itertools.combinations(p.order, k):
                        for vals in itertools.product(*(p.dom[n] for n in combo)):
                            g = {**f, **dict(zip(combo, vals))}
                            assert not p.ok(g) or E.decide(p, g)["decision"] == E.decide(p, f)["decision"]


def test_justification_checker():
    """Checks valid, non-minimal, wrong-rule, wrong-assumption, missing-default and cannot-determine accounts."""
    p = pol({"a": V5, "b": BOOL, "n": BOOL}, "a <= 4", "b", "n", ("n", False))
    f = {"a": 6, "b": True}
    assert E.is_valid_justification(p, f, {"a": "6"}, {"a": "R1"}, {})["valid"]
    assert E.sufficient_sets(p, f) == [["a"], ["n"]]
    both = E.is_valid_justification(p, f, {"a": 6, "b": True}, ["R1", "R2"], {"n": False})
    assert both["sufficient"] and not both["minimal"] and both["wrong_rules"] == ["R2"]
    assert E.is_valid_justification(p, f, {}, ["R3", "R4"], {"n": False})["valid"]
    silent = E.is_valid_justification(p, {"a": 2, "b": True}, {"a": 2, "b": True}, ["R1", "R2"], {})
    assert silent["missing_defaults"] == ["n"] and not silent["sufficient"]
    p = pol({"a": V5, "b": BOOL, "n": BOOL}, "a <= 4", "n", ("n", True))
    assert E.is_valid_justification(p, f, {"a": 6}, ["R1"], {"n": True})["valid"]
    for asm in ({"n": False}, {"b": True}, {"n": [True, "R1"]}):
        res = E.is_valid_justification(p, f, {"a": 6}, ["R1"], asm)
        assert not res["valid"] and res["wrong_assumptions"] == list(asm)
    assert E.is_valid_justification(p, f, {"a": 6}, ["R2"], {})["wrong_rules"] == ["R2"]
    with pytest.raises(E.InvalidRecord, match="record x-1"):
        E.decide(E.Policy("q", {"a": V5}, [], valid=["a > 9"]), {}, rid="x-1")
    p = pol({"a": V5, "b": BOOL}, "a <= 4", "b")
    ok = E.is_valid_justification(p, {"b": True}, {"a": "unknown"}, ["R1"], {})
    assert ok["valid"] and ok["could_decide"] and ok["covers_needed"] and ok["minimal"] is None
    assert not E.is_valid_justification(p, {"b": True}, {"b": True}, ["R2"], {})["could_decide"]


def test_acceptance():
    """Checks the mandatory acceptance cases of PLAN.md 3.2, each asserted exactly."""
    ab = {"A": BOOL, "B": BOOL, "n": {"type": "int", "values": [0, 1, 2]}}
    p = pol(ab, "A")
    assert E.cd_witnesses(p, {"B": True, "n": 0}) == {"approve": {"A": True}, "deny": {"A": False}}
    assert E.min_reveal(p, {"B": True, "n": 0}) == {"kind": "add", "adds": {"A": False}, "radius": 1,
                                                    "certified_minimum": True, "decision": "deny"}
    assert E.decide(pol(ab, "A and B"), {"A": False, "n": 0})["decision"] == "deny"
    assert E.decide(pol(ab, "A or not A"), {"n": 0})["decision"] == "approve"
    assert E.decide(pol(ab, "A and not A"), {"n": 0})["decision"] == "deny"
    for cond, v, flip in (("A or B", True, {"A": False, "B": False}), ("A and B", False, {"A": True, "B": True})):
        p, f = pol(ab, cond), {"A": v, "B": v, "n": 0}
        assert E.sufficient_sets(p, f) == [["A"], ["B"]] and E.min_flip(p, f)["edits"] == flip
        for x in ("A", "B"):
            assert E.is_valid_justification(p, f, {x: v}, {x: "R1"}, {})["valid"]
            assert v is False or E.decide(p, {**f, x: False})["decision"] == "approve"
    assert E.min_flip(pol({"a": V5}, "a <= 4"), {"a": 0})["edits"] == {"a": 6}
    p = pol(ab, "n >= 1", ("n", 0))
    d = E.decide(p, {"A": True, "B": True})
    assert d["decision"] == "deny" and d["defaults_applied"] == {"n": 0}
    assert E.decide(p, {"A": True, "B": True, "n": 1})["decision"] == "approve"
    se = {"start": {"type": "int", "values": [10, 20]}, "end": {"type": "int", "values": [5, 15]}}
    for rec in ({"start": 20, "end": 5}, {"start": 20}):
        with pytest.raises(E.InvalidRecord):
            E.decide(pol(se, "end >= 5", valid=["end > start"]), rec)
    p = pol({x: BOOL for x in "abcde"}, "a + b + c + d + e >= 5")
    assert E.min_flip(p, {x: False for x in "abcde"}) == {"kind": "replace", "edits": None, "exhausted_radius": 4,
                                                         "target": "approve"}
    p = pol({x: {"type": "int", "values": list(range(8))} for x in "abcdefg"}, "a + b + c + d + e + f + g >= 49")
    mf = E.min_flip(p, {x: 0 for x in "abcdefg"}, budget=0.01)
    assert mf["uncertified"] and "budget" in mf["reason"] and mf["edits"] is None and "exhausted_radius" not in mf


def test_generated_policies_and_rendering():
    """Checks generated flips, invariant edits, aligned re-rendering, derived updates, policy_for and Gemini merges."""
    for dname in gen.DOMAINS:
        rng = random.Random(dname)
        p = gen.instantiate(dname, gen.sample_family(gen.load_domain(dname), rng, [], False), f"{dname}-t", rng)
        assert 8 <= len(p.requires) + len(p.defaults) <= 15
        for want in ["approve", "deny"]:
            f = gen.sample_case(p, rng, want)
            mf = E.min_flip(p, f)
            assert E.decide(p, {**f, **mf["edits"]})["decision"] == mf["target"]
            for n, _ in (E.invariant_edit(p, f, rng) or {}).items():
                assert all(E.decide(p, {**f, n: v})["decision"] == want for v in p.dom[n] if p.ok({**f, n: v}))
            n, v = next((n, v) for n in p.order for v in p.dom[n] if v != f[n])
            a, b = (gen.render_case(p, g, "seed", view="prose_derive").split(". ") for g in (f, {**f, n: v}))
            assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
    p = gen.instantiate("grant", gen.sample_family(gen.load_domain("grant"), random.Random(1), [], False), "grant-t",
                        random.Random(2))
    f = gen.sample_case(p, random.Random(3), "approve")
    g = {**f, "start_day": next(v for v in p.dom["start_day"] if (f["end_day"] - v) // 7 !=
                                (f["end_day"] - f["start_day"]) // 7)}
    old, new = p.derived_values(f)["duration_weeks"], p.derived_values(g)["duration_weeks"]
    assert E.fact_states(p, g)["duration_weeks"]["value"] == new != old
    prose, table = gen.render_case(p, g, "s"), gen.render_case(p, g, "s", view="table")
    assert f"project period of {new} weeks" in prose and f"project period of {old} weeks" not in prose
    assert f"project length in weeks: {new} (derived)" in table and f": {old} (derived)" not in table
    fmt = gen.Fmt(gen.load_domain("grant"), "start_day")
    for text in (prose, gen.render_case(p, g, "s", view="prose_derive"), table):
        assert fmt.format_field(g["start_day"], "date") in text and fmt.format_field(f["start_day"], "date") not in text
    assert "project period of" not in gen.render_case(p, g, "s", view="prose_derive")
    base = [{**x, "sentence": "REWRITTEN " + x["sentence"]} for x in gen.case_sentences(p, f, "b")]
    g = {**f, "travel_amount": next(v for v in p.dom["travel_amount"] if v != f["travel_amount"])}
    out = gen.case_sentences(p, g, "b", "prose", base)
    assert {x["fact"] for x, y in zip(base, out) if x["sentence"] != y["sentence"]} == {"travel_amount",
                                                                                         "equip_travel"}
    drop = gen.case_sentences(p, {k: v for k, v in f.items() if k != "start_day"}, "b", "prose_derive", base)
    assert len(out) == len(base) and not [x for x in drop if x["fact"] in ("start_day", "duration_weeks",
                                                                          "equip_travel")]
    p = gen.instantiate("trial", gen.sample_family(gen.load_domain("trial"), random.Random(4), [], False), "trial-t",
                        random.Random(5))
    f = gen.sample_case(p, random.Random(6), "deny")
    rec = {"domain": "trial", "policy_id": p.id, "policy_spec": p.spec, "fact_labels": p.labels, "policy_text": p.text}
    back = gen.policy_for(rec)
    assert E.decide(back, f) == E.decide(p, f) and E.min_flip(back, f) == E.min_flip(p, f)
    assert gen.render_case(rec, f, "trial-t-c00:prose") == gen.render_case(p, f, "trial-t-c00")


def test_mortgage_domain():
    """Checks the real-rules mortgage domain: held out of "all" with its own slice, generated policies meet the
    validity conditions, keep the required score, LTV and DTI rules and certify flips, and a hand-worked case gets
    the gift and ratio rules right."""
    assert "mortgage" not in gen.DOMAINS and gen.SLICE[gen.HELD_OUT["mortgage"]] == "real_transfer"
    dom = gen.load_domain("mortgage")
    for s in range(3):
        rng = random.Random(f"mortgage-{s}")
        fam = gen.sample_family(dom, rng, [], False)
        assert set(dom["required"]) <= {k for k, _ in fam["core"]}
        p = gen.instantiate("mortgage", fam, f"mortgage-t{s}", rng)
        assert 8 <= len(p.requires) + len(p.defaults) <= 15
        for want in ["approve", "deny"]:
            f = gen.sample_case(p, rng, want)
            assert p.ok(f) and f["loan_amount"] <= f["property_value"]
            assert f["liquid_assets"] + f["gift_funds"] >= f["cash_to_close"]
            mf = E.min_flip(p, f)
            assert E.decide(p, {**f, **mf["edits"]})["decision"] == mf["target"]
    rules = [{"id": "R1", "kind": "require", "cond": "dti <= 45"},
             {"id": "R2", "kind": "require", "cond": "ltv <= 75 or credit_score >= 700"},
             {"id": "R3", "kind": "require", "cond": "reserves_months >= 6"}]
    p = E.Policy("m", dom["facts"], rules, dom["valid"], {n: d["expr"] for n, d in dom["derived_facts"].items()})
    f = {"credit_score": 700, "monthly_income": 9000, "housing_payment": 2100, "monthly_debts": 1500,
         "loan_amount": 420000, "property_value": 450000,
         "liquid_assets": 60000, "gift_funds": 20000, "cash_to_close": 50000}
    # (2100 + 1500) / 9000 = 40%; 420k / 450k = 93% rounds down;
    # (60k + 20k gift - 50k) / 2100 = 14.3 months rounds down
    assert p.derived_values(f) == {"dti": 40, "reserves_months": 14, "ltv": 93}
    assert E.decide(p, f)["decision"] == "approve"
    for edit in ({"monthly_income": 7000}, {"credit_score": 680}, {"gift_funds": 0}):  # DTI 51%, R2, 4 months
        assert E.decide(p, {**f, **edit})["decision"] == "deny"
    assert E.min_flip(p, f)["radius"] == 1
    # the account's own numbers imply deny (DTI 51%), and a value off the fact's buckets or a wrong derived value is
    # unscored
    assert E.implied_decision(p, f, {"monthly_income": "7000"}, {}) == "deny"
    assert E.implied_decision(p, f, {"credit_score": 700, "dti": 40}, {}) == "approve"
    assert E.implied_decision(p, f, {"credit_score": 701}, {}) is None
    assert E.implied_decision(p, f, {"dti": 30}, {}, ["dti"]) is None

def test_snap_and_dependent_domains():
    """Checks the 2 added real-rules domains: held out of "all" with the real slice, generated policies keep their
    required rules and certify flips, the dependent claim type is never edited, nested derived facts count their
    source facts, and hand-worked cases match the FY2027 SNAP deductions and the 2026 dependent tests."""
    for name in ("snap", "dependent"):
        assert name not in gen.DOMAINS and gen.SLICE[gen.HELD_OUT[name]] == "real_transfer"
        dom = gen.load_domain(name)
        for s in range(3):
            rng = random.Random(f"{name}-{s}")
            fam = gen.sample_family(dom, rng, [], False)
            assert set(dom["required"]) <= {k for k, _ in fam["core"]}
            p = gen.instantiate(name, fam, f"{name}-t{s}", rng)
            assert len(p.referenced()) <= E.MAX_FACTS and p.fixed == tuple(dom.get("fixed", ()))
            for want in ["approve", "deny"]:
                f = gen.sample_case(p, rng, want)
                mf = E.min_flip(p, f)
                if mf["edits"]:
                    assert E.decide(p, {**f, **mf["edits"]})["decision"] == mf["target"]
                    assert "claim_type" not in mf["edits"]
    dom = gen.load_domain("snap")
    assert {"earned_income", "unearned_income", "household_size", "shelter_costs", "elderly_or_disabled"} == \
        gen.template_refs(dom, dom["derived"][0]) - {"categorical"}
    der = {n: d["expr"] for n, d in dom["derived_facts"].items()}
    net = [{"id": "R1", "kind": "require", "cond": "net_income <= 1330 + 474 * (household_size - 1)"}]
    p = E.Policy("s", dom["facts"], net, (), der)
    f = {"household_size": 3, "earned_income": 1800, "unearned_income": 300, "shelter_costs": 1500,
         "elderly_or_disabled": False}
    # 2100 - 1800 // 5 - 217 = 1523; shelter 1500 - 1523 // 2 = 739 (under the $769 cap); net 784 <= 2278
    assert p.derived_values(f) == {"gross_income": 2100, "adjusted_income": 1523, "excess_shelter": 739,
                                   "net_income": 784}
    assert E.decide(p, f)["decision"] == "approve"
    # 1 person, $1,900 shelter: the excess 1900 - 383 // 2 = 1709 is capped at 769 unless elderly or disabled
    g = {"household_size": 1, "earned_income": 0, "unearned_income": 600, "shelter_costs": 1900}
    assert E.Policy("s", dom["facts"], net, (), der).derived_values({**g, "elderly_or_disabled": False})[
        "net_income"] == 383 - 769
    dom = gen.load_domain("dependent")
    der = {n: d["expr"] for n, d in dom["derived_facts"].items()}
    rules = [{"id": "R1", "kind": "require", "cond": "claim_type != 'qr' or gross_income < 5300"},
             {"id": "R2", "kind": "require", "cond": "claim_type != 'qc' or age < 19 or (full_time_student and "
              "age < 24)"}]
    p = E.Policy("d", dom["facts"], rules, (), der)
    # rent counts before expenses: 4000 wages + 1200 rent + 250 interest = 5450, over the limit
    f = {"claim_type": "qr", "wages": 4000, "rental_receipts": 1200, "interest_income": 250, "age": 22,
         "full_time_student": False}
    assert E.decide(p, f)["decision"] == "deny"
    assert E.decide(p, {**f, "claim_type": "qc", "full_time_student": True})["decision"] == "approve"


def test_counter_templates(tmp_path):
    """
    Checks one counter template per training domain, sampled only when asked and engine-valid, and that gen.py
    --counter gives every record prior_conflict, true exactly when a policy uses a counter template.
    """
    for dname in gen.DOMAINS:
        dom, rng = gen.load_domain(dname), random.Random(dname)
        ck = [t["key"] for t in dom["rules"] if t.get("counter")]
        assert len(ck) == (dname not in gen.HELD_OUT)
        fams = [gen.sample_family(dom, rng, [], False, counter=c) for c in [False] * 20 + [True] * 20]
        assert not {k for f in fams[:20] for k, _ in f["core"]} & set(ck)
        for i, f in enumerate(fams[20:] if ck else []):
            p = gen.instantiate(dname, f, f"{dname}-c{i}", rng)
            assert p.counter == (ck[0] in {k for k, _ in f["core"]})
        assert not ck or any(ck[0] in {k for k, _ in f["core"]} for f in fams[20:])
    out = tmp_path / "c.jsonl"
    subprocess.run([sys.executable, str(ROOT / "gen.py"), "--domains", "review", "--n-policies", "6",
            "--cases-per-family", "2", "--prose", "template", "--counter", "--out", str(out)], check=True,
            capture_output=True, cwd=ROOT)
    rs = [json.loads(ln) for ln in out.read_text().splitlines()]
    pc, ck = {r["policy_id"]: r["prior_conflict"] for r in rs}, next(t["key"] for t in gen.load_domain("review")[
            "rules"] if t.get("counter"))
    assert all(isinstance(r["prior_conflict"], bool) for r in rs) and set(pc.values()) == {True, False}
    assert all(pc[r["policy_id"]] == any(q.get("key") == ck for q in r["policy_spec"]["rules"]) for r in rs)


MESSY = [
    ("Decision: approve\nPolicy support: site zone=industrial (R4); operator certificate=current (R2)\n"
     "Assumptions: none\nSmallest change to make this deny: operator certificate -> lapsed; site zone -> residential",
     "approve", [("site zone", "industrial", "R4"), ("operator certificate", "current", "R2")], [],
     [("operator certificate", "lapsed"), ("site zone", "residential")], []),
    ("   decision :   APPROVE  \n relied on:  operator certificate = current ( r2 ) ;  site zone=industrial (R4)  \n"
     "assumptions:   none \n  smallest change to make this deny:  operator certificate   ->   lapsed  ",
     "approve", [("operator certificate", "current", "R2"), ("site zone", "industrial", "R4")], [],
     [("operator certificate", "lapsed")], []),
    ("**Decision:** Deny.\n**Policy support:** Noise rating=78 dB (R4).\n**Assumptions:** none\n"
     "**Smallest change to make this approve:** no change within 4 edits", "deny", [("Noise rating", "78 dB", "R4")],
     [], [], []),
    ("Decision: deny\nPolicy support: Site zone=residential (R4)", "deny", [("Site zone", "residential", "R4")], [], [],
     ["assumptions", "smallest change"]),
    ("Decision: Denied\nPolicy support: requested amount = 15,000 credits (rule 3); organization type: registered "
     "nonprofit (Rule 2)\nAssumptions: none\nSmallest change to make this approve: requested amount to 25,000 credits",
     "deny", [("requested amount", "15,000 credits", "R3"), ("organization type", "registered nonprofit", "R2")], [],
     [("requested amount", "25,000 credits")], []),
    ("Decision: can't determine.\nPolicy support: none\nAssumptions: proof of insurance on file=yes (default from R6)"
     "\nSmallest change to make this approve: none", "cannot determine", [],
     [("proof of insurance on file", "yes", "R6")], [], []),
    ("Policy support:\n- Site zone = industrial (R4)\n- Noise rating = 85 dB (R4)\nAssumptions: None.\n"
     "Decision: approved\nSmallest change: None", "approve",
     [("Site zone", "industrial", "R4"), ("Noise rating", "85 dB", "R4")], [], [], []),
    ("I think the permit should probably go through.", None, [], [], [],
     ["decision", "policy support", "assumptions", "smallest change"]),
]


@pytest.mark.parametrize("text,dec,rel,ass,chg,miss", MESSY)
def test_parse(text, dec, rel, ass, chg, miss):
    """Checks decision, policy support, assumptions, edits, missing lines and the error flag of one messy output."""
    p = parse(text)
    assert (p["dec"], p["relied"], p["assume"], p["change"], p["miss"], p["err"]) == (dec, rel, ass, chg, miss,
                                                                                      dec is None or bool(miss))


@pytest.fixture
def stub(monkeypatch):
    """Replaces policy lookup and the engine check with set matching on the fixture's sufficient sets."""
    monkeypatch.setattr(evaluate, "policy", lambda rec: rec)
    monkeypatch.setattr(evaluate.engine, "is_valid_justification", lambda p, f, cit, rules, ass: {
        "valid": any(set(s) <= set(cit) for s in p["gold"]["sufficient_sets"]),
        "minimal": None if p["gold"]["decision"] == "cannot determine" else
        any(set(s) == set(cit) for s in p["gold"]["sufficient_sets"])})
    monkeypatch.setattr(evaluate.engine, "implied_decision", lambda p, f, cit, ass, wrong=(): p["gold"]["decision"])


def fake_rows(over=None):
    """Returns 3 fake samples per fixture record, over replacing the decisions of some ids."""
    spec = {
        "p1-b1": (["approve", "approve", "deny"], "Operator certificate=current (R2); Proof of insurance=on file (R3); "
                  "Equipment color=heritage green (R7)", "none", "no change within 4 edits"),
        "p1-b1-f": (["deny"] * 3, "none", "none", "none"), "p1-b1-i": (["approve"] * 3, "none", "none", "none"),
        "p1-b1-m": (["cannot determine"] * 3, "none", "none", "none"),
        "p1-b2": (["deny"] * 3, "Site zone=residential (R4); Noise rating=78 dB (R4)", "none", "Noise rating -> 65 dB"),
        "p1-b2-f": (["cannot determine"] * 3, "none", "none", "none"),
        "p2-b1": (["deny"] * 3, "Requested amount=15,000 credits (R3)", "none",
                  "Requested amount -> 25,000 credits; Project location -> outside"),
        "p2-b1-f": (["deny"] * 3, "none", "none", "none"), "p2-b1-i": (["approve"] * 3, "none", "none", None),
        "p2-b1-m": (["approve"] * 3, "none", "Overdue prior report=no (default from R4)", "none"),
        "p2-b2": (["deny"] * 3, "Organization type=for-profit company (rule 2)", "none",
                  "Organization type -> registered nonprofit"),
        "p2-b2-f": (["approve"] * 3, "none", "none", "none")}
    return [{"id": i, "sample": k, "output": f"Decision: {d}\nPolicy support: {rel}\nAssumptions: {ass}" +
             (f"\nSmallest change to make this x: {chg}" if chg else "")}
            for i, (ds, rel, ass, chg) in spec.items() for k, d in enumerate((over or {}).get(i, ds))]


BANK = [{"bank_id": f"{c}|{k}", "kind": k, "case_id": c, "edited_id": e, "edits": {}, "oracle": o}
        for c, k, e, o in (("p1-b1", "pivotal_replace", "p1-b1-f", "deny"), ("p2-b1", "invariant_replace", "p2-b1-i",
                           "approve"), ("p1-b1", "remove", "p1-b1-m", "cannot determine"),
                           ("p2-b1-m", "add", "p2-b1", "approve"))]


def pr(bid, d, eid=None):
    """Returns one predict row for bank item bid with predicted decision d, echoing eid as the Edit ID."""
    return {"id": bid, "sample": 0, "output": f"Edit ID: {eid or bid}\nPredicted decision after edit: {d}"}


def check(ag, want, n=None):
    """Asserts each metric mean in want (and its unit count n when given) on aggregate group ag."""
    for m, v in want.items():
        assert ag[m]["mean"] == pytest.approx(v) and n in (None, ag[m]["n"]), m


def test_metrics(stub):
    """Checks every metric and coverage count on the fixture against values computed by hand from fake_rows."""
    U, cov, ivs = score(RECS, fake_rows(), {"repeat": fake_rows({"p1-b1-f": ["approve"] * 3})})
    ag = aggregate(U)
    check(ag["all"], {"acc_maj": 3 / 4, "acc_mean": 2 / 3, "acc_class[approve]": 5 / 7, "acc_class[deny]": 1.0,
                      "acc_class[cannot determine]": 1.0, "repeat_disagree": 1 / 12, "flip": 3 / 4,
                      "flip[approve->deny]": 1.0, "flip[deny->approve]": 1 / 2, "flip_to_cd": 1 / 4,
                      "flip_to_cd[deny->approve]": 1 / 2, "cf_pair_acc": 1 / 2, "flip~noise": 1 / 4,
                      "invariance": 1 / 2, "inv_pair_acc": 1 / 2, "invariance~noise": 0.0, "flip|correct": 2 / 3,
                      "flip|wrong": 1.0, "expl_valid": 2 / 11, "acct_consistent": 29 / 36, "expl_minimal": 2 / 10,
                      "cite_distractor": 1 / 12,
                      "cite_p_nec": 11 / 12, "cite_r_nec": 35 / 132, "assume_dec": 1.0, "assume_val": 1.0,
                      "none_claim_disproved": 1.0, "none_claim_unresolved": 0.0, "fmt_err": 3 / 36})
    assert ag["all"]["acc_maj"]["n"] == 4 and ag["all"]["acc_maj"]["n_clus"] == 2
    assert ag["slice=combined_transfer"]["acc_mean"]["mean"] == pytest.approx(5 / 6)
    assert ag[evaluate.PRIMARY]["acc_maj"]["mean"] == pytest.approx(1 / 2)
    assert (cov["none_claim_disproved"], cov["parse_fail"], cov["fmt_err"], cov["items_scored"],
            cov["expl_uncertified"]) == (3, 0, 3, 12, 3)
    edits = {"p1-b2|boundary|noise_rating_db=65 dB": ("approve", "approve"),
             "p2-b1|boundary|amount_credits=25,000 credits;project_region=outside": ("deny", "approve"),
             "p2-b2|boundary|org_type=registered nonprofit": ("approve", "deny"),
             "p1-b2|necessity|site_zone": ("approve", "approve"),
             "p1-b2|necessity|noise_rating_db": ("approve", "deny"),
             "p2-b2|necessity|org_type": ("approve", "approve")}
    assert {i["iid"] for i in ivs} == set(edits)
    recs = RECS | {iv["iid"]: RECS[iv["id"]] | {"id": iv["iid"], "gold": RECS[iv["id"]]["gold"] | {
        "decision": edits[iv["iid"]][0]}, "intervention": {"base": iv["id"]} | iv} for iv in ivs}
    ks = [b["bank_id"] for b in BANK]
    aux = {"answers": [{"id": i, "sample": 0, "output": f"Decision: {e[1]}"} for i, e in edits.items()],
           "predict": [pr(ks[0], "deny"), pr(ks[1], "deny"), {"id": ks[2], "sample": 0, "output": "it depends"},
                       pr(ks[3], "deny")],
           "predict_noacc": [pr(ks[0], "deny", "zzz"), pr(ks[1], "deny"), pr(ks[2], "cannot determine"),
                             pr(ks[3], "approve")]}
    for k, ds in (("simulate", ["deny", "approve", "cannot determine", "approve"]),
                  ("simulate_noacc", ["approve", "deny", "cannot determine", "deny"]),
                  ("simulate_shuf", ["approve"] * 4)):
        aux[k] = [pr(i, d) for i, d in zip(ks, ds)]
    U, cov, _ = score(recs, fake_rows(), aux, BANK)
    a = aggregate(U)["all"]
    check(a, {"bnd_both": 1 / 3, "bnd_oracle_only": 1 / 3, "bnd_model_only": 1 / 3, "bnd_neither": 0.0,
              "bnd_oracle_minimal": 2 / 3, "bnd_invalid": 0.0, "bnd_both[vs_gold]": 1 / 3,
              "bnd_oracle_only[vs_gold]": 2 / 3, "bnd_model_only[vs_gold]": 0.0, "bnd_oracle_minimal[vs_gold]": 2 / 3,
              "necessity_flip": 3 / 4, "necessity_flip[interaction]": 1 / 2, "acc_maj": 3 / 4, "self_S": 1 / 2,
              "self_S[pivotal_replace]": 1.0, "self_S_noacc": 1 / 4, "self_G": -1 / 4, "self_V": 1 / 4,
              "bank_unchanged": 0.0, "sim_acct": 3 / 4, "sim_noacc": 1 / 2, "sim_shuf": 1 / 4, "sim_delta": 1 / 2,
              "sim_delta[pivotal_replace]": 1.0, "sim_delta[invariant_replace]": 0.0, "sim_delta[add]": 0.0,
              "sim_gross": 1 / 4, "sim_gross[add]": -1.0, "sim_const_unchanged": 0.0, "sim_oracle": 3 / 4,
              "sim_delta[changed]": 1 / 2})
    assert "sim_delta[unchanged]" not in a and a["sim_oracle"]["n"] == 4
    assert (cov["predict_parse_fail"], cov["simulate_parse_fail"], cov["bank_unscored"]) == (1, 0, 0)
    aux["simulate_shuf"] = [r for r in aux["simulate_shuf"] if r["id"] != ks[2]]
    a = aggregate(score(recs, fake_rows(), aux, BANK)[0])["all"]
    check(a, {"sim_acct": 2 / 3, "sim_shuf": 1 / 3, "sim_noacc": 1 / 3, "sim_const_unchanged": 0.0,
              "sim_oracle": 2 / 3}, 3)
    check(a, {"self_S": 1 / 2}, 4)
    with pytest.raises(SystemExit, match="no fresh decision"):
        score(recs, [r for r in fake_rows() if r["id"] != "p1-b1-f"], aux, BANK)
    rows = fake_rows()
    for r in rows:
        r |= {"finish": "length"} if r["id"] == "p2-b2-f" else {"output": "<think>go"} if r["id"] == "p1-b1-i" else {}
    U, cov, _ = score(RECS, rows, {})
    a = aggregate(U)["all"]
    assert (a["flip"]["mean"], a["invariance"]["mean"], a["acc_class[approve]"]["mean"]) == pytest.approx(
        (1 / 2, 0.0, 3 / 7))
    assert (cov["truncated"], cov["parse_fail"], cov["flip_parse_fail_pairs"]) == (6, 6, 1)
    assert [norm_dec(x) for x in ("cannot determine whether to approve", "approve or deny", "insufficient facts",
                                  "Deny.")] == ["approve", None, "cannot determine", "deny"]


def test_domain_groups(stub, capsys):
    """Checks that every group is also split by domain and that each table gets a column per condition and domain."""
    ag = aggregate(score(RECS, fake_rows(), {})[0])
    for d, gk in (("grant", "slice=unseen_family_train_vocab"), ("permit", "slice=combined_transfer")):
        assert ag[f"domain={d}"] == ag[gk] == ag[f"{gk} domain={d}"] and ag[f"{gk} view=prose domain={d}"] == ag[gk]
    check(ag["domain=grant"], {"acc_maj": 1 / 2}, 2)
    check(ag["domain=permit"], {"acc_maj": 1.0}, 2)
    assert f"{evaluate.PRIMARY} domain=permit" not in ag
    evaluate.table("t", {"r": ag}, "all", lambda m: m == "acc_maj")
    out = capsys.readouterr().out.splitlines()
    assert out[3] == "| metric | r | r grant | r permit |"
    assert out[5].startswith("| acc_maj | 0.75 [") and "| 0.50 [" in out[5] and out[5].endswith("n=2 |")


def test_prior_conflict_split(stub):
    """Checks that accuracy and account validity split by prior_conflict when records carry it, and only then."""
    assert not any("prior_conflict" in m for g in aggregate(score(RECS, fake_rows(), {})[0]).values() for m in g)
    recs = {i: r | {"prior_conflict": r["domain"] == "grant"} for i, r in RECS.items()}
    ag = aggregate(score(recs, fake_rows(), {})[0])
    for m in evaluate.PC_SPLIT:
        assert ag["all"][f"{m}[prior_conflict=true]"] == ag["domain=grant"][m]
        assert ag["all"][f"{m}[prior_conflict=false]"] == ag["domain=permit"][m]
    assert not [m for m in ag["all"] if "prior_conflict" in m and m.split("[")[0] not in evaluate.PC_SPLIT]


def test_refusals(stub, tmp_path, monkeypatch):
    """Checks that evaluate.main refuses an old-shuffle shuf file and a companion from another model."""
    rows = [r | {"model": "m", "backend": "b"} for r in fake_rows()]
    rp = tmp_path / "r.jsonl"
    rp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(sys, "argv", ["evaluate.py", str(rp), "--data", str(ROOT / "tests/mini.jsonl"), "--json",
                                      str(tmp_path / "e.json")])
    shuf = [pr(b["bank_id"], "approve") | {"model": "sim", "shuf_src": "gold"} for b in BANK]
    for k, rs, msg in (("simulate_shuf", shuf, "old shuffle"), ("simulate_shuf", [r | {"shuf_src": "frozen"}
                       for r in shuf], "old shuffle"), ("repeat", [r | {"model": "m2"} for r in rows], "r.repeat")):
        (cp := tmp_path / f"r.{k}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs))
        with pytest.raises(SystemExit, match=msg):
            evaluate.main()
        cp.unlink()
    (tmp_path / "r.simulate_shuf.jsonl").write_text("".join(json.dumps(r | {"shuf_src": "frozen",
                                                    "shuf_decision_match": True}) + "\n" for r in shuf))
    evaluate.main()


def test_prompts_and_cache_key():
    """Checks the decision prompt names no target, predict and simulate prompts, and the response cache key."""
    tail = [build_prompt(RECS[i])[1].split(RECS[i]["case_text"].strip())[1] for i in ("p1-b1", "p1-b2")]
    assert RECS["p1-b1"]["gold"]["target"] == "deny" and RECS["p1-b2"]["gold"]["target"] == "approve"
    assert tail[0] == tail[1] and f"{CHANGE}:" in tail[0] and "make this" not in tail[0]
    it = {"bank_id": "p1-b1|remove", "kind": "remove", "edits": {"site_zone": None}}
    for sim in (False, True):
        u = build_prompt(RECS["p1-b1"], it, "Decision: approve\nPolicy support: x=y (R2)", sim)[1]
        assert f"Edit ID: {it['bank_id']}" in u and "Policy support: x=y (R2)" in u and "is no longer stated" in u
        assert (RECS["p1-b1"]["case_text"].strip() in u) != sim
    dec, ks = {"temperature": 0.0, "top_p": 1.0, "top_k": 0, "max_tokens": 64, "seed": 0, "thinking": False}, []
    for vx, ct in ((None, ""), ("global", ""), ("us-central1", ""), (None, "sft-e1"), (None, "sft-e2")):
        r = Runner.__new__(Runner)
        r.backend, r.base_url, r.model, r.extra, r.rep, r.ctag = "gemini", None, "m", {}, 0, ct
        r.tag = f"gemini/vertex:{vx}" if vx else "gemini"
        ks.append(r.key("s", "p", dec))
    assert len(set(ks)) == 5
    assert ks[0] == hashlib.sha256(json.dumps(["gemini", None, "m", {}, "s", "p", dec, 0], sort_keys=True)
                                   .encode()).hexdigest()


def test_select_and_boot():
    """Checks fixed-epoch selection and its refusals, the exploratory best-of-k, and bootstrap determinism."""
    r = lambda acc, d: {"slice=dev": {"acc_maj": {"mean": acc}} | ({"sim_delta": {"mean": d}} if d is not None
                                                                   else {})}
    res = {"ctrl-e1": r(0.70, 0.0), "ctrl-e2": r(0.71, 0.0), "acct-e1-s0": r(0.72, 0.10), "acct-e2-s0": r(0.60, 0.40),
           "acct-e1-s1": r(0.69, 0.20), "acct-e2-s1": r(0.70, 0.05)}
    got, rule = select_ckpt(res, list(res), 2)
    assert got == ["acct-e2-s0", "acct-e2-s1", "ctrl-e2"] and "fixed epoch 2" in rule
    assert select_ckpt(res, list(res), 1)[0] == ["acct-e1-s0", "acct-e1-s1", "ctrl-e1"]
    with pytest.raises(ValueError, match="no run for \\['ctrl'\\]"):
        select_ckpt({c: x for c, x in res.items() if c != "ctrl-e2"}, [c for c in res if c != "ctrl-e2"], 2)
    with pytest.raises(ValueError, match="acct-e2-s1"):
        select_ckpt(res | {"acct-e2-s1": r(0.70, None)}, list(res), 2)
    best, rule = explore_ckpt(res, [c for c in res if c.startswith("acct")], "ctrl-e2", "sim_delta")
    assert best == "acct-e1-s1" and "EXPLORATORY" in rule
    assert "eligible ['acct-e1-s0', 'acct-e1-s1', 'acct-e2-s1']" in rule
    v, cl = np.random.default_rng(1).random(60), [f"p{i % 12}" for i in range(60)]
    r0, r2 = boot(v, cl, seed=0), boot(v, cl, seed=7)
    assert r0 == boot(v, cl, seed=0) and r0["lo"] != r2["lo"] and r0["lo"] < r0["mean"] < r0["hi"]
    assert r0["n_clus"] == 12 and boot([0.5] * 10, ["a", "b"] * 5)["hi"] == 0.5 and boot(v - v, cl)["hi"] == 0.0
    assert boot([float("nan")], ["a"])["n"] == 0


def test_holm_and_boot_p():
    """Checks Holm adjustment (step-down, monotone, capped at 1) and that the bootstrap p is small for a clear
    nonzero mean and 1 for an all-zero one."""
    assert evaluate.holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    assert evaluate.holm({"a": 0.6, "b": 0.9}) == {"a": 1.0, "b": 1.0}
    clus = [i // 3 for i in range(60)]
    assert evaluate.boot_p([1.0] * 60, clus) == 0.0 and evaluate.boot_p([0.0] * 60, clus) == 1.0


def test_select_recs():
    """Checks --slice, --view and --cases K: K whole base cases with every variant, spread over domains, seeded."""
    recs = list(RECS.values())
    fam = {"p1-b1": ["p1-b1", "p1-b1-f", "p1-b1-i", "p1-b1-m"], "p1-b2": ["p1-b2", "p1-b2-f"],
           "p2-b1": ["p2-b1", "p2-b1-f", "p2-b1-i", "p2-b1-m"], "p2-b2": ["p2-b2", "p2-b2-f"]}
    assert {r["id"] for r in select_recs(recs, "unseen_family_train_vocab")} == {*fam["p2-b1"], *fam["p2-b2"]}
    assert select_recs(recs, view="table") == [] and select_recs(recs) == recs
    for k in (1, 2, 4):
        got = [r["id"] for r in select_recs(recs, cases=k)]
        bases = [i for i in got if i in fam]
        assert len(bases) == k and sorted(got) == sorted(i for b in bases for i in fam[b])
        assert k != 2 or {b[:2] for b in bases} == {"p1", "p2"}
    for k in (1, 3, 7):
        got = select_recs(SMOKE, "unseen_family_train_vocab", "prose", k, 3)
        assert len({root(r, BY) for r in got}) == k and got == select_recs(SMOKE, "unseen_family_train_vocab", "prose",
                                                                            k, 3)
    assert {root(r, BY) for r in select_recs(SMOKE, "unseen_family_train_vocab", "prose", 7, 3)} != \
        {root(r, BY) for r in select_recs(SMOKE, "unseen_family_train_vocab", "prose", 7, 4)}


def test_to_val_and_format_target():
    """Checks cited-value canonicalization on a grant policy and that the SFT target parses and justifies validly."""
    rec = next(r for r in SMOKE if r["domain"] == "grant")
    p = evaluate.policy(rec)
    got = [evaluate.to_val(p, n, v) for n, v in (("start_day", "January 4, 2027"), ("start_day", "2027-01-18"),
           ("end_day", "January 5, 2027"), ("pi_years_since_phd", "2024"), ("institution_type", "teaching hospital"),
           ("equipment_amount", "$30,000"), ("requested_amount", "40 thousand dollars"), ("duration_weeks", "34 weeks"),
           ("human_subjects", "no"))]
    assert got == [0, 14, 1, 3, "hospital", 30000, 40000, 34, "no"]
    for n, v in (("institution_type", "not a hospital"), ("duration_weeks", "more than 34"),
                 ("pi_years_since_phd", "under 3")):
        assert evaluate.to_val(p, n, v) == v
    for r in [r for r in SMOKE if r["variant"] == "base"][:40]:
        t, p = format_target(r), evaluate.policy(r)
        q = parse(t)
        assert t.startswith(f"Decision: {r['gold']['decision']}\n") and q["dec"] == r["gold"]["decision"], r["id"]
        assert q["miss"] == [] and not q["err"] and f"\n{CHANGE}: " in t
        if r["gold"]["decision"] != "cannot determine" and not r["gold"].get("uncertified"):
            lab = r["fact_labels"]
            cit = {n: evaluate.to_val(p, n, v) for l, v, _ in q["relied"] if (n := evaluate.to_name(l, lab))}
            ass = {n: evaluate.to_val(p, n, v) for l, v, _ in q["assume"] if (n := evaluate.to_name(l, lab))}
            assert E.is_valid_justification(p, r["facts"], cit, [x for _, _, x in q["relied"] if x], ass)["valid"]


def test_bank():
    """Checks the bank mix, ids, determinism, engine labels and pivotal edits independent of gold.min_flip."""
    bk, meta = build_bank(PRIM)
    grp = {"noncrossing_replace": "invariant", "invariant_replace": "invariant"}
    assert bk and (bk, meta) == build_bank(PRIM) and len({b["bank_id"] for b in bk}) == len(bk)
    for gk, p in PROPS.items():
        assert abs(sum(grp.get(b["kind"], b["kind"]) == gk for b in bk) - p * len(bk)) <= 1, gk
    br = evaluate.bank_recs(bk, BY)
    for b in bk:
        e, g = br.get(b["edited_id"]) or BY[b["edited_id"]], BY[b["case_id"]]["gold"]
        assert b["oracle"] == e["gold"]["decision"] == E.decide(gen.policy_for(BY[b["case_id"]]), e["facts"])[
            "decision"], b["bank_id"]
        gold = (g.get("min_flip") or {}).get("edits") or {}
        if b["kind"] == "pivotal_replace":
            assert b["oracle"] == E.flip_target(g["decision"]) and set(b["edits"]) != set(gold)
            assert not any(gold.get(n) == v for n, v in b["edits"].items())
        assert b["kind"] != "noncrossing_replace" or b["oracle"] == g["decision"]
    assert all(r["parent"] == next(b["case_id"] for b in bk if b["edited_id"] == i) for i, r in br.items())


def frozen_text(i):
    """Returns a fake frozen answer whose decision depends on id i and whose other lines name i."""
    return (f"**Decision:** {('approve', 'deny')[sum(map(ord, i)) % 2]}\nPolicy support: tag {i}=yes (R1)\n"
            f"Assumptions: none\nSmallest change that would reverse this decision: tag {i} -> no")


def test_simulate_accounts(monkeypatch, tmp_path):
    """Checks shuffle partners and the 3 --all-sim passes of infer.main through a stub Runner on a smoke sample."""

    class Stub:
        """Stands in for Runner: returns each item's frozen text as a cached row, calling no model."""

        def __init__(self, *a):
            """Ignores the backend settings."""

        def run(self, items, n, mode):
            """Returns one cached row per item carrying the text shown as the frozen account."""
            return [{"id": rid, "sample": 0, "cached": True, "mode": mode, "shown": fz} for rid, _, _, fz in items]

    sel = select_recs(SMOKE, "unseen_family_train_vocab", "prose", 12)
    bk = build_bank(sel)[0]
    br = evaluate.bank_recs(bk, BY)
    cs, c0 = BY | br, BY[bk[0]["case_id"]]
    fz = {i: frozen_text(i) for i in [r["id"] for r in sel] + list(br)}
    sp = infer.shuffle_partners(fz, cs, BY, 1)
    assert sp == infer.shuffle_partners(fz, cs, BY, 1)
    for i in (i for i in fz if i in BY):
        ok = [j for j in fz if cs[j]["policy_id"] == BY[i]["policy_id"] and root(cs[j], cs) != root(BY[i], cs)]
        assert (i in sp) == bool(ok) and (not ok or sp[i][0] in ok and sp[i][1] == (
            parse(fz[sp[i][0]])["dec"] == parse(fz[i])["dec"])), i
    fz = {i: t for i, t in fz.items() if cs[i]["policy_id"] != c0["policy_id"] or root(cs[i], cs) == root(c0, cs)}
    bp, fp = tmp_path / "b.jsonl", tmp_path / "f.jsonl"
    bp.write_text("".join(json.dumps(b) + "\n" for b in bk))
    fp.write_text("".join(json.dumps({"id": i, "sample": 0, "output": t}) + "\n" for i, t in fz.items()))
    monkeypatch.setattr(infer, "Runner", Stub)
    monkeypatch.setattr(sys, "argv", ["infer.py", "--mode", "simulate", "--all-sim", "--data", str(ROOT /
                                      "data/smoke.jsonl"), "--bank", str(bp), "--frozen", str(fp), "--backend",
                                      "gemini", "--model", "sim", "--sample-seed", "2"])
    infer.main()
    out = {x: evaluate.load(tmp_path / f"f.simulate{x}.jsonl") for x in ("", "_shuf", "_noacc")}
    meta = json.loads((tmp_path / "f.simulate_shuf.meta.json").read_text())
    cid, own = {b["bank_id"]: b["case_id"] for b in bk}, lambda i: frozen_text(i).splitlines()[0].replace("**", "")
    assert len(out[""]) == len(out["_noacc"]) == sum(b["case_id"] in fz for b in bk) == len(out["_shuf"]) + meta[
        "shuf_missing"] and out["_shuf"] and meta["shuf_missing"]
    for x, r in [(x, r) for x in out for r in out[x]]:
        c, j = cid[r["id"]], r.get("shuf_partner", cid[r["id"]])
        acct = f"\nPolicy support: tag {j}=yes (R1)\nAssumptions: none"
        assert r["shown"] == own(c) + ("" if x == "_noacc" else acct)
        if x == "_shuf":
            assert r["shuf_src"] == "frozen" and cs[j]["policy_id"] == BY[c]["policy_id"] and root(cs[j], cs) != c
            assert r["shuf_decision_match"] == (parse(fz[j])["dec"] == parse(fz[c])["dec"])
            assert r["mode"] == "simulate_shuf"


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    """Exports the smoke train split twice under one seed, checks the files match and returns the rows."""
    outs = [tmp_path_factory.mktemp("sft") / f"t{i}.jsonl" for i in range(2)]
    for o in outs:
        subprocess.run([sys.executable, str(ROOT / "train.py"), "export", "--data", str(ROOT / "data/smoke.jsonl"),
                        "--split", "train", "--out", str(o), "--seed", "3"], check=True, capture_output=True)
    assert outs[0].read_bytes() == outs[1].read_bytes()
    return [json.loads(ln) for ln in outs[0].read_text().splitlines()]


@pytest.fixture(scope="module")
def tok():
    """Returns the Qwen2.5-0.5B-Instruct tokenizer, or skips when it is neither cached nor downloadable."""
    tf = pytest.importorskip("transformers")
    try:
        return tf.AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
    except OSError as e:
        pytest.skip(f"Qwen/Qwen2.5-0.5B-Instruct tokenizer unavailable: {e}")


def test_export_and_weights(rows, tok):
    """
    Checks the export (train rows, all views, harness prompt and target, one account span after the Decision line),
    then per row that Collator.check holds, decision tokens get weight 1 / n_dec in every condition, account tokens
    lam / n_acc, lam 0 reproduces the decision labels and weights, and the realized sums in token_stats.
    """
    from train import Collator, token_stats
    assert len(rows) == sum(r["split"] == "train" for r in SMOKE)
    assert {r["id"].rsplit(":", 1)[1] for r in rows} == {"table", "prose", "prose_derive"}
    for x in rows:
        s, u, t = x["messages"]
        assert (s["role"], u["role"], t["role"], s["content"]) == ("system", "user", "assistant", infer.SYSTEM)
        assert t["content"] == format_target(BY[x["id"]])
        (a, b), = x["mask_spans"]
        assert t["content"][:a] == f"Decision: {BY[x['id']]['gold']['decision']}\n" and b == len(t["content"])
    cs = {"dec": Collator(tok, "decision", lam=2.0), "acc": Collator(tok, "account"),
          "half": Collator(tok, "account", lam=0.5), "zero": Collator(tok, "account", lam=0.0)}
    assert [c.lam for c in cs.values()] == [0.0, 1.0, 0.5, 0.0]
    for x in rows:
        es = {k: c.check(x) for k, c in cs.items()}
        ed = es["dec"]
        nd = sum(s and not a for s, a in zip(ed["sup"], ed["acct"]))
        assert tok.decode(ed["ids"][:ed["sup"].index(True)]).endswith("<|im_start|>assistant\n")
        for k, e in es.items():
            assert [w for w, s, a in zip(e["w"], e["sup"], e["acct"]) if s and not a] == [1 / nd] * nd, (k, x["id"])
            assert {w for w, a in zip(e["w"], e["acct"]) if a} == {cs[k].lam / sum(e["acct"])}, (k, x["id"])
            assert e["ids"] == ed["ids"] and all(w == 0 for w, s in zip(e["w"], e["sup"]) if not s)
        assert es["zero"]["lab"] == ed["lab"] and es["zero"]["w"] == ed["w"]
    for k, c in cs.items():
        t = token_stats(c, rows)
        assert t["w_dec_per_row"] == pytest.approx(1) and t["w_acc_per_row"] == pytest.approx(c.lam)
        assert t["truncated"] == 0 and t["masked_frac"] == (round(t["account"] / t["answer"], 6) if c.lam == 0 else 0)


def test_batch_and_weighted_loss(rows, tok):
    """Checks padding of a collated batch and weighted_loss against mean_dec + lam * mean_acc on random logits."""
    torch = pytest.importorskip("torch")
    from train import Collator, weighted_loss
    for lam in (0.0, 1.0, 0.5):
        col = Collator(tok, "account", lam=lam)
        b, es = col(rows[:4]), [col.encode(x) for x in rows[:4]]
        lg = torch.randn(*b["input_ids"].shape, len(tok), generator=torch.Generator().manual_seed(0))
        per = []
        for i, e in enumerate(es):
            n, ids = len(e["ids"]), torch.tensor(e["ids"])
            assert b["labels"][i, :n].tolist() == e["lab"] and set(b["labels"][i, n:].tolist()) <= {-100}
            assert b["weights"][i, :n].tolist() == pytest.approx(e["w"]) and b["weights"][i, n:].sum().item() == 0
            assert b["attention_mask"][i].sum().item() == n
            ce = torch.nn.functional.cross_entropy(lg[i, :n - 1], ids[1:], reduction="none")
            dm, am = torch.tensor([s and not a for s, a in zip(e["sup"], e["acct"])])[1:], torch.tensor(e["acct"])[1:]
            per.append(ce[dm].mean() + lam * ce[am].mean())
        assert weighted_loss(lg, b["labels"], b["weights"]).item() == pytest.approx(torch.stack(per).mean().item(),
                                                                                    rel=1e-5)


def test_chunked_resume_matches_one_run(tmp_path):
    """
    Trains a toy dropout regressor for 2 epochs once, and as chunk 1 (stop_cb(1)) plus chunk 2 (resume from the
    epoch-1 checkpoint), under train.py's schedule settings (cosine, warmup, data_seed, epoch saves), and checks the
    chunks stop at the epoch boundary and match the single run in steps, learning rates, losses and final weights.
    """
    torch = pytest.importorskip("torch")
    tf = pytest.importorskip("transformers")
    from train import stop_cb

    class Toy(torch.nn.Module):
        """Linear regressor with dropout, so the loss depends on the restored RNG state."""

        def __init__(self):
            """Builds the layers from a fixed seed."""
            super().__init__()
            torch.manual_seed(0)
            self.lin, self.drop = torch.nn.Linear(4, 1), torch.nn.Dropout(0.5)

        def forward(self, x, y):
            """Returns the mean squared error of the dropout-masked prediction."""
            return {"loss": torch.nn.functional.mse_loss(self.lin(self.drop(x)).squeeze(-1), y)}

    g = torch.Generator().manual_seed(1)
    ds = [{"x": torch.randn(4, generator=g).tolist(), "y": float(i % 3)} for i in range(22)]

    def fit(out, cb=None, ck=None):
        """Runs one Trainer call into out and returns the trainer and its model."""
        m = Toy()
        cfg = tf.TrainingArguments(output_dir=str(out), num_train_epochs=2, learning_rate=0.05, seed=0, data_seed=0,
                per_device_train_batch_size=2, gradient_accumulation_steps=2, warmup_steps=0.1,
                lr_scheduler_type="cosine", logging_steps=1, save_strategy="epoch", report_to="none", use_cpu=True,
                remove_unused_columns=False, disable_tqdm=True)
        tr = tf.Trainer(model=m, args=cfg, train_dataset=ds, callbacks=[cb] if cb else None)
        tr.train(resume_from_checkpoint=ck)
        return tr, m

    one, m1 = fit(tmp_path / "one")
    c1, _ = fit(tmp_path / "ch", stop_cb(1))
    n = one.state.max_steps
    assert c1.state.epoch == pytest.approx(1) and c1.state.global_step == n // 2 < c1.state.max_steps == n
    assert sorted(p.name for p in (tmp_path / "ch").glob("checkpoint-*")) == [f"checkpoint-{n // 2}"]
    c2, m2 = fit(tmp_path / "ch", ck=str(tmp_path / "ch" / f"checkpoint-{n // 2}"))
    assert c2.state.global_step == c2.state.max_steps == n and c2.state.epoch == pytest.approx(2)
    lg = lambda t: [h[k] for h in t.state.log_history if "loss" in h for k in ("step", "learning_rate", "loss")]
    assert len(lg(one)) == 3 * n and lg(c2) == pytest.approx(lg(one), rel=1e-6)
    assert all(torch.equal(a, b) for a, b in zip(m1.state_dict().values(), m2.state_dict().values()))
