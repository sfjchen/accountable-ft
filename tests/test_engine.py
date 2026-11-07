"""Tests for engine.py on hand-written policies with known answers, plus brute-force cross-checks.

The brute-force helpers enumerate every admissible completion directly, which is the literal definition
of sufficiency, and compare it with the engine's component search on small random policies. One block
checks generated policies from gen.py (flips flip, invariant edits hold, re-rendering an edited case
changes only that fact's sentence). The mandatory acceptance tests from the second review come last.
"""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine as E
import gen

V5 = {"type": "int", "values": [0, 2, 4, 6, 8]}
BOOL = {"type": "bool"}


def brute_decisions(pol, known):
    """
    Returns the set of decisions over every admissible completion of `known`, by full enumeration.
    """
    free = [n for n in pol.order if n not in known]
    out = set()
    for vals in itertools.product(*(pol.dom[n] for n in free)):
        z = {**known, **dict(zip(free, vals))}
        if all(fn(z) for fn, _ in pol.valid):
            out.add("approve" if all(r.holds(z) for r in pol.requires) else "deny")
    return out


def brute_sets(pol, facts):
    """
    Returns all subset-minimal sufficient sets by enumerating subsets and completions directly.
    """
    known, _ = E.known_facts(pol, facts)
    dec = brute_decisions(pol, known)
    if len(dec) != 1:
        return []
    names, suff = list(known), []
    for k in range(len(names) + 1):
        for sub in itertools.combinations(names, k):
            if brute_decisions(pol, {n: known[n] for n in sub}) == dec:
                suff.append(set(sub))
    mins = [s for s in suff if not any(t < s for t in suff)]
    return sorted(sorted(s, key=pol.order.index) for s in mins)


def test_exception_waives_failed_rule():
    """
    Checks that a true exception waives a failed condition and a false one leaves it failed.
    """
    pol = E.Policy("p", {"a": V5, "flag": BOOL}, [{"id": "R1", "kind": "require", "cond": "a <= 4",
                                                  "unless": "flag"}])
    d = E.decide(pol, {"a": 6, "flag": True})
    assert d["decision"] == "approve" and d["rule_trace"] == {"R1": "waived"}
    d = E.decide(pol, {"a": 6, "flag": False})
    assert d["decision"] == "deny" and d["rule_trace"] == {"R1": "fail"}
    assert E.decide(pol, {"a": 2, "flag": True})["rule_trace"] == {"R1": "pass"}


def test_default_fills_missing_fact():
    """
    Checks that a default fills a missing fact, is reported, and shows up as a default fact state.
    """
    pol = E.Policy("p", {"notice": BOOL, "a": V5}, [{"id": "R1", "kind": "require", "cond": "notice"},
                                                    {"id": "R2", "kind": "default", "fact": "notice",
                                                     "value": False}])
    d = E.decide(pol, {"a": 2})
    assert d["decision"] == "deny" and d["defaults_applied"] == {"notice": False} and d["needs_fact_for"] == []
    assert E.fact_states(pol, {"a": 2})["notice"] == {"state": "default", "value": False, "rule": "R2"}
    assert E.decide(pol, {"a": 2, "notice": True})["decision"] == "approve"


def test_missing_fact_matters_only_when_decision_differs():
    """
    Checks cannot-determine with the rule that needs the fact, and a decided outcome when it does not matter.
    """
    pol = E.Policy("p", {"a": V5, "b": BOOL}, [{"id": "R1", "kind": "require", "cond": "a <= 4"},
                                               {"id": "R2", "kind": "require", "cond": "b"}])
    d = E.decide(pol, {"b": True})
    assert d["decision"] == "cannot determine" and d["needs_fact_for"] == ["R1"]
    assert d["rule_trace"] == {"R1": "unknown", "R2": "pass"}
    d = E.decide(pol, {"b": False})
    assert d["decision"] == "deny" and d["needs_fact_for"] == []
    assert E.fact_states(pol, {"b": False})["a"] == {"state": "missing"}


def test_derived_fact_arithmetic():
    """
    Checks that a rule on a derived fact (end - start) evaluates the arithmetic and reports the value.
    """
    facts = {"start": {"type": "int", "values": [0, 7, 14]}, "end": {"type": "int", "values": [14, 21, 28]}}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "dur <= 14"}],
                   derived={"dur": "end - start"})
    assert E.decide(pol, {"start": 7, "end": 28})["decision"] == "deny"
    assert E.decide(pol, {"start": 7, "end": 21})["decision"] == "approve"
    st = E.fact_states(pol, {"start": 7, "end": 21})["dur"]
    assert st == {"state": "derived", "value": 14, "sources": ["end", "start"]}
    assert E.sufficient_sets(pol, {"start": 7, "end": 21}) == [["start", "end"]]


