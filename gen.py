"""Generates engine-labeled policy and case items from domains/*.yaml in 3 aligned views (table, prose,
prose_derive), with flip, invariant, missing and reveal variants, family-level splits and optional Gemini prose.
Entry points: main (generation, --report for stats and the blind sample, --audit for the cannot-determine audit),
policy_for and render_case (used by infer.py and evaluate.py).
"""
import argparse
import collections
import concurrent.futures
import datetime
import hashlib
import itertools
import json
import os
import random
import re
import string
import threading
import time
from pathlib import Path

import yaml

import engine as E

ROOT = Path(__file__).resolve().parent
DOMAINS = ["grant", "permit", "trial", "review"]
# Held-out domains and their split: permit (invented vocabulary) and mortgage (real rules, not in "all", generated with
# --domains mortgage) each get their own transfer slice, never train or dev.
HELD_OUT = {"permit": "test_domain", "mortgage": "test_real"}
VIEWS = ["table", "prose", "prose_derive"]
SLICE = {"train": "train", "dev": "dev", "test_policy": "unseen_family_train_vocab", "test_domain": "combined_transfer",
         "test_real": "real_transfer"}
EDIT_KIND = {"base": None, "flip": "replace", "invariant": "replace", "missing": "remove", "reveal": "add"}
P_APPROVE, P_CD, P_DEFAULT, MIN_FAM_DIST = 0.43, 0.6, 0.25, 4
FRAC_TEST, FRAC_DEV = 0.4, 0.1
DECISIONS = ["approve", "deny", "cannot determine"]
# USD per 1M input / output tokens (output includes thinking), qwen at the OpenRouter PrimeIntellect list price
PRICES = {"gemini-3.5-flash-lite": (0.30, 2.50), "qwen/qwen3.5-9b": (0.17, 0.25)}
DOM_CACHE, GEM, GEM_LOCK = {}, {"usage": collections.Counter(), "seam": collections.Counter(),
        "lossy": collections.Counter()}, threading.Lock()
STOP = set("a an the of to in on for by at is are was were be been has have had and or with from as that this "
           "it its any all no not per their there which who whose would will than into each one set".split())


def load_domain(name):
    """Returns the parsed domain yaml, cached, with a rule-free Policy over its facts under "_pol"."""
    if name not in DOM_CACHE:
        dom = yaml.safe_load((ROOT / "domains" / f"{name}.yaml").read_text())
        dom["_pol"] = E.Policy(name, dom["facts"], [], (), {n: d["expr"] for n, d in dom["derived_facts"].items()})
        DOM_CACHE[name] = dom
    return DOM_CACHE[name]


class Fmt(string.Formatter):
    """
    Formats rule and case templates. Specs: money, date (day offset), ago (ref year - v), k (thousands), t (tonnes
    from kg), e or e:<fact> (enum display name), before and after (signed day gaps such as "3 days after").
    """

    def __init__(self, dom, fact=None):
        """Binds the formatter to a domain vocabulary and optionally the fact being rendered."""
        super().__init__()
        self.dom, self.fact = dom, fact

    def format_field(self, v, spec):
        """Returns the display string for value v under spec."""
        ref = self.dom["ref_date"]
        if spec == "money":
            return f"${v:,}"
        if spec == "date":
            d = ref + datetime.timedelta(days=v)
            return f"{d:%B} {d.day}, {d.year}"
        if spec == "ago":
            return str(ref.year - v)
        if spec == "k":
            return f"{v / 1000:g} thousand"
        if spec == "t":
            return f"{v / 1000:g}"
        if spec in ("before", "after"):
            d = v if spec == "before" else -v
            n = f"{abs(d)} day" + "s" * (abs(d) != 1)
            return "on the same day as" if not d else f"{n} before" if d > 0 else f"{n} after"
        if spec.startswith("e"):
            names = self.dom["facts"][spec[2:] or self.fact]["names"]
            if not isinstance(v, list):
                return names[v]
            ws = [names[x] for x in v]
            return ", ".join(ws[:-1]) + " or " + ws[-1]
        return super().format_field(v, spec)


def dist_pats(f):
    """Returns {value: regexes} for an enum fact, one per name token no sibling value's name has."""
    tk = {v: re.findall(r"[A-Za-z0-9]+", nm) for v, nm in f["names"].items()}
    out = {}
    for v, ws in tk.items():
        other = {w for u, xs in tk.items() if u != v for w in xs}
        pats = []
        for i, w in enumerate(ws):
            if w in other or w.lower() in STOP and len(w) > 1:
                continue
            pats.append(rf"\b{ws[i - 1]}[\s-]*{w}\b" if len(w) <= 2 and i else rf"\b{w}(s|es)?\b")
        out[v] = pats
    return out


def names_value(f, v, s):
    """Returns whether sentence s carries a distinguishing name token of value v of enum fact f."""
    return any(re.search(p, s, re.I) for p in dist_pats(f)[v])


def template_refs(dom, t, exc=None):
    """Returns the source facts a rule template (and optionally one of its exceptions) reads."""
    src = t["cond"] + " " + (t["unless"][exc]["cond"] if exc is not None else "")
    out = set()
    for w in re.findall(r"[a-z_][a-z0-9_]*", src):
        if w in dom["facts"]:
            out.add(w)
        elif w in dom["derived_facts"]:
            out.update(re.findall(r"[a-z_][a-z0-9_]*", dom["derived_facts"][w]["expr"]))
    return out & set(dom["facts"])


def sample_family(dom, rng, hold, want_hold, prev=()):
    """
    Returns a template family {"core", "derived", "defaults", "parts"}: 5-8 core templates with 2-4 exceptions and
    2+ scoped rules, 1-2 derived-fact rules, 1-2 defaults on live facts, 8-15 rules, at most MAX_FACTS facts.
    want_hold forces a held-out exception/default pair in, else keeps all out; families within MIN_FAM_DIST parts of
    one in prev are rejected.
    """
    for _ in range(50000):
        core = rng.sample(dom["rules"], rng.randint(5, min(8, len(dom["rules"]))))
        exc = [t["key"] for t in core if t.get("unless")]
        if len(exc) < 2 or sum(bool(t.get("scoped")) for t in core) < 2:
            continue
        exc = set(rng.sample(exc, rng.randint(2, min(4, len(exc)))))
        der = rng.sample(dom["derived"], rng.randint(1, min(2, len(dom["derived"]))))
        live = set()
        for t in core:
            live |= template_refs(dom, t, 0 if t["key"] in exc else None)
        for t in der:
            live |= template_refs(dom, t)
        dc = [d["fact"] for d in dom["defaults"] if d["fact"] in live]
        vrefs = set(re.findall(r"[a-z_][a-z0-9_]*", " ".join(dom.get("valid", [])))) & set(dom["facts"])
        if not dc or len(live | vrefs) > E.MAX_FACTS:
            continue
        defs = rng.sample(dc, rng.randint(1, min(2, len(dc))))
        if not 8 <= len(core) + len(der) + len(defs) <= 15:
            continue
        held = any(k in exc and f in defs for k, f in hold)
        if held != want_hold:
            continue
        parts = {t["key"] for t in core} | {"x:" + k for k in exc} | {"d:" + t["key"] for t in der} | \
            {"f:" + f for f in defs}
        if all(len(parts ^ set(p["parts"])) >= MIN_FAM_DIST for p in prev):
            return {"core": sorted((t["key"], 0 if t["key"] in exc else None) for t in core),
                    "derived": sorted(t["key"] for t in der), "defaults": sorted(defs), "parts": sorted(parts)}
    raise RuntimeError(f"could not sample a {dom['name']} family (holdout={want_hold})")


def sample_params(params, rng, vals):
    """Adds sampled template parameters to vals: lists are choices, strings are expressions over earlier ones."""
    for k, p in (params or {}).items():
        vals[k] = rng.choice(p) if isinstance(p, list) else eval(p, {"__builtins__": {}}, dict(vals))


