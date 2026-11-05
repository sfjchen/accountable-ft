"""Generates policy/case items with engine gold labels for the accountable-ft project.

For each domain in domains/*.yaml it samples template families (which rule templates, exceptions and
defaults a policy uses, before thresholds), instantiates each family as several policies with fresh
thresholds and rule order, then samples base cases with a target approve/deny mix and three variants
per base: flip (engine minimal flip), invariant (edit outside every sufficient set) and missing (one
fact removed, which may trigger a default), plus a reveal variant (min_reveal facts added) for each
cannot-determine missing item. Edit kinds: replace (flip, invariant), remove (missing), add (reveal).
Every item is written in three aligned views: "table" (fact list with derived values), "prose" (derived
values stated) and "prose_derive" (only source facts, so the reader must derive). Prose comes from
fact-sentence templates. With --prose gemini each base case is rewritten once as fact-tagged sentences,
checked by re-extraction, and every variant and view swaps only the sentences of its edited facts; a
failed check drops the whole base family.

Splits are by template family: 70/10/20 train/dev/test_policy inside grant, trial and review, the whole
permit domain is test_domain, and one family per domain that carries a held-out exception/default
combination goes to test with holdout_structure true. "slice" names the evaluation population.

Eval helpers: policy_for(record) rebuilds the Policy, render_case(...) re-renders an edited case aligned.

Usage: python gen.py --domains all --n-policies 4 --cases-per-policy 5 --seed 0 --prose template --out data/smoke.jsonl
"""
import argparse
import collections
import datetime
import json
import random
import re
import string
import time
from pathlib import Path

import yaml

import engine as E

ROOT = Path(__file__).resolve().parent
DOMAINS = ["grant", "permit", "trial", "review"]
HELD_OUT = "permit"
VIEWS = ["table", "prose", "prose_derive"]
SLICE = {"train": "train", "dev": "dev", "test_policy": "unseen_family_train_vocab", "test_domain": "combined_transfer"}
EDIT_KIND = {"base": None, "flip": "replace", "invariant": "replace", "missing": "remove", "reveal": "add"}
P_APPROVE, P_CD, P_DEFAULT, MIN_FAM_DIST = 0.43, 0.6, 0.25, 4
DOM_CACHE, GEM = {}, {}


def load_domain(name):
    """
    Returns the parsed domain YAML for `name`, with compiled derived-fact functions under "_dfn", cached.
    """
    if name not in DOM_CACHE:
        dom = yaml.safe_load((ROOT / "domains" / f"{name}.yaml").read_text())
        dom["_dfn"] = {n: E.compile_cond(d["expr"], set(dom["facts"])) for n, d in dom["derived_facts"].items()}
        DOM_CACHE[name] = dom
    return DOM_CACHE[name]


class Fmt(string.Formatter):
    """
    Formats rule and case templates. Specs: money, date (day offset), ago (year = ref year - v),
    k (thousands), t (tonnes from kg), e (enum display name of the current fact), e:<fact>.
    """

    def __init__(self, dom, fact=None):
        """
        Builds a formatter bound to a domain vocabulary and optionally the fact being rendered.
        """
        super().__init__()
        self.dom, self.fact = dom, fact

    def format_field(self, v, spec):
        """
        Returns the display string for value v under the given spec.
        """
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
        if spec.startswith("e"):
            names = self.dom["facts"][spec[2:] or self.fact]["names"]
            if not isinstance(v, list):
                return names[v]
            ws = [names[x] for x in v]
            return ", ".join(ws[:-1]) + " or " + ws[-1]
        return super().format_field(v, spec)


def template_refs(dom, t, exc=None):
    """
    Returns the source facts a rule template (and optionally one of its exceptions) reads.
    """
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
    Returns a template family {"core": [(key, exception index or None)], "derived": [keys],
    "defaults": [facts], "parts": [structural parts]} with 2-4 exceptions, at least 2 scoped rules,
    1-2 derived-fact rules, 1-2 defaults on live facts, 8-15 rules and at most MAX_FACTS facts read.
    want_hold forces a held-out combination in, otherwise every held-out combination is kept out.
    Families within MIN_FAM_DIST parts of one in `prev` are rejected as near-duplicates.
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
    """
    Adds sampled template parameters to vals: lists are choices, strings are expressions over earlier ones.
    """
    for k, p in (params or {}).items():
        vals[k] = rng.choice(p) if isinstance(p, list) else eval(p, {"__builtins__": {}}, dict(vals))


