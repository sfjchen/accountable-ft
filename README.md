# accountable-ft

CS 224V final project (Stanford, fall 2026). Can fine-tuning make a small open model's stated reasons actually determine its decisions?

Setup: a policy (8-15 rules with exceptions and defaults) plus a case file written in prose. The model outputs a decision, the facts and rules it relied on, and any assumptions it made for missing facts. Domains are invented so the model can't lean on prior knowledge. Ground truth comes from a Python rule engine, and every account is checked by intervention: edit a cited fact in a fresh chat and the decision has to flip, edit an uncited one and it has to hold.

## Plan

Details and reasoning in `PLAN.md`.

- Data: 4 invented domains (grant, trial, review for training, permit held out), policies sampled from template families, each case in 3 views (table, prose, prose with derivation needed). Variants per case: certified minimal flip, invariant edit, removed fact, revealed fact.
- Model: Qwen3.5-9B. Gemma 4 26B and one API model as prompting references.
- Conditions: prompted base (thinking off and on), decision-only SFT, account SFT on the same sequences with the account in the loss, one CREDIT-style relabel round if the core result is clean. RL and a 27B run only if compute allows.
- Primary endpoint: how much the model's own account helps it predict its decision after an edit it did not choose, against an oracle-copying control and a no-account control. Also decision accuracy per class, counterfactual and invariance pair accuracy, explanation validity under the engine, own proposed smallest change checked against both engine and model.
- Greedy decoding with a repeat control, splits by template family, cluster bootstrap CIs, paired comparisons, 100 items hand-checked blind by both of us.

## Files

- `gen_z3_v0.py` — first generator (toy trial eligibility, z3). Kept as a cross-check only, the engine replaces it.
- `engine.py` — rule engine: decide, minimal sufficient sets (exact, over admissible completions), minimal flips up to radius 4, invariant edits, `is_valid_justification`.
- `gen.py` — generator: template families, policies, base cases and flip/invariant/missing variants in 3 views (table, prose, prose_derive), optional Gemini prose. `render_case()` re-renders edited cases for interventions.
- `domains/*.yaml` — 4 invented domains (grant, permit, trial, review): facts, derived facts, rule templates, defaults, prose vocabulary. Permit is the held-out domain.
- `tests/test_engine.py` — engine tests on hand-written policies plus brute-force cross-checks.
- Smoke run: `python gen.py --domains all --n-policies 4 --cases-per-policy 5 --seed 0 --prose template --out data/smoke.jsonl`
- `infer.py` — one `Runner` over OpenAI-compatible endpoints (vLLM serve, OpenRouter), Gemini and offline vLLM, with fixed decoding, a response cache, `--rep` for the repeat control, `--mode bank` (intervention bank, `data/<name>.bank.jsonl`) and `--mode predict` (self-prediction with or without the frozen account).
- `evaluate.py` — all metrics with cluster bootstrap CIs, slices (primary: prose, unseen families, training vocabularies), paired comparisons, seed aggregates, coverage, checkpoint selection. Markdown to stdout, every number in JSON.
- `tests/test_evaluate.py`, `tests/fixtures/mini.jsonl` — parser, metric math on a 12-record hand-made fixture, bank, selection, bootstrap.

## Data

- `data/v1.jsonl` (not in git, about 150 MB) comes from `python gen.py --domains all --n-policies 120 --cases-per-family 5 --seed 0 --prose gemini --vertex --gemini-model gemini-3.5-flash-lite --workers 8 --out data/v1.jsonl > data/v1.gen.log`, with gcloud ADC on our GCP project. Gemini replies are cached in `data/.gemini_cache/`, so a rerun with the same seed costs nothing. Facts and gold depend only on the seed, except that a search can hit its 2 s budget on a loaded machine and mark that one item uncertified.
- `python scripts/data_report.py data/v1.jsonl --log data/v1.gen.log` writes `data/v1.stats.md` (counts, class balance, families, spend) and the blind sample `data/v1.blind100.jsonl`, with gold in `data/v1.blind100.answers.jsonl`. We each label the blind file before opening the answers.
- Each domain has 60 families of 2 policies with 5 base cases per family. Grant, trial and review split their families 30/6/24 into train/dev/unseen, so the unseen slice has 72 families (24 per domain) for clustered stats while train stays near 5.5k records. Permit's 60 families are the transfer slice. The previous dataset is kept as `data/v1.0.jsonl`.

## Training

`scripts/sft_data.py` exports chat rows (harness prompt, gold answer from `infer.format_target`, account span) and `train.py` runs LoRA SFT on Qwen3.5-9B with Unsloth and TRL on a CUDA GPU. Both conditions use the same export, so the only difference is the account loss.

- Export (once, both conditions): `python scripts/sft_data.py --split train --out data/v1.sft.train.jsonl && python scripts/sft_data.py --split dev --out data/v1.sft.dev.jsonl`
- Account SFT: `python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-acct-s0`
- Decision-only SFT: `python train.py --condition decision --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-dec-s0`
- In `<out>`: `checkpoint-<step>/` per epoch, `adapter/` (final LoRA adapter and tokenizer), `merged/` (merged 16-bit model for vLLM) and `train_meta.json` (flags, commit and dirty state, library versions, GPU, token counts with the masked-token fraction, training log).
- `tests/test_train.py` checks the masking with the Qwen2.5-0.5B-Instruct tokenizer: on the smoke train rows the decision condition masks 94.5% of answer tokens (36,480 of 38,586) and the account condition none.

## Related

VERDICT (2609.03366), CREDIT (2610.35295), Chen et al. 2024 (2307.08678), Chua et al. 2024 (2403.05518), Hase & Potts 2026 (2602.20710), Jia et al. 2026 (2605.24286), Mayne et al. 2025 (2509.09396), Doi et al. 2025 (2512.07288).