def instantiate(dname, fam, pid, rng):
    """
    Returns a Policy for a family with sampled thresholds and shuffled rule order, with .domain, .spec, .text,
    .labels and .near set. Every rule must be able to hold and to fail, and approval must be reachable.
    """
    dom = load_domain(dname)
    byk = {t["key"]: t for t in dom["rules"] + dom["derived"]}
    dbyf = {d["fact"]: d for d in dom["defaults"]}
    for _ in range(200):
        specs = []
        for key, exc in fam["core"] + [(k, None) for k in fam["derived"]]:
            t, vals = byk[key], {}
            sample_params(t.get("params"), rng, vals)
            text = Fmt(dom).format(t["text"], **vals)
            sp = {"kind": "require", "key": key}
            if exc is not None:
                u = t["unless"][exc]
                sample_params(u.get("params"), rng, vals)
                sp["unless"] = u["cond"].format(**{k: repr(v) for k, v in vals.items()})
                ut = Fmt(dom).format(u["text"], **vals)
                text = rng.choice([f"{text}, unless {ut}.", f"{text}. This rule does not apply if {ut}."])
            else:
                text += "."
            sp["cond"], sp["text"] = t["cond"].format(**{k: repr(v) for k, v in vals.items()}), text
            if t.get("near"):
                sp["near"] = t["near"].format(**{k: repr(v) for k, v in vals.items()})
            specs.append(sp)
        for f in fam["defaults"]:
            d = dbyf[f]
            specs.append({"kind": "default", "fact": f, "value": d["value"], "text": d["text"] + "."})
        rng.shuffle(specs)
        for i, sp in enumerate(specs):
            sp["id"] = f"R{i + 1}"
        derived = {n: d["expr"] for n, d in dom["derived_facts"].items()}
        pol = E.Policy(pid, dom["facts"], specs, dom.get("valid", ()), derived)
        good = "approve" in E.possible(pol, {})
        for r in pol.requires:
            good &= E.sat(pol, ["+" + r.id], {}) and E.sat(pol, ["-" + r.id], {})
        if not good:
            continue
        pol.domain, pol.spec = dname, {"domain": dname, "rules": specs, "valid": list(dom.get("valid", ())),
                                       "derived": derived}
        pol.labels = {n: s["label"] for n, s in dom["facts"].items()}
        pol.labels.update({n: d["label"] for n, d in dom["derived_facts"].items()})
        pol.near = {sp["id"]: E.compile_cond(sp["near"], set(dom["facts"]), derived)[0] for sp in specs
                    if sp.get("near")}
        pol.text = "\n".join([dom["title"], dom["preamble"], ""] + [f"{sp['id']}. {sp['text']}" for sp in specs])
        return pol
    raise RuntimeError(f"could not instantiate {pid}")


def policy_for(record):
    """Returns the Policy of a record, rebuilt from its policy_spec and the domain schema, with the same attributes."""
    sp, dom = record["policy_spec"], load_domain(record["domain"])
    pol = E.Policy(record["policy_id"], dom["facts"], sp["rules"], sp["valid"], sp["derived"])
    pol.domain, pol.spec, pol.labels, pol.text = record["domain"], sp, record["fact_labels"], record["policy_text"]
    pol.near = {r["id"]: E.compile_cond(r["near"], set(dom["facts"]), sp["derived"])[0] for r in sp["rules"]
                if r.get("near")}
    return pol


def sample_case(pol, rng, want):
    """
    Returns a complete admissible fact dict with decision want: a random draw repaired until every rule holds, some
    rules moved into their waived or near-miss state, then for deny 1-2 rules broken.
    """

    def bad(g):
        """Returns the number of failed rules plus 1 for a validity violation."""
        return sum(not r.holds(g) for r in pol.requires) + (not pol.ok(g))

    vrefs = sorted({n for _, refs in pol.valid for n in refs})
    for _ in range(200):
        f = {n: rng.choice(pol.dom[n]) for n in pol.order}
        for _ in range(300):
            fails = [r for r in pol.requires if not r.holds(f)]
            if not fails and pol.ok(f):
                break
            n = rng.choice(rng.choice(fails).all_refs if fails else vrefs)
            vals = list(pol.dom[n])
            rng.shuffle(vals)
            f[n] = min(vals, key=lambda v: bad({**f, n: v}))
        if bad(f):
            continue
        for r in pol.requires:
            tgt = r.fu if r.unless else pol.near.get(r.id)
            if tgt and rng.random() < 0.5:
                for _ in range(40):
                    g = {**f, **{n: rng.choice(pol.dom[n]) for n in r.all_refs}}
                    if tgt(g) and (not r.unless or not r.fc(g)) and not bad(g):
                        f = g
                        break
        if want == "deny":
            for r in rng.sample(pol.requires, 1 if rng.random() < 0.6 else 2):
                refs = list(r.all_refs)
                rng.shuffle(refs)
                for n in refs:
                    vals = [v for v in pol.dom[n] if not r.holds({**f, n: v}) and pol.ok({**f, n: v})]
                    if vals:
                        f[n] = rng.choice(vals)
                        break
        if E.decide(pol, f)["decision"] == want:
            return f
    raise RuntimeError(f"could not sample a {want} case for {pol.id}")


def case_facts(policy, facts):
    """Returns (domain name, domain, stated source facts, derived values) for a Policy, record or domain name."""
    dname = policy["domain"] if isinstance(policy, dict) else getattr(policy, "domain", policy)
    dom = load_domain(dname)
    stated = {n: v for n, v in facts.items() if n in dom["facts"] and v is not None}
    return dname, dom, stated, dom["_pol"].derived_values(stated)


def case_sentences(policy, facts, seed, view="prose", base=None):
    """
    Returns the prose case as [{"fact", "value", "sentence"}] (fact None for header and color), with header,
    phrasing, order and color fixed by the base id in seed. With base (the base record's sentences, e.g. a Gemini
    rewrite) it keeps the base wording, swaps in the template sentence of each fact whose value differs and drops
    sentences of unstated facts.
    """
    _, dom, stated, dv = case_facts(policy, facts)
    rng = random.Random(str(seed).split(":")[0])
    head = rng.choice(dom["intro"]).format(name=rng.choice(dom["names"]), num=rng.randint(1000, 9999))
    picks = {n: rng.random() for n in dom["facts"]}
    pool = rng.sample(dom["color"], len(dom["color"]))
    ncol = rng.randint(2, 4)
    keys = list(dom["facts"]) + list(dom["derived_facts"]) + list(range(ncol))
    rng.shuffle(keys)
    out = [{"fact": None, "value": None, "sentence": head}]
    for k in keys:
        if isinstance(k, int):
            out.append({"fact": None, "value": None, "sentence": pool[k]})
        elif k in stated:
            s = dom["facts"][k]
            lst = s["say"] if s["type"] != "bool" else s["say_true"] if stated[k] else s["say_false"]
            out.append({"fact": k, "value": stated[k],
                        "sentence": Fmt(dom, k).format(lst[int(picks[k] * len(lst))], v=stated[k])})
        elif k in dv and view == "prose":
            out.append({"fact": k, "value": dv[k], "sentence": Fmt(dom, k).format(dom["derived_facts"][k]["say"][0],
                                                                                 v=dv[k])})
    for extra in pool[ncol:]:
        if len(" ".join(x["sentence"] for x in out).split()) >= 150:
            break
        out.append({"fact": None, "value": None, "sentence": extra})
    if base is None:
        return out
    tmpl, merged = {x["fact"]: x for x in out if x["fact"]}, []
    for b in base:
        if b["fact"] is None:
            merged.append(b)
        elif b["fact"] in tmpl:
            merged.append(b if tmpl[b["fact"]]["value"] == b["value"] else tmpl[b["fact"]])
    seen = {b["fact"] for b in base}
    return merged + [x for x in out if x["fact"] and x["fact"] not in seen]


def render_case(policy, facts, seed, prose="template", view="prose", base=None):
    """
    Returns the case text of facts in view; prose views need the base record's case_sentences as base when
    prose="gemini".
    """
    dname, dom, stated, dv = case_facts(policy, facts)
    if prose == "gemini" and base is None and view != "table":
        raise ValueError("prose='gemini' needs the base record's case_sentences as base")
    if view != "table":
        return " ".join(x["sentence"] for x in case_sentences(dname, facts, seed, view, base))
    rows = [case_sentences(dname, {}, seed)[0]["sentence"], ""]
    for n, s in list(dom["facts"].items()) + list(dom["derived_facts"].items()):
        v = stated.get(n, dv.get(n))
        if v is None:
            continue
        spec = (re.search(r"\{v:(money|date|e)\}", " ".join(s.get("say", []))) or [None, ""])[1]
        shown = ("yes" if v else "no") if isinstance(v, bool) else Fmt(dom, n).format_field(v, spec)
        rows.append(f"- {s['label']}: {shown}" + (" (derived)" if n in dom["derived_facts"] else ""))
    return "\n".join(rows)


