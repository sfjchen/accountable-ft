"""Runs one model over a data file and writes one JSONL row per (item, sample), plus <out>.meta.json with tokens, wall
time and a cost estimate.

A single Runner wraps three backends with the same prompt and fixed decoding: "openai" for any OpenAI-compatible
endpoint (vLLM serve, OpenRouter, OpenAI), "gemini" through google-genai, and "vllm" for offline batch generation.
"gemini" takes --vertex [LOCATION] to go through Vertex AI (ADC credentials, GCP_PROJECT) instead of the API key.
Sample i of an item uses seed + i. Every response is cached in a JSONL keyed by a hash of backend (with the Vertex
location), model, prompt, decoding and repeat index, so a rerun only calls the model for what is missing and
--rep 1 forces a fresh run of the same prompts (the repeat-without-edit control). --cache-tag joins the key too and
is required for a local checkpoint, whose model path stays the same when the weights under it change. API keys come
from environment variables, filled from ~/.config/cs224v/.env when unset, and are never printed. --slice, --view
and --cases K (a seeded sample of K base cases stratified over (domain, template_family), each with all its views
and variants, so pairs and bank items stay whole) pick a subset of the data file. Every row keeps finish, token
counts, response_id and model_version for auditing.

Modes:
- answer: the ordinary decision call (decision, policy support, assumptions, smallest change that would reverse the
  decision). The prompt never names a target label, so it carries no trace of the gold decision. With --bank it
  also answers the bank's engine-built edited cases of the selected records (the fresh decisions for those items).
- bank: builds the intervention bank once, data/<name>.bank.jsonl plus <bank>.meta.json (mix, sources, drops),
  reused for every model, on the primary population (slice unseen_family_train_vocab, view prose) unless
  --wide-bank or --slice/--view say otherwise.
- predict: the self-prediction call. For each bank item it shows the case, the model's own frozen answer from
  --frozen (sample 0 of an answer run; with --no-account only its decision), and one edit, and asks for the
  predicted decision after the edit. The fresh decision on the edited case is the answer run's own row for the
  edited record, so it carries no trace of the prediction.
- simulate: external simulatability. A fixed external predictor (gemini-3.5-flash-lite, thinking off, --vertex)
  sees the policy, the frozen account (decision, policy support, assumptions; no case text, no smallest change)
  and the edit, and predicts the model's decision after the edit. --no-account gives it only the decision, and
  --shuffle-accounts keeps the item's own Decision line but takes the Policy support and Assumptions lines from the
  frozen answer on another case under the same policy (rows carry shuf_src "frozen", shuf_partner and
  shuf_decision_match, whether the partner decided the same way). An item whose case has no such partner in the
  frozen run is skipped and counted in shuf_missing. --all-sim runs all 3 passes in one call into
  <frozen>.simulate.jsonl, <frozen>.simulate_shuf.jsonl and <frozen>.simulate_noacc.jsonl.

format_target(record) renders the gold account in the answer format; the SFT script uses it as the target sequence.

Usage:
  python infer.py --mode bank --data data/x.jsonl
  python infer.py --data data/x.jsonl --bank data/x.bank.jsonl --backend gemini --vertex \
          --model gemini-3.5-flash-lite --slice unseen_family_train_vocab --view prose --cases 13 --out runs/name.jsonl
  python infer.py --mode predict --data data/x.jsonl --bank data/x.bank.jsonl --frozen runs/name.jsonl \
          --backend gemini --vertex --model gemini-3.5-flash-lite --out runs/name.predict.jsonl [--no-account]
  python infer.py --mode simulate --data data/x.jsonl --bank data/x.bank.jsonl --frozen runs/name.jsonl \
          --backend gemini --vertex --model gemini-3.5-flash-lite --all-sim
"""
import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import engine
import gen
from evaluate import bank_recs, load, parse, sections

SYSTEM = ("You decide cases under a written policy. Apply only the numbered rules of the policy, not outside "
        "knowledge or common practice. Reply in exactly the requested format with no other text.")
FORMAT = """Reply in exactly these 4 lines, in this order:
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change that would reverse this decision: <fact> -> <value>; <fact> -> <value> | no change within 4 edits

The decision is cannot determine when the case file leaves out a fact the outcome turns on and no default in the \
policy covers it. "Policy support" lists the fewest facts from the case file that by themselves force your \
decision, each with the rule it triggers: for approve, the facts each rule needs to be met or waived; for deny, the \
facts of one rule the case fails; for cannot determine, the missing facts as <fact>=not stated. "Assumptions" \
lists any fact the case file does not state that you filled in from a default in the policy. The last line gives \
the fewest fact edits that would reverse your decision (approve to deny, deny to approve); for cannot determine it \
gives instead the fewest facts the case file leaves out, with values, whose addition would settle the decision. \
All edits on that line are applied together, so list one set of edits, not alternatives. Name every fact by \
exactly one of these labels: {labels}. Give each value as the case file states it (yes or no for yes/no facts)."""
CHANGE = "Smallest change that would reverse this decision"
PREDICT = """Your earlier answer on this case file:
{frozen}

Now consider one edit to the case file, with everything else unchanged.
Edit ID: {bid}
Edit: {desc}

Predict the decision you would give on the edited case file. Reply in exactly these 2 lines:
Edit ID: {bid}
Predicted decision after edit: approve | deny | cannot determine"""
SIM_SYSTEM = ("You predict the decisions of another system that decides cases under a written policy, from what it "
        "said about one case. Reply in exactly the requested format with no other text.")
