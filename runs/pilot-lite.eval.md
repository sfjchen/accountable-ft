pilot-lite: decoding ['{"max_tokens": 4096, "n": 1, "temperature": 0.0, "thinking": false, "top_k": 0, "top_p": 1.0}']; compute {'out_tokens': 4412, 'think_tokens': 0, 'call_latency_s': 67.83, 'pilot-lite.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'n': 1, 'rows': 58, 'cached': 0, 'errors': 0, 'fresh_calls': 58, 'wall_s': 14.2, 'in_tokens': 53832, 'out_tokens': 4412, 'think_tokens': 0, 'mean_latency_s': 1.17}, 'pilot-lite.answers.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'n': 1, 'rows': 38, 'cached': 38, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.23, 'in_tokens': 35363, 'out_tokens': 2989, 'think_tokens': 0, 'mean_latency_s': 0.0}, 'pilot-lite.predict.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': False, 'n': 1, 'rows': 30, 'cached': 0, 'errors': 0, 'fresh_calls': 30, 'wall_s': 11.69, 'in_tokens': 22506, 'out_tokens': 830, 'think_tokens': 0, 'mean_latency_s': 1.651}, 'pilot-lite.predict_noacc.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': True, 'n': 1, 'rows': 30, 'cached': 0, 'errors': 0, 'fresh_calls': 30, 'wall_s': 6.83, 'in_tokens': 20393, 'out_tokens': 830, 'think_tokens': 0, 'mean_latency_s': 0.815}}

### PRIMARY slice=unseen_family_train_vocab view=prose

| metric | pilot-lite |
|---|---|
| self_V | -0.03 [-0.14, 0.00] n=30 |
| self_V[add] | 0.00 [0.00, 0.00] n=5 |
| self_V[invariant_replace] | 0.00 [0.00, 0.00] n=9 |
| self_V[pivotal_replace] | -0.08 [-0.33, 0.00] n=13 |
| self_V[remove] | 0.00 [0.00, 0.00] n=3 |
| self_S | 0.80 [0.71, 0.83] n=30 |
| self_S[add] | 1.00 [1.00, 1.00] n=5 |
| self_S[invariant_replace] | 0.89 [0.50, 1.00] n=9 |
| self_S[pivotal_replace] | 0.69 [0.67, 0.70] n=13 |
| self_S[remove] | 0.67 [0.50, 1.00] n=3 |
| self_S_noacc | 0.83 [0.83, 0.86] n=30 |
| self_G | -0.03 [-0.04, 0.00] n=30 |
| bank_unchanged | 0.63 [0.57, 0.86] n=30 |
| acc_maj | 0.92 [0.67, 1.00] n=13 |
| acc_maj[interaction] | 1.00 [1.00, 1.00] n=5 |
| acc_mean | 0.92 [0.67, 1.00] n=13 |
| acc_class[approve] | 0.68 [0.25, 0.78] n=22 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=6 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=30 |
| flip | 0.69 [0.67, 0.70] n=13 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=5 |
| flip[deny->approve] | 0.50 [0.50, 0.50] n=8 |
| flip_to_cd | 0.00 [0.00, 0.00] n=13 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=8 |
| cf_pair_acc | 0.62 [0.33, 0.70] n=13 |
| invariance | 1.00 [1.00, 1.00] n=13 |
| inv_pair_acc | 0.92 [0.67, 1.00] n=13 |
| expl_valid | 0.26 [0.23, 0.36] n=58 |
| expl_minimal | 0.29 [0.23, 0.50] n=52 |
| cite_distractor | 0.41 [0.41, 0.43] n=58 |
| cite_p_nec | 0.37 [0.35, 0.38] n=58 |
| cite_r_nec | 0.46 [0.34, 0.50] n=43 |
| assume_dec | 0.54 [0.33, 0.60] n=13 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| bnd_both | 0.38 [0.33, 0.40] n=8 |
| bnd_oracle_only | 0.12 [0.00, 0.20] n=8 |
| bnd_model_only | 0.25 [0.00, 0.40] n=8 |
| bnd_neither | 0.25 [0.00, 0.67] n=8 |
| bnd_oracle_minimal | 0.38 [0.33, 0.40] n=8 |
| necessity_flip | 0.52 [0.00, 0.72] n=7 |
| fmt_err | 0.00 [0.00, 0.00] n=58 |
| len_chars | 280 [175, 314] n=58 |
| len_tok | 76 [46, 86] n=58 |

### all

