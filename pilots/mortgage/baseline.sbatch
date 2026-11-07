#!/bin/bash
# Mortgage pilot: Qwen3.5-9B on the 3 cases in cases.jsonl, thinking off and on, 1 GPU on FarmShare.
# Submit from the repo root on FarmShare:  sbatch pilots/mortgage/baseline.sbatch [model]
# Needs a venv with vllm 0.33.0 at $VENV (default /scratch/users/$USER/envs/vllm) and the model in $HF_HOME.
#SBATCH --job-name=mortgage-pilot
#SBATCH --partition=gpu
#SBATCH --qos=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=runs/slurm/mortgage-pilot-%j.out

set -euo pipefail
S=/scratch/users/$USER
MODEL=${1:-Qwen/Qwen3.5-9B}
VENV=${VENV:-$S/envs/vllm}
export HF_HOME=${HF_HOME:-$S/hf} HF_HUB_OFFLINE=1 VLLM_CACHE_ROOT=$S/cache/vllm
# FarmShare has no CUDA compiler on the PATH by default, so FlashInfer can't build its sampling kernels.
# Use vLLM's own sampler instead.
export VLLM_USE_FLASHINFER_SAMPLER=0

nvidia-smi --query-gpu=name,memory.total --format=csv
D=pilots/mortgage
"$VENV/bin/python" $D/run_vllm_batch.py \
  --model "$MODEL" \
  --template $D/prompt.txt \
  --cases $D/cases.jsonl \
  --out $D/out/baseline-$(basename "$MODEL")-$(date +%Y%m%d-%H%M).jsonl