SIM = """Another system decided one case file under this policy. You do not see the case file. Its answer:
{frozen}

Now one edit is made to that case file, with everything else unchanged.
Edit ID: {bid}
Edit: {desc}

Predict the decision that system gives on the edited case file. Reply in exactly these 2 lines:
Edit ID: {bid}
Predicted decision after edit: approve | deny | cannot determine"""
PROPS = {"pivotal_replace": 0.40, "invariant": 0.30, "remove": 0.15, "add": 0.15}
GROUPS = {"pivotal_replace": ("pivotal_replace",), "invariant": ("noncrossing_replace", "invariant_replace"),
        "remove": ("remove",), "add": ("add",)}
PRIME = ("unseen_family_train_vocab", "prose")
# USD per 1M input / output tokens (output includes thinking); qwen is the OpenRouter PrimeIntellect list price
PRICES = {"gemini-3.5-flash-lite": (0.30, 2.50), "qwen/qwen3.5-9b": (0.17, 0.25)}


def root(r, by):
    """
    Returns the base case id (without the view suffix) that r descends from, following parents through by.
    """
    while r.get("parent") in by:
        r = by[r["parent"]]
    return r["id"].rsplit(":", 1)[0]


def select_recs(recs, slc=None, view=None, cases=0, seed=0):
    """
    Returns the records of slice slc and view view (None keeps all), and with cases > 0 only those under a seeded
    sample of `cases` base cases (ids without the ":view" suffix, so every view of a case comes along) stratified
    over (domain, template_family): families are dealt round-robin across domains in shuffled order and one case is
    drawn per family per round. Every kept base keeps its flip, invariant, missing and reveal variants.
    """
    sel = [r for r in recs if (slc is None or r.get("slice") == slc) and (view is None or r.get("view") == view)]
    if not cases:
        return sel
    by, rng, fams = {r["id"]: r for r in recs}, random.Random(seed), defaultdict(lambda: defaultdict(set))
    for r in sel:
        if r["variant"] == "base":
            fams[r.get("domain")][r.get("template_family") or r["policy_id"]].add(r["id"].rsplit(":", 1)[0])
    doms = []
    for d in sorted(fams, key=str):
        fs = [sorted(fams[d][f]) for f in sorted(fams[d], key=str)]
        rng.shuffle(fs)
        for f in fs:
            rng.shuffle(f)
        doms.append(fs)
    rng.shuffle(doms)
    order = [fs[i] for i in range(max(map(len, doms), default=0)) for fs in doms if i < len(fs)]
    keep = []
    while len(keep) < cases and any(order):
        keep += [f.pop() for f in [f for f in order if f][:cases - len(keep)]]
    keep = set(keep)
    return [r for r in sel if root(r, by) in keep]


def show(dom, n, v):
    """
    Returns engine value v of fact n as the case-file table states it: yes or no, money, a date, an enum display name,
    else the raw value. Facts outside the domain schema and unformattable values come back as str(v).
    """
    s = dom.get("facts", {}).get(n)
    if isinstance(v, bool):
        return "yes" if v else "no"
    if s is None or v is None:
        return str(v)
    spec = (re.search(r"\{v:(money|date|e)\}", " ".join(s.get("say", []))) or [None, ""])[1]
    try:
        return gen.Fmt(dom, n).format_field(v, spec)
    except (KeyError, TypeError, ValueError):
        return str(v)


def format_target(rec):
    """
    Returns the gold account of rec in the answer FORMAT, decision first: the SFT target sequence. Policy support is
    the first minimum sufficient set (stated facts only) with the rule each fact triggers (a passed or waived rule for
    approve, a failed one for deny), or for cannot determine the missing facts behind the undecided rules as
    "not stated"; Assumptions are the defaults applied; the last line is the gold min_flip edits, for cannot
    determine the min_reveal additions, else "no change within 4 edits". Values are rendered as the case file
    states them, and nothing in it depends on the prompt.
    """
    g, pol, lab = rec["gold"], gen.policy_for(rec), rec.get("fact_labels", {})
    dom, dec, tr, da = gen.load_domain(rec["domain"]), g["decision"], g["rule_trace"], g["defaults_applied"]
    want = {"approve": ("pass", "waived"), "deny": ("fail",)}.get(dec, ("unknown",))
    rid = {n: next((r.id for r in pol.requires if n in r.all_refs and tr.get(r.id) in want), None) for n in pol.order}
    if dec == "cannot determine":
        sup = [f"{lab.get(n, n)}=not stated" + (f" ({rid[n]})" if rid[n] else "") for n in g["needs_facts"]]
        chg = (g.get("min_reveal") or {}).get("adds")
    else:
        sup = [f"{lab.get(n, n)}={show(dom, n, rec['facts'][n])}" + (f" ({rid[n]})" if rid[n] else "")
                for n in (g["minimum_sets"] or [[]])[0] if n not in da]
        chg = (g.get("min_flip") or {}).get("edits")
    ass = [f"{lab.get(n, n)}={show(dom, n, v)} (default from {pol.defaults[n][0]})" for n, v in da.items()]
    return (f"Decision: {dec}\nPolicy support: {'; '.join(sup) or 'none'}\nAssumptions: {'; '.join(ass) or 'none'}\n"
            f"{CHANGE}: " + ("; ".join(f"{lab.get(n, n)} -> {show(dom, n, v)}" for n, v in chg.items()) if chg else
            "no change within 4 edits"))


