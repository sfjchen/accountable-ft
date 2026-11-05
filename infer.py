"""Runs one model over a data file and writes one JSONL row per (item, sample), plus <out>.meta.json with tokens and
wall time.

A single Runner wraps three backends with the same prompt and fixed decoding: "openai" for any OpenAI-compatible
endpoint (vLLM serve, OpenRouter, OpenAI), "gemini" through google-genai, and "vllm" for offline batch generation.
Sample i of an item uses seed + i. Every response is cached in a JSONL keyed by a hash of backend, model, prompt,
decoding and repeat index, so a rerun only calls the model for what is missing and --rep 1 forces a fresh run of the
same prompts (the repeat-without-edit control). API keys come from environment variables, filled from
~/.config/cs224v/.env when unset, and are never printed.

Modes:
- answer: the ordinary decision call (decision, policy support, assumptions, smallest change to the record's target).
- bank: builds the intervention bank for a data file once, data/<name>.bank.jsonl, reused for every model.
- predict: the self-prediction call. For each bank item it shows the case, the model's own frozen answer from
  --frozen (sample 0 of an answer run; with --no-account only its decision), and one edit, and asks for the
  predicted decision after the edit. The fresh decision on the edited case is the answer run's own row for the
  edited record, so it carries no trace of the prediction.

Usage:
  python infer.py --data data/x.jsonl --backend gemini --model gemini-3.8-flash --out runs/name.jsonl --temperature 0
  python infer.py --mode bank --data data/x.jsonl
  python infer.py --mode predict --data data/x.jsonl --bank data/x.bank.jsonl --frozen runs/name.jsonl \
          --backend gemini --model gemini-3.8-flash --temperature 0 --out runs/name.predict.jsonl [--no-account]
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

from evaluate import load, parse

SYSTEM = ("You decide cases under a written policy. Apply only the numbered rules of the policy, not outside "
        "knowledge or common practice. Reply in exactly the requested format with no other text.")
FORMAT = """Reply in exactly these 4 lines, in this order:
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change to make this {target}: <fact> -> <value>; <fact> -> <value> | no change within 4 edits

"Policy support" lists the facts from the case file that your decision depends on, each with the rule it \
triggers. "Assumptions" lists any fact the case file does not state that you filled in from a default in the \
policy. The last line gives the fewest fact edits that would make the decision {target}."""
PREDICT = """Your earlier answer on this case file:
{frozen}

Now consider one edit to the case file, with everything else unchanged.
Edit ID: {bid}
Edit: {desc}

