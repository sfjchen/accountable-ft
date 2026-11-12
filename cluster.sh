#!/usr/bin/env bash
# cluster.sh: setup, cluster probe, smoke check, the training runs, their evaluation and the prompted-base evaluation
# on FarmShare (/scratch/users/$USER/accountable-ft) or the Stanford NLP sc cluster (CLUSTER=sc, detected from
# /juice2: the project space, partition sc-loprio, account nlp, MAIL must be set since jobs run under a shared
# account). smoke, train, eval, base and grid submit this script itself to Slurm with their resources (extra sbatch
# options in SB), and the job runs the body inside the allocation.
# train --chunks splits each 2-epoch run into 2 dependent 55-minute 1-epoch jobs, which fit backfill windows.
# MIX picks the training mix data/$MIX.sft.{train,dev}.jsonl: v1 (default, outputs/<cond>-s<seed>), r2 (grant, trial
# and mortgage, review held out) or mo (mortgage only), the last 2 under outputs/$MIX-<cond>-s<seed>. The row-matched
# grid trains inv (grant + trial), real (mortgage + SNAP) and mix (all 4) at 3,600 rows each, every domain an equal
# share, and tests on review and the dependent tests, which none of them trains on.
# Usage: bash cluster.sh setup | probe | smoke [account|decision] | train [--chunks [--runs <cond>-s<seed>,...]] |
#   eval [r2-|mo-]<cond>-s<seed> <epoch> (DATA=<file>[,<file>] for other data files) |
#   base (THINKING=on|off, CASES=N for a stratified subset) | notify <group> <jobid>[,<jobid>...] |
#   grid (18 jobs, at most 2 at once: inv, real, mix x account, decision x seeds 0-2, each trains then answers)
set -euo pipefail
{
cmd=${1:?usage: bash cluster.sh setup|probe|smoke|train|eval|base|grid|notify}
shift
CLUSTER=${CLUSTER:-$([[ -d /juice2/scr2/nlp/cs224v ]] && echo sc || echo farmshare)}
if [[ $CLUSTER == sc ]]; then
  # everything, the uv binary and run metadata included, stays in the project folder, not the shared account's home
  SCRATCH=${SCRATCH:-/juice2/scr2/nlp/cs224v/jchen04-aft} META_HOME=$SCRATCH/meta BIN=$SCRATCH/.local/bin
  PART=(--partition=sc-loprio --account=nlp) CPUPART=(--partition=sc-loprio --account=nlp)
  # any GPU with 48 GB or more that the cu126 training stack supports (not Blackwell)
  GPU=(--gres=gpu:1 "--constraint=48G|80G|141G")
else
  SCRATCH=${SCRATCH:-/scratch/users/$USER} META_HOME=$HOME/accountable-ft-meta BIN=$HOME/.local/bin
  PART=(--partition=gpu) CPUPART=(--partition=normal) GPU=(--gpus=1)
fi
REPO=$SCRATCH/accountable-ft
VENV=$REPO/.venv SERVE_VENV=$REPO/.venv-serve MODEL_FILE=$REPO/outputs/model_id
export CLUSTER SCRATCH REPO VENV SERVE_VENV MODEL_FILE META_HOME PATH=$BIN:$PATH
export HF_HOME=$SCRATCH/hf UV_CACHE_DIR=$SCRATCH/.uv/cache UV_PYTHON_INSTALL_DIR=$SCRATCH/.uv/python
export XDG_CACHE_HOME=$SCRATCH/.cache TRITON_CACHE_DIR=$SCRATCH/.cache/triton VLLM_CACHE_ROOT=$SCRATCH/.cache/vllm
OUT=$REPO/runs/slurm
# a job mails only when it fails (MAIL=<address>, default the SUNet address), and notify sends 1 mail when a whole
# group has ended, so the inbox only gets mail that needs action
[[ $CLUSTER == sc && -z ${MAIL:-} ]] && { echo "error: set MAIL on sc, jobs run under a shared account" >&2; exit 1; }
MAIL=${MAIL:-$USER@stanford.edu}
MAILF=("--mail-type=FAIL" "--mail-user=$MAIL")
# One decoding budget for every run served here (base, thinking on and off, trained): evaluate.py refuses to compare
# runs whose max_tokens differ, and thinking answers run 5-10k tokens. Non-thinking answers stop long before it.
MAX_TOKENS=${MAX_TOKENS:-16384} MAX_LEN=${MAX_LEN:-24576}
MIX=${MIX:-v1}
PRE=$([[ $MIX == v1 ]] || echo "$MIX-")
export MIX

# Prints a message to stderr and exits.
die() {
  echo "error: $*" >&2
  exit 1
}

if [[ $cmd == train && ${1:-} == --chunks && -z ${SLURM_JOB_ID:-} ]]; then
  # chunk 1 stops after epoch 1, chunk 2 resumes from its checkpoint. Everything stays on gpu: normal shares its
  # nodes at PriorityTier 1 (gpu has 5), so a GPU job there only gets a GPU the gpu queue leaves idle
  runs=account-s0,account-s1,account-s2,decision-s0,decision-s1,decision-s2
  [[ ${2:-} == --runs ]] && runs=${3:?usage: bash cluster.sh train --chunks --runs account-s1,decision-s0}
  mkdir -p "$REPO/runs/slurm"
  echo "mix $MIX: data/$MIX.sft.{train,dev}.jsonl -> outputs/$PRE<run>"
  printf '%-12s %-9s %-10s %-10s\n' run partition chunk1 chunk2
  for r in ${runs//,/ }; do
    [[ $r =~ ^(account|decision)-s([0-2])$ ]] || die "bad run $r, want <account|decision>-s<0-2>"
    if [[ -d $REPO/outputs/$PRE$r/merged ]]; then
      printf '%-12s %s\n' "$r" "skipped, outputs/$PRE$r/merged exists"
      continue
    fi
    p=("${PART[@]}")
    dep='' ids=()
    for c in 1 2; do
      # shellcheck disable=SC2086
      j=$(sbatch --parsable "${p[@]}" "${MAILF[@]}" "${GPU[@]}" --cpus-per-task=8 --mem=48G --time=00:55:00 \
          --job-name="aft-$PRE$r-c$c" --output="$OUT/$PRE${r}_c${c}_%j.out" ${dep:+"$dep"} ${SB:-} "$0" train \
          "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "$c")
      ids+=("${j%%;*}")
      dep=--dependency=afterok:${j%%;*}
    done
    printf '%-12s %-9s %-10s %-10s\n' "$r" "${p[0]#--partition=}" "${ids[@]}"
  done
  exit
fi
if [[ $cmd == notify ]]; then
  # a 1-minute CPU job that waits for every listed job (array ids cover all tasks) to end in any state, writes their
  # states to runs/slurm/done-<group>_<id>.out and mails once, named aft-done-<group>: the subject says COMPLETED
  # when every job completed and FAILED when any did not
  grp=${1:?usage: bash cluster.sh notify <group> <jobid>[,<jobid>...]} jl=${2:?missing job ids}
  sbatch "${CPUPART[@]}" --cpus-per-task=1 --mem=1G --time=00:05:00 --mail-type=END --mail-user="$MAIL" \
      --job-name="aft-done-$grp" --dependency="afterany:${jl//,/:}" --output="$OUT/done-${grp}_%j.out" \
      --wrap "sacct -X -j $jl -o JobID%16,JobName%20,State,Elapsed,ExitCode
! sacct -X -n -j $jl -o State | grep -qv COMPLETED"
  exit
fi
case $cmd in
  smoke) res="--job-name=aft-smoke --mem=48G --time=00:40:00 --output=$OUT/smoke_%j.out" ;;
  train) res="--job-name=aft-train-$MIX --mem=48G --time=${TIME:-08:00:00} --array=${ARRAY:-0-5}
    --output=$OUT/$PRE%A_%a.out" ;;
  eval) res="--job-name=aft-eval --mem=64G --time=${TIME:-02:00:00} --output=$OUT/eval_%j.out" ;;
  base) res="--job-name=aft-base --mem=36G --time=${TIME:-02:00:00} --output=$OUT/base_%j.out" ;;
  grid) res="--job-name=aft-grid --mem=64G --time=${TIME:-08:00:00} --array=${ARRAY:-0-17%2} --requeue
    --output=$OUT/grid_%A_%a.out" ;;
  *) res= ;;
