"""
Prints the simulator passes to rerun after a simulator prompt change, 1 sim.sh call per line:
<sim> <test file> <passes joined by +> <run regex>. It takes every run file the cited evals read (bash score.sh
list) and the passes that run already has (own, shuf, noacc, wrong companions), plus the wrong-reason pass on the
Opus grid's explanation runs, which the mix comparison needs. Grid runs (rm-*) come first, so a partial rerun covers
the mix comparison.
Usage: python resim.py [gemini|opus]; the Mac runs the lines with
  python resim.py opus | while read s f p r; do TAG=resim-$f SIMS=$p FILES=$f PAT="$r" bash sim.sh $s; done
"""
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

TESTS = ["mortgage-split-x", "snap-x", "dependent-x", "review-x", "v1-x", "mortgage-split", "snap", "dependent",
         "permit", "mortgage"]
PASSES = {"own": "", "shuf": "_shuf", "noacc": "_noacc", "wrong": "_wrong"}


def main():
    """
    Groups the run files of the cited evals by simulator, test file, grid or not and existing passes, and prints
    1 line per group, grid groups first.
    """
    want = sys.argv[1:] or ["gemini", "opus"]
    out = subprocess.run(["bash", "score.sh", "list"], capture_output=True, text=True, check=True).stdout
    files = sorted({w for w in out.replace("+", " ").split() if w.startswith("runs/") and w.endswith(".jsonl")})
    grp = defaultdict(list)
    for f in map(Path, files):
        sim, b = "opus" if f.parent.name == "sim-opus" else "gemini", f.name[:-6]
        t = next((t for t in TESTS if b.startswith(t + "-")), "v1")
        r = b if t == "v1" else b[len(t) + 1:]
        ps = [p for p, x in PASSES.items() if (f.parent / f"{b}.simulate{x}.jsonl").exists()]
        if sim == "opus" and r.startswith("rm-") and "-account-" in r and "wrong" not in ps:
            ps.append("wrong")
        if ps and sim in want:
            grp[(not r.startswith("rm-"), sim, t, "+".join(ps))].append(r)
    for (_, sim, t, ps), rs in sorted(grp.items()):
        print(sim, t, ps, "^(" + "|".join(sorted(rs)) + ")$")


if __name__ == "__main__":
    main()