| metric | pilot-lite |
|---|---|
| self_V | -0.03 [-0.14, 0.00] n=30 |
| self_V[add] | 0.00 [0.00, 0.00] n=5 |
| self_V[invariant_replace] | 0.00 [0.00, 0.00] n=9 |
| self_V[pivotal_replace] | -0.08 [-0.33, 0.00] n=13 |
| self_V[remove] | 0.00 [0.00, 0.00] n=3 |
| self_S | 0.80 [0.71, 0.83] n=30 |
| self_S[add] | 1.00 [1.00, 1.00] n=5 |
| self_S[invariant_replace] | 0.89 [0.50, 1.00] n=9 |
| self_S[pivotal_replace] | 0.69 [0.67, 0.70] n=13 |
| self_S[remove] | 0.67 [0.50, 1.00] n=3 |
| self_S_noacc | 0.83 [0.83, 0.86] n=30 |
| self_G | -0.03 [-0.04, 0.00] n=30 |
| bank_unchanged | 0.63 [0.57, 0.86] n=30 |
| acc_maj | 0.92 [0.67, 1.00] n=13 |
| acc_maj[interaction] | 1.00 [1.00, 1.00] n=5 |
| acc_mean | 0.92 [0.67, 1.00] n=13 |
| acc_class[approve] | 0.68 [0.25, 0.78] n=22 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=6 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=30 |
| flip | 0.69 [0.67, 0.70] n=13 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=5 |
| flip[deny->approve] | 0.50 [0.50, 0.50] n=8 |
| flip_to_cd | 0.00 [0.00, 0.00] n=13 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=8 |
| cf_pair_acc | 0.62 [0.33, 0.70] n=13 |
| invariance | 1.00 [1.00, 1.00] n=13 |
| inv_pair_acc | 0.92 [0.67, 1.00] n=13 |
| expl_valid | 0.26 [0.23, 0.36] n=58 |
| expl_minimal | 0.29 [0.23, 0.50] n=52 |
| cite_distractor | 0.41 [0.41, 0.43] n=58 |
| cite_p_nec | 0.37 [0.35, 0.38] n=58 |
| cite_r_nec | 0.46 [0.34, 0.50] n=43 |
| assume_dec | 0.54 [0.33, 0.60] n=13 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| bnd_both | 0.38 [0.33, 0.40] n=8 |
| bnd_oracle_only | 0.12 [0.00, 0.20] n=8 |
| bnd_model_only | 0.25 [0.00, 0.40] n=8 |
| bnd_neither | 0.25 [0.00, 0.67] n=8 |
| bnd_oracle_minimal | 0.38 [0.33, 0.40] n=8 |
| necessity_flip | 0.52 [0.00, 0.72] n=7 |
| fmt_err | 0.00 [0.00, 0.00] n=58 |
| len_chars | 280 [175, 314] n=58 |
| len_tok | 76 [46, 86] n=58 |

### secondary: slice=unseen_family_train_vocab

| metric | pilot-lite |
|---|---|
| self_V | -0.03 [-0.14, 0.00] n=30 |
| self_V[add] | 0.00 [0.00, 0.00] n=5 |
| self_V[invariant_replace] | 0.00 [0.00, 0.00] n=9 |
| self_V[pivotal_replace] | -0.08 [-0.33, 0.00] n=13 |
| self_V[remove] | 0.00 [0.00, 0.00] n=3 |
| self_S | 0.80 [0.71, 0.83] n=30 |
| self_S[add] | 1.00 [1.00, 1.00] n=5 |
| self_S[invariant_replace] | 0.89 [0.50, 1.00] n=9 |
| self_S[pivotal_replace] | 0.69 [0.67, 0.70] n=13 |
| self_S[remove] | 0.67 [0.50, 1.00] n=3 |
| self_S_noacc | 0.83 [0.83, 0.86] n=30 |
| self_G | -0.03 [-0.04, 0.00] n=30 |
| bank_unchanged | 0.63 [0.57, 0.86] n=30 |
| acc_maj | 0.92 [0.67, 1.00] n=13 |
| acc_maj[interaction] | 1.00 [1.00, 1.00] n=5 |
| acc_mean | 0.92 [0.67, 1.00] n=13 |
| acc_class[approve] | 0.68 [0.25, 0.78] n=22 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=6 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=30 |
| flip | 0.69 [0.67, 0.70] n=13 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=5 |
| flip[deny->approve] | 0.50 [0.50, 0.50] n=8 |
| flip_to_cd | 0.00 [0.00, 0.00] n=13 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=8 |
| cf_pair_acc | 0.62 [0.33, 0.70] n=13 |
| invariance | 1.00 [1.00, 1.00] n=13 |
| inv_pair_acc | 0.92 [0.67, 1.00] n=13 |
| expl_valid | 0.26 [0.23, 0.36] n=58 |
| expl_minimal | 0.29 [0.23, 0.50] n=52 |
| cite_distractor | 0.41 [0.41, 0.43] n=58 |
| cite_p_nec | 0.37 [0.35, 0.38] n=58 |
| cite_r_nec | 0.46 [0.34, 0.50] n=43 |
| assume_dec | 0.54 [0.33, 0.60] n=13 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| bnd_both | 0.38 [0.33, 0.40] n=8 |
| bnd_oracle_only | 0.12 [0.00, 0.20] n=8 |
| bnd_model_only | 0.25 [0.00, 0.40] n=8 |
| bnd_neither | 0.25 [0.00, 0.67] n=8 |
| bnd_oracle_minimal | 0.38 [0.33, 0.40] n=8 |
| necessity_flip | 0.52 [0.00, 0.72] n=7 |
| fmt_err | 0.00 [0.00, 0.00] n=58 |
| len_chars | 280 [175, 314] n=58 |
| len_tok | 76 [46, 86] n=58 |

