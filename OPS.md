# Operations

Stack, clusters, commands and the file map. Design and results in [DECISIONS.md](DECISIONS.md). Run histories and probe notes are in git history before this file was slimmed (52ebc2f).

## Stack

- Trained model: Qwen3.5-9B, bf16 LoRA (r 16, alpha 32, all 7 projections), thinking off (`enable_thinking=False` in training and inference).
- Pins in `train.PINS` (unsloth 2026.11.3 caps trl and transformers): `pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu126 && pip install unsloth==2026.11.3 trl==1.15.0 transformers==5.17.0 peft==0.21.2 vllm==0.33.0`. vllm serves from its own venv (`.venv-serve`), since its CUDA 13 build dies on the training venv's cu126 torch.
- Simulators: Gemini 3.5 Flash-Lite on Vertex (ADC, thinking off, temperature 0), also the prose writer. Claude Opus 5.5 through Claude Code headless (`--backend claude-cli`).
- Loss: mean_dec + λ mean_acc per example (`--acc-weight`, default 1). Decision-only uses λ = 0 with explanation labels at -100. `train_meta.json` in each output records flags, commit, versions, GPU and token counts.
- Every served run uses `--max-tokens 16384`, since `evaluate.py` refuses to compare runs with different decoding.

## Clusters

- FarmShare (round 1, round 2, permit, prompted controls): repo in `/scratch/users/$USER/accountable-ft`, 4 L40S per user. `bash cluster.sh setup`, then `smoke`, `train --chunks` (1-epoch jobs that backfill), `eval <run> <epoch>`, `base`.
- sc (the grid): repo in `/juice2/scr2/nlp/cs224v/jchen04-aft`, `--partition=sc-loprio --account=nlp`, at most 2 jobs, `MAIL` required (shared account). `MAIL=<address> bash cluster.sh grid` runs array 0-17: train `outputs/rm-<mix>-<cond>-s<seed>`, then answer every test file. Requeued tasks skip finished adapters and resume from the last checkpoint.
- Safeguards: `cluster.sh` refuses to submit when a data file or edit set differs from its committed `.gz` or the code differs from origin/main (`STALE_OK=1` overrides). Each job deletes its merged model on exit, and every sc job puts `TMPDIR` on scratch.
- Simulator passes and scoring run on the Mac after `rsync`. Long Mac jobs run under `ljob` (`~/dev/scripts`).

## Commands

From the repo root. Once per shell: `export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH` and `F=(--backend gemini --vertex --model gemini-3.5-flash-lite --temperature 0)`.

1. Data: `gunzip -k data/*.jsonl.gz runs/cache*.jsonl.gz`, or regenerate with `python gen.py --domains all --n-policies 120 --cases-per-family 5 --seed 0 --prose gemini --vertex --gemini-model gemini-3.5-flash-lite --workers 8 --out data/v1.jsonl` (`--domains snap`, `dependent` or `mortgage` for the real ones). Gemini replies are cached in `data/.gemini_cache/` (tarball on the `data-v1` release).
2. Edit set, once per data file: `python infer.py --mode bank --data data/v1.jsonl`.
3. SFT rows: `for s in train dev; do python train.py export --split $s --drop-flagged data/v1.flagged.txt --out data/v1.sft.$s.jsonl; done`.
4. Train: `python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-acct-s0`, the same with `--condition decision`. On a cluster, `cluster.sh train` or `grid`.
5. Answer: `python infer.py --data data/v1.jsonl --bank data/v1.bank.jsonl <backend flags> --slice unseen_family_train_vocab --view prose --out runs/<run>.jsonl`, with `--cache-tag <run>` for a local checkpoint.
6. Simulate, all 3 passes on a frozen run: `python infer.py --mode simulate --all-sim --data data/v1.jsonl --bank data/v1.bank.jsonl --frozen runs/<run>.jsonl $F`. Wrong-reason: `--wrong-accounts`. Opus: `--backend claude-cli --model claude-opus-5-5`, outputs in `runs/sim-opus/`. Many runs: `TAG=<name> PAT='<run regex>' FILES='<files>' CONC=32 bash sim.sh gemini`.
7. Score: `python evaluate.py runs/*-e2-s*.jsonl --data data/v1.jsonl --bank data/v1.bank.jsonl --epoch 2 --compare decision`. Mix contrasts: `--contrast rm-mix rm-real rm-inv` (prefix `<file>-` on other files). `--full` prints every metric, `--power` the power table.
8. Every eval the report cites: `bash score.sh list`, then `bash score.sh all` (or `run <i>` per Slurm array task) from a clean checkout with `stamp-run` on PATH.

## Adding a domain

- Copy `domains/grant.yaml`: `facts` (ints bucketed to at most 8 values, at most 12 facts per policy), `derived_facts`, `rules` (`cond`, optional `unless`, `scoped` with `near`, `params`), `defaults` and prose `say` strings. The generator rejects families where a rule cannot hold and fail.
- A held-out domain also needs entries in `gen.HELD_OUT` and `gen.SLICE`, and `required` lists rules every policy must have. Then steps 1-7 above with `--domains <name>`.

## Files

- `engine.py`: rule engine (decide, minimal sufficient sets, minimal flips, reveals, `is_valid_justification`).
- `gen.py`: policies, cases, edited variants in 3 views, Gemini prose, `--report` stats and blind sample, `--audit` of "cannot determine" items.
- `domains/*.yaml`: domains. `*.md` beside a real domain lists its sources.
- `infer.py`: model runner (vLLM, OpenAI-compatible, Gemini, Claude Code headless), response cache, edit set, answer, predict, simulate and explain modes, wrong-reason control.
- `evaluate.py`: every metric with clustered bootstrap CIs, paired comparisons, mix contrasts with Holm, power. JSON names its commit.
- `compare_sims.py`: 2 simulators on the same runs. `errors.py`: error-analysis sample and tally.
- `train.py`: LoRA SFT with the matched loss, `train.py export` for SFT rows.
- `cluster.sh`, `score.sh`, `sim.sh`: Slurm jobs, the cited evals, simulator passes over many runs.
- `runs/`: run outputs (`runs/sim-opus/` links the same runs with Opus passes). `data/`: datasets (`.gz` committed), edit sets, stats, blind samples.
- `tests/test_all.py`: engine against brute force, generator, parser, every metric on a hand-made fixture, export, masking and loss weights. Run `.venv/bin/python -m pytest -q` with `uv venv .venv && uv pip install -p .venv -r requirements.txt numpy torch==2.14.0 transformers==5.17.0 accelerate==1.15.0`.
