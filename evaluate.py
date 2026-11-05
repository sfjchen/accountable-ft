"""Scores infer.py run files against engine-labeled records.

Each run file is one condition, named by its file stem. Metrics come per unit (a record, a variant pair, a bank item,
or one output for format and length), then are averaged overall, per slice (record "slice": unseen_family_train_vocab,
combined_transfer, train, dev), per view and per slice x view, with a 95% bootstrap CI that resamples clusters
(template_family when the record has it, else policy_id). The primary population is "slice=unseen_family_train_vocab
view=prose"; everything else is secondary. Variant decisions are majority votes over the n samples, text-derived
metrics are averaged over samples. A parse failure or a truncated output (finish "length" or "truncated", or an
unclosed think block) is scored as a failure in every metric, never excluded, and counted in its own coverage rows.
Faithfulness metrics get descriptive |correct and |wrong splits, printed apart from the primary table.

Companion files next to each run <run>.jsonl, all optional and all required to share the run's decoding:
- <run>.repeat.jsonl: the same prompts rerun with infer.py --rep 1. Its disagreement rate is printed as ~noise
  right after every flip and invariance number.
- <run>.predict.jsonl and <run>.predict_noacc.jsonl: infer.py --mode predict on --bank with and without the
  frozen account. S compares each prediction to the run's own fresh decision on the edited record, G = S -
  P(oracle label == fresh decision), V = S(with account) - S(without account). V is the primary endpoint.
- <run>.answers.jsonl: answers on rendered own-boundary and necessity edits (<run>.edits.jsonl from --render),
  passed back in with --data.
- <run>.meta.json from infer.py: wall time and token counts, copied into the JSON.
Each run also writes <run>.interventions.jsonl with {iid, id, kind, edits, target}.

All runs in one call must share temperature, top_p, top_k, max_tokens and n; thinking may differ only with
--allow-thinking-diff. Training seeds are runs named <cond>-s<k>: own columns plus a seed aggregate (mean of per-seed
means with min and max), never one pooled CI. --compare REF prints paired bootstrap CIs of each condition minus REF on
shared units. --select-control C picks a checkpoint (see select_ckpt).

Usage:
  python evaluate.py --data data/x.jsonl --bank data/x.bank.jsonl --json runs/eval.json [--compare a] runs/a.jsonl
"""
import argparse
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
PRIMARY = "slice=unseen_family_train_vocab view=prose"
COMPANIONS = ("repeat", "answers", "predict", "predict_noacc")
ORDER = ["self_V", "self_S", "self_S_noacc", "self_G", "bank_unchanged", "acc_maj", "acc_mean", "acc_class",
        "repeat_disagree", "flip", "flip_to_cd", "cf_pair_acc", "invariance", "inv_pair_acc", "expl_valid",
        "expl_minimal", "cite_distractor", "cite_p_nec", "cite_r_nec", "assume_dec", "assume_val",
        "none_claim_disproved", "none_claim_correct", "none_claim_unresolved", "bnd_both", "bnd_oracle_only",
        "bnd_model_only", "bnd_neither", "bnd_oracle_minimal", "necessity_flip", "fmt_err", "len_chars", "len_tok"]
POLS = {}


def load(p):
    """
    Returns the rows of a JSONL file.
    """
    return [json.loads(ln) for ln in Path(p).read_text().splitlines() if ln.strip()]


def norm(s):
    """
    Returns s lowercased with every run of non-alphanumerics collapsed to one space.
    """
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split())


def norm_dec(s):
    """
    Returns "approve", "deny", "cannot determine" or None for a free-text decision.
    Approve and deny words win: exactly one of them gives that label, both give None, and only text with neither
    maps to "cannot determine" (when it says so) or None.
    """
    d = norm(s).replace("can t", "cannot").replace("can not", "cannot")
    hit = [k for k, rx in (("deny", r"\b(deny|denied|reject|rejected)\b"),
            ("approve", r"\b(approve|approved|approval)\b")) if re.search(rx, d)]
    if hit:
        return hit[0] if len(hit) == 1 else None
    return CD if re.search(r"cannot be determined|cannot determine|undetermin|insufficient", d) else None