def build_prompt(rec, item=None, frozen=None, sim=False):
    """
    Builds the (system, user) prompt pair for one record, identical across backends and stored with every row.
    Without a bank item it is the ordinary decision prompt, which lists the fact_labels labels as the names to cite
    and names no target label. With a bank item and the frozen answer text it is the self-prediction prompt (policy,
    case, answer, edit), or with sim the external-simulator prompt (policy, answer, edit, no case text). Each edited
    fact is described by its fact_labels label and its value as the case file would state it.
    """
    head, case = f"Policy:\n{rec['policy_text'].strip()}\n\n", f"Case file:\n{rec['case_text'].strip()}\n\n"
    if item is None:
        return SYSTEM, head + case + FORMAT.format(labels="; ".join(rec.get("fact_labels", {}).values()))
    lab, dom = rec.get("fact_labels", {}), gen.load_domain(rec["domain"]) if rec.get("domain") else {}
    desc = "; ".join(f"{lab.get(f, f)} is no longer stated" if item["kind"] == "remove" else
            f"{lab.get(f, f)} is now stated as {show(dom, f, v)}" if item["kind"] == "add" else
            f"{lab.get(f, f)} changes to {show(dom, f, v)}" for f, v in item["edits"].items())
    if sim:
        return SIM_SYSTEM, head + SIM.format(frozen=frozen.strip(), bid=item["bank_id"], desc=desc)
    return SYSTEM, head + case + PREDICT.format(frozen=frozen.strip(), bid=item["bank_id"], desc=desc)


