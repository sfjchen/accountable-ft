"""Exports SFT examples from a gen.py data file as chat-format JSONL, one row per record of the chosen split and views.

Each row is {id, messages: [system, user, assistant], mask_spans}. The system and user turns are infer.build_prompt,
the exact answer prompt of the harness, and the assistant turn is infer.format_target, the gold account in the
answer format that evaluate.parse reads (Decision line first, then Policy support, Assumptions and Smallest change).
mask_spans holds [start, end) character spans of the assistant content covering the account lines, everything after
the Decision line, so the decision-only control can drop them from the loss (train.py --condition decision).
--cases-per-family K keeps a seeded sample of K base cases per template family, each with all its variants and
views. --drop-flagged PATH drops the item ids listed one per line (scripts/audit_cd.py --flagged writes
data/v1.flagged.txt). Output order is shuffled under --seed, so the same flags give the same file.

Usage: python scripts/sft_data.py --split train --out data/v1.sft.train.jsonl [--view prose table] [--seed 0]
        [--cases-per-family 5] [--data data/v1.jsonl] [--drop-flagged data/v1.flagged.txt]
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from infer import build_prompt, format_target, root  # noqa: E402

VIEWS = ["table", "prose", "prose_derive"]


def to_example(rec):
    """
    Returns the SFT row of one record: the harness prompt, the gold target and the span of its account lines.
    """
    sys_, usr = build_prompt(rec)
    tgt = format_target(rec)
    cut = tgt.index("\n") + 1
    return {"id": rec["id"], "messages": [{"role": "system", "content": sys_}, {"role": "user", "content": usr},
            {"role": "assistant", "content": tgt}], "mask_spans": [[cut, len(tgt)]]}


def main():
    """
    Parses flags, filters and caps the records, writes the shuffled examples and prints counts per view and class.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data/v1.jsonl"))
    ap.add_argument("--split", required=True, choices=["train", "dev"])
    ap.add_argument("--view", nargs="+", default=VIEWS, choices=VIEWS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cases-per-family", type=int, default=0, help="base cases kept per family (0 keeps all)")
    ap.add_argument("--drop-flagged", metavar="PATH", help="file of item ids to drop, one per line")
    a = ap.parse_args()
    recs = [json.loads(ln) for ln in Path(a.data).read_text().splitlines() if ln.strip()]
    by = {r["id"]: r for r in recs}
    drop = set(Path(a.drop_flagged).read_text().split()) if a.drop_flagged else set()
    sel = [r for r in recs if r["split"] == a.split and r["view"] in a.view]
    nd, sel = len(sel), [r for r in sel if r["id"] not in drop]
    nd -= len(sel)
    rng = random.Random(a.seed)
    if a.cases_per_family:
        fams = defaultdict(set)
        for r in sel:
            if r["variant"] == "base":
                fams[r["template_family"]].add(r["id"].rsplit(":", 1)[0])
        keep = set()
        for f in sorted(fams):
            bs = sorted(fams[f])
            rng.shuffle(bs)
            keep.update(bs[:a.cases_per_family])
        sel = [r for r in sel if root(r, by) in keep]
    rows = [to_example(r) for r in sorted(sel, key=lambda r: r["id"])]
    rng.shuffle(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(json.dumps(x) + "\n" for x in rows))
    cnt = Counter((r["view"], r["gold"]["decision"]) for r in sel)
    decs = ["approve", "deny", "cannot determine"]
    print(f"{len(rows)} examples ({a.split}, views {', '.join(a.view)}, {nd} flagged dropped) -> {a.out}")
    print("view".ljust(14) + "".join(d.rjust(18) for d in decs) + "total".rjust(8))
    for v in a.view:
        print(v.ljust(14) + "".join(str(cnt[v, d]).rjust(18) for d in decs) +
                str(sum(cnt[v, d] for d in decs)).rjust(8))


if __name__ == "__main__":
    main()