def test_sufficiency_uses_admissible_completions():
    """
    Checks that validity conditions restrict completions: start=20 forces end=25, so {start} alone suffices.
    """
    facts = {"start": {"type": "int", "values": [10, 20]}, "end": {"type": "int", "values": [5, 15, 25]}}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "end >= 20"}], valid=["end > start"])
    assert E.sufficient_sets(pol, {"start": 20, "end": 25}) == [["start"], ["end"]]
    assert E.sufficient_sets(pol, {"start": 10, "end": 15}) == [["end"]]


def test_sufficient_sets_minimal_and_sufficient():
    """
    Checks the engine's sets against brute force on a policy with an exception and overdetermination.
    """
    pol = E.Policy("p", {"a": V5, "b": BOOL, "c": BOOL, "d": V5},
                   [{"id": "R1", "kind": "require", "cond": "a <= 4", "unless": "b"},
                    {"id": "R2", "kind": "require", "cond": "c or d >= 6"}])
    for facts in [{"a": 2, "b": True, "c": True, "d": 8}, {"a": 6, "b": False, "c": False, "d": 0},
                  {"a": 6, "b": True, "c": False, "d": 6}]:
        sets = E.sufficient_sets(pol, facts)
        assert sorted(sets) == brute_sets(pol, facts)
        known, _ = E.known_facts(pol, facts)
        for s in sets:
            assert len(brute_decisions(pol, {n: known[n] for n in s})) == 1
            for n in s:
                assert len(brute_decisions(pol, {m: known[m] for m in s if m != n})) == 2
    assert E.sufficient_sets(pol, {"a": 2, "b": True, "c": True, "d": 8}) == [["a", "c"], ["a", "d"],
                                                                              ["b", "c"], ["b", "d"]]


def test_min_flip_is_minimal():
    """
    Checks a 2-fact flip when no 1-fact edit flips, and the smallest 1-fact move otherwise.
    """
    pol = E.Policy("p", {"a": V5, "b": V5, "c": BOOL},
                   [{"id": "R1", "kind": "require", "cond": "a <= 2"},
                    {"id": "R2", "kind": "require", "cond": "b >= 6"}])
    f = {"a": 6, "b": 2, "c": True}
    mf = E.min_flip(pol, f)
    assert mf == {"kind": "replace", "edits": {"a": 2, "b": 6}, "radius": 2, "certified_minimum": True,
                  "target": "approve"}
    for n in pol.order:
        for v in pol.dom[n]:
            assert E.decide(pol, {**f, n: v})["decision"] == "deny"
    mf = E.min_flip(pol, {"a": 2, "b": 6, "c": True})
    assert mf["radius"] == 1 and mf["edits"] in ({"a": 4}, {"b": 4}) and mf["target"] == "deny"
    rigid = E.Policy("p", {"a": V5}, [{"id": "R1", "kind": "require", "cond": "a <= 8"}])
    mf = E.min_flip(rigid, {"a": 2})
    assert mf == {"kind": "replace", "edits": None, "exhausted_radius": 4, "target": "deny"}


def test_min_flip_skips_edits_without_completion():
    """
    Checks that min_flip skips a candidate edit whose partial record has no admissible completion (end 5 with
    start unstated) instead of raising InvalidRecord, as on permit-p000-c01 with start_day removed.
    """
    facts = {"start": {"type": "int", "values": [10, 20]}, "end": {"type": "int", "values": [5, 15, 25]}}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "end >= 25"}], valid=["end > start"])
    assert E.min_flip(pol, {"end": 15}) == {"kind": "replace", "edits": {"end": 25}, "radius": 1,
                                            "certified_minimum": True, "target": "approve"}


