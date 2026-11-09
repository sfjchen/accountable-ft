#!/usr/bin/env bash
# farmshare.sh: setup, cluster probe, smoke check, the 6 training runs, their evaluation and the prompted-base
# evaluation on FarmShare, from /scratch/users/$USER/accountable-ft. smoke, train, eval and base submit this script
# itself to Slurm with their resources (extra sbatch options in SB), and the job runs the body inside the allocation.
# Usage: bash farmshare.sh setup | probe | smoke [account|decision] | train | eval <cond>-s<seed> <epoch>
#        | base (THINKING=on|off, CASES=N for a stratified subset)
set -euo pipefail
{
cmd=${1:?usage: bash farmshare.sh setup|probe|smoke|train|eval|base}
shift
SCRATCH=${SCRATCH:-/scratch/users/$USER}
REPO=$SCRATCH/accountable-ft
VENV=$REPO/.venv MODEL_FILE=$REPO/outputs/model_id META_HOME=$HOME/accountable-ft-meta
export SCRATCH REPO VENV MODEL_FILE META_HOME PATH=$HOME/.local/bin:$PATH
export HF_HOME=$SCRATCH/hf UV_CACHE_DIR=$SCRATCH/.uv/cache UV_PYTHON_INSTALL_DIR=$SCRATCH/.uv/python
export XDG_CACHE_HOME=$SCRATCH/.cache TRITON_CACHE_DIR=$SCRATCH/.cache/triton VLLM_CACHE_ROOT=$SCRATCH/.cache/vllm
OUT=/scratch/users/%u/accountable-ft/runs/slurm
# One decoding budget for every run served here (base, thinking on and off, trained): evaluate.py refuses to compare
# runs whose max_tokens differ, and thinking answers run 5-10k tokens. Non-thinking answers stop long before it.
MAX_TOKENS=${MAX_TOKENS:-16384} MAX_LEN=${MAX_LEN:-24576}
case $cmd in
  smoke) res="--job-name=aft-smoke --mem=48G --time=00:15:00 --output=$OUT/smoke_%j.out" ;;
  train) res="--job-name=aft-train --mem=48G --time=08:00:00 --array=0-5 --output=$OUT/%A_%a.out" ;;
  eval) res="--job-name=aft-eval --mem=64G --time=06:00:00 --output=$OUT/eval_%j.out" ;;
  base) res="--job-name=aft-base --mem=64G --time=08:00:00 --output=$OUT/base_%j.out" ;;
  *) res= ;;
esac
if [[ -n $res && -z ${SLURM_JOB_ID:-} ]]; then
  mkdir -p "$REPO/runs/slurm"
  # shellcheck disable=SC2086
  sbatch --partition=gpu --gpus=1 --cpus-per-task=8 $res ${SB:-} "$0" "$cmd" "$@"
  exit
fi

# Prints a message to stderr and exits.
die() {
  echo "error: $*" >&2
  exit 1
}

set +u  # Lmod's scripts read unset variables
if ! type module &>/dev/null && [[ -f /etc/profile.d/lmod.sh ]]; then
  # shellcheck disable=SC1091
  source /etc/profile.d/lmod.sh
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
  [[ -s $MODEL_FILE ]] || die "$MODEL_FILE missing, run bash farmshare.sh setup first"
  cd "$REPO"
  echo "job ${SLURM_JOB_ID:-local} $cond s$seed on $(hostname), commit $(git rev-parse --short HEAD), out $out"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
  python train.py --condition "$cond" --data "$tr" --eval-data "$dv" --seed "$seed" --model "$(cat "$MODEL_FILE")" \
      --out "$out" "$@"
  mkdir -p "$META_HOME"
  cp "$out/train_meta.json" "$META_HOME/$(basename "$out").train_meta.json"
  echo "done: $out, meta in $META_HOME"
}

