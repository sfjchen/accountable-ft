"""Audits the "cannot determine" (cd) items of a generated dataset for leaked or distorted facts.

For one slice and view (default: the primary population, unseen_family_train_vocab, prose) it checks each cd
item by a lexicon built from domains/*.yaml (fact labels, say strings, enum names): whether the text mentions a
missing fact, whether stated_facts agrees with what the text states (presence of every fact, value of every
tagged sentence), and whether the engine's two cd witnesses still decide approve and deny under the record.
It then lists every enum value's renderings (yaml templates and Gemini sentences in all slices) and flags
those that carry no token distinguishing the value from its siblings (a hypernym such as "an academic
institution" for university, or an omitted value). With --run it adds the model's decisions on cd items.
Prints a markdown summary, then --sample stratified cd items for reading. --flagged PATH writes the ids of the
items to drop from training, one per line: every item (all slices and prose views) with a lossy enum sentence,
and every cd item whose text presupposes the object a missing zero guard covers (zero_guard_presupposed).

Usage: python scripts/audit_cd.py data/v1.jsonl --run runs/v1-lite.jsonl --sample 30 --seed 0
        [--flagged data/v1.flagged.txt]
"""
import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import engine as E  # noqa: E402
from gen import STOP, Fmt, dist_pats, load_domain, names_value, policy_for  # noqa: E402

NEG = re.compile(r"\b(no|not|none|never|without|lacks?|lacking|absent|neither|nor|missing|omits?|declined|yet to|"
                 r"zero|exclud\w*|omit\w*|absence of|free of|lack\w*|unavailable|fail\w*|pending|unspecified|undecided|"
                 r"(?:be|been) (?:decided|determined)|under (?:internal )?consideration|has not|have not|"
                 r"did not|does not|was not|were not|nothing)\b|n't", re.I)