def test_min_flip_exclude_and_prefer_disjoint():
    """
    Checks that exclude bars fact names, or (fact, value) edits plus every edit of exactly their fact set, and
    prefer_disjoint takes a disjoint flip at a larger radius, else the smallest overlapping one.
    """
    pol = E.Policy("p", {"a": V5, "b": V5, "c": BOOL},
                   [{"id": "R1", "kind": "require", "cond": "a <= 2"},
                    {"id": "R2", "kind": "require", "cond": "b >= 6"}])
    f = {"a": 2, "b": 6, "c": True}
    assert E.min_flip(pol, f)["edits"] == {"a": 4}
    assert E.min_flip(pol, f, exclude={"a"})["edits"] == {"b": 4}
    assert E.min_flip(pol, f, exclude={"a": 4})["edits"] == {"b": 4}
    mf = E.min_flip(pol, f, prefer_disjoint={"a": 4})
    assert mf["edits"] == {"b": 4} and mf["disjoint"] is True
    one = E.Policy("p", {"a": V5}, [{"id": "R1", "kind": "require", "cond": "a <= 2"}])
    mf = E.min_flip(one, {"a": 2}, prefer_disjoint={"a": 4})
    assert mf["edits"] == {"a": 4} and mf["disjoint"] is False and mf["radius"] == 1
    assert E.min_flip(one, {"a": 2}, exclude={"a": 4})["edits"] is None
    alt = E.Policy("p", {"a": V5, "b": V5, "c": BOOL},
                   [{"id": "R1", "kind": "require", "cond": "a <= 2 or b >= 6 and c"}])
    mf = E.min_flip(alt, {"a": 6, "b": 2, "c": False}, prefer_disjoint={"a": 2})
    assert mf["edits"] == {"b": 6, "c": True} and mf["radius"] == 2 and mf["disjoint"] is True


def test_coerce_bool_text():
    """
    Checks that only yes/no words coerce to bools and other text stays raw, so it never matches False.
    """
    pol = E.Policy("p", {"c": BOOL}, [{"id": "R1", "kind": "require", "cond": "c"}])
    assert [E.coerce(pol, "c", t) for t in ("Yes", "'no'", "true", "0")] == [True, False, True, False]
    assert E.coerce(pol, "c", "unknown") == "unknown" and E.coerce(pol, "c", "") == ""


def test_random_policies_match_brute_force():
    """
    Checks possible(), sufficient_sets() and min_flip radius against brute force on 60 random policies.
    """
    rng = random.Random(7)
    for _ in range(60):
        facts = {"a": {"type": "int", "values": [0, 1, 2, 3]}, "b": {"type": "int", "values": [0, 1, 2]},
                 "c": BOOL, "d": {"type": "enum", "values": ["x", "y", "z"]}}
        rules = [{"id": "R1", "kind": "require", "cond": f"a + b <= {rng.randint(1, 4)}",
                  "unless": rng.choice([None, "c", "d == 'z'"])},
                 {"id": "R2", "kind": "require", "cond": rng.choice(["not c or b >= 1", "d != 'x'", "a >= 1"])},
                 {"id": "R3", "kind": "require", "cond": rng.choice(["d in ['x', 'y'] or a == 3", "c or b == 0"])}]
        pol = E.Policy("p", facts, rules, valid=rng.choice([(), ("a >= b",)]))
        for _ in range(4):
            f = {n: rng.choice(pol.dom[n]) for n in pol.order if rng.random() < 0.8}
            known, _ = E.known_facts(pol, f)
            want = brute_decisions(pol, known)
            try:
                assert E.possible(pol, known) == want
            except E.InvalidRecord:
                assert want == set()
                continue
            if len(f) == 4 and pol.ok(f):
                assert sorted(E.sufficient_sets(pol, f)) == brute_sets(pol, f)
                mf = E.min_flip(pol, f)
                for k in range(1, mf.get("radius", 5)):
                    for combo in itertools.combinations(pol.order, k):
                        for vals in itertools.product(*(pol.dom[n] for n in combo)):
                            g = {**f, **dict(zip(combo, vals))}
                            if pol.ok(g) and g != f:
                                assert E.decide(pol, g)["decision"] == E.decide(pol, f)["decision"]