Predict the decision you would give on the edited case file. Reply in exactly these 2 lines:
Edit ID: {bid}
Predicted decision after edit: approve | deny | cannot determine"""
PROPS = {"pivotal_replace": 0.40, "invariant_replace": 0.30, "remove": 0.15, "add": 0.15}


def build_prompt(rec, item=None, frozen=None):
    """
    Builds the (system, user) prompt pair for one record, identical across backends and stored with every row.
    Without a bank item it is the ordinary decision prompt, naming the record's target label (gold.target, else
    gold.min_flip.target, else "a different decision"). With a bank item and the frozen answer text it is the
    self-prediction prompt, describing each edited fact by its fact_labels label.
    """
    head = f"Policy:\n{rec['policy_text'].strip()}\n\nCase file:\n{rec['case_text'].strip()}\n\n"
    if item is None:
        g = rec.get("gold", {})
        tgt = g.get("target") or (g.get("min_flip") if isinstance(g.get("min_flip"), dict) else {}).get("target")
        return SYSTEM, head + FORMAT.format(target=tgt or "a different decision")
    lab, vals = rec.get("fact_labels", {}), {f: ("yes" if v else "no") if isinstance(v, bool) else v
            for f, v in item["edits"].items()}
    desc = "; ".join(f"{lab.get(f, f)} is no longer stated" if item["kind"] == "remove" else
            f"{lab.get(f, f)} is now stated as {v}" if item["kind"] == "add" else
            f"{lab.get(f, f)} changes to {v}" for f, v in vals.items())
    return SYSTEM, head + PREDICT.format(frozen=frozen.strip(), bid=item["bank_id"], desc=desc)


def build_bank(recs, seed=0):
    """
    Returns the intervention bank for a data file, built from its own variant records so every edited case is one
    the generator already rendered and labeled. Per view it draws 40% pivotal replace (base -> flip variant), 30%
    invariant replace (base -> invariant), 15% remove (base -> missing) and 15% add (missing -> base), scaled to
    the scarcest kind. Each item is {bank_id, kind, view, case_id, edited_id, edits, oracle}.
    """
    by, cands = {r["id"]: r for r in recs}, defaultdict(list)
    for r in recs:
        p = by.get(r.get("parent"))
        if p is None:
            continue
        rf = r.get("removed_fact")
        pairs = {"flip": [("pivotal_replace", p, r, r["changed_facts"])],
                "invariant": [("invariant_replace", p, r, r["changed_facts"])],
                "missing": [("remove", p, r, {rf: None}), ("add", r, p, {rf: p["facts"].get(rf)})] if rf else []}
        for kind, c, e, ed in pairs.get(r["variant"], []):
            cands[(r.get("view", "prose"), kind)].append({"bank_id": f"{c['id']}|{kind}", "kind": kind,
                    "view": r.get("view", "prose"), "case_id": c["id"], "edited_id": e["id"], "edits": ed,
                    "oracle": e["gold"]["decision"]})
    rng, bank = random.Random(seed), []
    for view in sorted({v for v, _ in cands}):
        tot = min(len(cands[(view, k)]) / p for k, p in PROPS.items())
        for k, p in PROPS.items():
            pool = sorted(cands[(view, k)], key=lambda x: x["bank_id"])
            rng.shuffle(pool)
            bank += pool[:round(tot * p)]
    return bank


class Runner:
    """
    Calls one backend and model with fixed decoding.
    Handles concurrency, retries with backoff, an optional requests-per-minute cap and the response cache.
    """

    def __init__(self, backend, model, dec, base_url=None, key_env=None, extra=None, conc=8, retries=6, rpm=0,
            cache="runs/cache.jsonl", rep=0):
        """
        Sets up the backend client and loads the cache.
        dec holds temperature, top_p, top_k (0 = off), max_tokens, seed and thinking (bool). extra is merged into
        extra_body for "openai" (a null value drops a default key) and passed to vllm.LLM() for "vllm". rep is the
        repeat index: it shifts every seed by 1000 * rep and is part of the cache key.
        """
        envf = Path("~/.config/cs224v/.env").expanduser()
        for ln in envf.read_text().splitlines() if envf.exists() else []:
            m = re.match(r"\s*(?:export\s+)?(\w+)\s*=\s*['\"]?([^'\"\s#]*)", ln)
            if m:
                os.environ.setdefault(m[1], m[2])
        self.backend, self.model, self.dec, self.extra, self.rep = backend, model, dec, extra or {}, rep
        self.conc, self.retries, self.rpm, self.base_url = conc, retries, rpm, base_url
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
        Returns the cache key: a sha256 over backend, base_url, model, extra options, both prompt parts, the decoding
        (temperature, top_p, top_k, max_tokens, seed, thinking) and rep.
        """
        blob = json.dumps([self.backend, self.base_url, self.model, self.extra, sys_, prm, d, self.rep], sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def call(self, sys_, prm, d):
        """
        Sends one request and returns {output, reasoning, out_tokens, think_tokens, finish}.
        Thinking goes through chat_template_kwargs and reasoning in extra_body for "openai", and through
        ThinkingConfig for "gemini" (thinking_budget 0 when off, -1 for dynamic when on; 3.8-flash rejects
        thinking_level "minimal" but accepts budget 0). finish is "length" when the output hit max_tokens.
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
                    getattr(m, "reasoning", None), "out_tokens": r.usage.completion_tokens if r.usage else None,
                    "think_tokens": None, "finish": r.choices[0].finish_reason}
        from google.genai import types
        cfg = types.GenerateContentConfig(system_instruction=sys_, temperature=d["temperature"], top_p=d["top_p"],
                top_k=d["top_k"] or None, max_output_tokens=d["max_tokens"], seed=d["seed"],
                thinking_config=types.ThinkingConfig(thinking_budget=-1 if d["thinking"] else 0))
        r = await self.cli.aio.models.generate_content(model=self.model, contents=prm, config=cfg)
        u, fr = r.usage_metadata, str(r.candidates[0].finish_reason) if r.candidates else None
        return {"output": r.text or "", "reasoning": None, "out_tokens": u.candidates_token_count if u else None,
                "think_tokens": u.thoughts_token_count if u else None,
                "finish": "length" if fr and "MAX_TOKENS" in fr else fr}

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
        decoding with its per-sample seed, the mode, the repeat index, and whether it came from the cache.
        """
        jobs = []
        for rid, rec, it, fz in items:
            sys_, prm = build_prompt(rec, it, fz)
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
                            "out_tokens": len(o.outputs[0].token_ids), "think_tokens": None,
                            "finish": o.outputs[0].finish_reason, "latency": lat}, j[4])
                    fh.write(json.dumps({"key": j[5]} | res[j[5]]) + "\n")
        rows = []
        for rid, i, sys_, prm, d, k in jobs:
            rows.append({"id": rid, "sample": i, "seed": d["seed"], "backend": self.backend, "model": self.model,
                    "mode": mode, "rep": self.rep, "decoding": d, "system": sys_, "prompt": prm,
                    "cached": k in self.cache} | (self.cache.get(k) or res[k]))
        return rows


