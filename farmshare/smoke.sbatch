#!/usr/bin/env bash
#SBATCH --job-name=aft-smoke
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --output=/scratch/users/%u/accountable-ft/runs/slurm/smoke_%j.out
# farmshare/smoke.sbatch: 15-minute load, train, save, merge check of the stack on 64 train and 16 dev rows, 1 epoch
# (16 optimizer steps). train.py has no --max-steps flag, so the subset bounds the steps.
# Usage: sbatch farmshare/smoke.sbatch [account|decision]   -> outputs/smoke-<cond>/
set -euo pipefail
# shellcheck source=farmshare/env.sh
source "${SCRATCH:-/scratch/users/$USER}/accountable-ft/farmshare/env.sh"
cond=${1:-account}
out=$REPO/outputs/smoke-$cond
mkdir -p "$out"
head -n 64 "$REPO/data/v1.sft.train.jsonl" > "$out/train.jsonl"
head -n 16 "$REPO/data/v1.sft.dev.jsonl" > "$out/dev.jsonl"
train_one "$cond" 0 "$out" "$out/train.jsonl" "$out/dev.jsonl" --epochs 1 --grad-accum 1
