#!/bin/bash
# Rescores every eval the report cites, each under stamp-run (~/dev/scripts/stamp-run on PATH), from a clean
# checkout of the commit to stamp. Every eval is independent, so a Slurm array can run them at once.
#   bash score.sh list        prints the evals, 1 per line: <log label> <command>
#   bash score.sh run <i>     runs eval i (1-based) under stamp-run, log final-<label>-eval-<commit>-<date>.log
#   bash score.sh all         runs every eval in turn
# Env: LOGS (stamp-run logs, default ~/dev/logs; JSON tables go to LOGS/evals-final), PY (default python3),
#   RAW=<cond> (run only: adds --contrast-raw <cond>, label and JSON get a -raw suffix).
# The extended test families are scored only once their simulator passes exist (the last run's shuf file).
set -euo pipefail
LOGS=${LOGS:-$HOME/dev/logs} PY=${PY:-python3} J=${LOGS:-$HOME/dev/logs}/evals-final
E="$PY evaluate.py"

# Prints the run files of conditions $2... with prefix $1 (runs/ or runs/sim-opus/), seeds 0-2 at epoch 2.
r() {
  local d=$1 c s
  shift
  for c in "$@"; do for s in 0 1 2; do printf '%s ' "$d$c-e2-s$s.jsonl"; done; done
}

# Prints the 18 grid run files on test prefix $1, each joined with the same run on prefix $2 (pooled) when given.
g() {
  local m c s
  for m in inv real mix; do for c in account decision; do for s in 0 1 2; do
    printf '%s ' "runs/$1rm-$m-$c-e2-s$s.jsonl${2:++runs/$2rm-$m-$c-e2-s$s.jsonl}"
  done; done; done
}