esac
if [[ $cmd == setup && $CLUSTER == sc && -z ${SLURM_JOB_ID:-} ]]; then
  # no heavy work on the shared login node: the install and checks run as a CPU job
  mkdir -p "$REPO/runs/slurm"
  sbatch "${CPUPART[@]}" --cpus-per-task=8 --mem=32G --time=03:00:00 "${MAILF[@]}" --job-name=aft-setup \
      --output="$OUT/setup_%j.out" ${SB:-} "$0" setup
  exit
fi
if [[ -n $res && -z ${SLURM_JOB_ID:-} ]]; then
  mkdir -p "$REPO/runs/slurm"
  # shellcheck disable=SC2086
  sbatch "${PART[@]}" "${GPU[@]}" --cpus-per-task=8 "${MAILF[@]}" $res ${SB:-} "$0" "$cmd" "$@"
  exit
fi

set +u  # Lmod's scripts read unset variables
if ! type module &>/dev/null; then
  # FarmShare names it z00_lmod.sh; without it a job submitted from a non-login shell gets no nvcc
  for f in /etc/profile.d/lmod.sh /etc/profile.d/z00_lmod.sh; do
    # shellcheck disable=SC1090
    [[ -f $f ]] && { source "$f"; break; }
  done
fi
# CUDA toolkit for JIT kernels (triton, flashinfer), torch wheels bring their own runtime
type module &>/dev/null && { module load cuda/12.9.0 &>/dev/null || true; }
set -u
# shellcheck disable=SC1091
[[ -f $VENV/bin/activate ]] && source "$VENV/bin/activate"