def build_bank(recs, seed=0):
    """
    Returns (bank, meta) for a list of records, with every edit chosen independently of the gold account. Kinds:
    - pivotal_replace: a certified engine flip of the base (decide gives the flip target) whose fact set differs from
      gold.min_flip and that repeats none of its (fact, value) edits (engine.min_flip with radius 3, exclude and
      prefer_disjoint gold.min_flip); a base with none is dropped with its reason.
    - invariant_replace: base -> its invariant variant (an edit outside every sufficient set).
    - noncrossing_replace: the smallest move of one necessary fact that keeps the decision and the rule trace (a
      cited fact moved without crossing its threshold); counted in the invariant share.
    - remove (base -> missing variant) and add (missing -> base).
    Per view it draws 40% pivotal, 30% invariant (split evenly between the two subtypes, overflow to the other),
    15% remove and 15% add, scaled to the scarcest group. Each item is {bank_id, kind, view, slice, case_id,
    edited_id, edits, oracle, bank_source}; engine-built edited cases also carry "edited", the fields that override
    the base record (see evaluate.bank_recs). meta holds the mix, the sources and the drops.
    """
    by, cands, drops = {r["id"]: r for r in recs}, defaultdict(list), []
    for r in sorted(recs, key=lambda r: r["id"]):
        p, v = by.get(r.get("parent")), r.get("view", "prose")
        rf, its = r.get("removed_fact"), []
        if r["variant"] == "invariant" and p:
            its = [("invariant_replace", p, r, r["changed_facts"], "variant_record")]
        elif r["variant"] == "missing" and p and rf:
            its = [("remove", p, r, {rf: None}, "variant_record"),
                    ("add", r, p, {rf: p["facts"].get(rf)}, "variant_record")]
        elif r["variant"] == "base":
            pol, f, g = gen.policy_for(r), r["facts"], r["gold"]
            gold = (g.get("min_flip") or {}).get("edits") or {}
            mf = engine.min_flip(pol, f, radius=3, exclude=gold, prefer_disjoint=gold)
            if not mf["edits"] or engine.decide(pol, {**f, **mf["edits"]})["decision"] != mf["target"]:
                drops.append({"case_id": r["id"], "reason": "cannot determine base" if not mf["target"] else
                        mf.get("reason") or "no certified flip within radius 3" +
                          (" other than gold.min_flip" if gold else "")})
            else:
                its.append(("pivotal_replace", r, None, mf["edits"], "engine_alt_disjoint" if mf["disjoint"] else
                        "engine_alt_overlap"))
            rng, nc = random.Random(r["id"]), None
            for n in sorted((n for n in g["necessary_facts"] if f.get(n) is not None), key=lambda n: rng.random()):
                i0 = pol.dom[n].index(f[n])
                for x in sorted((x for x in pol.dom[n] if x != f[n]), key=lambda x: abs(pol.dom[n].index(x) - i0)):
                    ff = {**f, n: x}
                    d = engine.decide(pol, ff) if pol.ok(engine.known_facts(pol, ff)[0]) else {}
                    if d.get("decision") == g["decision"] and d["rule_trace"] == g["rule_trace"]:
                        nc = min(nc or (abs(pol.dom[n].index(x) - i0), {n: x}), (abs(pol.dom[n].index(x) - i0),
                                {n: x}), key=lambda t: t[0])
                        break
            if nc:
                its.append(("noncrossing_replace", r, None, nc[1], "engine_noncrossing"))
        for kind, c, e, ed, src in its:
            it = {"bank_id": f"{c['id']}|{kind}", "kind": kind, "view": v, "slice": r.get("slice"), "case_id": c["id"],
                    "edits": ed, "bank_source": src}
            if e is not None:
                cands[(v, kind)].append(it | {"edited_id": e["id"], "oracle": e["gold"]["decision"]})
                continue
            ff, eid = {**c["facts"], **ed}, f"{c['id']}|bank|{kind}"
            d = engine.decide(pol, ff)
            cands[(v, kind)].append(it | {"edited_id": eid, "oracle": d["decision"], "edited": {"id": eid,
                    "parent": c["id"], "variant": "intervention", "edit_kind": "replace", "edited_from": c["id"],
                    "changed_facts": ed, "facts": ff, "stated_facts": list(ff), "case_sentences": None,
                    "fact_states": engine.fact_states(pol, ff), "case_text": gen.render_case(pol, ff,
                    c["id"].rsplit(":", 1)[0], c.get("prose_source", "template"), view=v,
                    base=c.get("case_sentences")), "gold": {"decision": d["decision"], "rule_trace": d["rule_trace"],
                    "defaults_applied": d["defaults_applied"]}, "intervention": {"base": c["id"], "kind": "bank",
                    "edits": ed}}})
    rng, bank = random.Random(seed), []
    for view in sorted({v for v, _ in cands}):
        pools = {}
        for k in (k for ks in GROUPS.values() for k in ks):
            pools[k] = sorted(cands[(view, k)], key=lambda x: x["bank_id"])
            rng.shuffle(pools[k])
        tot = min(sum(len(pools[k]) for k in ks) / PROPS[gk] for gk, ks in GROUPS.items())
        for gk, ks in GROUPS.items():
            n, take = round(tot * PROPS[gk]), Counter()
            while sum(take.values()) < n:
                for k in ks:
                    take[k] += take[k] < len(pools[k]) and sum(take.values()) < n
            bank += [x for k in ks for x in pools[k][:take[k]]]
    meta = {"items": len(bank), "kinds": dict(sorted(Counter(b["kind"] for b in bank).items())),
            "groups": {gk: sum(b["kind"] in ks for b in bank) / max(1, len(bank)) for gk, ks in GROUPS.items()},
            "sources": dict(sorted(Counter(b["bank_source"] for b in bank).items())),
            "candidates": {f"{v}/{k}": len(x) for (v, k), x in sorted(cands.items())},
            "drop_reasons": dict(Counter(d["reason"] for d in drops)), "drops": drops}
    return bank, meta