def test_justification_checker():
    """
    Checks valid, non-minimal, wrong-rule and missing-default accounts.
    """
    pol = E.Policy("p", {"a": V5, "b": BOOL, "n": BOOL},
                   [{"id": "R1", "kind": "require", "cond": "a <= 4"}, {"id": "R2", "kind": "require", "cond": "b"},
                    {"id": "R3", "kind": "require", "cond": "n"}, {"id": "R4", "kind": "default", "fact": "n",
                                                                     "value": False}])
    f = {"a": 6, "b": True}
    ok = E.is_valid_justification(pol, f, {"a": "6"}, {"a": "R1"}, {})
    assert ok["valid"] and ok["missing_defaults"] == []
    assert E.sufficient_sets(pol, f) == [["a"], ["n"]]
    both = E.is_valid_justification(pol, f, {"a": 6, "b": True}, ["R1", "R2"], {"n": False})
    assert both["sufficient"] and not both["minimal"] and both["wrong_rules"] == ["R2"]
    good = E.is_valid_justification(pol, f, {"a": 6}, {"a": "R1"}, {"n": False})
    assert good["valid"]
    only_n = E.is_valid_justification(pol, f, {}, ["R3", "R4"], {"n": False})
    assert only_n["valid"], only_n
    silent = E.is_valid_justification(pol, {"a": 2, "b": True}, {"a": 2, "b": True}, ["R1", "R2"], {})
    assert silent["missing_defaults"] == ["n"] and not silent["sufficient"]


def test_generated_policies_flip_invariant_and_render():
    """
    Checks generated policies: flips reach their target, invariant edits keep the decision for every
    value, and re-rendering an edited case changes only the edited fact's sentence.
    """
    for dname in gen.DOMAINS:
        dom = gen.load_domain(dname)
        rng = random.Random(dname)
        fam = gen.sample_family(dom, rng, [], False)
        pol = gen.instantiate(dname, fam, f"{dname}-t", rng)
        assert 8 <= len(pol.requires) + len(pol.defaults) <= 15
        for want in ["approve", "deny"]:
            f = gen.sample_case(pol, rng, want)
            mf = E.min_flip(pol, f)
            assert E.decide(pol, {**f, **mf["edits"]})["decision"] == mf["target"]
            inv = E.invariant_edit(pol, f, rng)
            if inv:
                (n, _), = inv.items()
                for v in pol.dom[n]:
                    if pol.ok({**f, n: v}):
                        assert E.decide(pol, {**f, n: v})["decision"] == want
            n, v = next((n, v) for n in pol.order for v in pol.dom[n] if v != f[n])
            a = gen.render_case(pol, f, "seed", view="prose_derive").split(". ")
            b = gen.render_case(pol, {**f, n: v}, "seed", view="prose_derive").split(". ")
            assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def one(cond, facts, default=None, valid=()):
    """
    Returns a Policy with bool facts A and B (plus int n in 0..2), one require rule and an optional default.
    """
    rules = [{"id": "R1", "kind": "require", "cond": cond}]
    if default:
        rules.append({"id": "R2", "kind": "default", "fact": default[0], "value": default[1]})
    return E.Policy("p", {"A": BOOL, "B": BOOL, "n": {"type": "int", "values": [0, 1, 2]}, **facts}, rules, valid)


def test_accept_cd_has_both_witnesses():
    """
    Checks approve iff A with A missing: cannot determine, with an approving and a denying completion.
    """
    pol = one("A", {})
    assert E.decide(pol, {"B": True, "n": 0})["decision"] == "cannot determine"
    w = E.cd_witnesses(pol, {"B": True, "n": 0})
    assert w == {"approve": {"A": True}, "deny": {"A": False}}
    for dec, z in w.items():
        assert E.decide(pol, {"B": True, "n": 0, **z})["decision"] == dec
    assert E.min_reveal(pol, {"B": True, "n": 0}) == {"kind": "add", "adds": {"A": False}, "radius": 1,
                                                      "certified_minimum": True, "decision": "deny"}


def test_accept_false_conjunct_decides_despite_missing():
    """
    Checks require A and B with A false and B missing: deny.
    """
    assert E.decide(one("A and B", {}), {"A": False, "n": 0})["decision"] == "deny"


def test_accept_tautology_and_contradiction_with_missing():
    """
    Checks require (A or not A) with A missing gives approve and (A and not A) gives deny.
    """
    assert E.decide(one("A or not A", {}), {"B": False, "n": 0})["decision"] == "approve"
    assert E.decide(one("A and not A", {}), {"B": False, "n": 0})["decision"] == "deny"


def test_accept_disjunction_overdetermined():
    """
    Checks approve iff A or B with both true: both singletons are valid, and replacing one alone does not flip.
    """
    pol, f = one("A or B", {}), {"A": True, "B": True, "n": 0}
    assert E.sufficient_sets(pol, f) == [["A"], ["B"]]
    for x in ("A", "B"):
        assert E.is_valid_justification(pol, f, {x: True}, {x: "R1"}, {})["valid"]
        assert E.decide(pol, {**f, x: False})["decision"] == "approve"
    assert E.min_flip(pol, f)["edits"] == {"A": False, "B": False}