# Trains one run and copies its train_meta.json to home. Usage: train_one <cond> <seed> <out> <train> <dev> [flags]
train_one() {
  local cond=$1 seed=$2 out=$3 tr=$4 dv=$5
  shift 5
  [[ -s $MODEL_FILE ]] || die "$MODEL_FILE missing, run bash cluster.sh setup first"
  cd "$REPO"
  if [[ -d $out/adapter ]]; then
    echo "skip training: $out/adapter exists"
    return
  fi
  # a requeued (preempted) job restarts here and resumes from its last epoch checkpoint
  [[ ${RESUME_OK:-0} == 1 ]] && compgen -G "$out/checkpoint-*" > /dev/null && set -- "$@" --resume
  echo "job ${SLURM_JOB_ID:-local} $cond s$seed on $(hostname), commit $(git rev-parse --short HEAD), out $out"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
  python train.py --condition "$cond" --data "$tr" --eval-data "$dv" --seed "$seed" --model "$(cat "$MODEL_FILE")" \
      --out "$out" "$@"
  mkdir -p "$META_HOME"
  cp "$out/train_meta.json" "$META_HOME/$(basename "$out").train_meta.json"
  echo "done: $out, meta in $META_HOME"
}

# Serves a model with vllm on this job's GPU and runs the answer, repeat and both predict passes on the primary
# slice of each data file (CASES=N for a stratified subset, THINKING=on|off, CONC=N parallel requests, default 32,
# DATA a comma list of data files, default data/v1.jsonl, SLICE for another slice, e.g. DATA=data/mortgage.jsonl
# SLICE=real_transfer, PASSES=answer for the answer pass alone). Runs on a file other than v1 are named <file stem>-<run>, so 1 served model covers several
# files without their outputs colliding.
# Usage: run_passes <model path> <run name> <cache tag>
run_passes() {
  local model=$1 run=$2 tag=$3 dl=${DATA:-data/v1.jsonl} data r slc=${SLICE:-unseen_family_train_vocab}
  local port=$((8000 + SLURM_JOB_ID % 1000)) vlog=$REPO/runs/slurm/vllm_$SLURM_JOB_ID.log  # 1-GPU jobs share nodes
  # vllm serve runs from SERVE_VENV (VLLM overrides the binary): PyPI vllm 0.33 is built for CUDA 13 and dies on
  # .venv's cu126 torch (libcudart.so.13 not found), so serving has its own venv with the default cu130 torch.
  # flashinfer's JIT ops dlopen libcudart.so.13, which only the serving venv's nvidia/cu13 wheel ships. Its sampling
  # kernel is JIT-built with the module's CUDA 12.9 nvcc, links libcudart.so.12 and fails to load, and greedy decoding
  # (temperature 0) never needs it, so vllm samples in PyTorch (VLLM_USE_FLASHINFER_SAMPLER=0)
  local cu13=("$SERVE_VENV"/lib/python3*/site-packages/nvidia/cu13/lib)
  LD_LIBRARY_PATH=${cu13[0]}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH} VLLM_USE_FLASHINFER_SAMPLER=0 \
      "${VLLM:-$SERVE_VENV/bin/vllm}" serve "$model" \
      --served-model-name "$run" --host 127.0.0.1 --port "$port" --dtype bfloat16 --max-model-len "$MAX_LEN" \
      --gpu-memory-utilization 0.9 --seed 0 > "$vlog" 2>&1 &
  vpid=$!
  trap 'kill "$vpid" 2>/dev/null || true' EXIT
  for _ in $(seq 240); do
    curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null && break
    kill -0 "$vpid" 2>/dev/null || die "vllm exited, see $vlog"
    sleep 5
  done
  curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null || die "vllm not up after 20 min, see $vlog"
  for data in ${dl//,/ }; do
    r=$run
    [[ $data == data/v1.jsonl ]] || r=$(basename "${data%.jsonl}")-$run
    echo "passes: $data -> runs/$r.*"
    local S=(--data "$data" --bank "${data%.jsonl}.bank.jsonl" --slice "$slc" --view prose)
    [[ ${CASES:-0} -gt 0 ]] && S+=(--cases "$CASES")
    S+=(--backend openai --base-url "http://127.0.0.1:$port/v1" --model "$run" --cache-tag "$tag"
      --cache "runs/cache.$r.jsonl" --conc "${CONC:-32}" --max-tokens "$MAX_TOKENS" --thinking "${THINKING:-off}")
    python infer.py "${S[@]}" --out "runs/$r.jsonl"
    [[ ${PASSES:-all} == answer ]] && continue
    python infer.py "${S[@]}" --rep 1 --out "runs/$r.repeat.jsonl"
    python infer.py --mode predict "${S[@]}" --frozen "runs/$r.jsonl" --out "runs/$r.predict.jsonl"
    python infer.py --mode predict "${S[@]}" --frozen "runs/$r.jsonl" --no-account \
        --out "runs/$r.predict_noacc.jsonl"
  done
}

