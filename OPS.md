# Operations

Compute, clusters, pipeline commands and the file map. Design decisions and results are in [DECISIONS.md](DECISIONS.md).

## Compute and clusters

### Compute

- Evaluation multiplies: 1,000 base cases, a 10-edit set, prediction call plus fresh call, is about 20,000 generations per checkpoint before repeats, and thinking tokens can dominate.
- Floor: 6 core SFT runs 12-24 GPU-hours, eval and debugging about 30, relabel round 5-10 (one seed), 47-64 hours before anything deferred.
- Options checked Nov 5 and 7: FarmShare (Stanford's free coursework cluster), Modal ($30 free per month, A100 about $2.50/h), RunPod Community A100 80 GB $1.19/h (H100 from $1.99/h), Vast A100 about $0.84/h with less reliable hosts, Colab Pro (A100 not guaranteed), a GCP quota request (often denied, 2 days to a week). Marlowe and Sherlock need a faculty PI, NSF ACCESS Explore needs an advisor letter, and Kaggle, Lightning free and the GitHub pack have no 40 GB GPU. GCP education credits ($50) have GPU quota 0.
- FarmShare, probed Nov 7: 6 GPU nodes with 4 L40S 48 GB each, 4 GPUs and 4 jobs per user, 2-day wall limit (normal partition 1 GPU per user, long QoS 7 days), CUDA 12.9 module, home 50 GB, scratch 81% full cluster-wide, 1-GPU jobs getting start estimates about 2 hours out. Decision: FarmShare is the primary GPU route, RunPod the fallback if the queue exceeds a day.
- Gemini prose and reference runs go through Vertex (ADC, location global, gemini-3.5-flash-lite), billed to the education credits. The AI Studio key is free tier (20 requests a day) and only serves smoke tests. Spend so far: data v1 about $9, the two pilots $2.25 (Results).

### Models and stack (verified Nov 4 and Nov 7)

- Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`, Vertex, thinking off, temperature 0) does 3 jobs: writes the case prose, is the external reference model, and is the frozen simulator behind simulatability gain.
  - Why: it was the cheapest Flash model on Vertex (v1 prose about $9, a full pilot about $1.50), billed to the education credits. Thinking off at temperature 0 gives fixed decoding, so every run is scored by the same simulator.
  - It is a different model family from Qwen, so the simulator cannot share the trained model's quirks, and it never sees the case text.
  - Picked as gen's default on cost, not tuned. Claude Opus 5.5 is the 2nd simulator family (Yu et al.), run through `--backend claude-cli`.

- Qwen3.5-9B (Apache-2.0, Feb 2026, bf16 LoRA about 22 GB, Unsloth advises against 4-bit for this family, thinking off via `enable_thinking: False`). Qwen's card gives mode-specific sampling, and we fix ours from the pilot. Unsloth's "keep 75% reasoning examples" is guidance for preserving thinking mode, and explanation lines are not reasoning traces.
- Qwen3.8-27B (dense, Aug 2026): deferred. Qwen3-8B and Qwen3.6-27B dropped as stale, not disqualified.
- Stack, verified on PyPI Nov 7: unsloth 2026.11.3 caps trl at 1.15.0 and transformers at 5.17.0, so the co-installable set is the one in `train.PINS` (newer trl and transformers do not install with unsloth). vllm 0.33.0 is built for CUDA 13, so on FarmShare it serves from its own venv (Nov 9). Unsloth's Qwen3.5 page: r 16, alpha 16, all 7 projections, bf16 LoRA, adamw_8bit, no 9B-specific recipe. TRL masks the prompt by default, and our per-token weights go through a custom collator. Compatibility is verified by a load, train, save, reload, evaluate smoke test before the runs.
- RL: Unsloth documents `fast_inference=False` for Qwen3.5 and 3.8, and a second GPU does not fix an unsupported integration.

### Training

The explanation condition's loss per example is mean_dec + λ mean_acc (mean token loss over the Decision line plus end-of-turn, plus λ times the mean over the explanation lines), averaged over the batch, so the decision tokens carry the same total weight in both conditions however long the explanation is. λ = `--acc-weight` (default 1.0), and the decision condition uses λ = 0 with the explanation labels set to -100.

- Stack (pinned in `train.PINS`, these co-install since unsloth caps trl at 1.15 and transformers at 5.17): `pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu126 && pip install unsloth==2026.11.3 trl==1.15.0 transformers==5.17.0 peft==0.21.2 vllm==0.33.0`. `train_meta.json` records the installed versions and whether they match the pins.
- Thinking: Qwen3.5-9B has thinking off by default per Unsloth's docs, and the chat template is still rendered with `enable_thinking=False` so training and inference prompts stay identical.
- Export (once, both conditions): `for s in train dev; do python train.py export --split $s --drop-flagged data/v1.flagged.txt --out data/v1.sft.$s.jsonl; done`
- Explanation SFT: `python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-acct-s0`. Decision-only SFT: the same with `--condition decision --out outputs/qwen9b-dec-s0`.
- In `<out>`: `checkpoint-<step>/` per epoch, `adapter/` (final LoRA adapter and tokenizer), `merged/` (16-bit model for vLLM) and `train_meta.json` (flags, λ, commit and dirty state, pinned and installed versions, GPU, token counts with the masked-token fraction, realized weight sums, training log).
- The tests check the masking and weights with the Qwen2.5-0.5B-Instruct tokenizer: the decision condition masks exactly the explanation tokens, decision tokens get identical weights summing to 1 per row in both conditions, explanation tokens sum to λ, λ = 0 reproduces the decision masking, and the trainer's loss equals mean_dec + λ mean_acc on random logits.

### FarmShare

Everything lives in `/scratch/users/$USER/accountable-ft` (purged after 90 idle days), model under `/scratch/users/$USER/hf`, `train_meta.json` copies in `~/accountable-ft-meta`. Log in with `ssh $USER@login.farmshare.stanford.edu` (Duo) or the Open OnDemand shell, inside `tmux new -s aft`. `smoke`, `train` and `eval` submit `cluster.sh` itself to Slurm, extra sbatch options go in `SB`.

- Pull the cluster checkout only when no pending job depends on a file the pull changes. A pending job runs the script as it is when it starts.
- Serving: `setup` builds `.venv-serve` with vllm alone, since PyPI vllm 0.33 is built for CUDA 13 and dies on the training venv's cu126 torch (libcudart.so.13). `eval` and `base` serve from it, `VLLM=<binary>` overrides.
- Setup, idempotent (about 40 GB of wheels and weights in scratch, rerun to update): `git clone https://github.com/sfjchen/accountable-ft /scratch/users/$USER/accountable-ft && cd /scratch/users/$USER/accountable-ft && bash cluster.sh setup`. It ends with the import, `train.PINS` and Collator checks.
- Probe: `bash cluster.sh probe | tee ~/probe.txt`. Need gpu MaxTime and qos MaxWall of at least 8 h, GPU memory of at least 40 GB. If gpu caps time, add `SB="--partition=normal --qos=long"` to the train command (only if normal shows gpu gres).
- Smoke (40 min): `bash cluster.sh smoke`, after it ends `CASES=13 bash cluster.sh eval smoke-account 1`. Logs in `runs/slurm/smoke_*.out` and `eval_*.out`.
- The 6-run array (explanation and decision, seeds 0-2, 8 h each): `jid=$(SB=--parsable bash cluster.sh train)`. One run: `SB=--array=4 bash cluster.sh train`. Watch with `squeue -u $USER` and `tail -f runs/slurm/${jid}_0.out`.
- Chunked runs (preferred): 8 h GPU jobs wait behind the queue, while 55-minute jobs fit the gaps Slurm backfills, so `train --chunks` splits each 2-epoch run into 2 1-epoch jobs. Chunk 1 runs `train.py --epochs 2 --stop-after-epochs 1`, chunk 2 runs `--epochs 2 --resume` with `--dependency=afterok:<chunk 1>` and continues the same seed, data order and LR (learning rate) schedule from the epoch-1 checkpoint, and only chunk 2 saves `adapter/` and `merged/`.
- A subset: `bash cluster.sh train --chunks --runs account-s1,decision-s0`. It prints run, partition and the 2 job ids, puts the first run on `--partition=normal --qos=normal` (1 GPU per user) and the rest on gpu, and skips runs whose `outputs/<run>/merged` exists. Logs in `runs/slurm/<run>_c<k>_<jobid>.out`, chunk boundaries in `train_meta.json` under `chunks`.
- For eval after chunked runs, use the chunk-2 id of each run as the `afterok` dependency.
- Eval every run at both epochs once training ends: `for r in {account,decision}-s{0,1,2}; do for k in 1 2; do SB=--dependency=afterok:$jid bash cluster.sh eval $r $k; done; done`. Eval runs are named `<cond>-e<k>-s<seed>`, the cache tag adds the adapter hash, each run has its own `runs/cache.<run>.jsonl`, and the merged model is deleted afterwards unless `KEEP_MERGED=1`. Eval and base jobs ask for 2 h (`TIME` overrides) so they backfill, and a timed-out one resumes from its cache when resubmitted. A timed-out train job restarts from scratch (no resume outside `--chunks`).
- Prompted base, the same 4 passes with no checkpoint: `bash cluster.sh base` (thinking off, full primary slice) and `THINKING=on CASES=150 bash cluster.sh base` (thinking answers run 5-10k tokens, so a subset). Runs are named `base-think<on|off>[-c<N>]`. `DATA=data/mortgage.jsonl SLICE=real_transfer bash cluster.sh base` runs the same passes on the mortgage domain (run name prefixed `mortgage-`). Every run served here uses `--max-tokens 16384` (`MAX_TOKENS`, model length `MAX_LEN` 24576), because evaluate.py refuses to compare runs whose max_tokens differ, so base and trained runs stay comparable. Earlier API pilots used 4096.
- Back on the Mac: `rsync -av --exclude slurm $USER@login.farmshare.stanford.edu:/scratch/users/$USER/accountable-ft/runs/ runs/`, then the simulate and score commands under Pipeline commands on `data/v1.jsonl`, e.g. `python evaluate.py runs/*-e2-s*.jsonl --data data/v1.jsonl --bank data/v1.bank.jsonl --epoch 2`.

#### FarmShare run history

- Training (L40S 48 GB, `cluster.sh`): all 6 runs finished by Nov 9, about 81 minutes each (jobs 1951241_0 and 1957278_[1-5]). Run account-s0: 692 steps, train loss 0.074, dev loss 0.048.
  - The first 2 eval jobs (1957283, 1957284) died at vllm startup on libcudart.so.13, fixed with `.venv-serve` (FarmShare).
  - Nov 9 the first serve jobs (base 1967638 and 1967639, smoke 1967678) died in vllm startup: flashinfer's sampling kernel was JIT-built with the module's CUDA 12.9 nvcc and could not load next to the serving venv's CUDA 13 runtime. Greedy decoding never needs it, so serving now samples in PyTorch (`VLLM_USE_FLASHINFER_SAMPLER=0`). Every queued eval was cancelled and resubmitted.
  - Queued Nov 10, all on the gpu partition: smoke 1967803 (13 cases), r2 training array 1967804 (6 runs), mo array 1967805 (explanation and decision, seed 0), base on both files 1967806, round 1 epoch 2 on both files and epoch 1 on v1 1967807-1967818, r2 evals 1967819-1967824, mo evals 1967825-1967826. Every eval waits on the smoke job and its own training, so a broken serve path costs 1 short job. Submit log: `runs/slurm/submit-r2.txt` on the cluster.
  - One eval job serves 1 model and runs every data file in `DATA`, which halves the merges, vllm startups and queue waits.
  - Partition choice: the gpu partition caps a user at 32 queued and 4 running jobs. The normal partition shares the same 6 GPU nodes at PriorityTier 1 (gpu has 5), so a GPU job there only gets a GPU the gpu queue leaves idle. Consolidated, the whole plan is 30 jobs, under the cap.
  - Fallback if the queue does not clear by Nov 11: RunPod A100 at $1.19/h.

### sc cluster

Used from Nov 12 for the row-matched grid, through Cyrus's account. `cluster.sh` detects sc from `/juice2/scr2/nlp/cs224v` and keeps everything in `/juice2/scr2/nlp/cs224v/jchen04-aft` (repo, venvs, model, uv, run metadata).

- Jobs run on `--partition=sc-loprio --account=nlp`, 1 GPU of at least 48 GB each, at most 2 at once. `MAIL` must be set, since the account is shared.
- Setup runs as a CPU job (8 CPUs, 32 GB, 3 h): `MAIL=<address> bash cluster.sh setup`. It also exports the 3 grid mixes.
- Grid: `MAIL=<address> bash cluster.sh grid`, array 0-17 with `%2`. Each task trains `outputs/rm-<mix>-<cond>-s<seed>`, deletes the merged model, then answers v1, mortgage-split, SNAP and dependent (answer pass only). A requeued task skips a finished adapter and resumes from its last checkpoint.
- Simulator passes and scoring run on the Mac after `rsync` through the data transfer node.
- Grid runs, Nov 12.
  - 1st queue at 00227d7: setup 18470254 (done, 18 min), smoke 18470266, grid array 18470267 (after smoke), 1 mail when the grid ends (18470268).
  - Smoke 18470266 trained fine (eval loss 0.34) but hit its 15-min limit while merging: loading the model and merging each of 4 shards take about 3 and 1 min on sc's network disk. The grid and its mail never ran. Smoke now gets 40 min.
  - Requeued at 83b512c: smoke 18475000 (done, 16 min), grid array 18475001 (after smoke), mail 18475002.
  - Task 1 (rm-inv-account-s1, RTX A6000) finished in 2 h 11 min: training, then answers on v1 (1,944 rows, 453 s), mortgage-split (687, 198 s), SNAP (915, 268 s) and dependent (747, 205 s).
  - Task 0 failed at vllm startup on viscam5: node /tmp was full ("No space left on device"), so triton's gcc build died. Task 2 sat on the same node. Fix at 4794e06: `TMPDIR` on scratch for every sc job.
  - Slurm runs the script as copied at submit, so the pending tasks could not pick up the fix. Array 18475001 was cancelled and resubmitted as 18477875 (tasks 0 and 2-17, `%2`), mail 18477878. Task 0 skips its finished adapter, task 2 resumes from its epoch-1 checkpoint.
  - Nov 12, 13:00: split the grid for speed. sc keeps tasks 0 and 2-9 (array 18478220, resubmitted so it picks up the merge fix, throttled to 1 until task 0 ends by job 18478224, so the account never runs more than 2). FarmShare runs tasks 10-17 as `train --chunks` (55-min jobs that backfill) plus `eval ... 2` with `REUSE_MERGED=1`, jobs 1977618-1977641, mail 1977642. Same torch 2.14, unsloth 2026.11.3, trl 1.15.0, transformers 5.17.0, vllm 0.33.0 on both, and all 12 data and edit-set files sha256-identical.
  - Nov 13: FarmShare ran 4 of 16 chunks in 19 h (queue-bound), sc finished tasks 2-9 overnight. FarmShare's pending jobs were cancelled and tasks 10-17 resubmitted on sc as array 18493080 (`%2`). Fill array 18493125 (`PASSES=all`, after 18493080) adds the repeat and self-prediction passes the grid skipped, reusing each finished adapter and the cached answers. Cancelling jobs whose mail type is FAIL sends 1 mail each, so set `scontrol update job=<id> MailType=NONE` first.
  - Merge fix (732c4d7): each grid run merged twice, about 9 min in train.py and again in eval. Eval now serves train.py's merge of the final weights (`REUSE_MERGED=1`), and train.py writes it as `merged.part` and renames it when complete, so a killed job never leaves a partial model.
  - Nov 15: extended test files. 13 of the review-x and dependent-x grid tasks (18517685) failed after a 10-min merge because the files were never copied to sc, 2 fill tasks hit uncorrectable ECC errors on viscam13, and the failed jobs left 16 merged models (18 GB each). Requeued as one serial chain: 18527731 (failed grid tasks), base 18517686, fill 18527732 (tasks 2, 17), then the grant, trial, SNAP and mortgage extension 18523802, all excluding viscam13.
- Run safeguards (Nov 15, 8cf026f), since every failure so far was found hours late at the end of a chain:
  - `cluster.sh` refuses to submit when a DATA file or its edit set is missing, differs from its committed `.gz` or origin/main, or the code differs from origin/main (`STALE_OK=1` overrides). Each job checks its inputs again before merging, and deletes its own merged model on any exit.
  - Mac jobs run under `ljob <label> <cmd>` (`~/dev/scripts`): a LaunchAgent with no relaunch, an appended log, a `.done` or `.failed` marker and a notification. `launchctl submit` relaunched a failing generation for 10 h.
  - The sc watcher (`~/dev/logs/sc-x.sh`) reports each failed, timed-out or cancelled task when its 25-min poll sees it, and checks that every expected answer file arrived before starting the simulator. `sim-grid.sh` fails at once on a missing file.
  - New code paths get a test or a dry run on existing data before a long job depends on them (`test_extend_from`, the pooled scoring path on dependent + mortgage).

## Pipeline commands

- Generate: `gen.py` samples policies and cases per domain, the engine labels them, Gemini writes the prose, an extraction check drops prose that distorts a fact.
- Export: `python train.py export` turns cases into chat examples with the explanation span marked, flagged items dropped.
- Train: `train.py`, LoRA on Qwen3.5-9B, condition `account` (explanation) or `decision`, 3 seeds each, same fixed epoch for both.
- Answer: `infer.py` runs the trained model on held-out cases and on the edit set.
- Edit set: 782 edits built by the engine, 40% flip a decision, 30% should not, 15% remove a fact, 15% reveal a missing one. Flip edits differ from the correct "smallest change" so the model cannot have memorized them.
- Simulate and evaluate: `infer.py --mode simulate`, then `evaluate.py` produces the table with CIs.

Commands, from the repo root. Once per shell: `export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH` (ADC for Vertex) and `F=(--backend gemini --vertex --model gemini-3.5-flash-lite --temperature 0)` (a zsh array, so `$F` splits into flags). The examples use the smoke data, swap in `data/v1.jsonl` for real runs.

- Bank, once per data file: `python infer.py --mode bank --data data/smoke.jsonl` writes `data/smoke.bank.jsonl` and its meta (mix, sources, drops) on the primary population (slice unseen_family_train_vocab, view prose).
- Answer run, always with `--bank` so the edit set's edited cases get fresh decisions: `python infer.py --data data/smoke.jsonl --bank data/smoke.bank.jsonl $F --slice unseen_family_train_vocab --view prose --out runs/pilot.jsonl` (`--cases 13` for a stratified subset).
- Repeat control: the same command with `--rep 1 --out runs/pilot.repeat.jsonl`.
- Simulator, all 3 passes on the frozen run: `python infer.py --mode simulate --all-sim --data data/smoke.jsonl --bank data/smoke.bank.jsonl --frozen runs/pilot.jsonl $F` writes `runs/pilot.simulate.jsonl` (own explanation), `.simulate_shuf.jsonl` (own Decision line, another case's explanation lines under the same policy, items without a partner skipped and counted in `shuf_missing`) and `.simulate_noacc.jsonl` (decision only). The simulator and its decoding stay fixed across every run compared.
- Self-prediction (secondary): `--mode predict --frozen runs/pilot.jsonl` with the model under test into `runs/pilot.predict.jsonl`, and with `--no-account` into `runs/pilot.predict_noacc.jsonl`.
- Score: `python evaluate.py runs/pilot.jsonl --data data/smoke.jsonl --bank data/smoke.bank.jsonl --json runs/pilot.eval.json`. It prints the CORE metrics (`--full` for all), and the JSON holds every metric and the commit it ran on.
- Checkpoints: `--epoch K` takes every condition and seed at the same fixed epoch K, fixed before any explanation metric is read. `--select-by sim_delta --select-control <ctrl-run>` adds a best-of-k table labelled EXPLORATORY, never the reported pick. Runs named `<cond>-e<k>[-s<seed>]` get per-seed columns and a seed aggregate.
- Local checkpoints: pass `--cache-tag` with the run name, since the model path can point at new weights and the cache would return old answers.
- Files: each run writes `<run>.jsonl` and `<run>.meta.json` (tokens, wall time, cost). evaluate reads the companions above, scores sim metrics on the edit-set items all 3 simulate files share, next to `sim_const_unchanged` and `sim_oracle`, and refuses mixed decoding, an old shuf file (no `shuf_src` "frozen") or a edit-set item without a fresh decision. `runs/cache.jsonl` holds every response, so reruns are free.

## Files

- `engine.py`: rule engine. Decide, minimal sufficient sets (exact, over possible completions), minimal flips up to radius 4, reveals, invariant edits, `is_valid_justification`.
- `gen.py`: generator. Template families, policies, base cases and flip, invariant, missing and reveal variants in 3 views (table, prose, prose_derive), optional Gemini prose. `--report` writes the stats and blind sample, `--audit` the "cannot determine" audit. `render_case()` re-renders edited cases.
- `domains/*.yaml`: the 4 domains (facts, derived facts, rule templates, defaults, prose vocabulary), plus `mortgage.yaml`, the real-rules domain outside `--domains all`, with its sources in `mortgage.md`.
- `infer.py`: one `Runner` over OpenAI-compatible endpoints (vLLM serve, OpenRouter), Gemini, offline vLLM and Claude Code headless (`claude-cli`, on a signed-in subscription), with fixed decoding, a response cache, `--rep` for the repeat control, and the `bank` (edit set), predict and simulate modes.
- `evaluate.py`: all metrics with cluster bootstrap CIs, slices (primary: prose, unseen families, training vocabularies), paired comparisons, seed aggregates, coverage, checkpoint selection, `--power`.
- `compare_sims.py`: 2 simulators on the same runs, item agreement and accuracy split by whether the model's post-edit decision is correct.
- `train.py`: LoRA SFT with the matched loss, and `train.py export` for the SFT rows.
- `cluster.sh`: setup and Slurm jobs on FarmShare or the NLP sc cluster: train (chunked or whole), eval, prompted base (`base`), the row-matched grid (`grid`).
- `runs/`: every run with its companions and eval tables (`runs/sim-opus/`: the same runs linked in, with Opus simulator passes), `data/`: datasets, banks, blind samples and stats.
- `tests/test_all.py`, `tests/mini.jsonl`: engine against brute force and the acceptance cases, the generator, the parser and every metric on a 12-record hand-made fixture, bank, prompts, cache key, shuffled control, export, masking and loss weights. Run `python -m pytest -q`.