def test_accept_conjunction_both_false():
    """
    Checks approve iff A and B with both false: either false fact justifies denial, min_flip has radius 2.
    """
    pol, f = one("A and B", {}), {"A": False, "B": False, "n": 0}
    assert E.sufficient_sets(pol, f) == [["A"], ["B"]]
    for x in ("A", "B"):
        assert E.is_valid_justification(pol, f, {x: False}, {x: "R1"}, {})["valid"]
    mf = E.min_flip(pol, f)
    assert mf["radius"] == 2 and mf["edits"] == {"A": True, "B": True} and mf["target"] == "approve"


def test_accept_threshold_move_without_crossing():
    """
    Checks that moving a threshold fact without crossing the threshold does not flip.
    """
    pol = E.Policy("p", {"a": V5}, [{"id": "R1", "kind": "require", "cond": "a <= 4"}])
    assert E.decide(pol, {"a": 0})["decision"] == E.decide(pol, {"a": 2})["decision"] == "approve"
    assert E.min_flip(pol, {"a": 0})["edits"] == {"a": 6}


def test_accept_remove_fires_default_replace_overrides():
    """
    Checks that removing n fires its default (deny) while replacing n with another value can approve.
    """
    pol = one("n >= 1", {}, default=("n", 0))
    f = {"A": True, "B": True, "n": 2}
    assert E.decide(pol, f)["decision"] == "approve"
    removed = {"A": True, "B": True}
    assert E.decide(pol, removed)["decision"] == "deny"
    assert E.decide(pol, removed)["defaults_applied"] == {"n": 0}
    assert E.decide(pol, {**f, "n": 1})["decision"] == "approve"


def test_accept_source_edit_updates_derived_and_text():
    """
    Checks that changing a source fact updates its derived fact and every textual assertion of it.
    """
    pol = gen.instantiate("grant", gen.sample_family(gen.load_domain("grant"), random.Random(1), [], False),
                          "grant-t", random.Random(2))
    f = gen.sample_case(pol, random.Random(3), "approve")
    g = {**f, "start_day": next(v for v in pol.dom["start_day"] if (f["end_day"] - v) // 7 !=
                                (f["end_day"] - f["start_day"]) // 7)}
    old, new = pol.derived_values(f)["duration_weeks"], pol.derived_values(g)["duration_weeks"]
    assert E.fact_states(pol, g)["duration_weeks"]["value"] == new != old
    prose, table = gen.render_case(pol, g, "s"), gen.render_case(pol, g, "s", view="table")
    assert f"project period of {new} weeks" in prose and f"project period of {old} weeks" not in prose
    assert f"project length in weeks: {new} (derived)" in table and f": {old} (derived)" not in table
    fmt = gen.Fmt(gen.load_domain("grant"), "start_day")
    for text in (prose, gen.render_case(pol, g, "s", view="prose_derive"), table):
        assert fmt.format_field(g["start_day"], "date") in text and fmt.format_field(f["start_day"], "date") not in text
    assert "project period of" not in gen.render_case(pol, g, "s", view="prose_derive")


def test_accept_no_completion_is_invalid_record():
    """
    Checks that constraints with no admissible completion raise InvalidRecord, for full and partial records.
    """
    facts = {"start": {"type": "int", "values": [10, 20]}, "end": {"type": "int", "values": [5, 15]}}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "end >= 5"}], valid=["end > start"])
    for rec in ({"start": 20, "end": 5}, {"start": 20}):
        try:
            E.decide(pol, rec)
        except E.InvalidRecord:
            continue
        raise AssertionError(f"{rec} should be invalid")


def test_accept_five_edit_boundary_is_uncertified():
    """
    Checks that a policy whose nearest approval needs 5 edits gets an uncertified result within radius 4.
    """
    facts = {x: BOOL for x in "abcde"}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "a + b + c + d + e >= 5"}])
    mf = E.min_flip(pol, {x: False for x in "abcde"})
    assert mf == {"kind": "replace", "edits": None, "exhausted_radius": 4, "target": "approve"}