# Merges the epoch-k checkpoint of outputs/<name>, serves it with vllm and runs the passes on DATA, then deletes the
# merged weights unless KEEP_MERGED=1. Usage: eval_one <name> <epoch>
eval_one() {
  local name=${1:?usage: eval_one <name> <epoch>} ep=${2:?missing epoch} out run ckpt tag merged
  out=$REPO/outputs/$name
  [[ -f $out/train_meta.json ]] || die "$out has no train_meta.json, train it first"
  # run names follow evaluate.select_ckpt: <cond>-e<k>-s<seed> (smoke-<cond>-e<k> for smoke runs)
  if [[ $name =~ ^(.*)-s([0-9]+)$ ]]; then run=${BASH_REMATCH[1]}-e$ep-s${BASH_REMATCH[2]}; else run=$name-e$ep; fi
  cd "$REPO"
  echo "job $SLURM_JOB_ID: $run on $(hostname), commit $(git rev-parse --short HEAD)"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
  ckpt=$(python - "$out" "$ep" <<'PY'
import json
import sys
from pathlib import Path

out, ep = Path(sys.argv[1]), int(sys.argv[2])
hit = [c for c in out.glob("checkpoint-*") if round(json.loads((c / "trainer_state.json").read_text())["epoch"]) == ep]
if len(hit) != 1:
    sys.exit(f"expected 1 checkpoint at epoch {ep} in {out}, found {[c.name for c in hit]}")
print(hit[0])
PY
)
  # the adapter hash in the cache tag keeps retrained weights under one name from hitting old answers
  tag=$run-$(sha256sum "$ckpt/adapter_model.safetensors" | cut -c1-12) merged=$out/merged-e$ep-j$SLURM_JOB_ID
  # each job merges into its own dir and removes it, so evals of one checkpoint on 2 data files never write or
  # delete each other's weights
  echo "merging $ckpt -> $merged"
  python - "$ckpt" "$merged" <<'PY'
import sys
from unsloth import FastLanguageModel
import torch

model, tok = FastLanguageModel.from_pretrained(sys.argv[1], dtype=torch.bfloat16, load_in_4bit=False,
        max_seq_length=4096)
model.save_pretrained_merged(sys.argv[2], tok, save_method="merged_16bit")
PY
  run_passes "$merged" "$run" "$tag"
  [[ ${KEEP_MERGED:-0} == 1 ]] || rm -rf "$merged"
  echo "done: $run on ${DATA:-data/v1.jsonl}, tag $tag"
}