def main():
    """
    Parses the CLI and runs the chosen mode: writes the bank, or runs answer or predict calls and writes the rows and
    <out>.meta.json.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--mode", choices=["answer", "bank", "predict"], default="answer")
    ap.add_argument("--backend", choices=["openai", "gemini", "vllm"])
    ap.add_argument("--model")
    ap.add_argument("--out")
    ap.add_argument("--bank", help="predict: bank JSONL from --mode bank")
    ap.add_argument("--frozen", help="predict: the answer run whose sample-0 outputs are frozen into the prompt")
    ap.add_argument("--no-account", action="store_true", help="predict: show only the frozen decision")
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
    ap.add_argument("--limit", type=int, default=0, help="first N items only")
    a = ap.parse_args()
    recs = load(a.data)
    if a.mode == "bank":
        bank, bp = build_bank(recs, a.seed), Path(a.out or Path(a.data).with_suffix(".bank.jsonl"))
        bp.write_text("".join(json.dumps(b) + "\n" for b in bank))
        print(f"bank={bp} items={len(bank)}", dict(sorted(Counter(b["kind"] for b in bank).items())))
        return
    if not (a.backend and a.model and a.out):
        ap.error("--backend, --model and --out are required for answer and predict")
    byid = {r["id"]: r for r in recs}
    if a.mode == "answer":
        items = [(r["id"], r, None, None) for r in recs]
    else:
        fz = {r["id"]: r["output"] for r in load(a.frozen) if r["sample"] == 0}
        items = [(b["bank_id"], byid[b["case_id"]], b, f"Decision: {parse(fz[b['case_id']])['dec'] or 'unreadable'}"
                if a.no_account else fz[b["case_id"]]) for b in load(a.bank) if b["case_id"] in fz]
    items = items[:a.limit] if a.limit else items
    dec = {"temperature": a.temperature, "top_p": a.top_p, "top_k": a.top_k, "max_tokens": a.max_tokens,
            "seed": a.seed, "thinking": a.thinking == "on"}
    t0 = time.monotonic()
    rows = Runner(a.backend, a.model, dec, a.base_url, a.key_env, a.extra, a.conc, a.retries, a.rpm, a.cache,
            a.rep).run(items, a.n, a.mode + ("_noacc" if a.no_account else ""))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    fresh = [r for r in rows if not r["cached"] and "latency" in r]
    errs = [r["error"] for r in rows if r.get("error")]
    meta = {"model": a.model, "backend": a.backend, "mode": a.mode, "no_account": a.no_account, "decoding": dec,
            "n": a.n, "rows": len(rows), "cached": sum(r["cached"] for r in rows), "errors": len(errs),
            "fresh_calls": len(fresh), "wall_s": round(time.monotonic() - t0, 2),
            "out_tokens": sum(r.get("out_tokens") or 0 for r in rows),
            "think_tokens": sum(r.get("think_tokens") or 0 for r in rows),
            "mean_latency_s": round(sum(r["latency"] for r in fresh) / max(1, len(fresh)), 3)}
    out.with_name(out.stem + ".meta.json").write_text(json.dumps(meta, indent=1))
    print(" ".join(f"{k}={v}" for k, v in meta.items() if k != "decoding"))
    for e in sorted(set(errs))[:3]:
        print("error:", e)


if __name__ == "__main__":
    main()
