# farmshare/env.sh: shared paths, caches and helpers, sourced by setup.sh and the sbatch scripts.
# Keeps every cache in scratch (home is 50 GB) and activates the venv when it exists.
SCRATCH=${SCRATCH:-/scratch/users/$USER}
REPO=$SCRATCH/accountable-ft
VENV=$REPO/.venv
MODEL_FILE=$REPO/outputs/model_id
META_HOME=$HOME/accountable-ft-meta
export SCRATCH REPO VENV MODEL_FILE META_HOME
export HF_HOME=$SCRATCH/hf UV_CACHE_DIR=$SCRATCH/.uv/cache UV_PYTHON_INSTALL_DIR=$SCRATCH/.uv/python
export XDG_CACHE_HOME=$SCRATCH/.cache TRITON_CACHE_DIR=$SCRATCH/.cache/triton VLLM_CACHE_ROOT=$SCRATCH/.cache/vllm
export PATH=$HOME/.local/bin:$PATH

set +u  # Lmod's scripts read unset variables
# Lmod is a shell function, missing in non-login shells until its profile script runs
if ! type module &>/dev/null && [[ -f /etc/profile.d/lmod.sh ]]; then
  # shellcheck disable=SC1091
  source /etc/profile.d/lmod.sh
fi
# CUDA toolkit for JIT kernels (triton, flashinfer); torch wheels bring their own runtime. Module name verified on FarmShare Nov 7.
if type module &>/dev/null; then
  module load cuda/12.9.0 &>/dev/null || true
fi
set -u
if [[ -f $VENV/bin/activate ]]; then
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
fi

# Prints a message to stderr and exits.
die() {
  echo "error: $*" >&2
  exit 1
}

# Trains one run and copies its train_meta.json to home.
# Usage: train_one <condition> <seed> <out dir> <train jsonl> <dev jsonl> [extra train.py flags]
train_one() {
  local cond=$1 seed=$2 out=$3 tr=$4 dv=$5
  shift 5
  [[ -s $MODEL_FILE ]] || die "$MODEL_FILE missing, run farmshare/setup.sh first"
  cd "$REPO" || return
  echo "job ${SLURM_JOB_ID:-local} $cond s$seed on $(hostname), commit $(git rev-parse --short HEAD), out $out"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
  python train.py --condition "$cond" --data "$tr" --eval-data "$dv" --seed "$seed" --model "$(cat "$MODEL_FILE")" \
      --out "$out" "$@"
  mkdir -p "$META_HOME"
  cp "$out/train_meta.json" "$META_HOME/$(basename "$out").train_meta.json"
  echo "done: $out, meta in $META_HOME"
}
