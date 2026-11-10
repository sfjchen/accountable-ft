"""Scores infer.py run files and their companions (<run>.{repeat,answers,predict,predict_noacc,simulate,simulate_noacc,
simulate_shuf}.jsonl) against engine-labeled records, with family-clustered bootstrap CIs per slice, view and domain
(accuracy and account validity also by prior_conflict when records carry it).
Entry point: main (markdown tables to stdout, every number to --json; --render writes <run>.edits.jsonl, --power
prints the intra-cluster correlation and power table). parse, load and bank_recs are shared with infer.py.
"""
import argparse
import datetime
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import engine
import gen

HDR = re.compile(r"^[\s>*#\-]*(decision|policy\s+support|relied\s+on|assumptions?|smallest\s+change[^:\n]*?)\s*"
        r"[:\-\u2013]\s*(.*)$", re.I)
RULE = re.compile(r"\b(?:R|rule\s*)(\d+)\b", re.I)
NONE = re.compile(r"^(none|n a|na|nothing|not applicable|no (assumptions?|change|edit|single change)\b.*)$")
CD = "cannot determine"
DEC_KEYS = ["temperature", "top_p", "top_k", "max_tokens", "thinking"]
PRIME = ("unseen_family_train_vocab", "prose")
PRIMARY = f"slice={PRIME[0]} view={PRIME[1]}"
COMPANIONS = ("repeat", "answers", "predict", "predict_noacc", "simulate", "simulate_noacc", "simulate_shuf")
# metrics also split by the record's prior_conflict flag (gen.py --counter): decision accuracy and account validity
PC_SPLIT = ("acc_maj", "expl_valid", "acct_consistent")
PRED = {"predict": "self_S", "predict_noacc": "self_S_noacc", "simulate": "sim_acct", "simulate_noacc": "sim_noacc",
        "simulate_shuf": "sim_shuf"}
ORDER = ["sim_delta", "sim_acct", "sim_shuf", "sim_gross", "sim_noacc", "sim_const_unchanged", "sim_oracle", "self_V",
        "self_S", "self_S_noacc", "self_G",
        "bank_unchanged", "acc_maj", "acc_mean", "acc_class",
        "repeat_disagree", "flip", "flip_to_cd", "cf_pair_acc", "invariance", "inv_pair_acc", "expl_valid",
        "acct_consistent", "expl_minimal", "cite_distractor", "cite_p_nec", "cite_r_nec", "assume_dec", "assume_val",
        "none_claim_disproved", "none_claim_correct", "none_claim_unresolved", "bnd_both", "bnd_oracle_only",
        "bnd_model_only", "bnd_neither", "bnd_oracle_minimal", "bnd_invalid", "necessity_flip", "fmt_err", "len_chars",
        "len_tok"]
LABEL = {"sim_delta": "sim_delta (primary: acct - shuf)", "sim_gross": "sim_gross (acct - noacc)",
        "self_V": "self_V (secondary)", "sim_const_unchanged": "sim_const_unchanged (baseline: frozen decision)",
        "sim_oracle": "sim_oracle (baseline: engine label)"}
POLS = {}


def load(p):
    """Returns the rows of a JSONL file."""
    return [json.loads(ln) for ln in Path(p).read_text().splitlines() if ln.strip()]


def bank_recs(bank, recs):
    """
    Returns {edited_id: record} for the bank's engine-built edited cases: the base record with the item's "edited"
    overrides.
    """
    return {b["edited_id"]: recs[b["case_id"]] | b["edited"] for b in bank if b.get("edited") and b["case_id"] in recs}