class Runner:
    """
    Calls one backend and model with fixed decoding.
    Handles concurrency, retries with backoff, an optional requests-per-minute cap and the response cache.
    """

    def __init__(self, backend, model, dec, base_url=None, key_env=None, extra=None, conc=8, retries=6, rpm=0,
            cache="runs/cache.jsonl", rep=0, vertex=None, ctag=""):
        """
        Sets up the backend client and loads the cache.
        dec holds temperature, top_p, top_k (0 = off), max_tokens, seed and thinking (bool). extra is merged into
        extra_body for "openai" (a null value drops a default key) and passed to vllm.LLM() for "vllm". rep is the
        repeat index: it shifts every seed by 1000 * rep and is part of the cache key. vertex is a Vertex AI location
        for "gemini" (None uses GEMINI_API_KEY) and tags the backend in the cache key as gemini/vertex:<location>.
        ctag is a free cache tag, required for a local checkpoint (e.g. the training run and epoch), since its model
        path can point at new weights.
        """
        envf = Path("~/.config/cs224v/.env").expanduser()
        for ln in envf.read_text().splitlines() if envf.exists() else []:
            m = re.match(r"\s*(?:export\s+)?(\w+)\s*=\s*['\"]?([^'\"\s#]*)", ln)
            if m:
                os.environ.setdefault(m[1], m[2])
        self.backend, self.model, self.dec, self.extra, self.rep = backend, model, dec, extra or {}, rep
        self.conc, self.retries, self.rpm, self.base_url, self.vertex, self.ctag = conc, retries, rpm, base_url, \
            vertex, ctag
        self.tag = f"{backend}/vertex:{vertex}" if vertex else backend
        self.cpath = Path(cache)
        self.cache = {}
        if self.cpath.exists():
            for ln in self.cpath.read_text().splitlines():
                if ln.strip():
                    row = json.loads(ln)
                    self.cache[row.pop("key")] = row
        if backend == "openai":
            from openai import AsyncOpenAI
            key = os.environ.get(key_env or "", "") or "EMPTY"
            self.cli = AsyncOpenAI(base_url=base_url, api_key=key, max_retries=0)
        elif backend == "gemini" and vertex:
            # Builds the same Vertex client as gen.gemini_call: ADC from gcloud, billed to GCP_PROJECT, no API key.
            import google.auth
            from google import genai
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    quota_project_id=os.environ["GCP_PROJECT"])
            self.cli = genai.Client(vertexai=True, project=os.environ["GCP_PROJECT"], location=vertex,
                    credentials=creds)
        elif backend == "gemini":
            from google import genai
            self.cli = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        elif backend == "vllm":
            from vllm import LLM
            self.cli = LLM(model=model, seed=dec["seed"], **self.extra)
        else:
            raise ValueError(f"unknown backend {backend}")

    def key(self, sys_, prm, d):
        """
        Returns the cache key: a sha256 over backend (tagged with the Vertex location), base_url, model, extra options,
        both prompt parts, the decoding (temperature, top_p, top_k, max_tokens, seed, thinking), rep and a non-empty
        cache tag (an empty one keeps the keys of earlier runs).
        """
        blob = json.dumps([self.tag, self.base_url, self.model, self.extra, sys_, prm, d, self.rep] +
                ([self.ctag] if self.ctag else []), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def call(self, sys_, prm, d):
        """
        Sends one request and returns {output, reasoning, in_tokens, out_tokens, think_tokens, finish, response_id,
        model_version}.
        Thinking goes through chat_template_kwargs and reasoning in extra_body for "openai", and through
        ThinkingConfig for "gemini" (thinking_budget 0 when off, -1 for dynamic when on). Gemini 3.x documents only
        thinking_level, whose lowest value "minimal" still allows some thinking and which 3.8-flash rejects, while
        budget 0 is accepted by 3.8-flash and by 3.5-flash and 3.5-flash-lite on Vertex with 0 thought tokens
        (checked Nov 5, 2026). finish is "length" when the output hit max_tokens.
        """
        if self.backend == "openai":
            eb = {"chat_template_kwargs": {"enable_thinking": d["thinking"]}, "reasoning": {"enabled": d["thinking"]}}
            eb |= {"top_k": d["top_k"]} if d["top_k"] > 0 else {}
            eb = {k: v for k, v in (eb | self.extra).items() if v is not None}
            r = await self.cli.chat.completions.create(model=self.model, messages=[{"role": "system", "content": sys_},
                    {"role": "user", "content": prm}], temperature=d["temperature"], top_p=d["top_p"],
                    max_tokens=d["max_tokens"], seed=d["seed"], extra_body=eb)
            m = r.choices[0].message
            return {"output": m.content or "", "reasoning": getattr(m, "reasoning_content", None) or
                    getattr(m, "reasoning", None), "in_tokens": r.usage.prompt_tokens if r.usage else None,
                    "out_tokens": r.usage.completion_tokens if r.usage else None,
                    "think_tokens": None, "finish": r.choices[0].finish_reason, "response_id": r.id,
                    "model_version": r.model}
        from google.genai import types
        cfg = types.GenerateContentConfig(system_instruction=sys_, temperature=d["temperature"], top_p=d["top_p"],
                top_k=d["top_k"] or None, max_output_tokens=d["max_tokens"], seed=d["seed"],
                thinking_config=types.ThinkingConfig(thinking_budget=-1 if d["thinking"] else 0))
        r = await self.cli.aio.models.generate_content(model=self.model, contents=prm, config=cfg)
        u, fr = r.usage_metadata, str(r.candidates[0].finish_reason) if r.candidates else None
        return {"output": r.text or "", "reasoning": None, "in_tokens": u.prompt_token_count if u else None,
                "out_tokens": u.candidates_token_count if u else None,
                "think_tokens": u.thoughts_token_count if u else None,
                "finish": "length" if fr and "MAX_TOKENS" in fr else fr, "response_id": r.response_id,
                "model_version": r.model_version}

    def split_think(self, res, d):
        """
        Moves a closed think block from the output into reasoning. An unclosed block (an opening tag without the
        closing one, or vllm thinking output with no closing tag) empties the output and sets finish "truncated".
        """
        o = res["output"]
        if "</think>" in o:
            think, _, ans = o.rpartition("</think>")
            return res | {"output": ans.strip(), "reasoning": think.replace("<think>", "").strip() or None}
        if "<think>" in o or (d["thinking"] and self.backend == "vllm"):
            return res | {"output": "", "reasoning": o.replace("<think>", "").strip(), "finish": "truncated"}
        return res

    async def one(self, sem, k, job):
        """
        Runs one job under the semaphore with rate pacing and exponential backoff.
        Returns (key, result), where a final failure gives an empty output and an error string. 400, 401, 403 and
        404 responses are not retried.
        """
        async with sem:
            for i in range(self.retries + 1):
                if self.rpm:
                    async with self.lock:
                        await asyncio.sleep(max(0.0, self.next - time.monotonic()))
                        self.next = time.monotonic() + 60 / self.rpm
                t = time.monotonic()
                try:
                    res = self.split_think(await self.call(*job[2:5]), job[4])
                    return k, res | {"latency": round(time.monotonic() - t, 3)}
                except Exception as e:
                    code = getattr(e, "status_code", None) or getattr(e, "code", None)
                    if i == self.retries or code in (400, 401, 403, 404):
                        return k, {"output": "", "error": f"{type(e).__name__}: {str(e)[:300]}"}
                    await asyncio.sleep(min(60, 2 ** i) + random.random())

    async def run_async(self, todo, fh):
        """
        Runs all uncached jobs concurrently and appends each success to the open cache file as it arrives.
        """
        sem, self.lock, self.next, res = asyncio.Semaphore(self.conc), asyncio.Lock(), 0.0, {}
        for fut in asyncio.as_completed([self.one(sem, k, j) for k, j in todo.items()]):
            k, r = await fut
            res[k] = r
            if not r.get("error"):
                fh.write(json.dumps({"key": k} | r) + "\n")
                fh.flush()
        return res

    def run(self, items, n, mode):
        """
        Returns one output row per (item, sample), calling the model only for jobs missing from the cache.
        items are (row id, record, bank item or None, frozen text or None). Each row carries the prompt, the
        decoding with its per-sample seed, the mode, the repeat index, whether it came from the cache, and the
        response's finish, token counts, response_id and model_version (None for cache rows older than Nov 5).
        """
        jobs = []
        for rid, rec, it, fz in items:
            sys_, prm = build_prompt(rec, it, fz, mode.startswith("simulate"))
            for i in range(n):
                d = self.dec | {"seed": self.dec["seed"] + 1000 * self.rep + i}
                jobs.append((rid, i, sys_, prm, d, self.key(sys_, prm, d)))
        todo = {j[5]: j for j in jobs if j[5] not in self.cache}
        self.cpath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cpath, "a") as fh:
            if self.backend != "vllm":
                res = asyncio.run(self.run_async(todo, fh))
            else:
                from vllm import SamplingParams
                d0, js = self.dec, list(todo.values())
                sps = [SamplingParams(temperature=d0["temperature"], top_p=d0["top_p"], max_tokens=d0["max_tokens"],
                        seed=j[4]["seed"], **({"top_k": d0["top_k"]} if d0["top_k"] > 0 else {})) for j in js]
                t = time.monotonic()
                outs = self.cli.chat([[{"role": "system", "content": j[2]}, {"role": "user", "content": j[3]}]
                        for j in js], sampling_params=sps, chat_template_kwargs={"enable_thinking": d0["thinking"]})
                lat = round((time.monotonic() - t) / max(1, len(js)), 3)
                res = {}
                for j, o in zip(js, outs):
                    res[j[5]] = self.split_think({"output": o.outputs[0].text, "reasoning": None,
                            "in_tokens": len(o.prompt_token_ids), "out_tokens": len(o.outputs[0].token_ids),
                            "think_tokens": None, "finish": o.outputs[0].finish_reason, "response_id": o.request_id,
                            "model_version": self.model, "latency": lat}, j[4])
                    fh.write(json.dumps({"key": j[5]} | res[j[5]]) + "\n")
        rows = []
        for rid, i, sys_, prm, d, k in jobs:
            rows.append({"id": rid, "sample": i, "seed": d["seed"], "backend": self.tag, "model": self.model,
                    "mode": mode, "rep": self.rep, "decoding": d, "system": sys_, "prompt": prm,
                    "cached": k in self.cache, "finish": None, "in_tokens": None, "out_tokens": None,
                    "think_tokens": None, "response_id": None, "model_version": None} | (self.cache.get(k) or res[k]))
        return rows


