# accountable-ft

Jon Chen and Eitan Green, CS 224V fall 2026. Design decisions, results and run history are in [DECISIONS.md](DECISIONS.md), compute, cluster notes, commands and the file map in [OPS.md](OPS.md).

Can fine-tuning make a model's stated reasons track its decisions? We train Qwen3.5-9B on rule-based eligibility cases (invented policies with exact labels from a rule engine, plus real mortgage, SNAP and IRS dependent rules). Explanation SFT (supervised fine-tuning) learns the decision and an engine-verified explanation. The matched control, decision-only SFT, sees the same rows with the explanation tokens masked out of the loss. The main score is simulatability gain: how much better a frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd) predicts the model's answer after an edit when it sees the model's own explanation rather than another case's. The simulator never sees the case.

## Results so far

Paired simulatability gain, explanation SFT minus decision-only, seed by seed, 95% CI clustered by rule family. v1 = unseen families of the invented domains, mortgage = 24 held-out mortgage families. Logs `final-v1-gemini-eval-abaa830-20261120-1542`, `final-mortgage-gemini-eval-abaa830-20261120-1542`, `final-v1-opus-eval-abaa830-20261120-1542`, `final-mortgage-opus-eval-abaa830-20261120-1542`.

| training mix | v1, Gemini | mortgage, Gemini | v1, Opus | mortgage, Opus | accuracy, v1 |
|---|---|---|---|---|---|
| round 1: grant, trial, review | 0.081 [0.043, 0.123] | 0.038 [-0.018, 0.094] | 0.161 [0.129, 0.195] | 0.091 [0.048, 0.137] | 0.004 [-0.008, 0.016] |
| round 2: grant, trial, mortgage | 0.041 [0.007, 0.078] | 0.094 [0.036, 0.151] | 0.120 [0.086, 0.151] | 0.170 [0.129, 0.211] | 0.033 [0.020, 0.049] |
| mortgage only, seed 0 | -0.005 [-0.044, 0.036] | 0.066 [-0.018, 0.150] | 0.009 [-0.038, 0.056] | 0.024 [-0.036, 0.083] | 0.006 [-0.018, 0.031] |

- Explanation SFT matches or beats decision-only on accuracy in every mix and is the only condition with valid explanations (0.756 vs 0.000 on v1, round 1).
- Each kind of training row helps most on tests like it. The row-matched grid below separates mix from size.

## Status (Nov 20)

- Row-matched grid: 3 mixes (`rm-inv` grant + trial, `rm-real` mortgage + SNAP, `rm-mix` all 4) at 3,600 train rows x 2 conditions x 3 seeds = 18 runs. Tests: unseen families of the 4 training domains, review and IRS dependent (both held out from every mix). Pre-registration in DECISIONS.md.
  - Main score failed: paired gain on IRS dependent is below 0 for every mix (-3.6 to -6.6), no contrast clears Holm. Opus agrees (no CI clear of 0).
  - New test families for every test (post hoc): pooled, real and mixed beat invented-only on mortgage (+6.6 to +6.7) and SNAP (+8.1 to +8.4) after Holm. IRS dependent real and mixed gain more on the new families than the old, so they are not pooled. Details in DECISIONS.md.