def gold_for(pol, facts, rid=None):
    """
    Returns the gold labels of a record: decision, trace, minimal sufficient sets (source level) with the minimum
    ones, necessary facts, flip target and min_flip, defaults, case-level distractor facts and rules, and for
    "cannot determine" the witnesses, needs_facts and min_reveal. Over-budget searches mark it uncertified with
    reasons.
    """
    d = E.decide(pol, facts, rid)
    cd, unc = d["decision"] == "cannot determine", []
    try:
        sets = E.sufficient_sets(pol, facts)
    except E.Timeout as e:
        sets = []
        unc.append(f"sufficient_sets: {e}")
    k = min((len(s) for s in sets), default=0)
    used = {n for s in sets for n in s}
    if cd:
        used = {n for r in pol.requires if d["rule_trace"][r.id] != "pass" for n in r.all_refs}
    mf = E.min_flip(pol, facts, target=E.flip_target(d["decision"]))
    mr = E.min_reveal(pol, facts) if cd else None
    for name, res in [("min_flip", mf), ("min_reveal", mr)]:
        if res and res.get("uncertified"):
            unc.append(f"{name}: {res['reason']}")
    known, _ = E.known_facts(pol, facts)
    return {"decision": d["decision"], "rule_trace": d["rule_trace"], "sufficient_sets": sets,
            "minimum_sets": [s for s in sets if len(s) == k], "necessary_facts": E.necessary_facts(pol, facts, sets),
            "single_condition": E.single_condition(pol, facts, sets), "defaults_applied": d["defaults_applied"],
            "needs_fact_for": d["needs_fact_for"],
            "needs_facts": [n for n in pol.order if n not in known and
                            any(n in r.all_refs for r in pol.requires if r.id in d["needs_fact_for"])],
            "cd_witnesses": E.cd_witnesses(pol, facts) if cd else None, "target": E.flip_target(d["decision"]),
            "min_flip": mf, "min_reveal": mr,
            "distractor_facts": [n for n in pol.order if n in facts and n not in used],
            "distractor_rules": [r.id for r in pol.requires if d["rule_trace"][r.id] in ("pass", "waived") and
                                 any(n not in used for n in r.all_refs)],
            "uncertified": bool(unc), "uncertified_reasons": unc}


def load_env():
    """Fills unset environment variables (API keys, GCP_PROJECT) from ~/.config/cs224v/.env and returns its path."""
    path = Path.home() / ".config" / "cs224v" / ".env"
    for ln in path.read_text().splitlines() if path.exists() else []:
        if m := re.match(r"\s*(?:export\s+)?(\w+)\s*=\s*['\"]?([^'\"\s#]*)", ln):
            os.environ.setdefault(m[1], m[2])
    return path


def gemini_client(vertex):
    """Returns a google-genai client on Vertex AI in location vertex (ADC, GCP_PROJECT) or on GEMINI_API_KEY."""
    from google import genai

    path, key = load_env(), "GCP_PROJECT" if vertex else "GEMINI_API_KEY"
    if not os.environ.get(key):
        raise RuntimeError(f"no {key} in the environment or {path}")
    if not vertex:
        return genai.Client(api_key=os.environ[key])
    import google.auth

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"],
                                   quota_project_id=os.environ[key])
    return genai.Client(vertexai=True, project=os.environ[key], location=vertex, credentials=creds)


def gemini_call(prompt, json_out=False):
    """
    Returns one Gemini reply, cached on disk under GEM["cache"] by model, mode and prompt with its token usage.
    Counts usage in GEM["usage"], retries server errors and rate limits with backoff, and falls through unavailable
    models (GEM["ids"], the pinned model or the flash-class ones, cheapest first).
    """
    from google.genai import errors, types

    with GEM_LOCK:
        if "client" not in GEM:
            GEM["client"] = gemini_client(GEM.get("vertex"))
            GEM["ids"] = [GEM["model"]] if GEM.get("model") else []
            for m in [] if GEM.get("model") else GEM["client"].models.list(
                    **({"config": {"query_base": True}} if GEM.get("vertex") else {})):
                mid, acts = m.name.split("/")[-1], m.supported_actions
                if (acts is None or "generateContent" in acts) and "flash" in mid and \
                  not re.search(r"image|tts|live|audio|embed|exp|preview|latest|thinking|native|computer", mid):
                    GEM["ids"].append(mid)
            if not GEM.get("model"):
                ver = {mid: float((re.search(r"gemini-(\d+(?:\.\d+)?)", mid) or [0, 0])[1]) for mid in GEM["ids"]}
                GEM["ids"].sort(key=lambda mid: ("lite" not in mid, -ver[mid], len(mid)))
                print("flash-class candidates, cheapest first:", ", ".join(GEM["ids"]))
    cfg = types.GenerateContentConfig(temperature=0.7 if not json_out else 0.0,
                                      response_mime_type="application/json" if json_out else "text/plain")
    tries = 0
    while GEM["ids"]:
        mid = GEM["ids"][0]
        key = hashlib.sha256(json.dumps([mid, json_out, prompt]).encode()).hexdigest()
        cp = Path(GEM["cache"]) / f"{key}.json" if GEM.get("cache") else None
        if cp and cp.exists():
            hit = json.loads(cp.read_text())
            with GEM_LOCK:
                GEM["usage"].update({"cached_calls": 1, **{"cached_" + k: v for k, v in hit["usage"].items()}})
            GEM.setdefault("chosen", mid)
            return hit["text"]
        try:
            res = GEM["client"].models.generate_content(model=mid, contents=prompt, config=cfg)
        except errors.ServerError:
            tries += 1
            if tries > 3:
                raise
            time.sleep(5 * tries)
            continue
        except errors.ClientError as e:
            if e.code == 429 and tries < 6:
                tries += 1
                time.sleep(2 ** tries + random.random())
                continue
            if e.code == 429 or GEM.get("chosen"):
                raise
            print(f"Gemini model {mid} unavailable ({e.code}), trying the next one")
            GEM["ids"].pop(0)
            continue
        um = res.usage_metadata
        use = {"in": um.prompt_token_count or 0, "out": um.candidates_token_count or 0,
               "think": um.thoughts_token_count or 0}
        with GEM_LOCK:
            GEM["usage"].update({"calls": 1, **use})
            if not GEM.get("chosen"):
                GEM["chosen"] = mid
                print("Gemini model:", mid)
        if cp:
            cp.parent.mkdir(parents=True, exist_ok=True)
            tmp = cp.with_suffix(f".{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps({"model": mid, "text": res.text, "usage": use}))
            tmp.replace(cp)
        return res.text
    raise RuntimeError("no usable Gemini model")


def md_table(rows, head):
    """Returns a markdown table for a header list and row lists."""
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(str(x) for x in r) + " |" for r in rows])


def crosstab(recs, rkey, ckey, cols=None):
    """Returns a markdown table counting records by rkey (rows) and ckey (columns), with totals."""
    c = collections.Counter((rkey(r), ckey(r)) for r in recs)
    rows, cols = sorted({k[0] for k in c}), cols or sorted({k[1] for k in c})
    body = [[rv] + [c[rv, cv] for cv in cols] + [sum(c[rv, cv] for cv in cols)] for rv in rows]
    body.append(["total"] + [sum(c[rv, cv] for rv in rows) for cv in cols] + [sum(c.values())])
    return md_table(body, [""] + list(cols) + ["total"])