def instantiate(dname, fam, pid, rng):
    """
    Returns a Policy for a template family with sampled thresholds and shuffled rule order. Sets
    .domain, .text, .labels and .near (rule id -> near-miss lambda). Every rule must be able both to
    hold and to fail, and approval must be reachable.
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
    """
    Returns the engine Policy for a record, rebuilt from its "policy_spec" (rules, validity conditions,
    derived facts) and the domain's fact schema, with .domain, .spec, .labels, .near and .text set.
    """
    sp, dom = record["policy_spec"], load_domain(record["domain"])
    pol = E.Policy(record["policy_id"], dom["facts"], sp["rules"], sp["valid"], sp["derived"])
    pol.domain, pol.spec, pol.labels, pol.text = record["domain"], sp, record["fact_labels"], record["policy_text"]
    pol.near = {r["id"]: E.compile_cond(r["near"], set(dom["facts"]), sp["derived"])[0] for r in sp["rules"]
                if r.get("near")}
    return pol


def sample_case(pol, rng, want):
    """
    Returns a complete admissible fact dict whose decision is `want`. Repairs a random draw until every
    rule holds, sometimes moves a rule into its waived state or a scoped rule into its near-miss state,
    then for deny breaks 1-2 rules.
    """

    def bad(g):
        """
        Returns the number of failed rules plus 1 if g violates a validity condition.
        """
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


def case_sentences(policy, facts, seed, view="prose", base=None):
    """
    Returns the case as [{"fact", "value", "sentence"}] (fact None for header and color sentences) for
    the prose views. The seed (base item id, any ":view" suffix stripped) fixes header, phrasings, order
    and color. With `base` (the base record's tagged sentences, e.g. a Gemini rewrite) it keeps the base
    order and wording, swaps in the template sentence for each fact whose value differs from the base,
    and drops sentences of facts that are unstated here (derived ones too in prose_derive).
    """
    dname = policy["domain"] if isinstance(policy, dict) else getattr(policy, "domain", policy)
    dom = load_domain(dname)
    rng = random.Random(str(seed).split(":")[0])
    head = rng.choice(dom["intro"]).format(name=rng.choice(dom["names"]), num=rng.randint(1000, 9999))
    picks = {n: rng.random() for n in dom["facts"]}
    pool = rng.sample(dom["color"], len(dom["color"]))
    ncol = rng.randint(2, 4)
    keys = list(dom["facts"]) + list(dom["derived_facts"]) + list(range(ncol))
    rng.shuffle(keys)
    stated = {n: v for n, v in facts.items() if n in dom["facts"] and v is not None}
    dv = {}
    for n, (fn, refs) in dom["_dfn"].items():
        if all(x in stated for x in refs):
            dv[n] = fn(stated)
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
    Returns the case text for `facts` in `view`; prose views join case_sentences (pass the base record's
    "case_sentences" as `base` to stay aligned with a Gemini rewrite, required for prose="gemini").
    """
    dname = policy["domain"] if isinstance(policy, dict) else getattr(policy, "domain", policy)
    dom = load_domain(dname)
    if prose == "gemini" and base is None and view != "table":
        raise ValueError("prose='gemini' needs the base record's case_sentences as base")
    if view != "table":
        return " ".join(x["sentence"] for x in case_sentences(dname, facts, seed, view, base))
    stated = {n: v for n, v in facts.items() if n in dom["facts"] and v is not None}
    dv = {n: fn(stated) for n, (fn, refs) in dom["_dfn"].items() if all(x in stated for x in refs)}
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
    Returns the gold dict for a fact dict: decision, trace, all minimal sufficient sets (always at source
    level: derived facts never appear) with the minimum-cardinality ones, necessary facts, the fixed flip
    target and min_flip, defaults,
    case-level distractors (facts outside every minimal sufficient set, and holding rules that read such
    a fact), and for "cannot determine" the two witness completions, the missing facts behind the
    undecided rules and min_reveal. Searches over budget mark the gold uncertified with reasons.
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


def gemini_call(prompt, json_out=False):
    """
    Returns one Gemini reply, building a Vertex (GEM["vertex"]) or API-key client on first use, cheapest flash first.
    """
    from google import genai
    from google.genai import errors, types

    if "client" not in GEM:
        path, env = Path.home() / ".config" / "cs224v" / ".env", {}
        for ln in path.read_text().splitlines() if path.exists() else []:
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
        if GEM.get("vertex"):
            import google.auth

            if not env.get("GCP_PROJECT"):
                raise RuntimeError(f"no GCP_PROJECT in {path}")
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"],
                                           quota_project_id=env["GCP_PROJECT"])
            GEM["client"] = genai.Client(vertexai=True, project=env["GCP_PROJECT"], location=GEM["vertex"],
                                         credentials=creds)
            models = GEM["client"].models.list(config={"query_base": True})
        else:
            if not env.get("GEMINI_API_KEY"):
                raise RuntimeError(f"no GEMINI_API_KEY in {path}")
            GEM["client"] = genai.Client(api_key=env["GEMINI_API_KEY"])
            models = GEM["client"].models.list()
        ids = []
        for m in models:
            mid = m.name.split("/")[-1]
            acts = m.supported_actions
            if (acts is None or "generateContent" in acts) and "flash" in mid and \
              not re.search(r"image|tts|live|audio|embed|exp|preview|latest|thinking|native|computer", mid):
                ids.append(mid)
        ver = {mid: float((re.search(r"gemini-(\d+(?:\.\d+)?)", mid) or [0, 0])[1]) for mid in ids}
        GEM["ids"] = sorted(ids, key=lambda mid: ("lite" not in mid, -ver[mid], len(mid)))
        print("flash-class candidates, cheapest first:", ", ".join(GEM["ids"]))
    cfg = types.GenerateContentConfig(temperature=0.7 if not json_out else 0.0,
                                      response_mime_type="application/json" if json_out else "text/plain")
    tries = 0
    while GEM["ids"]:
        try:
            out = GEM["client"].models.generate_content(model=GEM["ids"][0], contents=prompt, config=cfg).text
            if not GEM.get("chosen"):
                GEM["chosen"] = GEM["ids"][0]
                print("Gemini model:", GEM["chosen"])
            return out
        except errors.ServerError as e:
            tries += 1
            if tries > 3:
                raise
            time.sleep(5 * tries)
        except errors.ClientError as e:
            if e.code == 429 or GEM.get("chosen"):
                raise
            print(f"Gemini model {GEM['ids'][0]} unavailable ({e.code}), trying the next one")
            GEM["ids"].pop(0)
    raise RuntimeError("no usable Gemini model")


