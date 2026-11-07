"""
Tests evaluate.py and the data-side helpers of infer.py: the output parser on messy model text, every metric on the
12-record fixture against hand-computed values (fake run, repeat, answer and prediction outputs are written here),
simulator and self-prediction scores, the prompts, the --slice/--view/--cases filter and the Vertex cache key of
infer.py, and on data/smoke.jsonl the intervention bank mix, the SFT target format and cited-value canonicalization,
then checkpoint selection and bootstrap determinism under a seed.
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
import engine  # noqa: E402
import gen  # noqa: E402
from infer import (CHANGE, PROPS, Runner, build_bank, build_prompt, format_target, select_recs,  # noqa: E402
        shuffle_partners)

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

    ks = [b["bank_id"] for b in bank]
    aux = {"answers": [{"id": i, "sample": 0, "output": f"Decision: {e[1]}"} for i, e in edits.items()],
        "predict": [pr("p1-b1|pivotal_replace", "deny"), pr("p2-b1|invariant_replace", "deny"),
            {"id": "p1-b1|remove", "sample": 0, "output": "it depends"}, pr("p2-b1-m|add", "deny")],
        "predict_noacc": [pr("p1-b1|pivotal_replace", "deny", "zzz"), pr("p2-b1|invariant_replace", "deny"),
            pr("p1-b1|remove", "cannot determine"), pr("p2-b1-m|add", "approve")]}
    for k, ds in (("simulate", ["deny", "approve", "cannot determine", "approve"]),
            ("simulate_noacc", ["approve", "deny", "cannot determine", "deny"]), ("simulate_shuf", ["approve"] * 4)):
        aux[k] = [pr(i, d) for i, d in zip(ks, ds)]
    U, cov, _ = score(recs, fake_rows(), aux, bank)
    a = aggregate(U)["all"]
    for m, v in {"bnd_both": 1 / 3, "bnd_oracle_only": 1 / 3, "bnd_model_only": 1 / 3, "bnd_neither": 0.0,
            "bnd_oracle_minimal": 2 / 3, "bnd_invalid": 0.0, "bnd_both[vs_gold]": 1 / 3,
            "bnd_oracle_only[vs_gold]": 2 / 3, "bnd_model_only[vs_gold]": 0.0, "bnd_oracle_minimal[vs_gold]": 2 / 3,
            "necessity_flip": 3 / 4, "necessity_flip[interaction]": 1 / 2, "acc_maj": 3 / 4, "self_S": 1 / 2,
            "self_S[pivotal_replace]": 1.0, "self_S_noacc": 1 / 4, "self_G": -1 / 4, "self_V": 1 / 4,
            "bank_unchanged": 0.0, "sim_acct": 3 / 4, "sim_noacc": 1 / 2, "sim_shuf": 1 / 4, "sim_delta": 1 / 2,
            "sim_delta[pivotal_replace]": 1.0, "sim_delta[invariant_replace]": 0.0, "sim_delta[add]": 0.0,
            "sim_gross": 1 / 4, "sim_gross[add]": -1.0}.items():
        assert a[m]["mean"] == pytest.approx(v), m
    assert (cov["predict_parse_fail"], cov["simulate_parse_fail"], cov["bank_unscored"]) == (1, 0, 0)


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


def test_prompts():
    """
    Checks that the decision prompt names no target label (its instructions are identical for a gold-approve and a
    gold-deny case with the same labels), and that the predict and simulate prompts carry the frozen answer and the
    Edit ID, the simulate prompt without the case text.
    """
    tail = [build_prompt(RECS[i])[1].split(RECS[i]["case_text"].strip())[1] for i in ("p1-b1", "p1-b2")]
    assert RECS["p1-b1"]["gold"]["target"] == "deny" and RECS["p1-b2"]["gold"]["target"] == "approve"
    assert tail[0] == tail[1] and f"{CHANGE}:" in tail[0] and "make this" not in tail[0]
    it = {"bank_id": "p1-b1|remove", "kind": "remove", "edits": {"site_zone": None}}
    for sim in (False, True):
        u = build_prompt(RECS["p1-b1"], it, "Decision: approve\nPolicy support: x=y (R2)", sim)[1]
        assert f"Edit ID: {it['bank_id']}" in u and "Policy support: x=y (R2)" in u and "is no longer stated" in u
        assert (RECS["p1-b1"]["case_text"].strip() in u) != sim


def test_select():
    """
    Checks that checkpoint selection drops checkpoints more than 3 points from the control's accuracy and maximizes
    sim_delta by default, self_V when asked.
    """
    res = {c: {"slice=dev": {"acc_maj": {"mean": acc}, "sim_delta": {"mean": d}, "self_V": {"mean": v}}} for c, acc,
            d, v in (("ctrl", 0.70, None, None), ("c1", 0.72, 0.10, 0.30), ("c2", 0.60, 0.40, 0.50),
            ("c3", 0.69, 0.20, 0.10))}
    best, rule = select_ckpt(res, ["c1", "c2", "c3"], "ctrl")
    assert best == "c3" and "eligible ['c1', 'c3']" in rule and "highest sim_delta" in rule
    assert select_ckpt(res, ["c1", "c2", "c3"], "ctrl", met="self_V")[0] == "c1"


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


def test_select_recs():
    """
    Checks that --slice and --view filter records, and that --cases K keeps K whole base cases (every variant along),
    spread over both domains before a second case of either, the same under one seed.
    """
    recs = list(RECS.values())
    fam = {"p1-b1": ["p1-b1", "p1-b1-f", "p1-b1-i", "p1-b1-m"], "p1-b2": ["p1-b2", "p1-b2-f"],
        "p2-b1": ["p2-b1", "p2-b1-f", "p2-b1-i", "p2-b1-m"], "p2-b2": ["p2-b2", "p2-b2-f"]}
    assert {r["id"] for r in select_recs(recs, "unseen_family_train_vocab")} == {r["id"] for r in recs if
            r["id"].startswith("p2")}
    assert select_recs(recs, view="table") == [] and select_recs(recs) == recs
    for k in (1, 2, 4):
        got = [r["id"] for r in select_recs(recs, cases=k)]
        bases = [i for i in got if i in fam]
        assert len(bases) == k and sorted(got) == sorted(i for b in bases for i in fam[b])
        assert k != 2 or {b[:2] for b in bases} == {"p1", "p2"}
        assert got == [r["id"] for r in select_recs(recs, cases=k)]
    assert {r["id"] for r in select_recs(recs, "unseen_family_train_vocab", "prose", 1)} in ({*fam["p2-b1"]},
            {*fam["p2-b2"]})


def test_vertex_cache_key():
    """
    Checks that the cache key separates the Vertex and API-key gemini backends and keeps the old key without Vertex.
    """
    dec = {"temperature": 0.0, "top_p": 1.0, "top_k": 0, "max_tokens": 64, "seed": 0, "thinking": False}
    ks = []
    for vx in (None, "global", "us-central1"):
        r = Runner.__new__(Runner)
        r.backend, r.base_url, r.model, r.extra, r.rep = "gemini", None, "m", {}, 0
        r.tag = f"gemini/vertex:{vx}" if vx else "gemini"
        ks.append(r.key("s", "p", dec))
    assert len(set(ks)) == 3


SMOKE = ROOT / "data/smoke.jsonl"


@pytest.mark.skipif(not SMOKE.exists(), reason="needs data/smoke.jsonl")
def test_to_val(monkeypatch):
    """
    Checks that cited case-file renderings (dates, years for "ago", money, thousands, display names, derived numbers)
    map to engine values on the first grant policy, and that off-grid dates become day offsets.
    """
    monkeypatch.undo()
    rec = next(r for r in map(json.loads, SMOKE.read_text().splitlines()) if r["domain"] == "grant")
    pol = evaluate.policy(rec)
    got = {(n, v): evaluate.to_val(pol, n, v) for n, v in (("start_day", "January 4, 2027"),
            ("start_day", "2027-01-18"), ("end_day", "January 5, 2027"), ("pi_years_since_phd", "2024"),
            ("institution_type", "teaching hospital"), ("equipment_amount", "$30,000"),
            ("requested_amount", "40 thousand dollars"), ("duration_weeks", "34 weeks"), ("human_subjects", "no"))}
    assert list(got.values()) == [0, 14, 1, 3, "hospital", 30000, 40000, 34, "no"]
    for n, v in (("institution_type", "not a hospital"), ("duration_weeks", "more than 34"), ("pi_years_since_phd",
            "under 3")):
        assert evaluate.to_val(pol, n, v) == v


@pytest.mark.skipif(not SMOKE.exists(), reason="needs data/smoke.jsonl")
def test_bank(monkeypatch):
    """
    Checks the bank on the primary population of the smoke data: the 40/30/15/15 mix within one item, unique ids,
    determinism, engine oracles on every edited case, and pivotal edits that are certified flips independent of
    gold.min_flip (a different fact set, no shared edit). Also checks that bank_recs keys each edited case by
    edited_id under its base.
    """
    monkeypatch.undo()
    recs = select_recs([json.loads(ln) for ln in SMOKE.read_text().splitlines()], "unseen_family_train_vocab", "prose")
    bk, meta = build_bank(recs)
    by, grp = {r["id"]: r for r in recs}, {"noncrossing_replace": "invariant", "invariant_replace": "invariant"}
    assert bk and (bk, meta) == build_bank(recs) and len({b["bank_id"] for b in bk}) == len(bk)
    for gk, p in PROPS.items():
        assert abs(sum(grp.get(b["kind"], b["kind"]) == gk for b in bk) - p * len(bk)) <= 1, gk
    br = evaluate.bank_recs(bk, by)
    for b in bk:
        e = br.get(b["edited_id"]) or by[b["edited_id"]]
        pol = gen.policy_for(by[b["case_id"]])
        assert b["oracle"] == e["gold"]["decision"] == engine.decide(pol, e["facts"])["decision"], b["bank_id"]
        if b["kind"] == "pivotal_replace":
            g = by[b["case_id"]]["gold"]
            gold = (g.get("min_flip") or {}).get("edits") or {}
            assert b["oracle"] == engine.flip_target(g["decision"]) and set(b["edits"]) != set(gold)
            assert not any(gold.get(n) == v for n, v in b["edits"].items())
        if b["kind"] == "noncrossing_replace":
            assert b["oracle"] == by[b["case_id"]]["gold"]["decision"]
    assert all(r["parent"] == next(b["case_id"] for b in bk if b["edited_id"] == i) for i, r in br.items())


@pytest.mark.skipif(not SMOKE.exists(), reason="needs data/smoke.jsonl")
def test_format_target(monkeypatch):
    """
    Checks that the SFT target puts the decision first, parses with no missing line back to the gold decision, and
    for a settled decision cites a policy support the engine accepts as a valid justification.
    """
    monkeypatch.undo()
    recs = [r for r in map(json.loads, SMOKE.read_text().splitlines()) if r["variant"] == "base"][:40]
    for r in recs:
        t = format_target(r)
        p, pol = parse(t), evaluate.policy(r)
        assert t.startswith(f"Decision: {r['gold']['decision']}\n") and p["dec"] == r["gold"]["decision"], r["id"]
        assert p["miss"] == [] and not p["err"] and f"\n{CHANGE}: " in t
        if r["gold"]["decision"] != "cannot determine" and not r["gold"].get("uncertified"):
            lab = r.get("fact_labels", {})
            cit = {n: evaluate.to_val(pol, n, v) for l, v, _ in p["relied"] if (n := evaluate.to_name(l, lab))}
            ass = {n: evaluate.to_val(pol, n, v) for l, v, _ in p["assume"] if (n := evaluate.to_name(l, lab))}
            j = engine.is_valid_justification(pol, r["facts"], cit, [x for _, _, x in p["relied"] if x], ass)
            assert j["valid"], (r["id"], t, j)


@pytest.mark.skipif(not SMOKE.exists(), reason="needs data/smoke.jsonl")
def test_shuffle_partners(monkeypatch):
    """
    Checks on sparse samples of the smoke primary population that every bank item gets a shuffle partner under the
    same policy whose base case differs from the item's, that a frozen answer is preferred and the gold account
    (format_target) fills in when none qualifies, and that the draw is deterministic under the seed.
    """
    monkeypatch.undo()
    recs = [json.loads(ln) for ln in SMOKE.read_text().splitlines()]
    by, base, srcs = {r["id"]: r for r in recs}, lambda r: (r.get("parent") or r["id"]).rsplit(":", 1)[0], set()
    for n in (4, 10, 0):
        sel = select_recs(recs, "unseen_family_train_vocab", "prose", n)
        bk = build_bank(sel)[0]
        br = evaluate.bank_recs(bk, by)
        cs = by | br
        fz = {r["id"]: f"Decision: deny ({r['id']})" for r in sel} | {i: f"Decision: approve ({i})" for i in br}
        sp = shuffle_partners(fz, cs, by, 1)
        assert bk and sp == shuffle_partners(fz, cs, by, 1)
        for b in bk:
            t, src, j = sp[b["case_id"]]
            c, p = by[b["case_id"]], cs[j]
            assert p["policy_id"] == c["policy_id"] and base(p) != base(c), (b["bank_id"], j)
            assert t == (fz[j] if src == "frozen" else format_target(p)), (b["bank_id"], src)
            srcs.add(src)
    assert srcs == {"frozen", "gold"}