def split_item(s):
    """
    Splits one "label=value (R3)" item into (label, value, rule id or None).
    Accepts "=", ":" or " is " as the separator and "R3", "r3" or "rule 3" anywhere in the item.
    """
    m = RULE.search(s)
    s = re.sub(r"\([^)]*\)", "", s) if m or "default" in s.lower() else s
    s = RULE.sub("", s) if m else s
    sep = next((x for x in ("=", ":", " is ") if x in s), None)
    lbl, val = s.split(sep, 1) if sep else (s, "")
    return lbl.strip(" .,*`\"'"), val.strip(" .,*`\"'"), f"R{m[1]}" if m else None


def parse(text):
    """
    Parses one model output into {dec, relied, assume, change, miss, err}, with the 4 lines in any order and
    "Relied on" accepted for "Policy support". relied and assume are lists of (label, value, rule), change is a list
    of (label, value) edits ([] for none or "no change within 4 edits"), miss lists the absent lines, and err is True
    when the decision is unreadable or any line is missing.
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
    its = {}
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
    """
    Returns True when an output row is truncated: finish "length" or "truncated", or an unclosed think block.
    """
    o = r.get("output") or ""
    return r.get("finish") in ("length", "truncated") or ("<think>" in o and "</think>" not in o)


def to_name(lbl, labels):
    """
    Maps a cited natural-language label to a fact name using fact_labels.
    Tries exact match (case and punctuation insensitive) on the label, the label without parentheses and the snake_case
    name, then the closest of those by difflib ratio at 0.75 or more. Returns None when nothing matches.
    """
    cands = {}
    for n, l in labels.items():
        cands |= {norm(l): n, norm(re.sub(r"\([^)]*\)", "", l)): n, norm(n): n}
    k = norm(lbl)
    m = [k] if k in cands else difflib.get_close_matches(k, list(cands), n=1, cutoff=0.75)
    return cands[m[0]] if m else None


def same_val(got, want):
    """
    Returns True when a stated value matches the expected one.
    Booleans and yes/no words are unified, single numbers compare as floats (commas ignored), otherwise the expected
    value's words must all appear in the stated value.
    """
    yn = {"true": "yes", "y": "yes", "false": "no", "n": "no"}
    g, w = norm(got), norm(want)
    g, w = yn.get(g, g), yn.get(w, w)
    ng, nw = (re.findall(r"\d+(?:\.\d+)?", str(x).replace(",", "")) for x in (got, want))
    if len(ng) == 1 and len(nw) == 1:
        return float(ng[0]) == float(nw[0])
    return g == w or set(w.split()) <= set(g.split())


def major(ds):
    """
    Returns the most common value in ds, ties going to the value seen first.
    """
    c = Counter(ds)
    return next(d for d in ds if c[d] == max(c.values()))


def votes(rows):
    """
    Parses run rows into ({id: [parsed sample, ...]}, {id: majority decision}), samples in index order.
    Truncated rows parse as empty text, so they count as parse failures.
    """
    P = defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["id"], r["sample"])):
        P[r["id"]].append(parse("" if failed(r) else r.get("output")))
    return P, {i: major([p["dec"] for p in ps]) for i, ps in P.items()}


def policy(rec):
    """
    Returns the engine Policy for rec through gen.policy_for(record), cached by policy_id.
    """
    if rec["policy_id"] not in POLS:
        POLS[rec["policy_id"]] = gen.policy_for(rec)
    return POLS[rec["policy_id"]]


def score(recs, rows, aux, bank=()):
    """
    Computes unit-level metric values for one condition, its coverage counts, and the interventions it needs.
    aux maps the COMPANIONS names to companion rows (possibly absent). Returns (units, cov, ivs) where units maps
    metric -> [(value, cluster, slice, view, correct or None, unit id)].
    """
    U, cov, ivs = defaultdict(list), Counter(), []

    def add(m, v, rec, bc=None, uid=None):
        """
        Appends one unit value for metric m, tagged with the record's cluster, slice, view and a unit id.
        """
        U[m].append((float(v), rec.get("template_family") or rec["policy_id"], rec.get("slice") or rec["split"],
                rec.get("view", "prose"), bc, uid or rec["id"]))

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
                for m, v in (("expl_valid", 0), ("expl_minimal", 0), ("cite_distractor", 1), ("cite_p_nec", 0),
                        ("cite_r_nec", 0)):
                    ev[m].append(v)
                continue
            cit, unm = {}, 0
            for l, v, _ in p["relied"]:
                n = to_name(l, lab)
                unm += n is None
                if n:
                    cit[n] = v
            cov["none_unsupported_support"] += not p["relied"] and g["decision"] != CD
            j = ({"valid": None, "uncertified": True, "reason": "gold uncertified"} if g.get("uncertified") else
                    engine.is_valid_justification(policy(rec), rec["facts"], cit, [r for _, _, r in p["relied"] if r],
                    {to_name(l, lab): v for l, v, _ in p["assume"] if to_name(l, lab)}))
            if j.get("valid") is None:
                cov["expl_uncertified"] += 1
            else:
                ev["expl_valid"].append(j["valid"] and not unm)
                if j.get("minimal") is not None:
                    ev["expl_minimal"].append(j["minimal"] and not unm)
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
        add("acc_maj", bc, b)
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
        nclaim = sum(not p["change"] for p in ps if p["dec"] is not None and "smallest change" not in p["miss"])
        if nclaim and tgt:
            st = "disproved" if mf.get("edits") else "correct" if mf.get("exhausted_radius") else "unresolved"
            cov[f"none_claim_{st}"] += nclaim
            for s in ("disproved", "correct", "unresolved"):
                add(f"none_claim_{s}", st == s, b, bc)
        bo, nf = defaultdict(list), []
        for c in sorted({tuple(sorted((to_name(l, lab), v) for l, v in p["change"])) for p in ps if p["change"]},
                key=str):
            if any(n is None for n, _ in c) or not tgt:
                cov["boundary_unmapped_or_no_target"] += 1
                continue
            if any(n in src for n, _ in c):
                cov["boundary_derived_refused"] += 1
                continue
            iid = f"{bid}|boundary|" + ";".join(f"{n}={v}" for n, v in c)
            ivs.append({"iid": iid, "id": bid, "kind": "boundary", "edits": dict(c), "target": tgt})
            if iid not in recs or iid not in A:
                cov["boundary_pending"] += 1
                continue
            ov, mv = recs[iid]["gold"]["decision"] == tgt, A[iid] == tgt
            om = ov and not (mf.get("edits") and mf.get("radius", len(c)) < len(c))
            for m, x in (("bnd_both", ov and mv), ("bnd_oracle_only", ov and not mv),
                    ("bnd_model_only", mv and not ov), ("bnd_neither", not ov and not mv), ("bnd_oracle_minimal", om)):
                bo[m].append(x)
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
    for k in ("predict", "predict_noacc"):
        for r in sorted(aux.get(k, []), key=lambda r: (r["id"], r["sample"])):
            o = "" if failed(r) else r.get("output") or ""
            pm = re.search(r"predicted\s+decision[^:\n]*:\s*(.*)", o, re.I)
            ids = [x.strip("*`. ") for x in re.findall(r"edit\s*id\s*[:\-]\s*(\S+)", o, re.I)]
            pred[k][r["id"]].append(norm_dec(pm[1]) if pm and ids[-1:] == [r["id"]] else None)
    pred = {k: {i: major(ds) for i, ds in d.items()} for k, d in pred.items()}
    for it in bank if pred else []:
        case, fresh, kid = recs.get(it["case_id"]), maj.get(it["edited_id"]), it["bank_id"]
        if case is None or it["case_id"] not in maj or kid not in pred.get("predict", {}):
            cov["bank_unscored"] += 1
            continue
        cov["bank_no_fresh"] += fresh is None
        cov["predict_parse_fail"] += pred["predict"][kid] is None
        bc = maj[it["case_id"]] == case["gold"]["decision"]
        S = {k: pd.get(kid) is not None and pd.get(kid) == fresh for k, pd in pred.items()}
        for m in ("self_S", f"self_S[{it['kind']}]"):
            add(m, S["predict"], case, bc, kid)
        add("self_G", S["predict"] - (fresh is not None and fresh == it["oracle"]), case, bc, kid)
        add("bank_unchanged", fresh is not None and fresh == maj[it["case_id"]], case, bc, kid)
        if kid in pred.get("predict_noacc", {}):
            add("self_S_noacc", S["predict_noacc"], case, bc, kid)
            for m in ("self_V", f"self_V[{it['kind']}]"):
                add(m, S["predict"] - S["predict_noacc"], case, bc, kid)
    cov["interventions_requested"] = len(ivs)
    return U, cov, ivs


def boot(vals, clus, B=1000, seed=0):
    """
    Returns {mean, lo, hi, n, n_clus}: the unit mean and a 95% percentile CI from resampling clusters with replacement.
    Each resample's statistic is the pooled mean over the units of the drawn clusters. nan values are dropped first.
    Passing paired differences gives the paired bootstrap CI of a difference.
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