def test_accept_budget_timeout_is_flagged():
    """
    Checks that a search over budget returns uncertified with a reason instead of a truncated answer.
    """
    facts = {x: {"type": "int", "values": list(range(8))} for x in "abcdefg"}
    pol = E.Policy("p", facts, [{"id": "R1", "kind": "require", "cond": "a + b + c + d + e + f + g >= 49"}])
    mf = E.min_flip(pol, {x: 0 for x in "abcdefg"}, budget=0.01)
    assert mf["uncertified"] and "budget" in mf["reason"] and mf["edits"] is None and "exhausted_radius" not in mf


def test_cd_justification_branch():
    """
    Checks the cannot-determine branch: citing the missing fact is valid, citing an observed one is not,
    and minimality is not scored.
    """
    pol = E.Policy("p", {"a": V5, "b": BOOL}, [{"id": "R1", "kind": "require", "cond": "a <= 4"},
                                               {"id": "R2", "kind": "require", "cond": "b"}])
    f = {"b": True}
    ok = E.is_valid_justification(pol, f, {"a": "unknown"}, ["R1"], {})
    assert ok["valid"] and ok["could_decide"] and ok["covers_needed"] and ok["minimal"] is None
    bad = E.is_valid_justification(pol, f, {"b": True}, ["R2"], {})
    assert not bad["valid"] and not bad["could_decide"]


def test_policy_for_round_trip():
    """
    Checks that policy_for rebuilds a policy from a record that reproduces the record's gold decision
    and trace, and that a ":view" seed renders the same text as the bare base id.
    """
    dom = gen.load_domain("trial")
    pol = gen.instantiate("trial", gen.sample_family(dom, random.Random(4), [], False), "trial-t", random.Random(5))
    f = gen.sample_case(pol, random.Random(6), "deny")
    rec = {"domain": "trial", "policy_id": pol.id, "policy_spec": pol.spec, "fact_labels": pol.labels,
           "policy_text": pol.text}
    back = gen.policy_for(rec)
    assert E.decide(back, f) == E.decide(pol, f)
    assert E.min_flip(back, f) == E.min_flip(pol, f)
    assert gen.render_case(rec, f, "trial-t-c00:prose") == gen.render_case(pol, f, "trial-t-c00")


def test_wrong_assumption_and_flat_rule_list():
    """
    Checks that a wrong assumption invalidates an account, a flat rule list is checked against the cited
    facts, and a timed-out check returns valid False.
    """
    pol = E.Policy("p", {"a": V5, "b": BOOL, "n": BOOL},
                   [{"id": "R1", "kind": "require", "cond": "a <= 4"}, {"id": "R2", "kind": "require", "cond": "n"},
                    {"id": "R3", "kind": "default", "fact": "n", "value": True}])
    f = {"a": 6, "b": True}
    assert E.is_valid_justification(pol, f, {"a": 6}, ["R1"], {"n": True})["valid"]
    for asm in ({"n": False}, {"b": True}, {"n": [True, "R1"]}):
        res = E.is_valid_justification(pol, f, {"a": 6}, ["R1"], asm)
        assert not res["valid"] and res["wrong_assumptions"] == list(asm)
    res = E.is_valid_justification(pol, f, {"a": 6}, ["R2"], {})
    assert not res["valid"] and res["wrong_rules"] == ["R2"]
    try:
        E.decide(E.Policy("q", {"a": V5}, [], valid=["a > 9"]), {}, rid="x-1")
    except E.InvalidRecord as e:
        assert "record x-1" in str(e)
    else:
        raise AssertionError("expected InvalidRecord")


def test_gemini_style_alignment():
    """
    Checks that variants rendered against a rewritten base keep its wording except the edited fact.
    """
    pol = gen.instantiate("grant", gen.sample_family(gen.load_domain("grant"), random.Random(1), [], False),
                          "grant-t", random.Random(2))
    f = gen.sample_case(pol, random.Random(3), "approve")
    base = [{**x, "sentence": "REWRITTEN " + x["sentence"]} for x in gen.case_sentences(pol, f, "b")]
    g = {**f, "travel_amount": next(v for v in pol.dom["travel_amount"] if v != f["travel_amount"])}
    out = gen.case_sentences(pol, g, "b", "prose", base)
    changed = [x["fact"] for x, y in zip(base, out) if x["sentence"] != y["sentence"]]
    assert set(changed) == {"travel_amount", "equip_travel"} and len(out) == len(base)
    drop = gen.case_sentences(pol, {k: v for k, v in f.items() if k != "start_day"}, "b", "prose_derive", base)
    assert [x for x in drop if x["fact"] in ("start_day", "duration_weeks", "equip_travel")] == []