# Serves a model with vllm on this job's GPU and runs the answer, repeat and both predict passes on the primary
# slice (CASES=N for a stratified subset, THINKING=on|off, DATA and SLICE for another data file, e.g. the mortgage
# domain: DATA=data/mortgage.jsonl SLICE=real_transfer). Usage: run_passes <model path> <run name> <cache tag>
run_passes() {
  local model=$1 run=$2 tag=$3 data=${DATA:-data/v1.jsonl} slc=${SLICE:-unseen_family_train_vocab}
  local port=$((8000 + SLURM_JOB_ID % 1000)) vlog=$REPO/runs/slurm/vllm_$SLURM_JOB_ID.log  # 1-GPU jobs share nodes
  vllm serve "$model" --served-model-name "$run" --host 127.0.0.1 --port "$port" --dtype bfloat16 \
      --max-model-len "$MAX_LEN" --gpu-memory-utilization 0.9 --seed 0 > "$vlog" 2>&1 &
  vpid=$!
  trap 'kill "$vpid" 2>/dev/null || true' EXIT
  for _ in $(seq 240); do
    curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null && break
    kill -0 "$vpid" 2>/dev/null || die "vllm exited, see $vlog"
    sleep 5
  done
  curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null || die "vllm not up after 20 min, see $vlog"
  local S=(--data "$data" --bank "${data%.jsonl}.bank.jsonl" --slice "$slc" --view prose)
  [[ ${CASES:-0} -gt 0 ]] && S+=(--cases "$CASES")
  S+=(--backend openai --base-url "http://127.0.0.1:$port/v1" --model "$run" --cache-tag "$tag"
    --cache "runs/cache.$run.jsonl" --conc 32 --max-tokens "$MAX_TOKENS" --thinking "${THINKING:-off}")
  python infer.py "${S[@]}" --out "runs/$run.jsonl"
  python infer.py "${S[@]}" --rep 1 --out "runs/$run.repeat.jsonl"
  python infer.py --mode predict "${S[@]}" --frozen "runs/$run.jsonl" --out "runs/$run.predict.jsonl"
  python infer.py --mode predict "${S[@]}" --frozen "runs/$run.jsonl" --no-account \
      --out "runs/$run.predict_noacc.jsonl"
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
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh
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
    [[ -s data/v1.jsonl ]] || gunzip -k data/v1.jsonl.gz
    sha256sum data/v1.jsonl data/v1.bank.jsonl data/v1.flagged.txt
    for s in train dev; do
      python train.py export --split "$s" --drop-flagged data/v1.flagged.txt --out "data/v1.sft.$s.jsonl"
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
  smoke)  # 15 min: load, train 1 epoch (16 steps) on 64 train and 16 dev rows, save, merge
    cond=${1:-account} out=$REPO/outputs/smoke-$cond
    mkdir -p "$out"
    head -n 64 "$REPO/data/v1.sft.train.jsonl" > "$out/train.jsonl"
    head -n 16 "$REPO/data/v1.sft.dev.jsonl" > "$out/dev.jsonl"
    train_one "$cond" 0 "$out" "$out/train.jsonl" "$out/dev.jsonl" --epochs 1 --grad-accum 1 ;;
  train)  # array index i: condition account (0-2) or decision (3-5), seed i % 3, a checkpoint per epoch
    i=${SLURM_ARRAY_TASK_ID:?submit as an array job}
    conds=(account decision)
    train_one "${conds[i / 3]}" $((i % 3)) "$REPO/outputs/${conds[i / 3]}-s$((i % 3))" data/v1.sft.train.jsonl \
        data/v1.sft.dev.jsonl ;;
  eval)  # merges the epoch-k checkpoint, serves it with vllm, runs answer, repeat and both predict passes
    name=${1:?usage: bash farmshare.sh eval <cond>-s<seed> <epoch>} ep=${2:?missing epoch}
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
    tag=$run-$(sha256sum "$ckpt/adapter_model.safetensors" | cut -c1-12) merged=$out/merged-e$ep
    if [[ ! $merged/config.json -nt $ckpt/adapter_model.safetensors ]]; then
      echo "merging $ckpt -> $merged"
      python - "$ckpt" "$merged" <<'PY'
import sys
from unsloth import FastLanguageModel
import torch

model, tok = FastLanguageModel.from_pretrained(sys.argv[1], dtype=torch.bfloat16, load_in_4bit=False,
        max_seq_length=4096)
model.save_pretrained_merged(sys.argv[2], tok, save_method="merged_16bit")
PY
    fi
    run_passes "$merged" "$run" "$tag"
    [[ ${KEEP_MERGED:-0} == 1 ]] || rm -rf "$merged"
    echo "done: runs/$run.{jsonl,repeat.jsonl,predict.jsonl,predict_noacc.jsonl}, tag $tag" ;;
  base)  # prompted base model, the same passes as eval: THINKING=on|off, CASES=N for a stratified subset
    [[ -s $MODEL_FILE ]] || die "$MODEL_FILE missing, run bash farmshare.sh setup first"
    model_id=$(cat "$MODEL_FILE") run=base-think${THINKING:-off}
    [[ -n ${DATA:-} ]] && run=$(basename "${DATA%.jsonl}")-$run
    [[ ${CASES:-0} -gt 0 ]] && run=$run-c$CASES
    cd "$REPO"
    echo "job $SLURM_JOB_ID: $run ($model_id) on $(hostname), commit $(git rev-parse --short HEAD)"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
    # the local snapshot, so the job never needs the network
    model=$(python -c "import sys; from huggingface_hub import snapshot_download as s; print(s(sys.argv[1], \
local_files_only=True))" "$model_id")
    run_passes "$model" "$run" "$run-$model_id-mt$MAX_TOKENS"
    echo "done: runs/$run.{jsonl,repeat.jsonl,predict.jsonl,predict_noacc.jsonl}" ;;
  *) die "unknown command $cmd" ;;
esac
exit
}