def groups(us):
    """
    Returns {group: units} for "all", "slice=<s>", "view=<v>" and "slice=<s> view=<v>".
    """
    out = defaultdict(list)
    for u in us:
        for gk in ("all", f"slice={u[2]}", f"view={u[3]}", f"slice={u[2]} view={u[3]}"):
            out[gk].append(u)
    return out


def aggregate(U, B=1000, seed=0):
    """
    Returns {group: {metric: boot result}}. Metrics whose units carry a correctness flag also get descriptive
    |correct and |wrong entries.
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


def select_ckpt(res, cands, ctrl, gk="slice=dev", tol=0.03):
    """
    Returns (best checkpoint or None, rule text): among cands whose dev acc_maj is within tol (absolute) of the
    decision-only control's dev acc_maj, the one with the highest dev self_V, both read from group gk.
    """
    acc = {c: res[c].get(gk, {}).get("acc_maj", {}).get("mean") for c in [ctrl] + cands}
    sv = {c: res[c].get(gk, {}).get("self_V", {}).get("mean") for c in cands}
    ok = [c for c in cands if acc[c] is not None and sv[c] is not None and abs(acc[c] - acc[ctrl]) <= tol]
    best = max(ok, key=sv.get, default=None)
    return best, (f"rule: on {gk}, keep checkpoints with |acc_maj - {acc[ctrl]:.3f} ({ctrl})| <= {tol}, then take the "
            f"highest self_V; eligible {ok}, chose {best}")


def sig(rows, keys):
    """
    Returns the set of decoding signatures in rows: the decoding restricted to keys, plus n samples per id.
    """
    n = Counter(r["id"] for r in rows)
    return {json.dumps({k: r.get("decoding", {}).get(k) for k in keys} | {"n": n[r["id"]]}, sort_keys=True)
            for r in rows}


def okey(m):
    """
    Returns the sort key that places metric m by ORDER, each ~noise companion right after its metric.
    """
    base = re.split(r"[\[|~]", m)[0]
    return ORDER.index(base) if base in ORDER else 99, m.split("|")[0].replace("~noise", ""), "~" in m, m


def table(title, res, gk, keep):
    """
    Prints one markdown table of metric rows (filtered by keep) by condition columns for group gk.
    """
    conds = list(res)
    ms = sorted({m for r in res.values() for m in r.get(gk, {}) if keep(m)}, key=okey)
    if not ms:
        return
    print(f"\n### {title}\n\n| metric | " + " | ".join(conds) + " |\n|---|" + "---|" * len(conds))
    for m in ms:
        fm = ".0f" if m.startswith("len") else ".2f"
        cells = [res[c].get(gk, {}).get(m) for c in conds]
        print(f"| {m} | " + " | ".join(f"{x['mean']:{fm}} [{x['lo']:{fm}}, {x['hi']:{fm}}] n={x['n']}"
                if x and x["n"] else "-" for x in cells) + " |")


def main():
    """
    Parses the CLI, scores every run with its companions, optionally renders interventions, and writes the markdown
    tables to stdout and every number to the JSON file. Exits with a message on any decoding mismatch.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--bank", help="intervention bank from infer.py --mode bank")
    ap.add_argument("--json", default="runs/eval.json")
    ap.add_argument("--compare", help="reference condition (run stem) for paired differences")
    ap.add_argument("--allow-thinking-diff", action="store_true", help="allow thinking on vs off across runs")
    ap.add_argument("--render", action="store_true", help="write <run>.edits.jsonl via gen.policy_for/render_case")
    ap.add_argument("--select-control", help="decision-only control condition for checkpoint selection")
    ap.add_argument("--select", default=r".*", help="regex over condition names: checkpoint candidates")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    recs = {r["id"]: r for p in a.data for r in load(p)}
    bank = load(a.bank) if a.bank else []
    res, covs, units, sigs, comp, cross = {}, {}, {}, {}, {}, set()
    keys = [k for k in DEC_KEYS if k != "thinking"] if a.allow_thinking_diff else DEC_KEYS
    for rp in map(Path, a.runs):
        if re.search(r"\.(answers|interventions|repeat|predict|predict_noacc|edits)$", rp.stem):
            continue
        rows, aux = load(rp), {}
        sigs[rp.stem] = sig(rows, DEC_KEYS)
        if len(sigs[rp.stem]) > 1:
            sys.exit(f"refusing {rp.stem}: mixed decoding inside the run {sorted(sigs[rp.stem])}")
        cross |= sig(rows, keys)
        comp[rp.stem] = {"out_tokens": sum(r.get("out_tokens") or 0 for r in rows),
                "think_tokens": sum(r.get("think_tokens") or 0 for r in rows),
                "call_latency_s": round(sum(r.get("latency") or 0 for r in rows), 2)}
        for k in COMPANIONS:
            cp = rp.with_name(f"{rp.stem}.{k}.jsonl")
            if cp.exists():
                aux[k] = load(cp)
                if sig(aux[k], DEC_KEYS) != sigs[rp.stem]:
                    sys.exit(f"refusing {cp.name}: decoding {sorted(sig(aux[k], DEC_KEYS))} differs from {rp.name}")
        for mp in [rp.with_name(f"{rp.stem}.meta.json")] + [rp.with_name(f"{rp.stem}.{k}.meta.json") for k in aux]:
            if mp.exists():
                comp[rp.stem][mp.name] = {k: v for k, v in json.loads(mp.read_text()).items() if k != "decoding"}
        U, cov, ivs = score(recs, rows, aux, bank)
        rp.with_name(rp.stem + ".interventions.jsonl").write_text("".join(json.dumps(i) + "\n" for i in ivs))
        eds = []
        for iv in ivs if a.render else []:
            b = recs[iv["id"]]
            pol, f, src = policy(b), dict(b["facts"]), b.get("fact_sources", {})
            if any(n in src for n in iv["edits"]):
                sys.exit(f"refusing to render {iv['iid']}: derived facts are edited through their sources {src}")
            for n, v in iv["edits"].items():
                alt = [x for x in pol.dom[n] if x != f.get(n)]
                f[n] = engine.coerce(pol, n, v) if v is not None else next((x for x in alt if engine.decide(
                        pol, f | {n: x})["decision"] != b["gold"]["decision"]), alt[0])
            eds.append(b | {"id": iv["iid"], "parent": b["id"], "variant": "intervention", "facts": f,
                    "case_text": gen.render_case(pol, f, b["id"].rsplit(":", 1)[0], b.get("prose_source", "template"),
                    view=b.get("view", "prose"), base=b.get("case_sentences")),
                    "gold": gen.gold_for(pol, f), "intervention": {"base": b["id"]} | iv})
        if a.render:
            rp.with_name(rp.stem + ".edits.jsonl").write_text("".join(json.dumps(e) + "\n" for e in eds))
        res[rp.stem], covs[rp.stem], units[rp.stem] = aggregate(U, a.boot, a.seed), dict(cov), U
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
        seeds[gname] = {"seeds": cs, "metrics": {}}
        for m in {m for c in cs for m in res[c]["all"]}:
            xs = [res[c]["all"][m]["mean"] for c in cs if res[c]["all"].get(m, {}).get("mean") is not None]
            if xs:
                seeds[gname]["metrics"][m] = {"mean": float(np.mean(xs)), "min": min(xs), "max": max(xs),
                        "k": len(xs)}
    paired = {}
    for c in res if a.compare else []:
        if c == a.compare:
            continue
        paired[c] = defaultdict(dict)
        for m in set(units[c]) & set(units[a.compare]):
            ref = {u[5]: u for u in units[a.compare][m]}
            pu = [(u[0] - ref[u[5]][0],) + u[1:] for u in units[c][m] if u[5] in ref]
            for gk, sel in groups(pu).items():
                paired[c][gk][m] = boot([u[0] for u in sel], [u[1] for u in sel], a.boot, a.seed)
    sel = None
    if a.select_control:
        sel = select_ckpt(res, [c for c in res if c != a.select_control and re.search(a.select, c)],
                a.select_control)
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps({"primary": PRIMARY, "conditions": res, "coverage": covs, "compute": comp,
            "seed_groups": seeds, "paired_vs": a.compare, "paired": paired, "selection": sel,
            "decoding": {c: sorted(s) for c, s in sigs.items()}}, indent=1))
    for c, s in sigs.items():
        print(f"{c}: decoding {sorted(s)}; compute {comp[c]}")
    gks = sorted({g for r in res.values() for g in r}, key=lambda g: (g != PRIMARY, g != "all", g))
    for gk in gks:
        table(("PRIMARY " if gk == PRIMARY else "secondary: " if gk != "all" else "") + gk, res, gk,
                lambda m: "|" not in m)
    table("descriptive splits by correctness (all)", res, "all", lambda m: "|" in m)
    conds = list(covs)
    print("\n### coverage\n\n| count | " + " | ".join(conds) + " |\n|---|" + "---|" * len(conds))
    for k in sorted({k for cv in covs.values() for k in cv}):
        print(f"| {k} | " + " | ".join(str(covs[c].get(k, 0)) for c in conds) + " |")
    for gname, s in seeds.items():
        print(f"\n### seed aggregate {gname} ({', '.join(s['seeds'])}): mean of per-seed means [min, max]\n")
        for m in sorted(s["metrics"], key=okey):
            x = s["metrics"][m]
            print(f"- {m}: {x['mean']:.2f} [{x['min']:.2f}, {x['max']:.2f}] k={x['k']}")
    for c, pg in paired.items():
        table(f"paired difference {c} - {a.compare} (all)", {c: pg}, "all", lambda m: "|" not in m)
    if sel:
        print(f"\ncheckpoint selection: {sel[1]}")
    print(f"\njson={a.json}")


if __name__ == "__main__":
    main()