# Prints every eval as "<label> <command>".
evals() {
  local f p d sd o op fo B R
  # Opus reran only the grid after the Edit ID fix (resim.py), so the main, permit and prompted-control evals are
  # Gemini only
  for sd in gemini:runs/; do
    d=${sd#*:}
    echo "v1-${sd%:*} $E $(r $d account decision) ${d}base-thinkoff.jsonl $(r $d r2-account r2-decision)" \
      "${d}mo-account-e2-s0.jsonl ${d}mo-decision-e2-s0.jsonl --data data/v1.jsonl --bank data/v1.bank.jsonl" \
      "--compare decision --contrast '' r2 mo --json $J/v1-${sd%:*}.json"
    p=mortgage-split-
    echo "mortgage-${sd%:*} $E $(r $d ${p}account ${p}decision) ${d}${p}base-thinkoff.jsonl" \
      "$(r $d ${p}r2-account ${p}r2-decision) ${d}${p}mo-account-e2-s0.jsonl ${d}${p}mo-decision-e2-s0.jsonl" \
      "--data data/mortgage-split.jsonl --bank data/mortgage-split.bank.jsonl --compare decision" \
      "--contrast mortgage-split mortgage-split-r2 mortgage-split-mo --json $J/mortgage-${sd%:*}.json"
  done
  for sd in gemini:runs/; do
    d=${sd#*:} o=${sd%:*}
    echo "permit-$o $E $(r $d permit-account permit-decision) ${d}permit-base-thinkoff.jsonl" \
      "--data data/permit.jsonl --bank data/permit.bank.jsonl --compare decision --json $J/permit-$o.json"
    for f in v1 mortgage-split; do
      p=; [ $f = v1 ] || p=$f-
      echo "$f-peA-$o $E $(r $d ${p}account ${p}decision ${p}pe-decision) --data data/$f.jsonl" \
        "--bank data/$f.bank.jsonl --compare pe-decision --json $J/$f-peA-$o.json"
      echo "$f-peB-$o $E $(r $d ${p}account ${p}pe-account) --data data/$f.jsonl --bank data/$f.bank.jsonl" \
        "--compare pe-account --json $J/$f-peB-$o.json"
    done
  done
  for f in v1 mortgage-split snap dependent; do
    p=; [ $f = v1 ] || p=$f-
    for sd in gemini:runs/ opus:runs/sim-opus/; do
      R=$(g "$p" | sed "s#runs/#${sd#*:}#g")
      echo "$f-grid-${sd%:*} $E $R--data data/$f.jsonl --bank data/$f.bank.jsonl --compare decision" \
        "--contrast ${p}rm-mix ${p}rm-real ${p}rm-inv --json $J/$f-grid-${sd%:*}.json"
    done
  done
  # round 1 at epoch 1 on v1: exploratory, since epoch 2 was fixed at submit
  echo "v1-e1-gemini $E runs/account-e1-s0.jsonl runs/account-e1-s1.jsonl runs/account-e1-s2.jsonl" \
    "runs/decision-e1-s0.jsonl runs/decision-e1-s1.jsonl runs/decision-e1-s2.jsonl --data data/v1.jsonl" \
    "--bank data/v1.bank.jsonl --compare decision --json $J/v1-e1-gemini.json"
  # extended test families (registered Nov 14): the new families alone, then pooled with the original ones (a+b runs
  # and 2 banks, so evaluate also prints the old-minus-new gain per mix)
  for fo in review-x:v1 dependent-x:dependent v1-x:v1 snap-x:snap mortgage-split-x:mortgage-split; do
    f=${fo%:*} o=${fo#*:} op=
    [ $o = v1 ] || op=$o-
    # Opus scores only the files it simulated (the new mortgage and SNAP families, own, shuffled and wrong passes)
    for sd in gemini:runs/ opus:runs/sim-opus/; do
      d=${sd#*:}
      [ -s $d$f-rm-mix-decision-e2-s2.simulate_shuf.jsonl ] || continue
      B=; [ -s $d$f-base-thinkoff.simulate_shuf.jsonl ] && B="$d$f-base-thinkoff.jsonl "
      echo "$f-grid-${sd%:*} $E $(g $f- | sed "s#runs/#$d#g")$B--data data/$f.jsonl --bank data/$f.bank.jsonl" \
        "--compare decision --contrast $f-rm-mix $f-rm-real $f-rm-inv --json $J/$f-grid-${sd%:*}.json"
      echo "$f-pool-grid-${sd%:*} $E $(g "$op" $f- | sed "s#runs/#$d#g")--data data/$o.jsonl data/$f.jsonl" \
        "--bank data/$o.bank.jsonl data/$f.bank.jsonl --compare decision --contrast ${op}rm-mix ${op}rm-real" \
        "${op}rm-inv --json $J/$f-pool-grid-${sd%:*}.json"
    done
  done
  # real vs invented arms (registered Nov 24): the R4 and M explanation runs, seeds 0-4, on the 2 held-out domains
  # (IRS dependents with the original and new families pooled, FMLA), then the registered readout over both JSONs
  A=$(for m in r4 mix; do for s in 0 1 2 3 4; do printf 'rm-%s-account-e2-s%s ' $m $s; done; done)
  echo "dependent-pool-arms $E $(for x in $A; do printf 'runs/dependent-%s.jsonl+runs/dependent-x-%s.jsonl ' $x $x
    done)--data data/dependent.jsonl data/dependent-x.jsonl --bank data/dependent.bank.jsonl" \
    "data/dependent-x.bank.jsonl --json $J/dependent-arms.json"
  echo "fmla-arms $E $(for x in $A; do printf 'runs/fmla-%s.jsonl ' $x; done)--data data/fmla.jsonl" \
    "--bank data/fmla.bank.jsonl --json $J/fmla-arms.json"
  echo "arms-readout $PY arms.py $J/dependent-arms.json $J/fmla-arms.json"
  # secondary: mortgage-x and SNAP-x, the Gemini own and wrong-reason passes
  for f in mortgage-split-x snap-x; do
    echo "$f-arms $E $(for x in $A; do printf 'runs/%s-%s.jsonl ' $f $x; done)--data data/$f.jsonl" \
      "--bank data/$f.bank.jsonl --json $J/$f-arms.json"
  done
  echo "arms-secondary $PY arms.py $J/mortgage-split-x-arms.json $J/snap-x-arms.json --secondary"
  # error analysis on IRS dependents: the dump of every scored case and edit, then the tally of leading causes
  R=$(for m in inv real mix; do for s in 0 1 2; do printf 'dependent-rm-%s-account-e2-s%s ' $m $s; done; done)
  echo "dependent-errors bash -c \"$E $(for x in $R; do printf 'runs/%s.jsonl ' $x; done)--data data/dependent.jsonl" \
    "--bank data/dependent.bank.jsonl --json $J/errors-dump.json --dump $J/errors > /dev/null &&" \
    "$PY errors.py --dump $J/errors --runs $R--data data/dependent.jsonl --tally\""
}

mkdir -p "$J"
case ${1:?usage: bash score.sh list | run <i> | all} in
  list) evals | nl -w2 -s' ' ;;
  run)
    ln=$(evals | sed -n "${2:?missing eval number}p")
    [ -n "$ln" ] || { echo "no eval $2"; exit 1; }
    [ -z "${RAW:-}" ] || ln=$(sed -E "s/^([^ ]+)/\1-raw/; s/\.json( |\$)/-raw.json --contrast-raw $RAW\1/" <<< "$ln")
    eval "STAMP_DIR=$LOGS stamp-run final-${ln%% *}-eval -- ${ln#* }" > /dev/null ;;
  all) n=$(evals | wc -l); for i in $(seq "$n"); do bash "$0" run "$i"; done ;;
esac