def report(a):
    """Writes <data>.stats.md (counts, balance, families, Gemini drops and spend) and the blind validation sample."""
    src = Path(a.report)
    recs = [json.loads(ln) for ln in src.open()]
    pro = [r for r in recs if r["view"] == "prose"]
    base = [r for r in pro if r["variant"] == "base"]
    dec = lambda r: r["gold"]["decision"]
    fams = collections.defaultdict(set)
    for r in pro:
        fams[r["domain"], r["slice"]].add(r["template_family"])
    calls = tin = tout = 0
    for p in Path(a.cache).glob("*.json") if a.cache and Path(a.cache).exists() else []:
        u = json.loads(p.read_text())["usage"]
        calls, tin, tout = calls + 1, tin + u["in"], tout + u["out"] + u["think"]
    pin, pout = PRICES["gemini-3.5-flash-lite"]
    usd = tin / 1e6 * pin + tout / 1e6 * pout
    md = [f"# {src.stem} dataset stats", "", f"Generated by `gen.py --report` from `{src.name}`.", ""]
    md += ["```", a.cmd, "```", ""] if a.cmd else []
    md += [f"{len(recs)} records = {len(pro)} items x 3 views, {len(base)} base cases, "
           f"{len({r['policy_id'] for r in pro})} policies, {len({r['template_family'] for r in pro})} families.", "",
           "## Items (all views) by domain and slice", "",
           crosstab(recs, lambda r: r["domain"], lambda r: r["slice"]), "",
           "## Items by view and slice", "", crosstab(recs, lambda r: r["view"], lambda r: r["slice"]), "",
           "## Items (prose view) by variant and slice", "",
           crosstab(pro, lambda r: r["variant"], lambda r: r["slice"]), "",
           "## Decision balance (prose view) by slice", "", crosstab(pro, lambda r: r["slice"], dec, DECISIONS), "",
           "## Decision balance (prose view) by variant", "", crosstab(pro, lambda r: r["variant"], dec, DECISIONS), "",
           "## Template families by domain and slice", "",
           md_table([[d, s, len(v)] for (d, s), v in sorted(fams.items())], ["domain", "slice", "families"]), "",
           "Prose items per unseen family (unseen_family_train_vocab): " +
           ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(
               r["template_family"] for r in pro if r["slice"] == "unseen_family_train_vocab").items())), "",
           "## Gold properties (prose view)", ""]
    flips = collections.Counter(len(r["changed_facts"]) for r in pro if r["variant"] == "flip")
    md += [f"- interaction bases (no single condition, 2+ sufficient sets): "
           f"{sum(bool(r['interaction']) for r in base)} of {len(base)}",
           f"- single-condition items: {sum(r['gold']['single_condition'] for r in pro)} of {len(pro)}",
           "- flip radius: " + ", ".join(f"{k}: {v}" for k, v in sorted(flips.items())),
           f"- items certified with no flip within radius 4 (none are bases): "
           f"{sum('exhausted_radius' in r['gold']['min_flip'] for r in pro)}",
           f"- uncertified gold (search over budget): {sum(r['gold']['uncertified'] for r in pro)}",
           f"- holdout_structure items: {sum(r['holdout_structure'] for r in pro)}",
           "- missing-fact effects: " + ", ".join(f"{k}: {v}" for k, v in sorted(collections.Counter(
               r["removed_effect"] for r in pro if r["variant"] == "missing").items())), "",
           "## Prose source (prose and prose_derive views)", "",
           crosstab([r for r in recs if r["view"] != "table"], lambda r: r["domain"], lambda r: r["prose_source"]), ""]
    if a.log:
        log = Path(a.log).read_text().splitlines()
        dl = [ln for ln in log if ln.startswith("dropped base family")]
        dom, kept = collections.Counter(ln.split()[3].split("-")[0] for ln in dl), collections.Counter(
            r["domain"] for r in base)
        why = collections.Counter()
        for ln in dl:
            un = re.search(r"untagged sentences state ([^']+)", ln)
            why.update(re.findall(r"'([a-z_]+)': \(", ln) or [f"untagged sentence states {un[1]}" if un else
                                                              "tag names in prose" if "leak:" in ln else "other"])
        rows = [[d, kept[d], dom[d], f"{dom[d] / (kept[d] + dom[d]):.1%}"] for d in sorted(kept)]
        md += ["## Gemini check failures (base families dropped)", "",
               md_table(rows, ["domain", "kept bases", "dropped", "drop rate"]), "",
               "Mismatched facts: " + ", ".join(f"{k} {v}" for k, v in why.most_common()) +
               f". In {sum(bool(re.search(r'[(]None, ', ln)) for ln in dl)} of {len(dl)} drops the re-extraction "
               f"returned null for a fact the rewrite was asked to state.", "",
               *[ln.strip() for ln in log if ln.startswith(("seam:", "reveal skipped"))], ""]
    md += ["## Vertex spend", "",
           f"{calls} Gemini calls in the cache, {tin:,} input and {tout:,} output tokens, about ${usd:.2f} at "
           f"${pin}/${pout} per 1M input/output tokens (gemini-3.5-flash-lite list price, third-party "
           f"trackers, Nov 2026). This is everything the cache holds: the extraction call per base, dropped families "
           f"and earlier attempts whose cases later changed.", ""]
    rng, cells, picks, used = random.Random(a.seed), collections.defaultdict(list), [], set()
    for r in pro:
        cells[r["domain"], dec(r)].append(r)
    keys = sorted(cells)
    for k in keys:
        rng.shuffle(cells[k])
    while len(picks) < a.n_blind and any(cells[k] for k in keys):
        for k in keys:
            while cells[k] and len(picks) < a.n_blind:
                r = cells[k].pop()
                fam = (r["parent"] or r["id"]).split(":")[0]
                if fam not in used:
                    used.add(fam)
                    picks.append(r)
                    break
    rng.shuffle(picks)
    bl, ans = src.with_suffix(".blind100.jsonl"), src.with_suffix(".blind100.answers.jsonl")
    with bl.open("w") as fb, ans.open("w") as fa:
        for i, r in enumerate(picks):
            fb.write(json.dumps({"blind_id": f"b{i:03d}", "policy_text": r["policy_text"], "case_text": r["case_text"],
                                 "fact_labels": r["fact_labels"], "label_decision": None, "label_facts": [],
                                 "label_notes": ""}) + "\n")
            fa.write(json.dumps({"blind_id": f"b{i:03d}", "id": r["id"], "domain": r["domain"], "slice": r["slice"],
                                 "variant": r["variant"], "decision": dec(r),
                                 "minimum_sets": r["gold"]["minimum_sets"], "needs_facts": r["gold"]["needs_facts"],
                                 "defaults_applied": r["gold"]["defaults_applied"],
                                 "changed_facts": r["changed_facts"], "removed_fact": r["removed_fact"]}) + "\n")
    md += ["## Blind validation sample", "",
           f"`{bl.name}` ({len(picks)} prose items, at most 1 per base family, gold in `{ans.name}`). Each of us fills "
           "label_decision (approve, deny, cannot determine) and label_facts without opening the answer file.", "",
           crosstab(picks, lambda r: r["domain"], dec, DECISIONS), "",
           "By variant: " + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(
               r["variant"] for r in picks).items())), ""]
    src.with_suffix(".stats.md").write_text("\n".join(md))
    print("wrote", src.with_suffix(".stats.md"), bl, ans, f"spend ${usd:.2f}",
          dict(collections.Counter((r["domain"], dec(r)) for r in picks)))


NEG = re.compile(r"\b(no|not|none|never|without|lacks?|lacking|absent|neither|nor|missing|omits?|declined|yet to|"
                 r"zero|exclud\w*|omit\w*|absence of|free of|lack\w*|unavailable|fail\w*|pending|unspecified|undecided|"
                 r"(?:be|been) (?:decided|determined)|under (?:internal )?consideration|has not|have not|"
                 r"did not|does not|was not|were not|nothing)\b|n't", re.I)
WORDS = {"single": 1, "sole": 1, "a single": 1} | {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen".split())} | {w: 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty "
                                                                    "ninety".split(), 2)}
ORD = {"first": 1, "second": 2, "third": 3, "fifth": 5, "eighth": 8, "ninth": 9, "twelfth": 12}
MONTHS = "january february march april may june july august september october november december".split()


def toks(s):
    """Returns the lowercase content tokens of a string, placeholders removed and a plural s stripped."""
    return {re.sub(r"(?<=[a-z]{3})s$", "", w) for w in re.findall(r"[a-z][a-z-]+", re.sub(r"\{[^}]*\}", " ",
                                                                                         s).lower())} - STOP


def cues(lx, n, s):
    """Returns whether sentence s names fact n: 2 of its anchor tokens, or all of them when it has fewer."""
    return len(toks(s) & lx[n]) >= min(2, len(lx[n])) > 0


def renders(dom, n, v):
    """Returns the yaml template sentences for fact n at value v."""
    f = dom["facts"].get(n) or dom["derived_facts"][n]
    return [Fmt(dom, n).format(t, v=v) for t in f.get("say") or (f["say_true"] if v else f["say_false"])]


def kind(dom, n):
    """Returns "bool", "enum" or "number" for fact n (derived facts are numbers)."""
    return {"bool": "bool", "enum": "enum"}.get((dom["facts"].get(n) or {}).get("type"), "number")