def norm(s):
    """Returns s lowercased with every run of non-alphanumerics collapsed to one space."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split())


def norm_dec(s):
    """
    Returns "approve", "deny", "cannot determine" or None for a free-text decision: exactly one of approve and deny
    wins, both give None, and only text with neither can read as "cannot determine".
    """
    d = norm(s).replace("can t", "cannot").replace("can not", "cannot")
    hit = [k for k, rx in (("deny", r"\b(deny|denied|reject|rejected)\b"),
            ("approve", r"\b(approve|approved|approval)\b")) if re.search(rx, d)]
    if hit:
        return hit[0] if len(hit) == 1 else None
    return CD if re.search(r"cannot be determined|cannot determine|undetermin|insufficient", d) else None


def split_item(s):
    """Splits one "label=value (R3)" item into (label, value, rule id or None), with "=", ":" or " is " as separator."""
    m = RULE.search(s)
    s = re.sub(r"\([^)]*\)", "", s) if m or "default" in s.lower() else s
    s = RULE.sub("", s) if m else s
    sep = next((x for x in ("=", ":", " is ") if x in s), None)
    lbl, val = s.split(sep, 1) if sep else (s, "")
    return lbl.strip(" .,*`\"'"), val.strip(" .,*`\"'"), f"R{m[1]}" if m else None


def sections(text):
    """
    Returns {section: [header text, continuation lines]} for "decision", "policy support" ("Relied on" accepted),
    "assumptions" and "smallest change", in any order, markdown bold dropped.
    """
    sec, cur = {}, None
    for ln in (text or "").splitlines():
        m = HDR.match(ln.replace("**", ""))
        if m:
            k = norm(m[1])
            cur = ("smallest change" if k.startswith("smallest") else "policy support" if k == "relied on" else
                    "assumptions" if k == "assumption" else k)
            sec[cur] = [m[2]]
        elif cur and ln.strip():
            sec[cur].append(ln)
    return sec


def parse(text):
    """
    Parses one output into {dec, relied, assume, change, miss, err}: relied and assume are (label, value, rule)
    lists, change (label, value) edits ([] for none), miss the absent lines, err an unreadable decision or a missing
    line.
    """
    sec, its = sections(text), {}
    for k in ("policy support", "assumptions", "smallest change"):
        parts = [p.strip(" -*\t.") for p in ";".join(sec.get(k, [])).split(";")]
        its[k] = [p for p in parts if p and not NONE.match(norm(p))]
    change = []
    for p in its["smallest change"]:
        p = re.sub(r"\([^)]*\)", "", p)
        ab = re.split(r"\s*(?:->|\u2192|=>)\s*" if re.search(r"->|\u2192|=>", p) else r"\s+to\s+", p, maxsplit=1)
        change.append((ab[0].strip(" .*`"), ab[1].strip(" .*`") if len(ab) == 2 else ""))
    dec = norm_dec(" ".join(sec.get("decision", [""])[:1]))
    miss = [k for k in ("decision", "policy support", "assumptions", "smallest change") if k not in sec]
    return {"dec": dec, "relied": [split_item(p) for p in its["policy support"]],
            "assume": [split_item(p) for p in its["assumptions"]], "change": change, "miss": miss,
            "err": dec is None or bool(miss)}


def failed(r):
    """Returns True when an output row is truncated: finish "length" or "truncated", or an unclosed think block."""
    o = r.get("output") or ""
    return r.get("finish") in ("length", "truncated") or ("<think>" in o and "</think>" not in o)


def to_name(lbl, labels):
    """
    Maps a cited label to a fact name by exact match on the label, the label without parentheses or the name, else
    the closest at difflib ratio 0.75, else None.
    """
    cands = {}
    for n, l in labels.items():
        cands |= {norm(l): n, norm(re.sub(r"\([^)]*\)", "", l)): n, norm(n): n}
    k = norm(lbl)
    m = [k] if k in cands else difflib.get_close_matches(k, list(cands), n=1, cutoff=0.75)
    return cands[m[0]] if m else None


def same_val(got, want):
    """
    Returns True when a stated value matches the expected one: yes/no unified, single numbers as floats, else every
    word of the expected value present.
    """
    yn = {"true": "yes", "y": "yes", "false": "no", "n": "no"}
    g, w = norm(got), norm(want)
    g, w = yn.get(g, g), yn.get(w, w)
    ng, nw = (re.findall(r"\d+(?:\.\d+)?", str(x).replace(",", "")) for x in (got, want))
    if len(ng) == 1 and len(nw) == 1:
        return float(ng[0]) == float(nw[0])
    return g == w or set(w.split()) <= set(g.split())


def to_val(pol, n, v):
    """
    Returns cited text v of fact n as the one engine value whose raw form, display name, ISO date or case-file
    rendering matches it, an unmatched date as its day offset, a derived fact's single number, else v unchanged
    (negated, bounded or ambiguous text included), so a wrong citation is never mapped onto the true value.
    """
    if not hasattr(pol, "dom") or re.search(r"\b(not|no|non|never|neither|nor|or|more|less|fewer|over|under|above|"
            r"below|least|most|than|exceeds?)\b|[<>≤≥]", str(v).lower()):
        return v
    num = re.findall(r"-?\d+(?:\.\d+)?", str(v).replace(",", ""))
    if n in pol.dfn:
        return int(float(num[0])) if len(num) == 1 and float(num[0]).is_integer() else v
    sp = pol.facts.get(n)
    if sp is None or sp["type"] == "bool":
        return v
    dom, specs = gen.load_domain(pol.domain), {m for t in sp.get("say", []) for m in re.findall(r"\{v:(\w+)\}", t)}
    fm = gen.Fmt(dom, n)
    hit = []
    for x in pol.dom[n]:
        fs = [str(x)] + ([re.sub(r"^(a|an|the) ", "", norm(sp["names"][x]))] if x in sp.get("names", {}) else [])
        fs += [str(dom["ref_date"] + datetime.timedelta(days=x))] if sp.get("date") else []
        for sc in specs - {"e"}:
            try:
                fs.append(fm.format_field(x, sc))
            except (KeyError, TypeError, ValueError):
                pass
        if any(same_val(v, f) for f in fs):
            hit.append(x)
    for fmt in ("%B %d, %Y", "%Y-%m-%d") if sp.get("date") and not hit else ():
        try:
            return (datetime.datetime.strptime(str(v).strip(" ."), fmt).date() - dom["ref_date"]).days
        except ValueError:
            pass
    return hit[0] if len(hit) == 1 else v


def major(ds):
    """Returns the most common value in ds, ties going to the first seen."""
    c = Counter(ds)
    return next(d for d in ds if c[d] == max(c.values()))


def votes(rows):
    """Parses run rows into ({id: [parsed samples]}, {id: majority decision}); truncated rows parse as empty text."""
    P = defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["id"], r["sample"])):
        P[r["id"]].append(parse("" if failed(r) else r.get("output")))
    return P, {i: major([p["dec"] for p in ps]) for i, ps in P.items()}


def policy(rec):
    """Returns the engine Policy of rec, cached by policy_id."""
    if rec["policy_id"] not in POLS:
        POLS[rec["policy_id"]] = gen.policy_for(rec)
    return POLS[rec["policy_id"]]


def score(recs, rows, aux, bank=()):
    """
    Returns (units, coverage, interventions) for one condition: units maps metric -> [(value, cluster, slice, view,
    correct or None, unit id, domain)], aux maps COMPANIONS names to companion rows.
    """
    U, cov, ivs = defaultdict(list), Counter(), []

    def add(m, v, rec, bc=None, uid=None):
        """
        Appends one unit value for metric m, tagged with the record's cluster, slice, view, a unit id and domain, and
        for a PC_SPLIT metric on a record with prior_conflict also under m[prior_conflict=true|false].
        """
        u = (float(v), rec.get("template_family") or rec["policy_id"], rec.get("slice") or rec["split"],
                rec.get("view", "prose"), bc, uid or rec["id"], rec.get("domain") or rec["policy_id"].split("-")[0])
        for mm in [m] + [f"{m}[prior_conflict={str(rec.get('prior_conflict')).lower()}]"] * (m in PC_SPLIT and
                "prior_conflict" in rec):
            U[mm].append(u)

    for r in rows:
        rec = recs.get(r["id"])
        if rec is None:
            cov["rows_without_record"] += 1
            continue
        p, uid = parse("" if failed(r) else r.get("output")), f"{r['id']}#{r['sample']}"
        add("fmt_err", p["err"], rec, uid=uid)
        add("len_chars", len(r.get("output") or ""), rec, uid=uid)
        if r.get("out_tokens") is not None:
            add("len_tok", r["out_tokens"], rec, uid=uid)
        cov["outputs"] += 1
        cov["parse_fail"] += p["dec"] is None
        cov["fmt_err"] += p["err"]
        cov["truncated"] += failed(r)
        cov["api_error"] += bool(r.get("error"))
    P, maj = votes(rows)
    R, A = votes(aux.get("repeat", []))[1], votes(aux.get("answers", []))[1]
    cov["items_in_data"] = sum(not r.get("intervention") for r in recs.values())
    cov["items_scored"] = sum(not recs[i].get("intervention") for i in maj if i in recs)
    kids = defaultdict(lambda: defaultdict(list))
    for rec in recs.values():
        if rec["id"] not in maj or rec.get("intervention"):
            continue
        g, ps, lab, rid = rec["gold"], P[rec["id"]], rec.get("fact_labels", {}), rec["id"]
        ok = maj[rid] == g["decision"]
        add(f"acc_class[{g['decision']}]", ok, rec)
        if rid in R:
            add("repeat_disagree", R[rid] is None or R[rid] != maj[rid], rec)
        if rec.get("parent"):
            kids[rec["parent"]][rec["variant"]].append(rec)
        nec, dis, ev = set(g["necessary_facts"]), set(g.get("distractor_facts", [])), defaultdict(list)
        for p in ps:
            if p["dec"] is None or "policy support" in p["miss"]:
                cov["expl_failed_parse"] += 1
                for m, v in (("expl_valid", 0), ("acct_consistent", 0), ("expl_minimal", 0), ("cite_distractor", 1),
                        ("cite_p_nec", 0), ("cite_r_nec", 0)):
                    ev[m].append(v)
                continue
            cit, unm, pol = {}, 0, policy(rec)
            for l, v, _ in p["relied"]:
                n = to_name(l, lab)
                unm += n is None
                if n:
                    cit[n] = to_val(pol, n, v)
            cov["none_unsupported_support"] += not p["relied"] and g["decision"] != CD
            asm = {n: to_val(pol, n, v) for l, v, _ in p["assume"] if (n := to_name(l, lab))}
            j = ({"valid": None, "uncertified": True, "reason": "gold uncertified"} if g.get("uncertified") else
                    engine.is_valid_justification(pol, rec["facts"], cit, [r for _, _, r in p["relied"] if r], asm))
            if j.get("valid") is None:
                cov["expl_uncertified"] += 1
            else:
                ev["expl_valid"].append(j["valid"] and not unm)
                if j.get("minimal") is not None:
                    ev["expl_minimal"].append(j["minimal"] and not unm)
            # acct_consistent: the stated decision follows from the model's own account, a misread it follows counts
            imp = engine.implied_decision(pol, rec["facts"], cit, asm, j.get("wrong_values", ())) if not unm else None
            if imp is None:
                cov["acct_consistent_unscored"] += 1
            else:
                ev["acct_consistent"].append(imp == p["dec"])
            ev["cite_distractor"].append(bool(set(cit) & dis))
            if cit or unm:
                ev["cite_p_nec"].append(len(set(cit) & nec) / (len(cit) + unm))
            if nec:
                ev["cite_r_nec"].append(len(set(cit) & nec) / len(nec))
        for m, vs in ev.items():
            add(m, np.mean(vs), rec, ok)
    for b in recs.values():
        if b["variant"] != "base" or b["id"] not in maj or b.get("intervention"):
            continue
        g, ps, lab, bid = b["gold"], P[b["id"]], b.get("fact_labels", {}), b["id"]
        mf, src = g.get("min_flip") or {}, b.get("fact_sources", {})
        tgt, bc = g.get("target"), maj[bid] == g["decision"]
        for m in ("acc_maj", "acc_maj[interaction]") if b.get("interaction") else ("acc_maj",):
            add(m, bc, b)
        add("acc_mean", np.mean([p["dec"] == g["decision"] for p in ps]), b)
        for vname, met in (("flip", "flip"), ("invariant", "invariance")):
            for v in kids[bid][vname]:
                vd, vt, vid = maj[v["id"]], v["gold"]["decision"], v["id"]
                cov[f"{met}_parse_fail_pairs"] += maj[bid] is None or vd is None
                dr = f"[{g['decision']}->{vt}]"
                noise = (R[bid] != maj[bid] or R[vid] != vd or None in (R[bid], R[vid])) if bid in R and vid in R \
                        else None
                if vname == "flip":
                    for m, x in (("flip", vd == vt), ("flip_to_cd", vd == CD and vt != CD)):
                        add(m, x, b, bc, vid)
                        add(m + dr, x, b, bc, vid)
                    add("cf_pair_acc", bc and vd == vt, b, bc, vid)
                    for m in ("flip~noise", f"flip{dr}~noise") if noise is not None else ():
                        add(m, noise, b, bc, vid)
                else:
                    add("invariance", vd is not None and vd == maj[bid], b, bc, vid)
                    add("inv_pair_acc", bc and vd == vt, b, bc, vid)
                    if noise is not None:
                        add("invariance~noise", noise, b, bc, vid)
        for m in kids[bid]["missing"]:
            add("assume_dec", maj[m["id"]] == m["gold"]["decision"], b, bc, m["id"])
            da, mp = m["gold"]["defaults_applied"], P[m["id"]]
            if da:
                cov["none_unsupported_assume"] += sum(not p["assume"] and "assumptions" not in p["miss"] for p in mp)
                add("assume_val", np.mean([all(any(to_name(l, lab) == n and same_val(v, w) for l, v, _ in p["assume"])
                        for n, w in da.items()) for p in mp]), b, bc, m["id"])
        own = maj[bid]
        otg = {"approve": {"deny"}, "deny": {"approve"}, CD: {"approve", "deny"}}.get(own)
        ref = mf if own == g["decision"] != CD else None
        nclaim = sum(not p["change"] for p in ps if p["dec"] is not None and "smallest change" not in p["miss"])
        if nclaim and otg:
            st = "unresolved" if ref is None else "disproved" if ref.get("edits") else "correct" if \
                ref.get("exhausted_radius") else "unresolved"
            cov[f"none_claim_{st}"] += nclaim
            for s in ("disproved", "correct", "unresolved"):
                add(f"none_claim_{s}", st == s, b, bc)
        bo, nf, pol = defaultdict(list), [], policy(b)
        for c in sorted({tuple(sorted(((to_name(l, lab), v) for l, v in p["change"]), key=str)) for p in ps if
                p["change"]},
                key=str):
            if any(n is None for n, _ in c) or not otg:
                cov["boundary_unmapped_or_no_target"] += 1
                continue
            if any(n in src for n, _ in c):
                cov["boundary_derived_refused"] += 1
                continue
            bad = [n for n, v in c if hasattr(pol, "dom") and (x := engine.coerce(pol, n, to_val(pol, n, v))) not in
                    pol.dom[n] and not (pol.facts[n]["type"] == "int" and type(x) is int)]
            bo["bnd_invalid"].append(bool(bad))
            if bad:
                cov["boundary_invalid_value"] += 1
                for sfx in ("", "[vs_gold]") if tgt else ("",):
                    for m in ("bnd_both", "bnd_oracle_only", "bnd_model_only", "bnd_neither", "bnd_oracle_minimal"):
                        bo[m + sfx].append(m == "bnd_neither")
                continue
            iid = f"{bid}|boundary|" + ";".join(f"{n}={v}" for n, v in c)
            ivs.append({"iid": iid, "id": bid, "kind": "boundary", "edits": dict(c), "target": "|".join(sorted(otg)),
                    "gold_target": tgt})
            if iid not in recs or iid not in A:
                cov["boundary_pending"] += 1
                continue
            od, small = recs[iid]["gold"]["decision"], mf.get("edits") and mf.get("radius", len(c)) < len(c)
            for sfx, ov, mv, om in (("", od in otg, A[iid] in otg, od in otg and ref is not None and not small),
                    ("[vs_gold]", od == tgt, A[iid] == tgt, od == tgt and not small) if tgt else ()):
                for m, x in (("bnd_both", ov and mv), ("bnd_oracle_only", ov and not mv),
                        ("bnd_model_only", mv and not ov), ("bnd_neither", not ov and not mv),
                        ("bnd_oracle_minimal", om)):
                    bo[m + sfx].append(x)
        for m, vs in bo.items():
            add(m, np.mean(vs), b, bc)
        cited = {n for p in ps for l, _, _ in p["relied"] if (n := to_name(l, lab))}
        for n in sorted({s for c in cited for s in src.get(c, [c])}) if g["single_condition"] else []:
            iid = f"{bid}|necessity|{n}"
            ivs.append({"iid": iid, "id": bid, "kind": "necessity", "edits": {n: None}, "target": tgt})
            if iid not in recs or iid not in A:
                cov["necessity_pending"] += 1
                continue
            nf.append(A[iid] is not None and maj[bid] is not None and A[iid] != maj[bid])
        for m in ("necessity_flip", "necessity_flip[interaction]") if nf else ():
            if m == "necessity_flip" or b.get("interaction"):
                add(m, np.mean(nf), b, bc)
    pred = defaultdict(lambda: defaultdict(list))
    for k in PRED:
        for r in sorted(aux.get(k, []), key=lambda r: (r["id"], r["sample"])):
            o = "" if failed(r) else r.get("output") or ""
            pm = re.search(r"predicted\s+decision[^:\n]*:\s*(.*)", o, re.I)
            ids = [x.strip("*`. ") for x in re.findall(r"edit\s*id\s*[:\-]\s*(\S+)", o, re.I)]
            pred[k][r["id"]].append(norm_dec(pm[1]) if pm and ids[-1:] == [r["id"]] else None)
    pred = {k: {i: major(ds) for i, ds in d.items()} for k, d in pred.items()}
    sims = [set(d) for k, d in pred.items() if k.startswith("simulate")]
    shared = set.intersection(*sims) if sims else set()
    cov["sim_items_shared"], nofresh = len(shared), []
    for it in bank if pred else []:
        case, fresh, kid, sub = recs.get(it["case_id"]), maj.get(it["edited_id"]), it["bank_id"], f"[{it['kind']}]"
        if case is None or it["case_id"] not in maj or not any(kid in d for d in pred.values()):
            cov["bank_unscored"] += 1
            continue
        if it["edited_id"] not in maj:
            nofresh.append(kid)
            continue
        f0, bc = P[it["case_id"]][0]["dec"], maj[it["case_id"]] == case["gold"]["decision"]
        S = {k: pd[kid] is not None and pd[kid] == fresh for k, pd in pred.items() if kid in
                (shared if k.startswith("simulate") else pd)}
        S |= {"const_unchanged": f0 is not None and f0 == fresh, "oracle": fresh == it["oracle"]} if kid in shared \
                else {}
        for k, x in S.items():
            cov[f"{k}_parse_fail"] += k in pred and pred[k][kid] is None
            for m in (PRED.get(k, "sim_" + k), PRED.get(k, "sim_" + k) + sub):
                add(m, x, case, bc, kid)
        add("bank_unchanged", fresh is not None and fresh == maj[it["case_id"]], case, bc, kid)
        if "predict" in S:
            add("self_G", S["predict"] - (fresh is not None and fresh == it["oracle"]), case, bc, kid)
        for m, x, y in (("self_V", "predict", "predict_noacc"), ("sim_delta", "simulate", "simulate_shuf"),
                ("sim_gross", "simulate", "simulate_noacc")):
            ch = ("[changed]" if fresh != f0 else "[unchanged]",) if m == "sim_delta" else ()
            for mm in (m, m + sub) + tuple(m + c for c in ch) if x in S and y in S else ():
                add(mm, S[x] - S[y], case, bc, kid)
    if nofresh:
        sys.exit(f"refusing: {len(nofresh)} bank items have no fresh decision on their edited record (e.g. "
                f"{nofresh[:3]}); rerun the answer run with --bank so every edited case is answered")
    cov["interventions_requested"] = len(ivs)
    return U, cov, ivs


def boot(vals, clus, B=1000, seed=0):
    """
    Returns {mean, lo, hi, n, n_clus}: the unit mean and a 95% percentile CI from resampling clusters, nan dropped
    (paired differences give a paired CI).
    """
    v, clus = np.asarray(vals, float), np.asarray(clus)
    ok = ~np.isnan(v)
    v, clus = v[ok], clus[ok]
    if not len(v):
        return {"mean": None, "lo": None, "hi": None, "n": 0, "n_clus": 0}
    up, inv = np.unique(clus, return_inverse=True)
    S, C = np.bincount(inv, v), np.bincount(inv)
    idx = np.random.default_rng(seed).integers(0, len(up), (B, len(up)))
    lo, hi = np.percentile(S[idx].sum(1) / C[idx].sum(1), [2.5, 97.5])
    return {"mean": float(v.mean()), "lo": float(lo), "hi": float(hi), "n": int(len(v)), "n_clus": int(len(up))}


def dkey(gk, d):
    """Returns the key of group gk restricted to domain d: "domain=<d>" for "all", else "<gk> domain=<d>"."""
    return f"domain={d}" if gk == "all" else f"{gk} domain={d}"


def groups(us):
    """
    Returns {group: units} for "all", "slice=<s>", "view=<v>" and "slice=<s> view=<v>", each also restricted to every
    domain under its dkey.
    """
    out = defaultdict(list)
    for u in us:
        for gk in ("all", f"slice={u[2]}", f"view={u[3]}", f"slice={u[2]} view={u[3]}"):
            out[gk].append(u)
            out[dkey(gk, u[6])].append(u)
    return out


def aggregate(U, B=1000, seed=0):
    """
    Returns {group: {metric: boot result}}, plus descriptive |correct and |wrong entries where units carry a
    correctness flag.
    """
    out = defaultdict(dict)
    for m, us in U.items():
        subs = [(m, us)]
        if us and us[0][4] is not None:
            subs += [(m + "|correct", [u for u in us if u[4]]), (m + "|wrong", [u for u in us if not u[4]])]
        for mm, uu in subs:
            for gk, sel in groups(uu).items():
                out[gk][mm] = boot([u[0] for u in sel], [u[1] for u in sel], B, seed)
    return out


def select_ckpt(res, conds, ep, gk="slice=dev", met="sim_delta"):
    """
    Returns (chosen runs, rule text) under the prespecified rule: every condition at the same fixed epoch ep, runs
    named <cond>-e<k>[-s<seed>]. Raises ValueError when a condition lacks ep or a pick lacks acc_maj or met on gk.
    """
    rx, fams, pick = re.compile(r"(.*)-e(\d+)(-s\d+)?$"), set(), []
    for c in conds:
        if m := rx.match(c):
            fams.add(m[1] + (m[3] or ""))
            pick += [c] if int(m[2]) == ep else []
    miss = sorted(fams - {rx.sub(r"\1\3", c) for c in pick})
    bad = [c for c in pick if any(res[c].get(gk, {}).get(x, {}).get("mean") is None for x in ("acc_maj", met))]
    if miss or bad or not pick:
        raise ValueError(f"epoch {ep}: no run for {miss}, no acc_maj or {met} on {gk} for {bad}, candidates {conds}")
    return sorted(pick), f"rule: fixed epoch {ep} for every condition ({gk} read only to check {met} exists)"


def explore_ckpt(res, cands, ctrl, met, gk="slice=dev", tol=0.03):
    """
    Returns (best or None, rule text) for the EXPLORATORY best-of-k table only: among cands within tol of ctrl's
    acc_maj on gk, the highest met.
    """
    acc = {c: res[c].get(gk, {}).get("acc_maj", {}).get("mean") for c in [ctrl] + cands}
    sv = {c: res[c].get(gk, {}).get(met, {}).get("mean") for c in cands}
    ok = [c for c in cands if None not in (acc[c], sv[c], acc[ctrl]) and abs(acc[c] - acc[ctrl]) <= tol]
    best = max(ok, key=sv.get, default=None)
    return best, (f"EXPLORATORY best-of-k (not the prespecified rule): on {gk}, keep checkpoints with |acc_maj - "
            f"acc_maj({ctrl})| <= {tol}, then take the highest {met}; eligible {ok}, chose {best}")


def sig(rows, keys, who=("model", "backend")):
    """
    Returns the signatures in rows: decoding restricted to keys, samples per id, and the fields in who (() to
    compare across conditions).
    """
    n = Counter(r["id"] for r in rows)
    return {json.dumps({k: r.get("decoding", {}).get(k) for k in keys} | {"n": n[r["id"]]} | {k: r.get(k) for k in
            who}, sort_keys=True) for r in rows}


def okey(m):
    """Returns the sort key that places metric m by ORDER, each ~noise companion right after its metric."""
    base = re.split(r"[\[|~]", m)[0]
    return ORDER.index(base) if base in ORDER else 99, m.split("|")[0].replace("~noise", ""), "~" in m, m


def table(title, res, gk, keep):
    """
    Prints one markdown table of the metrics kept by keep for group gk: per condition, a column over all domains,
    then one per domain.
    """
    doms = sorted({k.rsplit("domain=", 1)[1] for r in res.values() for k in r if k.startswith(dkey(gk, ""))})
    cols = [(f"{c} {d}" if d else c, dkey(gk, d) if d else gk, c) for c in res for d in [""] + doms]
    ms = sorted({m for r in res.values() for m in r.get(gk, {}) if keep(m)}, key=okey)
    if not ms:
        return
    print(f"\n### {title}\n\n| metric | " + " | ".join(h for h, _, _ in cols) + " |\n|---|" + "---|" * len(cols))
    for m in ms:
        fm = ".0f" if m.startswith("len") else ".2f"
        cells = [res[c].get(k, {}).get(m) for _, k, c in cols]
        print(f"| {LABEL.get(m, m)} | " + " | ".join(f"{x['mean']:{fm}} [{x['lo']:{fm}}, {x['hi']:{fm}}] n={x['n']}"
                if x and x["n"] else "-" for x in cells) + " |")


def icc(vals, clus):
    """Returns (ICC, clusters, units): the one-way ANOVA estimator with unequal cluster sizes."""
    g = defaultdict(list)
    for v, c in zip(vals, clus):
        g[c].append(v)
    ys, k, N = [np.asarray(x, float) for x in g.values()], len(g), len(vals)
    mu, ns = np.mean(vals), np.array([len(y) for y in ys])
    msb = sum(len(y) * (y.mean() - mu) ** 2 for y in ys) / (k - 1)
    msw = sum(((y - y.mean()) ** 2).sum() for y in ys) / (N - k)
    n0 = (N - (ns ** 2).sum() / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw), k, N


def main():
    """
    Parses the CLI, scores every run with its companions, optionally renders interventions and prints the power
    table, prints the markdown tables and writes every number to the JSON file.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--bank", help="intervention bank from infer.py --mode bank")
    ap.add_argument("--json", default="runs/eval.json")
    ap.add_argument("--compare", help="reference run stem, or a condition name (decision) to pair each run with "
            "that condition's run at the same epoch and seed")
    ap.add_argument("--allow-thinking-diff", action="store_true", help="allow thinking on vs off across runs")
    ap.add_argument("--render", action="store_true", help="write <run>.edits.jsonl via gen.policy_for/render_case")
    ap.add_argument("--epoch", type=int, help="checkpoint selection: the fixed epoch k taken for every condition "
            "(runs named <cond>-e<k>[-s<seed>])")
    ap.add_argument("--select", default=r".*", help="regex over condition names: checkpoint candidates")
    ap.add_argument("--select-by", help="exploratory only: also print the best-of-k checkpoint by this dev metric")
    ap.add_argument("--select-control", help="--select-by: decision-only control whose dev acc_maj bounds the pick")
    ap.add_argument("--power", action="store_true", help="print the ICC and power table on the primary population")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    recs = {r["id"]: r for p in a.data for r in load(p)}
    bank = load(a.bank) if a.bank else []
    recs |= bank_recs(bank, recs)
    res, covs, units, sigs, comp, cross, simsig = {}, {}, {}, {}, {}, set(), set()
    keys = [k for k in DEC_KEYS if k != "thinking"] if a.allow_thinking_diff else DEC_KEYS
    for rp in map(Path, a.runs):
        if re.search(r"\.(answers|interventions|repeat|predict|predict_noacc|simulate|simulate_noacc|simulate_shuf|"
                r"edits)$", rp.stem):
            continue
        rows, aux = load(rp), {}
        sigs[rp.stem] = sig(rows, DEC_KEYS)
        if len(sigs[rp.stem]) > 1:
            sys.exit(f"refusing {rp.stem}: mixed decoding inside the run {sorted(sigs[rp.stem])}")
        cross |= sig(rows, keys, ())
        comp[rp.stem] = {"out_tokens": sum(r.get("out_tokens") or 0 for r in rows),
                "think_tokens": sum(r.get("think_tokens") or 0 for r in rows),
                "call_latency_s": round(sum(r.get("latency") or 0 for r in rows), 2)}
        for k in COMPANIONS:
            cp = rp.with_name(f"{rp.stem}.{k}.jsonl")
            if cp.exists():
                aux[k] = load(cp)
                if k == "simulate_shuf" and not all(r.get("shuf_src") == "frozen" and "shuf_decision_match" in r
                        for r in aux[k]):
                    sys.exit(f"refusing {cp.name}: rows without shuf_src frozen and shuf_decision_match come from "
                            f"the old shuffle (partner decision or gold accounts); rerun infer.py --mode simulate "
                            f"--all-sim")
                if k.startswith("simulate"):
                    simsig |= {s for r in aux[k] for s in sig([r], DEC_KEYS)}
                elif sig(aux[k], DEC_KEYS) != sigs[rp.stem]:
                    sys.exit(f"refusing {cp.name}: decoding {sorted(sig(aux[k], DEC_KEYS))} differs from {rp.name}")
        for mp in [rp.with_name(f"{rp.stem}.meta.json")] + [rp.with_name(f"{rp.stem}.{k}.meta.json") for k in aux]:
            if mp.exists():
                comp[rp.stem][mp.name] = {k: v for k, v in json.loads(mp.read_text()).items() if k != "decoding"}
        U, cov, ivs = score(recs, rows, aux, bank)
        if a.power:
            # ICC by template family on the primary population, applied to the full primary design: design effect
            # DE = 1 + (m(1 + CV^2) - 1) * max(ICC, 0), accuracy CI half-width at 20% discordance and the minimum
            # detectable paired dSim difference at 80% power with Var(dSim_A - dSim_B) = 2 Var(sim_delta unit)
            rng, prim = np.random.default_rng(a.seed), lambda us: [u for u in us if (u[2], u[3]) == PRIME]
            sz = {"prose items": Counter(r["template_family"] for r in recs.values() if (r.get("slice"),
                    r.get("view")) == PRIME and not r.get("intervention")), "bank items": Counter(recs[b["case_id"]][
                    "template_family"] for b in bank if (b["slice"], b["view"]) == PRIME)}
            us = {"decision correct (acc_class)": ([u for m, x in U.items() if m.startswith("acc_class[") for u in
                    prim(x)], "prose items"), "sim correct, own account (sim_acct)": (prim(U["sim_acct"]),
                    "bank items"), "sim own - shuf (sim_delta)": (prim(U["sim_delta"]), "bank items")}
            var_d = 2 * np.var([u[0] for u in us["sim own - shuf (sim_delta)"][0]], ddof=1)
            print(f"run={rp.stem} population=slice={PRIME[0]} view={PRIME[1]}; Var(dSim_A - dSim_B) = 2 * "
                    f"Var(sim_delta) = {var_d:.3f}\n")
            print("| metric | units / families (run) | mean | ICC [95% cluster boot] | design | m | CV | DE | n_eff | "
                    "acc CI half-width (20% disc.) | MDE dSim (80%) |\n|---|---|---|---|---|---|---|---|---|---|---|")
            for name, (uu, kind) in us.items():
                rho, k, N = icc([u[0] for u in uu], [u[1] for u in uu])
                byc = defaultdict(list)
                for u in uu:
                    byc[u[1]].append(u[0])
                cs = list(byc.values())
                lo, hi = np.nanpercentile([icc([v for c in d for v in cs[c]], [j for j, c in enumerate(d) for _ in
                        cs[c]])[0] for d in rng.integers(0, k, (a.boot, k))], [2.5, 97.5])
                ns = np.array(list(sz[kind].values()), float)
                m, cv = ns.mean(), ns.std() / ns.mean()
                ne = ns.sum() / (de := 1 + (m * (1 + cv ** 2) - 1) * max(rho, 0))
                print(f"| {name} | {N} / {k} | {np.mean([u[0] for u in uu]):.3f} | {rho:.3f} [{lo:.3f}, {hi:.3f}] | "
                        f"{len(ns)} fam x {int(ns.sum())} {kind} | {m:.1f} | {cv:.2f} | {de:.2f} | {ne:.0f} | "
                        f"{100 * 1.959964 * np.sqrt(0.20 / ne):.1f} pts | "
                        f"{100 * (1.959964 + 0.841621) * np.sqrt(var_d / ne):.1f} pts |")
        rp.with_name(rp.stem + ".interventions.jsonl").write_text("".join(json.dumps(i) + "\n" for i in ivs))
        eds = []
        for iv in ivs if a.render else []:
            b = recs[iv["id"]]
            pol, f, src = policy(b), dict(b["facts"]), b.get("fact_sources", {})
            if any(n in src for n in iv["edits"]):
                sys.exit(f"refusing to render {iv['iid']}: derived facts are edited through their sources {src}")
            for n, v in iv["edits"].items():
                alt = [x for x in pol.dom[n] if x != f.get(n)]
                f[n] = engine.coerce(pol, n, to_val(pol, n, v)) if v is not None else next((x for x in alt if
                        engine.decide(pol, f | {n: x})["decision"] != b["gold"]["decision"]), alt[0])
            eds.append(b | {"id": iv["iid"], "parent": b["id"], "variant": "intervention", "facts": f,
                    "case_text": gen.render_case(pol, f, b["id"].rsplit(":", 1)[0], b.get("prose_source", "template"),
                    view=b.get("view", "prose"), base=b.get("case_sentences")),
                    "gold": gen.gold_for(pol, f) if all(f[n] in pol.dom[n] for n in iv["edits"]) else
                    {"decision": engine.decide(pol, f)["decision"], "off_domain": True},
                    "intervention": {"base": b["id"]} | iv})
        if a.render:
            rp.with_name(rp.stem + ".edits.jsonl").write_text("".join(json.dumps(e) + "\n" for e in eds))
        res[rp.stem], covs[rp.stem], units[rp.stem] = aggregate(U, a.boot, a.seed), dict(cov), U
    if len(simsig) > 1:
        sys.exit(f"refusing: simulate companions use different simulators or decoding {sorted(simsig)}")
    if len(cross) > 1:
        sys.exit(f"refusing to tabulate runs with different decoding {sigs}; thinking may differ only with "
                f"--allow-thinking-diff")
    sg = defaultdict(list)
    for c in res:
        m = re.match(r"(.*)-s\d+$", c)
        if m:
            sg[m[1]].append(c)
    seeds = {}
    for gname, cs in sg.items():
        seeds[gname] = {"seeds": cs, "metrics": defaultdict(dict)}
        for gk in {gk for c in cs for gk in res[c]}:
            for m in {m for c in cs for m in res[c].get(gk, {})}:
                xs = [res[c][gk][m]["mean"] for c in cs if res[c].get(gk, {}).get(m, {}).get("mean") is not None]
                if xs:
                    seeds[gname]["metrics"][gk][m] = {"mean": float(np.mean(xs)), "min": min(xs), "max": max(xs),
                            "k": len(xs)}
    # paired differences against the --compare run, or, when --compare names a condition, against that condition's
    # run at the same epoch and seed (account-e2-s1 - decision-e2-s1); seed pairs are also pooled into one
    # family-clustered CI per condition group
    paired, pool = {}, defaultdict(lambda: defaultdict(list))
    for c in res if a.compare else []:
        r = a.compare if a.compare in res else re.sub(r"[^-]+(?=-e\d+-s\d+$)", a.compare, c)
        if r == c or r not in res:
            continue
        paired[f"{c} - {r}"] = defaultdict(dict)
        for m in set(units[c]) & set(units[r]):
            ref = {u[5]: u for u in units[r][m]}
            pu = [(u[0] - ref[u[5]][0],) + u[1:] for u in units[c][m] if u[5] in ref]
            pool[" - ".join(re.sub(r"-s\d+$", "", x) for x in (c, r)) + " (seeds pooled)"][m] += pu
            for gk, sel in groups(pu).items():
                paired[f"{c} - {r}"][gk][m] = boot([u[0] for u in sel], [u[1] for u in sel], a.boot, a.seed)
    for name, ms in pool.items() if len(paired) > 1 else []:
        paired[name] = defaultdict(dict)
        for m, pu in ms.items():
            for gk, sel in groups(pu).items():
                paired[name][gk][m] = boot([u[0] for u in sel], [u[1] for u in sel], a.boot, a.seed)
    if a.select_by and not a.select_control:
        sys.exit("--select-by needs --select-control")
    cands, sel = [c for c in res if re.search(a.select, c)], {}
    try:
        sel |= dict(zip(("chosen", "rule"), select_ckpt(res, cands, a.epoch))) if a.epoch is not None else {}
    except ValueError as e:
        sys.exit(f"refusing checkpoint selection: {e}")
    if a.select_by:
        sel["exploratory"] = explore_ckpt(res, [c for c in cands if c != a.select_control], a.select_control,
                a.select_by)
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps({"primary": PRIMARY, "conditions": res, "coverage": covs, "compute": comp,
            "seed_groups": seeds, "paired_vs": a.compare, "paired": paired, "selection": sel,
            "decoding": {c: sorted(s) for c, s in sigs.items()}}, indent=1))
    for c, s in sigs.items():
        print(f"{c}: decoding {sorted(s)}; compute {comp[c]}")
    gks = sorted({g for r in res.values() for g in r if "domain=" not in g},
            key=lambda g: (g != PRIMARY, g != "all", g))
    for gk in gks:
        table(("PRIMARY " if gk == PRIMARY else "secondary: " if gk != "all" else "") + gk, res, gk,
                lambda m: "|" not in m)
    table("descriptive splits by correctness (all)", res, "all", lambda m: "|" in m)
    conds = list(covs)
    print("\n### coverage\n\n| count | " + " | ".join(conds) + " |\n|---|" + "---|" * len(conds))
    for k in sorted({k for cv in covs.values() for k in cv}):
        print(f"| {k} | " + " | ".join(str(covs[c].get(k, 0)) for c in conds) + " |")
    for gname, s in seeds.items():
        doms = sorted({g.rsplit("domain=", 1)[1] for g in s["metrics"] if "domain=" in g})
        for gk in [k for g in (PRIMARY, "all") for d in [""] + doms if (k := dkey(g, d) if d else g) in s["metrics"]]:
            print(f"\n### seed aggregate {gname} {gk} ({', '.join(s['seeds'])}): mean of per-seed means [min, max]\n")
            for m in sorted((m for m in s["metrics"].get(gk, {}) if "|" not in m), key=okey):
                x = s["metrics"][gk][m]
                print(f"- {m}: {x['mean']:.2f} [{x['min']:.2f}, {x['max']:.2f}] k={x['k']}")
    for c, pg in paired.items():
        for gk in (PRIMARY, "all"):
            table(f"paired difference {c} ({gk})", {c: pg}, gk, lambda m: "|" not in m)
    if "chosen" in sel:
        print(f"\ncheckpoint selection: {sel['rule']}; chose {sel['chosen']}")
    if "exploratory" in sel:
        ex = sel["exploratory"]
        print(f"\n{ex[1]}")
        table(f"EXPLORATORY best-of-k by {a.select_by}, not the prespecified rule (slice=dev)",
                {c: res[c] for c in (a.select_control, ex[0]) if c}, "slice=dev", lambda m: "|" not in m)
    print(f"\njson={a.json}")


if __name__ == "__main__":
    main()
