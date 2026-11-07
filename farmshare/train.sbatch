#!/usr/bin/env bash
#SBATCH --job-name=aft-train
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --array=0-5
#SBATCH --output=/scratch/users/%u/accountable-ft/runs/slurm/%A_%a.out
# farmshare/train.sbatch: the 6 core SFT runs of PLAN.md 3.5, array index i -> condition (0-2 account,
# 3-5 decision) and seed i % 3, into outputs/<cond>-s<seed>/ with a checkpoint each epoch (train.py saves per epoch).
# Usage: sbatch farmshare/train.sbatch   (one run: sbatch --array=4 farmshare/train.sbatch)
# If the gpu partition caps time below 8 h (probe.sh: MaxTime, qos MaxWall), override on the command line:
#   sbatch --partition=normal --qos=long farmshare/train.sbatch   (only if normal lists gpu gres in probe.sh)
set -euo pipefail
# shellcheck source=farmshare/env.sh
source "${SCRATCH:-/scratch/users/$USER}/accountable-ft/farmshare/env.sh"
i=${SLURM_ARRAY_TASK_ID:?submit as an array job}
conds=(account decision)
cond=${conds[i / 3]} seed=$((i % 3))
train_one "$cond" "$seed" "$REPO/outputs/$cond-s$seed" data/v1.sft.train.jsonl data/v1.sft.dev.jsonl