case $cmd in
  setup)  # idempotent: pulls, builds the venv with train.PINS, fetches the model and data, exports SFT, checks
    if [[ -d $REPO/.git ]]; then
      git -C "$REPO" pull --ff-only
    else
      git clone https://github.com/sfjchen/accountable-ft "$REPO"
    fi
    mkdir -p "$REPO/runs/slurm" "$REPO/outputs" "$HF_HOME" "$META_HOME"
    cd "$REPO"
    command -v uv &>/dev/null || module load uv &>/dev/null || true
    command -v uv &>/dev/null ||
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$BIN" UV_NO_MODIFY_PATH=1 sh
    [[ -x $VENV/bin/python ]] || uv venv --python 3.12 "$VENV"
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
    # torch and torchvision both from cu126 (a PyPI torchvision breaks unsloth), pinned through the later install
    CU=https://download.pytorch.org/whl/cu126
    printf "torch==2.14.0+cu126\ntorchvision==0.29.0+cu126\n" > "$VENV/torch-pin.txt"
    uv pip install -r "$VENV/torch-pin.txt" --index-url "$CU"
    uv pip install -c "$VENV/torch-pin.txt" --extra-index-url "$CU" --index-strategy unsafe-best-match \
        unsloth==2026.11.3 trl==1.15.0 transformers==5.17.0 peft==0.21.2 vllm==0.33.0 huggingface_hub \
        -r requirements.txt
    # serving venv: vllm with its own default (CUDA 13) torch, apart from unsloth's cu126 pin
    [[ -x $SERVE_VENV/bin/vllm ]] || { uv venv --python 3.12 "$SERVE_VENV" &&
        VIRTUAL_ENV=$SERVE_VENV uv pip install vllm==0.33.0; }
    python - <<'PY'
import os
import sys
from huggingface_hub import HfApi, snapshot_download
from huggingface_hub.utils import RepositoryNotFoundError