def value_ok(dom, n, v, s):
    """
    Returns whether sentence s carries value v of fact n: for bools the side whose negation cue it shares when only
    one side negates, else whose own tokens it shares more; a distinguishing name token for enums; for numbers the
    numbers (words read as digits, "60k" scaled, month-day pairs) of some yaml rendering of v.
    """

    def num(m):
        """Returns the digit string of one matched run of number words."""
        tot = cur = 0
        for w in re.split(r"[\s-]+", m[0].lower()):
            x = ORD.get(w) or WORDS.get(w) or WORDS.get(re.sub(r"th$", "", w.replace("ieth", "y"))) or 0
            if w == "hundred":
                cur *= 100
            elif w == "thousand":
                tot, cur = tot + cur * 1000, 0
            elif w != "and":
                cur += x
        return str(tot + cur)

    def nums(t):
        """Returns the numbers and (month, day) pairs in a string."""
        ws, out = "|".join(list(WORDS) + list(ORD) + ["[a-z]+tieth", "[a-z]+teenth", "fourth", "sixth", "seventh",
                                                      "tenth"]), set()
        t = re.sub(rf"\b(?:{ws})(?:(?:[\s-]+|\s+and\s+)(?:{ws}|hundred|thousand))*\b|\bhundred\b", num, t, flags=re.I)
        for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(k\b|thousand\b)?", t, re.I):
            x = float(m[1].replace(",", "")) * (1000 if m[2] else 1)
            out.add(int(x) if x == int(x) else x)
        mo = "|".join(MONTHS)
        for m in re.finditer(rf"\b({mo})\s+(\d{{1,2}})\b|\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({mo})\b", t, re.I):
            out.add((m[1] or m[4]).lower() + " " + (m[2] or m[3]))
        return out

    f = dom["facts"].get(n) or dom["derived_facts"][n]
    if f.get("type") == "bool":
        ng = {b: [bool(NEG.search(t)) for t in f["say_true" if b else "say_false"]] for b in (True, False)}
        if all(ng[False]) and not any(ng[True]) or all(ng[True]) and not any(ng[False]):
            return bool(NEG.search(s)) == all(ng[v])
        tt, ff = (set().union(*map(toks, f[k])) for k in ("say_true", "say_false"))
        return (len(toks(s) & (tt - ff)) >= len(toks(s) & (ff - tt))) == v
    if f.get("type") == "enum":
        return names_value(f, v, s)
    got = nums(s)
    return any(nums(t) - {2027} <= got for t in renders(dom, n, v))


def presupposed(r):
    """Returns the sentence of a cd record that presupposes the object a missing, needed zero guard covers, or None."""
    miss = {n for n, st in r["fact_states"].items() if st["state"] == "missing"}
    for q in r["policy_spec"]["rules"]:
        m = re.fullmatch(r"(\w+) == 0 or (\w+)", q.get("cond", ""))
        if m and m[1] in miss and m[1] in r["gold"]["needs_facts"] and r["facts"].get(m[2]) is False:
            return next(x["sentence"] for x in r["case_sentences"] if x["fact"] == m[2])
    return None