def main():
    """
    Parses the CLI, generates and labels all items in three views, optionally rewrites prose with
    Gemini, writes JSONL and prints a run summary.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", default="all", help="comma list of " + ",".join(DOMAINS) + " or all")
    ap.add_argument("--n-policies", type=int, default=20, help="policies per domain")
    ap.add_argument("--policies-per-family", type=int, default=2)
    ap.add_argument("--cases-per-policy", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="data/out.jsonl")
    ap.add_argument("--prose", choices=["template", "gemini"], default="template")
    ap.add_argument("--limit", type=int, default=0, help="keep only the first N records (0 keeps all)")
    ap.add_argument("--vertex", nargs="?", const="global", default=None, metavar="LOCATION",
                    help="use Vertex AI (GCP_PROJECT, ADC) in LOCATION (default global) instead of the API key")
    a = ap.parse_args()
    GEM["vertex"] = a.vertex
    t0, recs, pols, tcase, invalid = time.time(), [], [], [], 0
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
        nt, nd = max(0, round(0.2 * nf) - (nf > 1)), round(0.1 * nf) if nf >= 5 else 0
        split = {0: "test_policy"} if nf > 1 else {}
        for i, fi in enumerate(rest):
            split[fi] = "test_policy" if i < nt else "dev" if i < nt + nd else "train"
        for p in range(a.n_policies):
            fi = p // a.policies_per_family
            rng = random.Random(f"{a.seed}-{dname}-{p}")
            pol = instantiate(dname, fams[fi], f"{dname}-p{p:03d}", rng)
            pols.append(pol)
            n_app = int(P_APPROVE * a.cases_per_policy + rng.random())
            wants = ["approve"] * n_app + ["deny"] * (a.cases_per_policy - n_app)
            rng.shuffle(wants)
            for c, want in enumerate(wants):
                tc = time.time()
                f = sample_case(pol, rng, want)
                bid = f"{pol.id}-c{c:02d}"
                items = [(bid, "base", f, {}, None, None)]
                try:
                    g = gold_for(pol, f, bid)
                except E.InvalidRecord:
                    invalid += 1
                    continue
                if g["min_flip"]["edits"]:
                    items.append((bid + "-flip", "flip", {**f, **g["min_flip"]["edits"]}, g["min_flip"]["edits"],
                                  None, bid))
                inv = E.invariant_edit(pol, f, rng, g["sufficient_sets"])
                if inv:
                    items.append((bid + "-inv", "invariant", {**f, **inv}, inv, None, bid))
                used = {n for s in g["sufficient_sets"] for n in s}
                nec = g["necessary_facts"] or sorted(used, key=pol.order.index)
                pools = [[x for x in nec if x not in pol.defaults], [x for x in nec if x in pol.defaults],
                         [x for x in pol.order if x not in used]]
                u = rng.random()
                first = 0 if u < P_CD else 1 if u < P_CD + P_DEFAULT else 2
                pool = next((pl for pl in [pools[first]] + pools if pl), [])
                if pool:
                    x = rng.choice(pool)
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
                        adds = gi["min_reveal"]["adds"]
                        items.append((bid + "-reveal", "reveal", {**facts, **adds}, adds, None, iid))
                    eff = None
                    if removed:
                        eff = "cannot determine" if gi["decision"] == "cannot determine" else \
                            "default applied" if removed in gi["defaults_applied"] else \
                            "unchanged" if gi["decision"] == g["decision"] else "changed"
                    sp = "test_domain" if dname == HELD_OUT else split[fi]
                    inter = not gi["single_condition"] and len(gi["sufficient_sets"]) >= 2 \
                        if variant == "base" else None
                    for view in VIEWS:
                        cs = case_sentences(pol, facts, bid, view) if view != "table" else None
                        recs.append({"id": f"{iid}:{view}", "domain": dname, "policy_id": pol.id,
                                     "template_family": f"{dname}-f{fi:02d}",
                                     "holdout_structure": nf > 1 and fi == 0, "split": sp, "slice": SLICE[sp],
                                     "view": view, "interaction": inter,
                                     "variant": variant, "edit_kind": EDIT_KIND[variant],
                                     "parent": None if iid == bid else f"{bid}:{view}",
                                     "edited_from": f"{src}:{view}" if src else None,
                                     "policy_text": pol.text, "case_sentences": cs, "prose_source": "template",
                                     "case_text": render_case(pol, facts, bid, view=view),
                                     "facts": facts, "stated_facts": list(facts), "fact_labels": pol.labels,
                                     "fact_states": E.fact_states(pol, facts),
                                     "fact_sources": {n: refs for n, (_, refs) in pol.dfn.items()},
                                     "policy_spec": pol.spec, "changed_facts": changed,
                                     "removed_fact": removed, "removed_effect": eff, "gold": gi})
                tcase.append(time.time() - tc)
    if a.limit:
        recs = recs[:a.limit]
    dropped, limited = 0, False
    if a.prose == "gemini":
        from google.genai import errors

        fams = collections.defaultdict(list)
        for r in recs:
            fams[r["id"].split(":")[0] if r["variant"] == "base" else r["parent"].split(":")[0]].append(r)
        kept = []
        for bid, rs in fams.items():
            base = next((r for r in rs if r["variant"] == "base" and r["view"] == "prose"), None)
            if limited or base is None:
                kept.extend(rs)
                continue
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
                    f"else; untagged sentences must not state any fact. Dates stay dates, amounts stay amounts. Do "
                    f"not mention rules or decisions.\n\n{json.dumps(tagged)}", json_out=True))
                text = " ".join(x["sentence"] for x in new)
                raw = json.loads(gemini_call(
                    "Read the case file and return one JSON object with exactly these keys. Use null when the case "
                    "file does not state the fact. Compute a value only when the key's description asks for it.\n" +
                      "\n".join(lines) + f"\n\nCase file:\n{text}", json_out=True))
            except (errors.APIError, RuntimeError) as e:
                code = getattr(e, "code", None)
                if code not in (429, 503, None):
                    raise
                print("Gemini rate limited (429)" if code == 429 else f"Gemini unavailable ({code or e})",
                      "- falling back to template prose for the remaining items")
                limited = True
                kept.extend(rs)
                continue
            back = {}
            for n, sf in dom["facts"].items():
                v = raw.get(n)
                if v is not None and sf.get("date"):
                    v = (datetime.date.fromisoformat(str(v)) - dom["ref_date"]).days
                elif v is not None and sf["type"] == "int":
                    v = int(v)
                back[n] = v
            same = [x["fact"] for x in new] == [x["fact"] for x in tagged]
            if not same or any(back[n] != base["facts"].get(n) for n in dom["facts"]):
                dropped += 1
                print("dropped base family", bid, "tags changed" if not same else
                      {n: (back[n], base["facts"].get(n)) for n in dom["facts"] if back[n] != base["facts"].get(n)})
                continue
            gs = [{**x, "sentence": y["sentence"]} for x, y in zip(base["case_sentences"], new)]
            for r in rs:
                if r["view"] != "table":
                    r["case_sentences"] = case_sentences(r, r["facts"], bid, r["view"], gs)
                    r["case_text"] = " ".join(x["sentence"] for x in r["case_sentences"])
                    r["prose_source"] = "gemini"
                kept.append(r)
        recs = kept
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
    print("uncertified (over budget):", sum(r["gold"]["uncertified"] for r in one),
          dict(collections.Counter(x.split(":")[0] for r in one for x in r["gold"]["uncertified_reasons"])))
    print("reveal radius:", dict(collections.Counter(r["gold"]["min_reveal"].get("radius") for r in one
                                                     if r["gold"]["min_reveal"])))
    if a.prose == "gemini":
        print(f"gemini: model {GEM.get('chosen')}, dropped {dropped} base families on check failure, "
              f"rate limited: {limited}")


if __name__ == "__main__":
    main()
