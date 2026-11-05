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

## Related

VERDICT (2609.03366), CREDIT (2610.35295), Chen et al. 2024 (2307.08678), Chua et al. 2024 (2403.05518), Hase & Potts 2026 (2602.20710), Jia et al. 2026 (2605.24286), Mayne et al. 2025 (2509.09396), Doi et al. 2025 (2512.07288).
