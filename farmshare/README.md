# FarmShare runs

Train the 6 core SFT runs (PLAN.md 3.5) and their answer and predict passes on FarmShare. Simulate and score from the
Mac. Everything lives in `/scratch/users/$USER/accountable-ft` (purged after 90 idle days), train_meta.json copies
go to `~/accountable-ft-meta`. Set `S=<sunet>` in the Mac shell first.

1. Mac, copy the git-ignored data (1 Duo prompt):
   `rsync -av --rsync-path="mkdir -p /scratch/users/$S/aft-data && rsync" data/v1.jsonl data/v1.bank.jsonl
   $S@login.farmshare.stanford.edu:/scratch/users/$S/aft-data/`
2. Log in and start tmux: `ssh $S@login.farmshare.stanford.edu`, `tmux new -s aft`
3. Clone and set up (idempotent, about 40 GB of wheels and weights in scratch):
   `git clone https://github.com/sfjchen/accountable-ft /scratch/users/$USER/accountable-ft`
   `DATA_SRC=/scratch/users/$USER/aft-data bash /scratch/users/$USER/accountable-ft/farmshare/setup.sh`
   It ends with the import, PINS and Collator checks. Later updates: rerun the same command.
4. `cd /scratch/users/$USER/accountable-ft && bash farmshare/probe.sh | tee ~/probe.txt`
   Check: gpu MaxTime and qos MaxWall at least 8 h, GPU memory at least 40 GB, GPUs per user.
   If gpu caps time: `sbatch --partition=normal --qos=long farmshare/train.sbatch` in step 6 (only if normal
   shows gpu gres), or lower `--time` and pass fewer `--epochs` in train.sbatch.
5. Smoke (15 min, then a small eval): `sbatch farmshare/smoke.sbatch`, after it ends
   `CASES=13 sbatch farmshare/eval.sbatch smoke-account 1`. Read `runs/slurm/smoke_*.out` and `eval_*.out`.
6. Train: `jid=$(sbatch --parsable farmshare/train.sbatch)`. Watch: `squeue -u $USER`,
   `tail -f runs/slurm/${jid}_0.out`.
7. Eval every run at both epochs once training ends:
   `for r in {account,decision}-s{0,1,2}; do for k in 1 2; do sbatch --dependency=afterok:$jid farmshare/eval.sbatch
   $r $k; done; done`
8. Mac, copy results back:
   `rsync -av --exclude slurm $S@login.farmshare.stanford.edu:/scratch/users/$S/accountable-ft/runs/ runs/`
9. Mac, simulate and score per runs/README.md, e.g. for `account-e2-s0`:
   `python infer.py --mode simulate --all-sim --data data/v1.jsonl --bank data/v1.bank.jsonl
   --frozen runs/account-e2-s0.jsonl $F`, then `python evaluate.py runs/*-e2-s*.jsonl --data data/v1.jsonl
   --bank data/v1.bank.jsonl --epoch 2`

Notes: eval run names are `<cond>-e<k>-s<seed>` so `evaluate.py --epoch` and the seed aggregates parse them. The
cache tag adds the adapter hash and each run has its own `runs/cache.<run>.jsonl`. eval.sbatch deletes the merged
model after the run unless `KEEP_MERGED=1`. A timed-out train run restarts from scratch (train.py has no resume).