### secondary: view=prose

| metric | pilot-lite |
|---|---|
| self_V | -0.03 [-0.14, 0.00] n=30 |
| self_V[add] | 0.00 [0.00, 0.00] n=5 |
| self_V[invariant_replace] | 0.00 [0.00, 0.00] n=9 |
| self_V[pivotal_replace] | -0.08 [-0.33, 0.00] n=13 |
| self_V[remove] | 0.00 [0.00, 0.00] n=3 |
| self_S | 0.80 [0.71, 0.83] n=30 |
| self_S[add] | 1.00 [1.00, 1.00] n=5 |
| self_S[invariant_replace] | 0.89 [0.50, 1.00] n=9 |
| self_S[pivotal_replace] | 0.69 [0.67, 0.70] n=13 |
| self_S[remove] | 0.67 [0.50, 1.00] n=3 |
| self_S_noacc | 0.83 [0.83, 0.86] n=30 |
| self_G | -0.03 [-0.04, 0.00] n=30 |
| bank_unchanged | 0.63 [0.57, 0.86] n=30 |
| acc_maj | 0.92 [0.67, 1.00] n=13 |
| acc_maj[interaction] | 1.00 [1.00, 1.00] n=5 |
| acc_mean | 0.92 [0.67, 1.00] n=13 |
| acc_class[approve] | 0.68 [0.25, 0.78] n=22 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=6 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=30 |
| flip | 0.69 [0.67, 0.70] n=13 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=5 |
| flip[deny->approve] | 0.50 [0.50, 0.50] n=8 |
| flip_to_cd | 0.00 [0.00, 0.00] n=13 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=8 |
| cf_pair_acc | 0.62 [0.33, 0.70] n=13 |
| invariance | 1.00 [1.00, 1.00] n=13 |
| inv_pair_acc | 0.92 [0.67, 1.00] n=13 |
| expl_valid | 0.26 [0.23, 0.36] n=58 |
| expl_minimal | 0.29 [0.23, 0.50] n=52 |
| cite_distractor | 0.41 [0.41, 0.43] n=58 |
| cite_p_nec | 0.37 [0.35, 0.38] n=58 |
| cite_r_nec | 0.46 [0.34, 0.50] n=43 |
| assume_dec | 0.54 [0.33, 0.60] n=13 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| bnd_both | 0.38 [0.33, 0.40] n=8 |
| bnd_oracle_only | 0.12 [0.00, 0.20] n=8 |
| bnd_model_only | 0.25 [0.00, 0.40] n=8 |
| bnd_neither | 0.25 [0.00, 0.67] n=8 |
| bnd_oracle_minimal | 0.38 [0.33, 0.40] n=8 |
| necessity_flip | 0.52 [0.00, 0.72] n=7 |
| fmt_err | 0.00 [0.00, 0.00] n=58 |
| len_chars | 280 [175, 314] n=58 |
| len_tok | 76 [46, 86] n=58 |

### descriptive splits by correctness (all)

