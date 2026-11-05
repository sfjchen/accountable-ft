# accountable-ft

CS 224V final project (Stanford, fall 2026). Can fine-tuning make a small open model's stated reasons actually determine its decisions?

Setup: a policy (8-15 rules with exceptions and defaults) plus a case file written in prose. The model outputs a decision, the facts and rules it relied on, and any assumptions it made for missing facts. Domains are invented so the model can't lean on prior knowledge. Ground truth comes from a Python rule engine, and every account is checked by intervention: edit a cited fact in a fresh chat and the decision has to flip, edit an uncited one and it has to hold.

## Plan

- Data: one schema, several domain skins (admin rulebooks like permits, grants, trial protocols, plus an invented conference review policy). One skin and a slice of policies held out. Variants per case: minimal flip, irrelevant edit, missing fact, model-proposed flip.
- Models: Qwen3.5-9B for everything, Qwen3.8-27B for the final SFT only if compute allows. Gemma 4 26B and one API model as prompting references.
- Conditions: base, base + CoT, SFT (admin only / review only / mix), SFT + RL or DPO with the engine as reward, one CREDIT-style relabel round on top of the best SFT.
- Metrics, reported on correct and wrong items separately: accuracy, flip rate (both directions), invariance, cited-fact precision/recall vs the minimal sufficient set, assumption accuracy on missing facts, validity of the model's own proposed flip.
- Decoding fixed across conditions, splits by policy, bootstrap CIs by policy, 100 items hand-checked by both of us.

## Files

- `gen_z3_v0.py` — first generator (toy trial eligibility, z3). Kept as a cross-check only, the engine replaces it.

## Related

VERDICT (2609.03366), CREDIT (2610.35295), Chen et al. 2024 (2307.08678), Chua et al. 2024 (2403.05518), Hase & Potts 2026 (2602.20710), Jia et al. 2026 (2605.24286), Mayne et al. 2025 (2509.09396).