def shuffle_partners(fz, cases, byid, seed=0):
    """
    Returns {id: (partner id, same decision)} for every frozen id in byid: a frozen answer on another case of cases
    (byid plus the bank's edited records) under the same policy_id, never a view, variant or edit of the same base
    case, and whether its parsed decision equals the id's own. Ids with no such partner are left out. Draws are
    deterministic under seed.
    """
    rng, pf, out = random.Random(seed), defaultdict(list), {}
    for j in sorted(j for j in fz if j in cases):
        pf[cases[j]["policy_id"]].append(j)
    for i in sorted(i for i in fz if i in byid):
        if o := [j for j in pf[byid[i]["policy_id"]] if root(cases[j], cases) != root(byid[i], cases)]:
            j = rng.choice(o)
            out[i] = (j, parse(fz[j])["dec"] == parse(fz[i])["dec"])
    return out


def main():
    """
    Parses the CLI and runs the chosen mode: writes the bank and its meta, or runs answer, predict or simulate calls
    and writes the rows and <out>.meta.json, printing a one-line cost estimate.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--mode", choices=["answer", "bank", "predict", "simulate"], default="answer")
    ap.add_argument("--backend", choices=["openai", "gemini", "vllm"])
    ap.add_argument("--model")
    ap.add_argument("--out")
    ap.add_argument("--bank", help="answer: also answer the bank's edited cases; predict, simulate: the bank")
    ap.add_argument("--frozen", help="predict, simulate: the answer run whose sample-0 outputs are frozen")
    ap.add_argument("--no-account", action="store_true", help="predict, simulate: show only the frozen decision")
    ap.add_argument("--shuffle-accounts", action="store_true",
            help="simulate: keep each item's decision, take the rest of the account from another case's frozen answer "
            "under the same policy")
    ap.add_argument("--all-sim", action="store_true", help="simulate: run the account, --shuffle-accounts and "
            "--no-account passes in one call, writing <frozen>.simulate{,_shuf,_noacc}.jsonl")
    ap.add_argument("--wide-bank", action="store_true", help="bank: every slice and view, not only the primary one")
    ap.add_argument("--vertex", nargs="?", const="global", default=None, metavar="LOCATION",
            help="gemini backend: use Vertex AI (GCP_PROJECT, ADC) in LOCATION (default global) instead of the API key")
    ap.add_argument("--slice", help="only records of this slice, e.g. unseen_family_train_vocab")
    ap.add_argument("--view", choices=["table", "prose", "prose_derive"], help="only records of this view")
    ap.add_argument("--cases", type=int, default=0,
            help="seeded sample of K base cases stratified over (domain, template_family), 0 = all")
    ap.add_argument("--sample-seed", type=int, default=0, help="seed of the --cases sample and --shuffle-accounts")
    ap.add_argument("--base-url", help="openai backend: endpoint, e.g. http://localhost:8000/v1")
    ap.add_argument("--key-env", help="openai backend: name of the env var holding the API key")
    ap.add_argument("--extra", type=json.loads, default=None, help="JSON: extra_body (openai) or LLM kwargs (vllm)")
    ap.add_argument("--temperature", type=float, default=0.0, help="0 = greedy, the main diagnostic decoding")
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--thinking", choices=["on", "off"], default="off")
    ap.add_argument("--n", type=int, default=1, help="samples per prompt, seeds seed..seed+n-1")
    ap.add_argument("--rep", type=int, default=0, help="repeat index; 1 gives the repeat-without-edit control")
    ap.add_argument("--conc", type=int, default=8)
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--rpm", type=float, default=0, help="requests per minute cap, 0 = none")
    ap.add_argument("--cache", default="runs/cache.jsonl")
    ap.add_argument("--cache-tag", default="", help="extra cache-key tag, required for a local checkpoint (e.g. "
            "sft-acct-s0-e2), whose model path can point at new weights")
    ap.add_argument("--limit", type=int, default=0, help="first N items only")
    a = ap.parse_args()
    if a.vertex and a.backend != "gemini":
        ap.error("--vertex needs --backend gemini")
    if a.no_account and a.shuffle_accounts:
        ap.error("--no-account and --shuffle-accounts are separate controls")
    recs = load(a.data)
    if a.mode == "bank":
        wide = a.wide_bank or a.slice or a.view
        sel = select_recs(recs, a.slice if wide else PRIME[0], a.view if wide else PRIME[1], a.cases, a.sample_seed)
        (bank, meta), bp = build_bank(sel, a.seed), Path(a.out or Path(a.data).with_suffix(".bank.jsonl"))
        bp.write_text("".join(json.dumps(b) + "\n" for b in bank))
        meta = {"data": a.data, "slice": a.slice if wide else PRIME[0], "view": a.view if wide else PRIME[1],
                "seed": a.seed} | meta
        bp.with_name(bp.stem + ".meta.json").write_text(json.dumps(meta, indent=1))
        print(f"bank={bp} items={meta['items']}", meta["kinds"], meta["sources"], "dropped", len(meta["drops"]),
                meta["drop_reasons"])
        return
    if a.all_sim and (a.mode != "simulate" or a.no_account or a.shuffle_accounts or a.out):
        ap.error("--all-sim runs all 3 simulate passes itself and names their files after --frozen")
    if not (a.backend and a.model and (a.out or a.all_sim)):
        ap.error("--backend, --model and --out are required for answer, predict and simulate")
    sel, bank = select_recs(recs, a.slice, a.view, a.cases, a.sample_seed), load(a.bank) if a.bank else []
    byid, keep = {r["id"]: r for r in recs}, {r["id"] for r in sel}
    br = bank_recs(bank, byid)
    passes = [(a.no_account, a.shuffle_accounts, a.out)]
    if a.all_sim:
        st = Path(a.frozen).with_suffix("")
        passes = [(na, sh, f"{st}.simulate{x}.jsonl") for na, sh, x in ((False, False, ""), (False, True, "_shuf"),
                (True, False, "_noacc"))]
    dec = {"temperature": a.temperature, "top_p": a.top_p, "top_k": a.top_k, "max_tokens": a.max_tokens,
            "seed": a.seed, "thinking": a.thinking == "on"}
    for na, sh, op in passes:
        mode = a.mode
        if a.mode == "answer":
            items = [(r["id"], r, None, None) for r in sel] + [(i, r, None, None) for i, r in br.items()
                    if r["parent"] in keep]
        else:
            fz = {r["id"]: r["output"] for r in load(a.frozen) if r["sample"] == 0}
            elig = [b for b in bank if b["case_id"] in fz and b["case_id"] in keep and
                    (b["edited_id"] in keep or b["edited_id"] in br)]
            sp = shuffle_partners(fz, byid | br, byid, a.sample_seed) if sh else {i: (i, True) for i in fz}
            miss = sum(b["case_id"] not in sp for b in elig)
            if sh or a.mode == "simulate":
                # Rebuilds each account in the answer FORMAT from parsed sections, the Decision line from the item's
                # own answer and the rest from its partner (itself without --shuffle-accounts). simulate drops the
                # smallest change: the simulator sees no case text and no smallest change.
                hs = {"decision": "Decision", "policy support": "Policy support", "assumptions": "Assumptions"} | (
                        {} if a.mode == "simulate" else {"smallest change": CHANGE})
                acct = {}
                for i, (j, _) in sp.items():
                    sec = {k: v for k, v in sections(fz[j]).items() if k != "decision"} | {k: v for k, v in
                            sections(fz[i]).items() if k == "decision"}
                    acct[i] = "\n".join(f"{h}: {sec[k][0]}".strip() + "".join("\n" + x.strip() for x in sec[k][1:])
                            for k, h in hs.items() if k in sec) or "(no readable answer)"
                fz = acct
            mode += "_shuf" if sh else ""
            items = [(b["bank_id"], byid[b["case_id"]], b, f"Decision: {parse(fz[b['case_id']])['dec'] or 'unreadable'}"
                    if na else fz[b["case_id"]]) for b in elig if b["case_id"] in sp]
            mode += "_noacc" if na else ""
        items = items[:a.limit] if a.limit else items
        t0 = time.monotonic()
        rows = Runner(a.backend, a.model, dec, a.base_url, a.key_env, a.extra, a.conc, a.retries, a.rpm, a.cache,
                a.rep, a.vertex, a.cache_tag).run(items, a.n, mode)
        if sh:
            cid = {b["bank_id"]: b["case_id"] for b in bank}
            rows = [r | {"shuf_src": "frozen", "shuf_partner": sp[cid[r["id"]]][0], "shuf_decision_match":
                    sp[cid[r["id"]]][1]} for r in rows]
        out = Path(op)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps(r) + "\n" for r in rows))
        fresh = [r for r in rows if not r["cached"] and "latency" in r]
        errs = [r["error"] for r in rows if r.get("error")]
        tok = {k: (sum(r.get(k) or 0 for r in fresh), sum(r.get(k) or 0 for r in rows)) for k in
                ("in_tokens", "out_tokens", "think_tokens")}
        pr = PRICES.get(a.model)
        cost = [round((tok["in_tokens"][i] * pr[0] + (tok["out_tokens"][i] + tok["think_tokens"][i]) * pr[1]) /
                1e6, 4) for i in (0, 1)] if pr else None
        meta = {"model": a.model, "backend": a.backend, "vertex": a.vertex, "mode": mode, "no_account": na,
                "shuffle_accounts": sh, "shuf_missing": miss if a.mode != "answer" and sh else None,
                "cases": a.cases, "cache_tag": a.cache_tag, "sample_seed": a.sample_seed, "decoding": dec,
                "n": a.n, "rows": len(rows), "cached": sum(r["cached"] for r in rows), "errors": len(errs),
                "fresh_calls": len(fresh), "wall_s": round(time.monotonic() - t0, 2),
                "in_tokens": tok["in_tokens"][1], "out_tokens": tok["out_tokens"][1],
                "think_tokens": tok["think_tokens"][1], "finish": dict(Counter(str(r.get("finish")) for r in rows)),
                "model_versions": sorted({str(r.get("model_version")) for r in rows}),
                "mean_latency_s": round(sum(r["latency"] for r in fresh) / max(1, len(fresh)), 3),
                "cost_usd_fresh": cost and cost[0], "cost_usd_if_uncached": cost and cost[1]}
        out.with_name(out.stem + ".meta.json").write_text(json.dumps(meta, indent=1))
        print(" ".join(f"{k}={v}" for k, v in meta.items() if k not in ("decoding", "cost_usd_fresh",
                "cost_usd_if_uncached")))
        for e in sorted(set(errs))[:3]:
            print("error:", e)
        print(f"cost estimate: ${cost[0]:.4f} for {len(fresh)} fresh calls (${cost[1]:.4f} if uncached) at ${pr[0]}/"
                f"${pr[1]} per 1M in/out tokens" if pr else f"cost estimate: no price for {a.model} in PRICES")


if __name__ == "__main__":
    main()
