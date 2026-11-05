"""
Tests evaluate.py and the data-side helpers of infer.py: the output parser on messy model text, every metric on the
12-record fixture against hand-computed values (fake run, repeat, answer and prediction outputs are written here),
the intervention bank proportions, checkpoint selection, and bootstrap determinism under a seed.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate  # noqa: E402
from evaluate import aggregate, boot, norm_dec, parse, score, select_ckpt  # noqa: E402
from infer import build_bank, build_prompt  # noqa: E402

RECS = {r["id"]: r for r in map(json.loads, (ROOT / "tests/fixtures/mini.jsonl").read_text().splitlines())}
ALL4 = ["decision", "policy support", "assumptions", "smallest change"]

MESSY = [
    ("Decision: approve\nPolicy support: site zone=industrial (R4); operator certificate=current (R2)\n"
        "Assumptions: none\nSmallest change to make this deny: operator certificate -> lapsed; "
        "site zone -> residential",
        "approve", [("site zone", "industrial", "R4"), ("operator certificate", "current", "R2")], [],
        [("operator certificate", "lapsed"), ("site zone", "residential")], []),
    ("   decision :   APPROVE  \n relied on:  operator certificate = current ( r2 ) ;  site zone=industrial (R4)  \n"
        "assumptions:   none \n  smallest change to make this deny:  operator certificate   ->   lapsed  ",
        "approve", [("operator certificate", "current", "R2"), ("site zone", "industrial", "R4")], [],
        [("operator certificate", "lapsed")], []),
    ("**Decision:** Deny.\n**Policy support:** Noise rating=78 dB (R4).\n**Assumptions:** none\n"
        "**Smallest change to make this approve:** no change within 4 edits",
        "deny", [("Noise rating", "78 dB", "R4")], [], [], []),
    ("Decision: deny\nPolicy support: Site zone=residential (R4)",
        "deny", [("Site zone", "residential", "R4")], [], [], ["assumptions", "smallest change"]),
    ("Decision: Denied\nPolicy support: requested amount = 15,000 credits (rule 3); organization type: registered "
        "nonprofit (Rule 2)\nAssumptions: none\nSmallest change to make this approve: "
        "requested amount to 25,000 credits",
        "deny", [("requested amount", "15,000 credits", "R3"), ("organization type", "registered nonprofit", "R2")],
        [], [("requested amount", "25,000 credits")], []),
    ("Decision: can't determine.\nPolicy support: none\nAssumptions: proof of insurance on file=yes (default from R6)"
        "\nSmallest change to make this approve: none", "cannot determine", [],
        [("proof of insurance on file", "yes", "R6")], [], []),
    ("Policy support:\n- Site zone = industrial (R4)\n- Noise rating = 85 dB (R4)\nAssumptions: None.\n"
        "Decision: approved\nSmallest change: None", "approve",
        [("Site zone", "industrial", "R4"), ("Noise rating", "85 dB", "R4")], [], [], []),
    ("I think the permit should probably go through.", None, [], [], [], ALL4),
]


@pytest.mark.parametrize("text,dec,rel,ass,chg,miss", MESSY)
def test_parse(text, dec, rel, ass, chg, miss):
    """
    Checks decision, policy support, assumptions, proposed edits, missing lines and the error flag for one output.
    """
    p = parse(text)
    assert (p["dec"], p["relied"], p["assume"], p["change"], p["miss"]) == (dec, rel, ass, chg, miss)
    assert p["err"] == (dec is None or bool(miss))


def fake_valid(pol, facts, cit, rules, ass):
    """
    Stands in for engine.is_valid_justification with set matching against the record's sufficient sets (pol is the
    record itself here), returning minimal None for "cannot determine" as the engine does.
    """
    sets = [set(s) for s in pol["gold"]["sufficient_sets"]]
    cd = pol["gold"]["decision"] == "cannot determine"
    return {"valid": any(s <= set(cit) for s in sets), "minimal": None if cd else any(s == set(cit) for s in sets)}


@pytest.fixture(autouse=True)
def stub_engine(monkeypatch):
    """
    Replaces gen.policy_for and engine.is_valid_justification so the hand-made fixture needs no policy_spec.
    """
    monkeypatch.setattr(evaluate, "policy", lambda rec: rec)
    monkeypatch.setattr(evaluate.engine, "is_valid_justification", fake_valid)


def fake_rows(over=None):
    """
    Builds 3 fake samples per fixture record, with over replacing the decisions of some ids. p1-b1 votes approve,
    approve, deny and claims no change exists; p2-b1 is wrongly denied; p1-b2-f goes to cannot determine; p2-b1-i
    drops its last line.
    """
    spec = {
        "p1-b1": (["approve", "approve", "deny"], "Operator certificate=current (R2); Proof of insurance=on file (R3); "
            "Equipment color=heritage green (R7)", "none", "no change within 4 edits"),
        "p1-b1-f": (["deny"] * 3, "none", "none", "none"),
        "p1-b1-i": (["approve"] * 3, "none", "none", "none"),
        "p1-b1-m": (["cannot determine"] * 3, "none", "none", "none"),
        "p1-b2": (["deny"] * 3, "Site zone=residential (R4); Noise rating=78 dB (R4)", "none", "Noise rating -> 65 dB"),
        "p1-b2-f": (["cannot determine"] * 3, "none", "none", "none"),
        "p2-b1": (["deny"] * 3, "Requested amount=15,000 credits (R3)", "none",
            "Requested amount -> 25,000 credits; Project location -> outside"),
        "p2-b1-f": (["deny"] * 3, "none", "none", "none"),
        "p2-b1-i": (["approve"] * 3, "none", "none", None),
        "p2-b1-m": (["approve"] * 3, "none", "Overdue prior report=no (default from R4)", "none"),
        "p2-b2": (["deny"] * 3, "Organization type=for-profit company (rule 2)", "none",
            "Organization type -> registered nonprofit"),
        "p2-b2-f": (["approve"] * 3, "none", "none", "none"),
    }
    rows = []
    for i, (ds, rel, ass, chg) in spec.items():
        for k, d in enumerate((over or {}).get(i, ds)):
            txt = f"Decision: {d}\nPolicy support: {rel}\nAssumptions: {ass}" + (
                    f"\nSmallest change to make this x: {chg}" if chg else "")
            rows.append({"id": i, "sample": k, "output": txt})
    return rows


def test_metrics():
    """
    Checks every metric and coverage count on the fixture against values computed by hand from fake_rows.
    """
    U, cov, ivs = score(RECS, fake_rows(), {"repeat": fake_rows({"p1-b1-f": ["approve"] * 3})})
    ag = aggregate(U)
    a = ag["all"]
    want = {"acc_maj": 3 / 4, "acc_mean": 2 / 3, "acc_class[approve]": 5 / 7, "acc_class[deny]": 1.0,
        "acc_class[cannot determine]": 1.0, "repeat_disagree": 1 / 12, "flip": 3 / 4, "flip[approve->deny]": 1.0,
        "flip[deny->approve]": 1 / 2, "flip_to_cd": 1 / 4, "flip_to_cd[deny->approve]": 1 / 2, "cf_pair_acc": 1 / 2,
        "flip~noise": 1 / 4, "invariance": 1 / 2, "inv_pair_acc": 1 / 2, "invariance~noise": 0.0,
        "flip|correct": 2 / 3, "flip|wrong": 1.0, "expl_valid": 2 / 11, "expl_minimal": 2 / 10,
        "cite_distractor": 1 / 12, "cite_p_nec": 11 / 12, "cite_r_nec": 35 / 132,
        "assume_dec": 1.0, "assume_val": 1.0, "none_claim_disproved": 1.0, "none_claim_unresolved": 0.0,
        "fmt_err": 3 / 36}
    for m, v in want.items():
        assert a[m]["mean"] == pytest.approx(v), m
    assert a["acc_maj"]["n"] == 4 and a["acc_maj"]["n_clus"] == 2
    assert ag["slice=combined_transfer"]["acc_mean"]["mean"] == pytest.approx(5 / 6)
    assert ag[evaluate.PRIMARY]["acc_maj"]["mean"] == pytest.approx(1 / 2)
    assert (cov["none_claim_disproved"], cov["parse_fail"], cov["fmt_err"], cov["items_scored"],
            cov["expl_uncertified"]) == (3, 0, 3, 12, 3)
    edits = {"p1-b2|boundary|noise_rating_db=65 dB": ("approve", "approve"),
        "p2-b1|boundary|amount_credits=25,000 credits;project_region=outside": ("deny", "approve"),
        "p2-b2|boundary|org_type=registered nonprofit": ("approve", "deny"),
        "p1-b2|necessity|site_zone": ("approve", "approve"), "p1-b2|necessity|noise_rating_db": ("approve", "deny"),
        "p2-b2|necessity|org_type": ("approve", "approve")}
    assert {i["iid"] for i in ivs} == set(edits)
    recs = dict(RECS)
    for iv in ivs:
        b = iv["id"]
        recs[iv["iid"]] = RECS[b] | {"id": iv["iid"], "gold": RECS[b]["gold"] | {"decision": edits[iv["iid"]][0]},
                "intervention": {"base": b} | iv}
    bank = [{"bank_id": f"{c}|{k}", "kind": k, "case_id": c, "edited_id": e, "edits": {}, "oracle": o}
        for c, k, e, o in (("p1-b1", "pivotal_replace", "p1-b1-f", "deny"), ("p2-b1", "invariant_replace", "p2-b1-i",
        "approve"), ("p1-b1", "remove", "p1-b1-m", "cannot determine"), ("p2-b1-m", "add", "p2-b1", "approve"))]

    def pr(bid, d, eid=None):
        """
        Returns one predict row for bank item bid with predicted decision d, echoing eid as the Edit ID.
        """
        return {"id": bid, "sample": 0, "output": f"Edit ID: {eid or bid}\nPredicted decision after edit: {d}"}

    aux = {"answers": [{"id": i, "sample": 0, "output": f"Decision: {e[1]}"} for i, e in edits.items()],
        "predict": [pr("p1-b1|pivotal_replace", "deny"), pr("p2-b1|invariant_replace", "deny"),
            {"id": "p1-b1|remove", "sample": 0, "output": "it depends"}, pr("p2-b1-m|add", "deny")],
        "predict_noacc": [pr("p1-b1|pivotal_replace", "deny", "zzz"), pr("p2-b1|invariant_replace", "deny"),
            pr("p1-b1|remove", "cannot determine"), pr("p2-b1-m|add", "approve")]}
    U, cov, _ = score(recs, fake_rows(), aux, bank)
    a = aggregate(U)["all"]
    for m, v in {"bnd_both": 1 / 3, "bnd_oracle_only": 2 / 3, "bnd_model_only": 0.0, "bnd_neither": 0.0,
            "bnd_oracle_minimal": 2 / 3, "necessity_flip": 3 / 4, "necessity_flip[interaction]": 1 / 2,
            "acc_maj": 3 / 4, "self_S": 1 / 2,
            "self_S[pivotal_replace]": 1.0, "self_S_noacc": 1 / 4, "self_G": -1 / 4, "self_V": 1 / 4,
            "bank_unchanged": 0.0}.items():
        assert a[m]["mean"] == pytest.approx(v), m
    assert cov["predict_parse_fail"] == 1


def test_failures():
    """
    Checks that truncated outputs (finish "length", unclosed think block) score as failures in pairs and accuracy,
    and that approve/deny words win over "cannot determine" in a decision line.
    """
    rows = fake_rows()
    for r in rows:
        r |= ({"finish": "length"} if r["id"] == "p2-b2-f" else
                {"output": "<think>still going"} if r["id"] == "p1-b1-i" else {})
    U, cov, _ = score(RECS, rows, {})
    a = aggregate(U)["all"]
    assert (a["flip"]["mean"], a["invariance"]["mean"], a["acc_class[approve]"]["mean"]) == pytest.approx(
            (1 / 2, 0.0, 3 / 7))
    assert (cov["truncated"], cov["parse_fail"], cov["flip_parse_fail_pairs"]) == (6, 6, 1)
    assert [norm_dec(x) for x in ("cannot determine whether to approve", "approve or deny", "insufficient facts",
            "Deny.")] == ["approve", None, "cannot determine", "deny"]


def test_bank_and_prompts():
    """
    Checks the bank's kind counts on the fixture (40/30/15/15 scaled to the 2 invariant items), its oracle labels,
    determinism, and that both prompts carry the target label, the frozen answer and the Edit ID.
    """
    bk = build_bank(list(RECS.values()))
    assert sorted((b["kind"] for b in bk)) == ["add", "invariant_replace", "invariant_replace", "pivotal_replace",
        "pivotal_replace", "pivotal_replace", "remove"]
    assert all(b["oracle"] == RECS[b["edited_id"]]["gold"]["decision"] for b in bk) and bk == build_bank(
        list(RECS.values()))
    assert "Smallest change to make this deny:" in build_prompt(RECS["p1-b1"])[1]
    it = next(b for b in bk if b["kind"] == "remove")
    u = build_prompt(RECS[it["case_id"]], it, "Decision: approve\nPolicy support: x=y (R2)")[1]
    assert f"Edit ID: {it['bank_id']}" in u and "Policy support: x=y (R2)" in u and "is no longer stated" in u


def test_select():
    """
    Checks that checkpoint selection drops checkpoints more than 3 points from the control's accuracy.
    """
    res = {c: {"slice=dev": {"acc_maj": {"mean": acc}, "self_V": {"mean": v}}} for c, acc, v in
            (("ctrl", 0.70, None), ("c1", 0.72, 0.10), ("c2", 0.60, 0.40), ("c3", 0.69, 0.20))}
    best, rule = select_ckpt(res, ["c1", "c2", "c3"], "ctrl")
    assert best == "c3" and "eligible ['c1', 'c3']" in rule


def test_boot():
    """
    Checks that the bootstrap CI repeats under one seed, moves under another, brackets the mean, collapses on
    constant data, and gives a zero-width CI for a paired difference of identical runs.
    """
    rng = np.random.default_rng(1)
    v, cl = rng.random(60), [f"p{i % 12}" for i in range(60)]
    r0, r1, r2 = boot(v, cl, seed=0), boot(v, cl, seed=0), boot(v, cl, seed=7)
    assert r0 == r1 and r0["lo"] != r2["lo"]
    assert r0["lo"] < r0["mean"] < r0["hi"] and r0["n_clus"] == 12
    c = boot([0.5] * 10, ["a", "b"] * 5)
    assert c["lo"] == c["hi"] == 0.5
    assert boot(v - v, cl)["hi"] == 0.0
    assert boot([float("nan")], ["a"])["n"] == 0
