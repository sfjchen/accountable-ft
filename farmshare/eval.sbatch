#!/usr/bin/env bash
#SBATCH --job-name=aft-eval
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/scratch/users/%u/accountable-ft/runs/slurm/eval_%j.out
# farmshare/eval.sbatch: evaluates the epoch-k checkpoint of outputs/<name>/ with the runs/README.md pipeline.
# Merges the LoRA checkpoint to 16-bit, serves it with vllm inside the job, then runs answer (with --bank), the
# --rep 1 repeat and predict with and without the account. The Gemini simulate step runs later from the Mac.
# Run name follows evaluate.select_ckpt: <cond>-e<k>-s<seed> (smoke-<cond>-e<k> for smoke runs).
# Usage: [CASES=13] [KEEP_MERGED=1] sbatch farmshare/eval.sbatch <cond>-s<seed> <epoch>
set -euo pipefail
# shellcheck source=farmshare/env.sh
source "${SCRATCH:-/scratch/users/$USER}/accountable-ft/farmshare/env.sh"
name=${1:?usage: sbatch farmshare/eval.sbatch <cond>-s<seed> <epoch>} ep=${2:?missing epoch}
out=$REPO/outputs/$name
[[ -f $out/train_meta.json ]] || die "$out has no train_meta.json, train it first"
if [[ $name =~ ^(.*)-s([0-9]+)$ ]]; then
  run=${BASH_REMATCH[1]}-e$ep-s${BASH_REMATCH[2]}
else
  run=$name-e$ep
fi
cd "$REPO"
echo "job $SLURM_JOB_ID: $run on $(hostname), commit $(git rev-parse --short HEAD)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

# the checkpoint whose trainer_state.json epoch rounds to ep
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
# the cache tag carries the adapter hash, so retrained weights under the same name never hit old cached answers
tag=$run-$(sha256sum "$ckpt/adapter_model.safetensors" | cut -c1-12)
merged=$out/merged-e$ep
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

# a job-specific port, since several 1-GPU jobs can share a node
port=$((8000 + SLURM_JOB_ID % 1000))
vlog=$REPO/runs/slurm/vllm_$SLURM_JOB_ID.log
vllm serve "$merged" --served-model-name "$run" --host 127.0.0.1 --port "$port" --dtype bfloat16 \
    --max-model-len 8192 --gpu-memory-utilization 0.9 --seed 0 > "$vlog" 2>&1 &
vpid=$!
trap 'kill "$vpid" 2>/dev/null || true' EXIT
for _ in $(seq 240); do
  curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null && break
  kill -0 "$vpid" 2>/dev/null || die "vllm exited, see $vlog"
  sleep 5
done
curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null || die "vllm not up after 20 min, see $vlog"

S=(--data data/v1.jsonl --bank data/v1.bank.jsonl --slice unseen_family_train_vocab --view prose)
[[ ${CASES:-0} -gt 0 ]] && S+=(--cases "$CASES")
B=(--backend openai --base-url "http://127.0.0.1:$port/v1" --model "$run" --cache-tag "$tag"
  --cache "runs/cache.$run.jsonl" --conc 32)
python infer.py "${S[@]}" "${B[@]}" --out "runs/$run.jsonl"
python infer.py "${S[@]}" "${B[@]}" --rep 1 --out "runs/$run.repeat.jsonl"
python infer.py --mode predict "${S[@]}" "${B[@]}" --frozen "runs/$run.jsonl" --out "runs/$run.predict.jsonl"
python infer.py --mode predict "${S[@]}" "${B[@]}" --frozen "runs/$run.jsonl" --no-account \
    --out "runs/$run.predict_noacc.jsonl"
[[ ${KEEP_MERGED:-0} == 1 ]] || rm -rf "$merged"
echo "done: runs/$run.{jsonl,repeat.jsonl,predict.jsonl,predict_noacc.jsonl}, tag $tag"