- Error analysis of 50 IRS dependent failures (`errors.py`): 61% of wrong decisions cite a rule that is waived or covers the other claim type.
- Prompted-explanation control (`--mode explain`, runs `pe-*`): a fluent untrained explanation gets half the invented-test gain and all of the mortgage gain at 8% correct. Trained explanations win on answer-changing edits (+11.8).
- Wrong-reason control (`infer.py --wrong-accounts`): each round 1 explanation keeps its decision, format, item count and length, with its cited facts swapped for true facts that leave the case open. Own minus wrong is +9.1 on the invented test (every seed's CI clear of 0) and -0.2 on mortgage, so the invented-test gain needs the right reason and the mortgage gain doesn't. On the grid, every mix gets +6.1 to +7.5 on the invented test, -0.2 to +1.6 on the original mortgage families (+5.0 and +6.7 for real and mixed with the new families pooled) and +5.4 to +9.7 on SNAP.
- Arithmetic: case text states every computed value, so no model computes. Among denials, real and mixed models gain most where the failing rule reads a derived value (mortgage +14.5 and +14.9, SNAP mixed +22.9), invented-trained models don't, so it tracks training domain, not arithmetic.
- Opus agrees on prompted explanations: trained minus prompted on the same decisions is +11.1 [8.2, 14.1] on the invented test and +0.9 [-2.6, 4.6] on mortgage.
- Permit transfer (round 1 on a never-trained invented domain): paired gain +10.0 [6.5, 13.6], +13.3 [9.7, 16.8] with Opus.
- Recommendation: train on the mixed set. It has the best grid gain on trained-on domains (+6.9 vs +4.5 real, +3.2 invented) and held-out ones (0.0 vs -2.3, -3.5), the best correctness and accuracy, at a cost of 2-6 points of correctness on each specialist's own tests. Its comparison with real-only is not dose-matched (half the real rows) and rests on 1 held-out domain per kind.
- Every number above was rescored at abaa830 (`score.sh`, sc job 18610835, 34 evals, logs `final-*-eval-abaa830-20261120-*`).

## Files

- `engine.py`: rule engine (decisions, minimal sufficient sets, minimal flips, explanation checks).
- `gen.py`: case generator, 3 views, optional Gemini prose, stats and audits.
- `domains/*.yaml`: policy domains. `*.md` beside a real domain lists its sources.
- `infer.py`: model runner (vLLM, Gemini, Claude Code headless), edit-set bank, predict and simulate modes, response cache.
- `evaluate.py`: every metric with clustered bootstrap CIs, paired comparisons, mix contrasts, power. Prints the CORE metrics (`--full` for all), and its JSON holds every metric and the commit.
- `score.sh`, `sim.sh`: every stamped eval the report cites, and the simulator passes over a set of runs.
- `compare_sims.py`: 2 simulators on the same runs.
- `train.py`: LoRA SFT with the matched loss, `train.py export` for SFT rows.
- `cluster.sh`: setup and Slurm jobs on FarmShare or sc (smoke, train, eval, base, grid, notify).
- `runs/`: run outputs and eval tables. `data/`: datasets (`.gz` committed), edit sets, stats, blind samples.
- `tests/test_all.py`: engine, generator, metrics, export and loss tests. `.venv/bin/python -m pytest -q`, with the local
  `.venv` from `uv venv .venv && uv pip install -p .venv -r requirements.txt numpy torch==2.14.0 transformers==5.17.0
  accelerate==1.15.0` (CPU torch for the loss tests, kept out of the global Python).

## Reproduce

From the repo root. Once per shell: `export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH` (ADC for Vertex) and `F=(--backend gemini --vertex --model gemini-3.5-flash-lite --temperature 0)`.

1. Data. `gunzip -k data/*.jsonl.gz runs/cache*.jsonl.gz` (data files and the simulator response caches) or regenerate:
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
8. Simulate, all 3 passes on a frozen run: `python infer.py --mode simulate --all-sim --data data/v1.jsonl --bank data/v1.bank.jsonl --frozen runs/<run>.jsonl $F`. Opus: `--backend claude-cli --model claude-opus-5-5` in place of `$F`, outputs in `runs/sim-opus/`. Over many runs and files, on any host: `TAG=<name> PAT='<run regex>' FILES='<files>' CONC=32 bash sim.sh gemini`.
9. Score: `python evaluate.py runs/*-e2-s*.jsonl --data data/v1.jsonl --bank data/v1.bank.jsonl --epoch 2`. Mix contrasts: `--contrast rm-mix rm-real rm-inv` on v1, `--contrast <file>-rm-mix <file>-rm-real <file>-rm-inv` on the other files. Every eval the report cites: `bash score.sh list`, then `bash score.sh run <i>` (1 per Slurm array task) or `bash score.sh all`, from a clean checkout with `stamp-run` on PATH.

Every cited number comes from a stamped log (`~/dev/scripts/stamp-run`) whose name sits next to its table.