for m in ("unsloth/Qwen3.5-9B", "Qwen/Qwen3.5-9B"):
    try:
        HfApi().model_info(m)
    except RepositoryNotFoundError:
        print(f"{m}: not found")
        continue
    print(m, "->", snapshot_download(m))
    open(os.environ["MODEL_FILE"], "w").write(m + "\n")
    break
else:
    sys.exit("neither unsloth/Qwen3.5-9B nor Qwen/Qwen3.5-9B is available")
PY
    for z in data/*.jsonl.gz; do [[ -s ${z%.gz} ]] || gunzip -k "$z"; done  # v1, mortgage
    sha256sum data/v1.jsonl data/v1.bank.jsonl data/v1.flagged.txt
    for s in train dev; do
      python train.py export --split "$s" --drop-flagged data/v1.flagged.txt --out "data/v1.sft.$s.jsonl"
      python train.py export --split "$s" --data data/v1.jsonl data/mortgage-split.jsonl --domains grant trial \
          mortgage --drop-flagged data/v1.flagged.txt --out "data/r2.sft.$s.jsonl"
      python train.py export --split "$s" --data data/mortgage-split.jsonl --out "data/mo.sft.$s.jsonl"
      # row-matched grid: 3,600 train rows (400 dev) per mix, split evenly over its domains
      n=$([[ $s == train ]] && echo 1800 || echo 200)
      python train.py export --split "$s" --data data/v1.jsonl --domains grant trial --drop-flagged \
          data/v1.flagged.txt --rows-per-domain "$n" --out "data/rm-inv.sft.$s.jsonl"
      python train.py export --split "$s" --data data/mortgage-split.jsonl data/snap.jsonl --rows-per-domain "$n" \
          --out "data/rm-real.sft.$s.jsonl"
      python train.py export --split "$s" --data data/v1.jsonl data/mortgage-split.jsonl data/snap.jsonl --domains \
          grant trial mortgage snap --drop-flagged data/v1.flagged.txt --rows-per-domain $((n / 2)) \
          --out "data/rm-mix.sft.$s.jsonl"
    done
    python - <<'PY'
import importlib.metadata as md
import itertools
import json
import os
import sys
import torch, transformers, trl, peft, vllm, openai, yaml, numpy, google.genai, infer, evaluate, engine, gen
from transformers import AutoTokenizer
from train import PINS, Collator

print("imports ok, torch", torch.__version__, "cuda", torch.version.cuda)
assert torch.version.cuda == "12.6", torch.version.cuda
got = {k: md.version(k) for k in PINS}
for k, v in PINS.items():
    print(f"{k:14} pinned {v:14} installed {got[k]:14} {'ok' if got[k] == v else 'MISMATCH'}")
tok = AutoTokenizer.from_pretrained(open(os.environ["MODEL_FILE"]).read().strip())
with open("data/v1.sft.train.jsonl") as fh:
    rows = [json.loads(ln) for ln in itertools.islice(fh, 16)]
for c in ("account", "decision"):
    col = Collator(tok, c)
    for r in rows:
        col.check(r)
print("Collator.check ok on", len(rows), "rows, both conditions")
sys.exit(0 if got == PINS else "installed versions differ from train.PINS")
PY
    echo "setup done: repo $REPO, model $(cat "$MODEL_FILE"), venv $VENV" ;;
  probe)  # read-only: the cluster facts the jobs depend on
    for c in 'sinfo -p gpu -o "%P %a %l %D %c %m %G %T"' 'sinfo -p gpu -N -o "%N %c %m %G %f %T"' 'sinfo -s' \
        'scontrol show partition gpu' 'scontrol show partition normal' \
        'sacctmgr -P show qos gpu,normal,long format=Name,MaxTRESPU,MaxWall,MaxJobsPU,MaxSubmitPU,Priority' \
        "sacctmgr -P show assoc user=$USER format=Cluster,Account,User,Partition,QOS,DefaultQOS,MaxTRES,MaxWall" \
        'module -t avail cuda' "df -h $HOME $SCRATCH" 'quota -s'; do
      printf '\n== %s\n' "$c"
      eval "$c" 2>&1 || echo "(exit $?)"
    done ;;
  smoke)  # 40 min (slow load and merge on sc): load, train 1 epoch (16 steps) on 64 train and 16 dev rows, save, merge
    cond=${1:-account} out=$REPO/outputs/smoke-$cond
    mkdir -p "$out"
    head -n 64 "$REPO/data/v1.sft.train.jsonl" > "$out/train.jsonl"
    head -n 16 "$REPO/data/v1.sft.dev.jsonl" > "$out/dev.jsonl"
    train_one "$cond" 0 "$out" "$out/train.jsonl" "$out/dev.jsonl" --epochs 1 --grad-accum 1 ;;
  train)  # array index i: account (0-2) or decision (3-5), seed i % 3, or one chunk: train <cond> <seed> 1|2
    if [[ -n ${SLURM_ARRAY_TASK_ID:-} ]]; then
      conds=(account decision) i=$SLURM_ARRAY_TASK_ID
      set -- "${conds[i / 3]}" $((i % 3))
    fi
    cond=${1:?usage: train <cond> <seed> [1|2]} seed=${2:?missing seed}
    case ${3:-} in
      1) fl=(--epochs 2 --stop-after-epochs 1) ;;
      2) fl=(--epochs 2 --resume) ;;
      *) fl=(--epochs 2) ;;
    esac
    train_one "$cond" "$seed" "$REPO/outputs/$PRE$cond-s$seed" "data/$MIX.sft.train.jsonl" "data/$MIX.sft.dev.jsonl" \
        "${fl[@]}" ;;
  eval)  # merges the epoch-k checkpoint, serves it with vllm, runs answer, repeat and both predict passes
    eval_one "${1:?usage: bash cluster.sh eval [r2-|mo-]<cond>-s<seed> <epoch>}" "${2:?missing epoch}" ;;
  grid)  # array index i: mix (inv, real, mix) i / 6, account (0-2) or decision (3-5) by i % 6, seed i % 3
    mixes=(inv real mix) conds=(account decision) i=${SLURM_ARRAY_TASK_ID:?grid runs as an array job}
    MIX=${mixes[i / 6]} cond=${conds[i % 6 / 3]} seed=$((i % 3))
    RESUME_OK=1 train_one "$cond" "$seed" "$REPO/outputs/rm-$MIX-$cond-s$seed" "data/rm-$MIX.sft.train.jsonl" \
        "data/rm-$MIX.sft.dev.jsonl" --epochs 2
    rm -rf "$REPO/outputs/rm-$MIX-$cond-s$seed/merged"  # eval merges the epoch checkpoint itself
    # every grid model answers the same 4 test files; the simulator passes run on the Mac
    DATA=data/v1.jsonl,data/mortgage-split.jsonl,data/snap.jsonl,data/dependent.jsonl PASSES=answer \
        eval_one "rm-$MIX-$cond-s$seed" 2 ;;
  base)  # prompted base model, the same passes as eval: THINKING=on|off, CASES=N for a stratified subset
    [[ -s $MODEL_FILE ]] || die "$MODEL_FILE missing, run bash cluster.sh setup first"
    model_id=$(cat "$MODEL_FILE") run=base-think${THINKING:-off}
    [[ ${CASES:-0} -gt 0 ]] && run=$run-c$CASES
    cd "$REPO"
    echo "job $SLURM_JOB_ID: $run ($model_id) on $(hostname), commit $(git rev-parse --short HEAD)"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
    # the local snapshot, so the job never needs the network
    model=$(python -c "import sys; from huggingface_hub import snapshot_download as s; print(s(sys.argv[1], \
local_files_only=True))" "$model_id")
    run_passes "$model" "$run" "$run-$model_id-mt$MAX_TOKENS"
    echo "done: $run on ${DATA:-data/v1.jsonl}" ;;
  *) die "unknown command $cmd" ;;
esac
exit
}