def audit(a):
    """
    Audits the "cannot determine" (cd) items of one slice and view for leaked or distorted facts (lexicon cues,
    stated_facts vs tags, values, witnesses), lists lossy enum renderings, adds the --run model's cd decisions and
    --sample items, and with --flagged writes the ids to drop from training (lossy enum or zero_guard_presupposed).
    """
    recs = [json.loads(line) for line in open(a.audit)]
    byid = {r["id"]: r for r in recs}
    doms = {d: load_domain(d) for d in sorted({r["domain"] for r in recs})}
    lex = {}
    for d, dom in doms.items():
        raw, anc = {}, {}
        for n, f in list(dom["facts"].items()) + list(dom["derived_facts"].items()):
            say = f.get("say", []) + f.get("say_true", []) + f.get("say_false", [])
            nm = list(f.get("names", {}).values())
            raw[n] = set().union(*map(toks, [f["label"]] + say + nm))
            cnt = collections.Counter(w for t in say for w in toks(t))
            anc[n] = toks(f["label"]) | set().union(*map(toks, nm)) | {w for w, k in cnt.items() if k >= 2}
        common = set().union(*map(toks, dom["intro"] + dom["color"] + [dom["title"], dom["preamble"]] + dom["names"]))
        lex[d] = {n: ws - common - set().union(*(v for m, v in raw.items() if m != n)) for n, ws in anc.items()}
    pop = [r for r in recs if r["slice"] == a.slice and r["view"] == a.view]
    cd = [r for r in pop if r["gold"]["decision"] == "cannot determine"]
    c, bad = collections.Counter(), collections.defaultdict(list)
    for r in cd:
        dom, lx, pol = doms[r["domain"]], lex[r["domain"]], policy_for(r)
        miss = [n for n, s in r["fact_states"].items() if s["state"] == "missing"]
        sents, tagged = r["case_sentences"], {x["fact"] for x in r["case_sentences"] if x["fact"]}
        c["items"] += 1
        c["removed_fact_is_needed"] += r["removed_fact"] in r["gold"]["needs_facts"]
        hit = [(n, x["sentence"]) for n in miss for x in sents if cues(lx, n, x["sentence"])]
        hit += [(n, x["sentence"]) for n in miss if dom["facts"][n]["type"] == "enum" for x in sents
                for v in dom["facts"][n]["values"] if all(re.search(p, x["sentence"], re.I)
                                                          for p in dist_pats(dom["facts"][n])[v])]
        if hit:
            c["missing_fact_mentioned"] += 1
            bad["missing_fact_mentioned"].append((r["id"], hit[0]))
        if set(r["stated_facts"]) != tagged or set(miss) & tagged:
            c["stated_facts_vs_tags"] += 1
            bad["stated_facts_vs_tags"].append((r["id"], sorted(set(r["stated_facts"]) ^ tagged)))
        for x in sents:
            if x["fact"] and not value_ok(dom, x["fact"], x["value"], x["sentence"]):
                c["value_not_found_" + kind(dom, x["fact"])] += 1
                bad["value_not_found_" + kind(dom, x["fact"])].append((r["id"], (x["fact"], x["value"], x["sentence"])))
            for n in set(lx) - tagged - set(miss) - {x["fact"]}:
                if cues(lx, n, x["sentence"]) and n not in r["fact_sources"].get(x["fact"], ()):
                    c["unlisted_fact_cue"] += 1
                    bad["unlisted_fact_cue"].append((r["id"], (n, x["sentence"])))
        if any(set(r["fact_sources"].get(n, ())) & set(miss) for n in tagged):
            c["derived_from_missing_stated"] += 1
            bad["derived_from_missing_stated"].append((r["id"], miss))
        if zs := presupposed(r):
            c["zero_guard_presupposed"] += 1
            bad["zero_guard_presupposed"].append((r["id"], zs))
        w, ok = r["gold"]["cd_witnesses"], E.decide(pol, r["facts"])["decision"] == "cannot determine"
        for d in ("approve", "deny"):
            ok = ok and w[d] is not None and set(w[d]) <= set(miss) and E.decide(pol, {**r["facts"], **w[d]})[
                "decision"] == d
        c["witness_pair_holds"] += ok
        if not ok:
            bad["witness_pair_fails"].append((r["id"], w))
    print(f"# cd audit: {a.audit}, slice {a.slice}, view {a.view}\n")
    print(f"{len(pop)} items, {len(cd)} cd ({len(cd) / len(pop):.1%}); by domain " +
          ", ".join(f"{d} {n}" for d, n in sorted(collections.Counter(r["domain"] for r in cd).items())) + "\n")
    print("| check | cd items or sentences |\n|---|---|")
    for k in ["items", "removed_fact_is_needed", "witness_pair_holds", "missing_fact_mentioned",
              "stated_facts_vs_tags", "derived_from_missing_stated", "zero_guard_presupposed", "unlisted_fact_cue",
              "value_not_found_enum", "value_not_found_number", "value_not_found_bool"]:
        print(f"| {k} | {c[k]} |")
    for k, xs in bad.items():
        print(f"\n## {k} ({len(xs)}), first 8\n")
        for i, x in xs[:8]:
            print(f"- {i}: {x}")
    print("\n## Enum renderings (yaml templates and Gemini sentences, all slices, prose views)\n")
    lossy_ids = collections.defaultdict(set)
    for d, dom in doms.items():
        seen = collections.defaultdict(collections.Counter)
        for r in recs:
            for x in r["case_sentences"] if r["domain"] == d and r["case_sentences"] else []:
                if x["fact"] in dom["facts"] and dom["facts"][x["fact"]]["type"] == "enum":
                    seen[x["fact"], x["value"]][x["sentence"]] += 1
        for n, f in dom["facts"].items():
            for v in f["values"] if f["type"] == "enum" else []:
                yml, ss = [s for s in renders(dom, n, v) if not names_value(f, v, s)], seen[n, v]
                lost = {s: k for s, k in ss.items() if not names_value(f, v, s)}
                wrong = {s for s in ss for u in f["values"] if u != v and names_value(f, u, s)}
                print(f"- {d}.{n}={v} ({f['names'][v]!r}, tokens {dist_pats(f)[v]}): yaml lossy {len(yml)}/"
                      f"{len(f['say'])}, Gemini {len(ss)} distinct / {sum(ss.values())} uses, lossy {len(lost)} "
                      f"distinct / {sum(lost.values())} uses, names another value {len(wrong)}")
                for s, k in sorted(lost.items(), key=lambda t: -t[1])[:4]:
                    print(f"  - lossy x{k}: {s!r}")
                lossy_ids[d] |= {(n, s) for s in lost}
    hurt = [r for r in cd if any((x["fact"], x["sentence"]) in lossy_ids[r["domain"]] and
                                 any(x["fact"] in q.all_refs for q in policy_for(r).requires)
                                 for x in r["case_sentences"])]
    print(f"\ncd items with a lossy enum sentence for a fact some rule reads: {len(hurt)}/{len(cd)}")
    for sl in sorted({r["slice"] for r in recs}):
        rs = [r for r in recs if r["slice"] == sl and r["view"] == a.view]
        k = sum(any((x["fact"], x["sentence"]) in lossy_ids[r["domain"]] for x in r["case_sentences"]) for r in rs)
        nb = sum(any(x["fact"] and kind(doms[r["domain"]], x["fact"]) == "number" and
                     not value_ok(doms[r["domain"]], x["fact"], x["value"], x["sentence"]) for x in r["case_sentences"])
                 for r in rs)
        print(f"- {sl}: {k}/{len(rs)} {a.view} items carry a lossy enum sentence, {nb} a number the heuristic misses")
    zg = [r for r in pop if any((m := re.fullmatch(r"(\w+) == 0 or (\w+)", q.get("cond", ""))) and r["facts"].get(
        m[1]) == 0 and m[2] in r["stated_facts"] for q in r["policy_spec"]["rules"])]
    print(f"\nitems in the slice whose text states a zero guard (e.g. 0 MB) next to a sentence presupposing the "
          f"guarded object (e.g. its logos): {len(zg)}/{len(pop)}")
    if a.flagged:
        fl = sorted(r["id"] for r in recs if r["case_sentences"] and (
            any((x["fact"], x["sentence"]) in lossy_ids[r["domain"]] for x in r["case_sentences"]) or
                r["gold"]["decision"] == "cannot determine" and presupposed(r)))
        Path(a.flagged).write_text("".join(i + "\n" for i in fl))
        print(f"\nflagged {len(fl)} items -> {a.flagged}: " + ", ".join(f"{k} {v}" for k, v in sorted(
            collections.Counter((byid[i]["split"], byid[i]["view"]) for i in fl).items())))
    out = {}
    for line in open(a.run) if a.run else []:
        o = json.loads(line)
        if o.get("mode") == "answer" and str(o.get("rep", "0")) == "0":
            m = re.search(r"Decision:\s*(approve|deny|cannot determine)", o.get("output") or "", re.I)
            out[o["id"]] = m[1].lower() if m else "unparsed"
    if a.run:
        got, hid = [(r, out[r["id"]]) for r in cd if r["id"] in out], {r["id"] for r in hurt}
        print(f"\n## Model decisions on cd items ({a.run})\n")
        for name, xs in [("all cd", got), ("with lossy enum", [g for g in got if g[0]["id"] in hid]),
                         ("without lossy enum", [g for g in got if g[0]["id"] not in hid])]:
            print(f"- {name}: n={len(xs)}, " + ", ".join(f"{k} {v}" for k, v in
                                                          collections.Counter(d for _, d in xs).most_common()))
    if a.sample:
        rng, by = random.Random(a.seed), collections.defaultdict(list)
        for r in cd:
            by[r["domain"]].append(r)
        per = -(-a.sample // len(by))
        print(f"\n## Sample: {a.sample} cd items, {per} per domain, seed {a.seed}\n")
        for d in sorted(by):
            for r in rng.sample(by[d], min(per, len(by[d]))):
                rules = {q["id"]: q["text"] for q in r["policy_spec"]["rules"]}
                print(f"### {r['id']} missing {r['gold']['needs_facts']} for "
                      f"{[(i, rules[i]) for i in r['gold']['needs_fact_for']]}")
                print(f"witnesses {r['gold']['cd_witnesses']}; model {out.get(r['id']) if a.run else '-'}")
                print("trace", r["gold"]["rule_trace"], "defaults", r["gold"]["defaults_applied"])
                print(r["case_text"] + "\n")


def main():
    """Parses the CLI and generates, labels and writes the items (or runs --report or --audit), printing a summary."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", default="all", help="comma list of " + ",".join(DOMAINS) + " or all")
    ap.add_argument("--n-policies", type=int, default=20, help="policies per domain")
    ap.add_argument("--policies-per-family", type=int, default=2)
    ap.add_argument("--cases-per-family", type=int, default=10, help="base cases per family, split over its policies")
    ap.add_argument("--train-cases-per-family", type=int, default=0,
                    help="base cases per train-split family (0 uses --cases-per-family)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="data/out.jsonl")
    ap.add_argument("--prose", choices=["template", "gemini"], default="template")
    ap.add_argument("--limit", type=int, default=0,
                    help="keep only the first N base families, each with its variants and views (0 keeps all)")
    ap.add_argument("--vertex", nargs="?", const="global", default=None, metavar="LOCATION",
                    help="use Vertex AI (GCP_PROJECT, ADC) in LOCATION (default global) instead of the API key")
    ap.add_argument("--gemini-model", default=None, help="pin the Gemini model (default: cheapest flash found)")
    ap.add_argument("--workers", type=int, default=4, help="parallel Gemini base rewrites")
    ap.add_argument("--cache", default="data/.gemini_cache", help="Gemini reply cache directory ('' disables)")
    ap.add_argument("--report", metavar="DATA", help="write DATA's stats.md and blind sample instead of generating")
    ap.add_argument("--log", default="", help="--report: gen.py stdout, for Gemini drops by domain and reason")
    ap.add_argument("--cmd", default="", help="--report: generation command, copied into the report")
    ap.add_argument("--n-blind", type=int, default=100)
    ap.add_argument("--audit", metavar="DATA", help="audit DATA's cannot-determine items instead of generating")
    ap.add_argument("--slice", default="unseen_family_train_vocab", help="--audit population")
    ap.add_argument("--view", default="prose", help="--audit population")
    ap.add_argument("--run", help="--audit: answer run whose decisions on cd items are reported")
    ap.add_argument("--sample", type=int, default=0, help="--audit: cd items printed for reading")
    ap.add_argument("--flagged", metavar="PATH", help="--audit: write lossy-enum and zero_guard_presupposed ids")
    a = ap.parse_args()
    if a.report or a.audit:
        return report(a) if a.report else audit(a)
    GEM.update(vertex=a.vertex, model=a.gemini_model, cache=a.cache)
    t0, recs, pols, tcase, invalid, norev = time.time(), [], [], [], 0, 0
    for dname in DOMAINS if a.domains == "all" else a.domains.split(","):
        dom = load_domain(dname)
        drng = random.Random(f"{a.seed}-{dname}-families")
        pairs = [(t["key"], d["fact"]) for t in dom["rules"] for d in dom["defaults"]
                 if t.get("unless") and d["fact"] in template_refs(dom, t, 0)]
        hold = drng.sample(pairs, min(len(pairs), drng.randint(1, 2)))
        nf = max(1, -(-a.n_policies // a.policies_per_family))
        fams = []
        for i in range(nf):
            fams.append(sample_family(dom, drng, hold, nf > 1 and i == 0, fams))
        rest = list(range(1, nf)) if nf > 1 else [0]
        drng.shuffle(rest)
        nt, nd = max(0, round(FRAC_TEST * nf) - (nf > 1)), round(FRAC_DEV * nf) if nf >= 5 else 0
        split = {0: "test_policy"} if nf > 1 else {}
        for i, fi in enumerate(rest):
            split[fi] = "test_policy" if i < nt else "dev" if i < nt + nd else "train"
        for p in range(a.n_policies):
            fi = p // a.policies_per_family
            rng = random.Random(f"{a.seed}-{dname}-{p}")
            pol = instantiate(dname, fams[fi], f"{dname}-p{p:03d}", rng)
            pols.append(pol)
            ncase = a.train_cases_per_family if a.train_cases_per_family and dname not in HELD_OUT and \
                split.get(fi) == "train" else a.cases_per_family
            j, npf = p % a.policies_per_family, min(a.policies_per_family, a.n_policies - fi * a.policies_per_family)
            ncase = ncase // npf + (j < ncase % npf)
            n_app = int(P_APPROVE * ncase + rng.random())
            wants = ["approve"] * n_app + ["deny"] * (ncase - n_app)
            rng.shuffle(wants)
            for c, want in enumerate(wants):
                tc = time.time()
                crng = random.Random(f"{a.seed}-{dname}-{p}-c{c}")
                f = sample_case(pol, crng, want)
                bid = f"{pol.id}-c{c:02d}"
                items, bcs = [(bid, "base", f, {}, None, None)], {}
                try:
                    g = gold_for(pol, f, bid)
                except E.InvalidRecord:
                    invalid += 1
                    continue
                if g["min_flip"]["edits"]:
                    items.append((bid + "-flip", "flip", {**f, **g["min_flip"]["edits"]}, g["min_flip"]["edits"],
                                  None, bid))
                inv = E.invariant_edit(pol, f, crng, g["sufficient_sets"])
                if inv:
                    items.append((bid + "-inv", "invariant", {**f, **inv}, inv, None, bid))
                used = {n for s in g["sufficient_sets"] for n in s}
                nec = g["necessary_facts"] or sorted(used, key=pol.order.index)
                pools = [[x for x in nec if x not in pol.defaults], [x for x in nec if x in pol.defaults],
                         [x for x in pol.order if x not in used]]
                u = crng.random()
                first = 0 if u < P_CD else 1 if u < P_CD + P_DEFAULT else 2
                pool = next((pl for pl in [pools[first]] + pools if pl), [])
                if pool:
                    x = crng.choice(pool)
                    items.append((bid + "-miss", "missing", {k: v for k, v in f.items() if k != x}, {}, x, bid))
                for iid, variant, facts, changed, removed, src in items:
                    try:
                        gi = g if variant == "base" else gold_for(pol, facts, iid)
                    except E.InvalidRecord:
                        invalid += 1
                        continue
                    if variant == "flip":
                        assert gi["decision"] == g["target"]
                    if variant == "invariant":
                        assert gi["decision"] == g["decision"]
                    if variant == "missing" and gi["min_reveal"] and gi["min_reveal"]["adds"]:
                        # takes the cheapest deciding add no sibling has, since min_reveal often restores the base
                        ks, sib = list(gi["min_reveal"]["adds"]), [it[2] for it in items]
                        for vs in sorted(itertools.product(*(pol.dom[n] for n in ks)),
                                         key=lambda vs: sum(pol.dom[n].index(v) for n, v in zip(ks, vs))):
                            adds = dict(zip(ks, vs))
                            try:
                                ok = {**facts, **adds} not in sib and \
                                  E.decide(pol, {**facts, **adds})["decision"] != "cannot determine"
                            except E.InvalidRecord:
                                ok = False
                            if ok:
                                items.append((bid + "-reveal", "reveal", {**facts, **adds}, adds, None, iid))
                                break
                        else:
                            norev += 1
                    eff = None
                    if removed:
                        eff = "cannot determine" if gi["decision"] == "cannot determine" else \
                            "default applied" if removed in gi["defaults_applied"] else \
                            "unchanged" if gi["decision"] == g["decision"] else "changed"
                    sp = HELD_OUT[dname] if dname in HELD_OUT else split[fi]
                    inter = not gi["single_condition"] and len(gi["sufficient_sets"]) >= 2 \
                        if variant == "base" else None
                    fs = E.fact_states(pol, facts)
                    for view in VIEWS:
                        cs = case_sentences(pol, facts, bid, view, bcs.get(view)) if view != "table" else None
                        if variant == "base":
                            bcs[view] = cs
                        said = [x["fact"] for x in cs if x["fact"]] if cs else \
                            [n for n, s in fs.items() if s["state"] == "observed" or
                             s["state"] == "derived" and all(x in facts for x in s["sources"])]
                        recs.append({"id": f"{iid}:{view}", "domain": dname, "policy_id": pol.id,
                                     "template_family": f"{dname}-f{fi:02d}",
                                     "holdout_structure": nf > 1 and fi == 0, "split": sp, "slice": SLICE[sp],
                                     "view": view, "interaction": inter,
                                     "variant": variant, "edit_kind": EDIT_KIND[variant],
                                     "parent": None if iid == bid else f"{bid}:{view}",
                                     "edited_from": f"{src}:{view}" if src else None,
                                     "policy_text": pol.text, "case_sentences": cs, "prose_source": "template",
                                     "seam_template": None, "case_text": " ".join(x["sentence"] for x in cs) if cs
                                     else render_case(pol, facts, bid, view=view),
                                     "facts": facts, "stated_facts": said, "fact_labels": pol.labels,
                                     "fact_states": fs,
                                     "fact_sources": {n: refs for n, (_, refs) in pol.dfn.items()},
                                     "policy_spec": pol.spec, "changed_facts": changed,
                                     "removed_fact": removed, "removed_effect": eff, "gold": gi})
                tcase.append(time.time() - tc)
            pol.cache.clear()

    def base_of(r):
        """Returns the base item id (view suffix stripped) of a record's family."""
        return (r["parent"] or r["id"]).split(":")[0]

    if a.limit:
        keep = set(list(dict.fromkeys(map(base_of, recs)))[:a.limit])
        recs = [r for r in recs if base_of(r) in keep]
    dropped, limited = 0, threading.Event()
    if a.prose == "gemini":
        from google.genai import errors

        fams = collections.defaultdict(list)
        for r in recs:
            fams[base_of(r)].append(r)

        def rewrite(bid, rs):
            """
            Returns (records, dropped) for one base family: the Gemini rewrite swapped into every prose view
            if its re-extraction matches the base facts and no tag name or untagged fact shows, else ([],
            1), or unchanged as template prose once `limited` is set. Each template sentence a variant swaps
            in is restyled against the base file and kept only if read alone it states exactly its fact and
            value. Enum sentences without a distinguishing name token stay template.
            """
            base = next((r for r in rs if r["variant"] == "base" and r["view"] == "prose"), None)
            if limited.is_set() or base is None:
                return rs, 0
            dom = load_domain(base["domain"])
            tagged = [{"fact": x["fact"], "sentence": x["sentence"]} for x in base["case_sentences"]]
            lines = []
            for n, sf in dom["facts"].items():
                kind = "date as YYYY-MM-DD" if sf.get("date") else "integer" if sf["type"] == "int" else \
                    "true or false" if sf["type"] == "bool" else \
                    "one of " + ", ".join(f"{v!r} ({sf['names'][v]})" for v in sf["values"])
                lines.append(f"- {n}: {sf['label']}; {kind}")
            try:
                new = json.loads(gemini_call(
                    f"Rewrite this case file for {dom['title']} so it reads like a realistic file. The input is a "
                    f"JSON list of sentences, each tagged with the fact it states (null for header or color). Return a "
                    f"JSON list of the same length and order with the same \"fact\" tags and a rewritten \"sentence\" "
                    f"for each. Every tagged sentence must state exactly its fact with the same value and nothing "
                    f"else; untagged sentences must not state any fact. Dates stay dates, amounts stay amounts. Write "
                    f"each as a full natural sentence and never put a tag name in it. Do not mention rules or "
                    f"decisions.\n\n{json.dumps(tagged)}", json_out=True))
                ask = "Read the case file and return one JSON object with exactly these keys. Use null when the " \
                    "case file does not state the fact. Compute a value only when the key's description asks for " \
                    "it.\n" + "\n".join(lines) + "\n\nCase file:\n"
                raw = json.loads(gemini_call(ask + " ".join(x["sentence"] for x in new), json_out=True))
                stray = json.loads(gemini_call(
                    "Here is a list of fact keys with descriptions, then a short text. Return a JSON list of the keys "
                    "whose value the text states or clearly implies. Return [] if it states none. Do not guess from "
                    "what the text leaves out.\n" +
                      "\n".join(f"- {n}: {sf['label']}" for n, sf in dom["facts"].items()) +
                    "\n\nText:\n" + " ".join(y["sentence"] for y in new if y.get("fact") is None), json_out=True))
            except (errors.APIError, RuntimeError) as e:
                code = getattr(e, "code", None)
                if code not in (429, 503, None):
                    raise
                if not limited.is_set():
                    print("Gemini rate limited (429)" if code == 429 else f"Gemini unavailable ({code or e})",
                          "- falling back to template prose for the remaining items")
                limited.set()
                return rs, 0
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                print("dropped base family", bid, "unparsable reply:", e)
                return [], 1

            def conv(n, v):
                """Returns an extracted value in engine form: dates as day offsets, ints as int."""
                sf = dom["facts"].get(n)
                if v is None or sf and sf["type"] != "int":
                    return v
                return (datetime.date.fromisoformat(str(v)) - dom["ref_date"]).days if sf and sf.get("date") else int(v)

            keys = [k for k in list(dom["facts"]) + list(dom["derived_facts"]) if "_" in k]
            leaky = lambda s: bool(re.match(r"\s*[a-z_]+\s*:", s) or any(re.search(rf"\b{k}\b", s) for k in keys))
            lossy = lambda n, v, s: dom["facts"].get(n, {}).get("type") == "enum" and \
                    not names_value(dom["facts"][n], v, s)
            try:
                back = {n: conv(n, raw.get(n)) for n in dom["facts"]}
            except (ValueError, TypeError, AttributeError) as e:
                print("dropped base family", bid, "unparsable extraction:", e)
                return [], 1
            same = [x.get("fact") for x in new] == [x["fact"] for x in tagged]
            leak = [y["sentence"] for y in new if leaky(y["sentence"])]
            leak += [f"untagged sentences state {n}" for n in (stray if isinstance(stray, list) else ["?"])]
            if not same or leak or any(back[n] != base["facts"].get(n) for n in dom["facts"]):
                print("dropped base family", bid, "tags changed" if not same else f"leak: {leak[0]!r}"
                      if leak else {n: (back[n], base["facts"].get(n)) for n in dom["facts"]
                                    if back[n] != base["facts"].get(n)})
                return [], 1
            gs = [x if lossy(x["fact"], x["value"], y["sentence"]) else {**x, "sentence": y["sentence"]}
                  for x, y in zip(base["case_sentences"], new)]
            nl = sum(x is y for x, y in zip(gs, base["case_sentences"]) if x["fact"])
            orig, sw = {x["fact"]: x["sentence"] for x in gs if x["fact"]}, {}
            for r in rs:
                if r["view"] != "table":
                    r["case_sentences"] = case_sentences(r, r["facts"], bid, r["view"], gs)
                    sw.update({(x["fact"], x["value"]): x["sentence"] for x in r["case_sentences"]
                               if x["fact"] and x["sentence"] != orig.get(x["fact"])})
            fix, todo = {}, list(sw.items())
            try:
                if todo:
                    out = json.loads(gemini_call(
                        f"Below is a case file for {dom['title']}, then a JSON list of edits. Each edit gives a "
                        f"sentence from the file (\"old\", null if none) and a plain sentence (\"new\") that states "
                        f"a different value for the same point. For each edit, write the new sentence in the style "
                        f"of the file: reuse the old sentence's wording and change only what the new value "
                        f"requires. It must state exactly what \"new\" states, with the same value, and nothing "
                        f"else. Never put a tag name in it and do not mention rules or decisions. Return a JSON list "
                        f"of strings, one per edit, in order.\n\nCase file:\n{' '.join(x['sentence'] for x in gs)}"
                        f"\n\nEdits:\n{json.dumps([{'old': orig.get(f), 'new': s} for (f, _), s in todo])}",
                        json_out=True))
                    out = [s if isinstance(s, str) and not leaky(s) else None for s in out][:len(todo)]
                    dl = [f"- {n}: {d['label']}; integer" for n, d in dom["derived_facts"].items()]
                    chk = json.loads(gemini_call(
                        "For each numbered sentence below, return the facts it states: a JSON list with one object "
                        "per sentence, in order, mapping each key the sentence states to its value and leaving out "
                        "every key it does not state. Compute a value only when the key's description asks for "
                        "it.\n" + "\n".join(lines + dl) + "\n\nSentences:\n" +
                          "\n".join(f"{i + 1}. {s}" for i, s in enumerate(out)), json_out=True))
                    for ((f, v), _), s, got in zip(todo, out, chk):
                        try:
                            if s and {k: conv(k, w) for k, w in got.items() if w is not None} == {f: v}:
                                if not lossy(f, v, s):
                                    fix[f, v] = s
                                else:
                                    nl += 1
                        except (ValueError, TypeError, AttributeError):
                            pass
            except (errors.APIError, RuntimeError, ValueError, TypeError) as e:
                print("seam rewrite fell back to template sentences for", bid, e)
            with GEM_LOCK:
                GEM["seam"].update({"rewritten": len(fix), "template": len(todo) - len(fix)})
                GEM["lossy"]["enum"] += nl
            for r in rs:
                if r["view"] != "table":
                    r["case_sentences"] = [{**x, "sentence": fix[x["fact"], x["value"]]}
                                           if (x["fact"], x["value"]) in fix else x for x in r["case_sentences"]]
                    r["seam_template"] = [x["fact"] for x in r["case_sentences"] if
                                          (x["fact"], x["value"]) in sw and (x["fact"], x["value"]) not in fix]
                    r["case_text"] = " ".join(x["sentence"] for x in r["case_sentences"])
                    r["prose_source"] = "gemini"
            return rs, 0

        kept = []
        with concurrent.futures.ThreadPoolExecutor(max(1, a.workers)) as ex:
            futs = [ex.submit(rewrite, bid, rs) for bid, rs in fams.items()]
            for i, fu in enumerate(futs):
                rs, d = fu.result()
                kept.extend(rs)
                dropped += d
                if (i + 1) % 50 == 0:
                    print(f"gemini: {i + 1}/{len(futs)} base families, dropped {dropped}, usage",
                          dict(GEM["usage"]), flush=True)
        recs = kept
    # drops items whose text repeats an earlier one, with the items built from them, in every view
    seen, dup = set(), set()
    for r in recs:
        if (r["view"], r["case_text"]) in seen:
            dup.add(r["id"].split(":")[0])
        seen.add((r["view"], r["case_text"]))
    drop = dup | {r["id"].split(":")[0] for r in recs if
                  any((x or "").split(":")[0] in dup for x in (r["parent"], r["edited_from"]))}
    recs = [r for r in recs if r["id"].split(":")[0] not in drop]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    one = [r for r in recs if r["view"] == "prose"]
    cnt = collections.Counter((r["variant"], r["gold"]["decision"]) for r in one)
    print(f"{len(recs)} records ({len(one)} items x {len(VIEWS)} views) from {len(pols)} policies -> {out} "
          f"in {time.time() - t0:.1f}s, {sum(tcase) / max(1, len(tcase)):.2f}s per base case with its variants")
    print("decisions:", dict(collections.Counter(r["gold"]["decision"] for r in one)))
    print("variant x decision:", {f"{v}/{d}": k for (v, d), k in sorted(cnt.items())})
    print("missing effects:", dict(collections.Counter(r["removed_effect"] for r in one if r["variant"] == "missing")))
    print("splits (items):", dict(collections.Counter(r["split"] for r in one)),
          "holdout_structure items:", sum(r["holdout_structure"] for r in one))
    print(f"policy: {sum(len(p.requires) + len(p.defaults) for p in pols) / len(pols):.1f} rules, "
          f"{sum(len(p.text.split()) for p in pols) / len(pols):.0f} words on average")
    for view in VIEWS:
        wc = [len(r["case_text"].split()) for r in recs if r["view"] == view]
        if wc:
            print(f"{view} words: mean {sum(wc) / len(wc):.0f}, min {min(wc)}, max {max(wc)}")
    print("flip radius:", dict(collections.Counter(len(r["changed_facts"]) for r in one if r["variant"] == "flip")),
          "certified no flip within radius 4:", sum("exhausted_radius" in r["gold"]["min_flip"] for r in one))
    print("single_condition:", sum(r["gold"]["single_condition"] for r in one), "of", len(one),
          "| interaction bases:", sum(bool(r["interaction"]) for r in one), "| invalid records skipped:", invalid)
    print("reveal skipped (every deciding add copies a sibling):", norev,
          "| items dropped as duplicate text:", len(dup))
    print("uncertified (over budget):", sum(r["gold"]["uncertified"] for r in one),
          dict(collections.Counter(x.split(":")[0] for r in one for x in r["gold"]["uncertified_reasons"])))
    print("reveal radius:", dict(collections.Counter(r["gold"]["min_reveal"].get("radius") for r in one
                                                     if r["gold"]["min_reveal"])))
    if a.prose == "gemini":
        print(f"gemini: model {GEM.get('chosen')}, dropped {dropped} base families on check failure, "
              f"rate limited: {limited.is_set()}, usage {dict(GEM['usage'])}")
        sm = GEM["seam"]
        print(f"seam: {sm['rewritten']} swapped sentences restyled, {sm['template']} kept as template "
              f"({sm['template'] / max(1, sum(sm.values())):.1%} fallback), {GEM['lossy']['enum']} lossy enum "
              f"sentences kept as template")


if __name__ == "__main__":
    main()
