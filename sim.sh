#!/bin/bash
# Runs the simulator ($1 = gemini or opus) over the runs named in runs/ by the regex PAT (v1 file names, default the
# row-matched grid) on each test file in FILES (default the 4 original ones), repeating until a pass has no errors,
# with a 10 min pause after a pass with errors (rate or usage limit), up to 12 passes. Runs from any host with the
# repo as the working directory: the Mac under ljob, a FarmShare or sc Slurm job, a VM.
# Env: TAG (names the done marker LOGS/sim-<TAG>-<sim>.done), PAT, FILES, CONC (parallel Gemini requests, default 16,
# OCONC for Opus, default 8),
# PY (python, default python3), LOGS (marker dir, default ~/dev/logs), PUSH (branch to push the results to), SIMS
# (all, the default, for the own, shuffled and no-explanation passes, or own+shuf for the 2 the paired gain needs).
# Finished calls come from the response cache, so a rerun after more runs land, or on another host with the cache
# copied over (or gunzip -k runs/cache.jsonl.gz on a fresh clone), is cheap.
# Fails at once when a frozen answer file or data file is missing.
set -u
# node for the Opus CLI and gcloud on the Mac (absent elsewhere, harmless)
export PATH=$HOME/.nvm/versions/node/v22.18.0/bin:/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/bin:$PATH
SIMS=${SIMS:-all} TAG=${TAG:-grid} PAT=${PAT:-'^rm-(inv|real|mix)-(account|decision)-e2-s[0-2]$'}
FILES=${FILES:-"v1 mortgage-split snap dependent"} CONC=${CONC:-16} PY=${PY:-python3} LOGS=${LOGS:-$HOME/dev/logs}
mkdir -p "$LOGS"
if [ "$1" = gemini ]; then
  D=runs F="--backend gemini --vertex --model gemini-3.5-flash-lite --temperature 0 --conc $CONC"
else
  D=runs/sim-opus F="--backend claude-cli --model claude-opus-5-5 --conc ${OCONC:-8} --retries 6
      --cache runs/cache-opus.jsonl"
fi
RS=$(for p in runs/*.jsonl; do b=${p#runs/}; b=${b%.jsonl}; [[ $b =~ ^[a-z0-9-]+$ ]] && echo "$b"; done |
    grep -E "$PAT")
[ -n "$RS" ] || { echo "no runs match $PAT"; exit 1; }
echo "runs: $(echo $RS | wc -w) ($(echo $RS)) on $FILES, conc $CONC, $(hostname)"
for r in $RS; do for f in $FILES; do fr=$r; [ $f = v1 ] || fr=$f-$r
  [ -s runs/$fr.jsonl ] && [ -s data/$f.jsonl ] && [ -s data/$f.bank.jsonl ] ||
      { echo "missing runs/$fr.jsonl or data/$f"; exit 1; }
done; done
for try in $(seq 12); do
  bad=0
  for r in $RS; do
    for f in $FILES; do
      fr=$r; [ $f = v1 ] || fr=$f-$r
      # Opus gets its own copy of the frozen answers so its simulate files never overwrite Gemini's
      [ $D = runs ] || [ -s $D/$fr.jsonl ] || cp runs/$fr.jsonl $D/$fr.jsonl
      # captured, then printed once: tee to /dev/stderr truncated the shared Slurm log on every pass
      if [ "$SIMS" = all ]; then sp=(--all-sim); else sp=(--out $D/$fr.simulate.jsonl); fi
      out=$($PY infer.py --mode simulate "${sp[@]}" --data data/$f.jsonl --bank data/$f.bank.jsonl \
          --frozen $D/$fr.jsonl $F 2>&1)
      [ "$SIMS" = all ] || out+=$'\n'$($PY infer.py --mode simulate --shuffle-accounts \
          --out $D/$fr.simulate_shuf.jsonl --data data/$f.jsonl --bank data/$f.bank.jsonl --frozen $D/$fr.jsonl $F 2>&1)
      echo "$out"
      grep -q "errors=[1-9]" <<< "$out" && bad=1
    done
  done
  if [ $bad = 0 ]; then
    echo ALL_DONE; touch "$LOGS/sim-$TAG-$1.done"
    # PUSH=<branch> commits the new runs and pushes them there (FarmShare deploy key), so no login is needed to
    # collect them: git fetch origin <branch> && git merge origin/<branch> on the Mac
    if [ -n "${PUSH:-}" ]; then
      git add runs && git commit -qm "runs: $TAG $1 simulator passes ($(hostname))" &&
          git push -q origin "HEAD:refs/heads/$PUSH" ||
        { echo "PUSH_FAILED"; exit 1; }
    fi
    exit 0
  fi
  echo "pass $try had errors, sleeping"; sleep 600
done
echo GAVE_UP; exit 1