| metric | pilot-lite |
|---|---|
| self_V|correct | -0.04 [-0.25, 0.00] n=26 |
| self_V|wrong | 0.00 [0.00, 0.00] n=4 |
| self_V[add]|correct | 0.00 [0.00, 0.00] n=3 |
| self_V[add]|wrong | 0.00 [0.00, 0.00] n=2 |
| self_V[invariant_replace]|correct | 0.00 [0.00, 0.00] n=8 |
| self_V[invariant_replace]|wrong | 0.00 [0.00, 0.00] n=1 |
| self_V[pivotal_replace]|correct | -0.08 [-0.50, 0.00] n=12 |
| self_V[pivotal_replace]|wrong | 0.00 [0.00, 0.00] n=1 |
| self_V[remove]|correct | 0.00 [0.00, 0.00] n=3 |
| self_S|correct | 0.81 [0.75, 0.82] n=26 |
| self_S|wrong | 0.75 [0.67, 1.00] n=4 |
| self_S[add]|correct | 1.00 [1.00, 1.00] n=3 |
| self_S[add]|wrong | 1.00 [1.00, 1.00] n=2 |
| self_S[invariant_replace]|correct | 1.00 [1.00, 1.00] n=8 |
| self_S[invariant_replace]|wrong | 0.00 [0.00, 0.00] n=1 |
| self_S[pivotal_replace]|correct | 0.67 [0.50, 0.70] n=12 |
| self_S[pivotal_replace]|wrong | 1.00 [1.00, 1.00] n=1 |
| self_S[remove]|correct | 0.67 [0.50, 1.00] n=3 |
| self_S_noacc|correct | 0.85 [0.82, 1.00] n=26 |
| self_S_noacc|wrong | 0.75 [0.67, 1.00] n=4 |
| self_G|correct | -0.04 [-0.05, 0.00] n=26 |
| self_G|wrong | 0.00 [0.00, 0.00] n=4 |
| bank_unchanged|correct | 0.62 [0.59, 0.75] n=26 |
| bank_unchanged|wrong | 0.75 [0.00, 1.00] n=4 |
| flip|correct | 0.67 [0.50, 0.70] n=12 |
| flip|wrong | 1.00 [1.00, 1.00] n=1 |
| flip[approve->deny]|correct | 1.00 [1.00, 1.00] n=4 |
| flip[approve->deny]|wrong | 1.00 [1.00, 1.00] n=1 |
| flip[deny->approve]|correct | 0.50 [0.50, 0.50] n=8 |
| flip_to_cd|correct | 0.00 [0.00, 0.00] n=12 |
| flip_to_cd|wrong | 0.00 [0.00, 0.00] n=1 |
| flip_to_cd[approve->deny]|correct | 0.00 [0.00, 0.00] n=4 |
| flip_to_cd[approve->deny]|wrong | 0.00 [0.00, 0.00] n=1 |
| flip_to_cd[deny->approve]|correct | 0.00 [0.00, 0.00] n=8 |
| cf_pair_acc|correct | 0.67 [0.50, 0.70] n=12 |
| cf_pair_acc|wrong | 0.00 [0.00, 0.00] n=1 |
| invariance|correct | 1.00 [1.00, 1.00] n=12 |
| invariance|wrong | 1.00 [1.00, 1.00] n=1 |
| inv_pair_acc|correct | 1.00 [1.00, 1.00] n=12 |
| inv_pair_acc|wrong | 0.00 [0.00, 0.00] n=1 |
| expl_valid|correct | 0.29 [0.22, 0.56] n=45 |
| expl_valid|wrong | 0.15 [0.00, 0.25] n=13 |
| expl_minimal|correct | 0.33 [0.25, 0.67] n=45 |
| expl_minimal|wrong | 0.00 [0.00, 0.00] n=7 |
| cite_distractor|correct | 0.38 [0.33, 0.39] n=45 |
| cite_distractor|wrong | 0.54 [0.50, 0.60] n=13 |
| cite_p_nec|correct | 0.38 [0.32, 0.39] n=45 |
| cite_p_nec|wrong | 0.35 [0.31, 0.40] n=13 |
| cite_r_nec|correct | 0.53 [0.46, 0.55] n=36 |
| cite_r_nec|wrong | 0.11 [0.10, 0.11] n=7 |
| assume_dec|correct | 0.58 [0.50, 0.60] n=12 |
| assume_dec|wrong | 0.00 [0.00, 0.00] n=1 |
| assume_val|correct | 0.80 [0.80, 0.80] n=5 |
| bnd_both|correct | 0.29 [0.00, 0.40] n=7 |
| bnd_both|wrong | 1.00 [1.00, 1.00] n=1 |
| bnd_oracle_only|correct | 0.14 [0.00, 0.20] n=7 |
| bnd_oracle_only|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_model_only|correct | 0.29 [0.00, 0.40] n=7 |
| bnd_model_only|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_neither|correct | 0.29 [0.00, 1.00] n=7 |
| bnd_neither|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_oracle_minimal|correct | 0.29 [0.00, 0.40] n=7 |
| bnd_oracle_minimal|wrong | 1.00 [1.00, 1.00] n=1 |
| necessity_flip|correct | 0.60 [0.00, 0.72] n=6 |
| necessity_flip|wrong | 0.00 [0.00, 0.00] n=1 |

### coverage

| count | pilot-lite |
|---|---|
| api_error | 0 |
| bank_no_fresh | 0 |
| bank_unscored | 570 |
| boundary_derived_refused | 5 |
| flip_parse_fail_pairs | 0 |
| fmt_err | 0 |
| interventions_requested | 38 |
| invariance_parse_fail_pairs | 0 |
| items_in_data | 1104 |
| items_scored | 58 |
| none_unsupported_assume | 1 |
| none_unsupported_support | 0 |
| outputs | 58 |
| parse_fail | 0 |
| predict_parse_fail | 0 |
| truncated | 0 |

json=runs/pilot-lite.eval.json