W = {"single": 1, "sole": 1, "a single": 1}
W.update({w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                     "thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())})
W.update({w: 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)})
ORD = {"first": 1, "second": 2, "third": 3, "fifth": 5, "eighth": 8, "ninth": 9, "twelfth": 12}
MONTHS = "january february march april may june july august september october november december".split()


def toks(s):
    """
    Returns the lowercase content tokens of a string, placeholders removed and a plural s stripped.
    """
    s = re.sub(r"\{[^}]*\}", " ", s)
    return {re.sub(r"(?<=[a-z]{3})s$", "", w) for w in re.findall(r"[a-z][a-z-]+", s.lower())} - STOP


def lexicon(dom):
    """
    Returns {fact: anchor tokens}: tokens of the fact's label and enum names, or shared by 2 of its say strings,
    that no other fact's strings and no header, color, title or preamble text of the domain use.
    """
    raw, anc = {}, {}
    for n, f in list(dom["facts"].items()) + list(dom["derived_facts"].items()):
        say = f.get("say", []) + f.get("say_true", []) + f.get("say_false", [])
        nm = list(f.get("names", {}).values())
        raw[n] = set().union(*map(toks, [f["label"]] + say + nm))
        cnt = collections.Counter(w for t in say for w in toks(t))
        anc[n] = toks(f["label"]) | set().union(*map(toks, nm)) | {w for w, k in cnt.items() if k >= 2}
    gen = set().union(*map(toks, dom["intro"] + dom["color"] + [dom["title"], dom["preamble"]] + dom["names"]))
    return {n: ws - gen - set().union(*(v for m, v in raw.items() if m != n)) for n, ws in anc.items()}


def cues(lx, n, s):
    """
    Returns whether sentence s names fact n: 2 of its anchor tokens, or all of them when it has fewer.
    """
    return len(toks(s) & lx[n]) >= min(2, len(lx[n])) > 0


def words2num(s):
    """
    Returns s with spelled-out numbers ("one hundred seven", "thirty-five thousand", "fifteenth") as digits.
    """
    def num(m):
        """
        Returns the digit string of one matched run of number words.
        """
        tot = cur = 0
        for w in re.split(r"[\s-]+", m[0].lower()):
            v = ORD.get(w) or W.get(w) or W.get(re.sub(r"th$", "", w.replace("ieth", "y"))) or 0
            if w == "hundred":
                cur *= 100
            elif w == "thousand":
                tot, cur = tot + cur * 1000, 0
            elif w != "and":
                cur += v
        return str(tot + cur)
    ws = "|".join(list(W) + list(ORD) + ["[a-z]+tieth", "[a-z]+teenth", "fourth", "sixth", "seventh", "tenth"])
    return re.sub(rf"\b(?:{ws})(?:(?:[\s-]+|\s+and\s+)(?:{ws}|hundred|thousand))*\b|\bhundred\b", num, s, flags=re.I)


def nums(s):
    """
    Returns the numbers in a string (words read as digits, commas dropped, "60k" and "60 thousand" scaled)
    plus (month, day) pairs in either order.
    """
    s, out = words2num(s), set()
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(k\b|thousand\b)?", s, re.I):
        v = float(m[1].replace(",", "")) * (1000 if m[2] else 1)
        out.add(int(v) if v == int(v) else v)
    mo = "|".join(MONTHS)
    for m in re.finditer(rf"\b({mo})\s+(\d{{1,2}})\b|\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({mo})\b", s, re.I):
        out.add((m[1] or m[4]).lower() + " " + (m[2] or m[3]))
    return out


def renders(dom, n, v):
    """
    Returns the yaml template sentences for fact n at value v.
    """
    f = dom["facts"].get(n) or dom["derived_facts"][n]
    lst = f.get("say") or (f["say_true"] if v else f["say_false"])
    return [Fmt(dom, n).format(t, v=v) for t in lst]


def value_ok(dom, n, v, s):
    """
    Returns whether sentence s carries value v of fact n: for bools the side (say_true or say_false) whose
    negation cue it shares when only one side negates, else whose own tokens it shares more (True on a tie);
    a distinguishing name token for enums; for numbers the numbers of some yaml rendering of v.
    """
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


def kind(dom, n):
    """
    Returns "bool", "enum" or "number" for fact n of a domain (derived facts are numbers).
    """
    return {"bool": "bool", "enum": "enum"}.get((dom["facts"].get(n) or {}).get("type"), "number")


def presupposed(r):
    """
    Returns the sentence of a cd record that states the false side of a zero guard ("supp_mb == 0 or x") whose
    guard fact is missing and needed, so the text presupposes the guarded object, else None.
    """
    miss = {n for n, st in r["fact_states"].items() if st["state"] == "missing"}
    for q in r["policy_spec"]["rules"]:
        m = re.fullmatch(r"(\w+) == 0 or (\w+)", q.get("cond", ""))
        if m and m[1] in miss and m[1] in r["gold"]["needs_facts"] and r["facts"].get(m[2]) is False:
            return next(x["sentence"] for x in r["case_sentences"] if x["fact"] == m[2])
    return None


def main():
    """
    Parses arguments, runs the item, enum and model checks and prints the summary and the sample.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--slice", default="unseen_family_train_vocab")
    ap.add_argument("--view", default="prose")
    ap.add_argument("--run", help="answer run jsonl whose decisions on cd items are reported")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--flagged", metavar="PATH", help="writes the ids of lossy-enum and zero_guard_presupposed items")
    a = ap.parse_args()
    recs = [json.loads(line) for line in open(a.data)]
    byid = {r["id"]: r for r in recs}
    doms = {d: load_domain(d) for d in sorted({r["domain"] for r in recs})}
    lex = {d: lexicon(dom) for d, dom in doms.items()}
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
        enum_hit = [(n, x["sentence"]) for n in miss if dom["facts"][n]["type"] == "enum" for x in sents
                    for v in dom["facts"][n]["values"] if all(re.search(p, x["sentence"], re.I)
                                                              for p in dist_pats(dom["facts"][n])[v])]
        if hit or enum_hit:
            c["missing_fact_mentioned"] += 1
            bad["missing_fact_mentioned"].append((r["id"], (hit + enum_hit)[0]))
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
    print(f"# cd audit: {a.data}, slice {a.slice}, view {a.view}\n")
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
            if r["domain"] == d and r["case_sentences"]:
                for x in r["case_sentences"]:
                    if x["fact"] in dom["facts"] and dom["facts"][x["fact"]]["type"] == "enum":
                        seen[x["fact"], x["value"]][x["sentence"]] += 1
        for n, f in dom["facts"].items():
            if f["type"] != "enum":
                continue
            pats = dist_pats(f)
            for v in f["values"]:
                yml = [s for s in renders(dom, n, v) if not names_value(f, v, s)]
                ss = seen[n, v]
                lost = {s: k for s, k in ss.items() if not names_value(f, v, s)}
                wrong = {s for s in ss for u in f["values"] if u != v and names_value(f, u, s)}
                print(f"- {d}.{n}={v} ({f['names'][v]!r}, tokens {pats[v]}): yaml lossy {len(yml)}/{len(f['say'])}, "
                      f"Gemini {len(ss)} distinct / {sum(ss.values())} uses, lossy {len(lost)} distinct / "
                      f"{sum(lost.values())} uses, names another value {len(wrong)}")
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
    if a.run:
        out = {}
        for line in open(a.run):
            o = json.loads(line)
            if o.get("mode") == "answer" and str(o.get("rep", "0")) == "0":
                m = re.search(r"Decision:\s*(approve|deny|cannot determine)", o.get("output") or "", re.I)
                out[o["id"]] = m[1].lower() if m else "unparsed"
        got = [(r, out[r["id"]]) for r in cd if r["id"] in out]
        hid = {r["id"] for r in hurt}
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


if __name__ == "__main__":
    main()
