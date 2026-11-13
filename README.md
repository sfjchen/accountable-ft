# accountable-ft

Jon Chen and Eitan Green, CS 224V fall 2026. Design decisions, every run's history and the technical reference are in [DECISIONS.md](DECISIONS.md).

Can fine-tuning make a model's stated reasons track its decisions? We train Qwen3.5-9B on rule-based eligibility cases (invented policies with exact labels from a rule engine, plus real mortgage, SNAP and IRS dependent rules). Explanation SFT (supervised fine-tuning) learns the decision and an engine-verified explanation. The matched control, decision-only SFT, sees the same rows with the explanation tokens masked out of the loss. The main score is simulatability gain: how much better a frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd) predicts the model's answer after an edit when it sees the model's own explanation rather than another case's. The simulator never sees the case.

## Results so far

Paired simulatability gain, explanation SFT minus decision-only, seed by seed, 95% CI clustered by rule family. v1 = unseen families of the invented domains, mortgage = 24 held-out mortgage families. Logs `final-v1-gemini-eval-053d9ef-20261112-0351`, `final-mortgage-gemini-eval-053d9ef-20261112-0351`, `final-v1-opus-eval-053d9ef-20261112-0353`, `final-mortgage-opus-eval-053d9ef-20261112-0353`.

| training mix | v1, Gemini | mortgage, Gemini | v1, Opus | mortgage, Opus | accuracy, v1 |
|---|---|---|---|---|---|
| round 1: grant, trial, review | 0.081 [0.043, 0.123] | 0.038 [-0.018, 0.094] | 0.161 [0.129, 0.195] | 0.091 [0.048, 0.137] | 0.004 [-0.008, 0.016] |
| round 2: grant, trial, mortgage | 0.041 [0.007, 0.078] | 0.094 [0.036, 0.151] | 0.120 [0.086, 0.151] | 0.170 [0.129, 0.211] | 0.033 [0.020, 0.049] |
| mortgage only, seed 0 | -0.005 [-0.044, 0.036] | 0.066 [-0.018, 0.150] | 0.009 [-0.038, 0.056] | 0.024 [-0.036, 0.083] | 0.006 [-0.018, 0.031] |

- Explanation SFT matches or beats decision-only on accuracy in every mix and is the only condition with valid explanations (0.756 vs 0.000 on v1, round 1).
- Each kind of training row helps most on tests like it. The row-matched grid below separates mix from size.

## Status (Nov 13)

- Row-matched grid: 3 mixes (`rm-inv` grant + trial, `rm-real` mortgage + SNAP, `rm-mix` all 4) at 3,600 train rows x 2 conditions x 3 seeds = 18 runs. Tests: unseen families of the 4 training domains, review and IRS dependent (both held out from every mix). Pre-registration in DECISIONS.md.
  - 10 runs done on sc (tasks 0-9). Tasks 10-17 moved from FarmShare's stalled queue to sc, array 18493080. Fill array 18493125 then adds the repeat and self-prediction passes to all 18.
  - Gemini and Opus simulator passes run on the Mac (`~/dev/logs/sim-grid.sh`), then scoring with the 3 contrasts per test file.
- On FarmShare: permit transfer for round 1 (`data/permit.jsonl`) and the prompted-explanation control (`--mode explain`, runs `pe-*`).
- New metric: simulatability gain on hard edits, `sim_delta[hard]`.

## Files

- `engine.py`: rule engine (decisions, minimal sufficient sets, minimal flips, explanation checks).
- `gen.py`: case generator, 3 views, optional Gemini prose, stats and audits.
- `domains/*.yaml`: policy domains. `*.md` beside a real domain lists its sources.
- `infer.py`: model runner (vLLM, Gemini, Claude Code headless), edit-set bank, predict and simulate modes, response cache.
- `evaluate.py`: every metric with clustered bootstrap CIs, paired comparisons, mix contrasts, power.
- `compare_sims.py`: 2 simulators on the same runs.
- `train.py`: LoRA SFT with the matched loss, `train.py export` for SFT rows.
- `cluster.sh`: setup and Slurm jobs on FarmShare or sc (smoke, train, eval, base, grid, notify).
- `runs/`: run outputs and eval tables. `data/`: datasets (`.gz` committed), edit sets, stats, blind samples.
- `tests/test_all.py`: engine, generator, metrics, export and loss tests. `python -m pytest -q`.

## Reproduce

From the repo root. Once per shell: `export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH` (ADC for Vertex) and `F=(--backend gemini --vertex --model gemini-3.5-flash-lite --temperature 0)`.

1. Data. `gunzip -k data/v1.jsonl.gz` (and the other `.gz` files) or regenerate:
   - `python gen.py --domains all --n-policies 120 --cases-per-family 5 --seed 0 --prose gemini --vertex --gemini-model gemini-3.5-flash-lite --workers 8 --out data/v1.jsonl > data/v1.gen.log`
   - `python gen.py --domains <name> --n-policies 120 --cases-per-family 5 --seed 0 --prose gemini --vertex --gemini-model gemini-3.5-flash-lite --workers 8 --out data/<name>.jsonl > data/<name>.gen.log` for `snap` or `dependent`
2. Edit set, once per data file: `python infer.py --mode bank --data data/v1.jsonl`.
3. SFT rows: `for s in train dev; do python train.py export --split $s --drop-flagged data/v1.flagged.txt --out data/v1.sft.$s.jsonl; done`.
4. Cluster setup.
   - FarmShare: `git clone https://github.com/sfjchen/accountable-ft /scratch/users/$USER/accountable-ft && cd /scratch/users/$USER/accountable-ft && bash cluster.sh setup`
   - sc: `MAIL=<address> bash cluster.sh setup` from `/juice2/scr2/nlp/cs224v/jchen04-aft/accountable-ft` (also exports the 3 grid mixes)
5. Smoke: `bash cluster.sh smoke`.
6. Train and answer.
   - FarmShare, 6 runs in 1-epoch chunks: `bash cluster.sh train --chunks`, then `for r in {account,decision}-s{0,1,2}; do for k in 1 2; do SB=--dependency=afterok:$jid bash cluster.sh eval $r $k; done; done`
   - sc, the 18-run grid (trains, then answers all 4 test files): `MAIL=<address> bash cluster.sh grid`
   - Prompted base: `bash cluster.sh base`
7. Copy back: `rsync -av --exclude slurm $USER@login.farmshare.stanford.edu:/scratch/users/$USER/accountable-ft/runs/ runs/`.
8. Simulate, all 3 passes on a frozen run: `python infer.py --mode simulate --all-sim --data data/v1.jsonl --bank data/v1.bank.jsonl --frozen runs/<run>.jsonl $F`. Opus: `--backend claude-cli --model claude-opus-5-5` in place of `$F`, outputs in `runs/sim-opus/`.
9. Score: `python evaluate.py runs/*-e2-s*.jsonl --data data/v1.jsonl --bank data/v1.bank.jsonl --epoch 2`. Mix contrasts: `--contrast rm-mix rm-real rm-inv` on v1, `--contrast <file>-rm-mix <file>-rm-real <file>-rm-inv` on the other files.

Every cited number comes from a stamped log (`~/dev/scripts/stamp-run`) whose name sits next to its table.
