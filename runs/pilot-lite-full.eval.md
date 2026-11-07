pilot-lite-full: decoding ['{"max_tokens": 4096, "n": 1, "temperature": 0.0, "thinking": false, "top_k": 0, "top_p": 1.0}']; compute {'out_tokens': 10337, 'think_tokens': 0, 'call_latency_s': 196.9, 'pilot-lite-full.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'n': 1, 'rows': 140, 'cached': 58, 'errors': 0, 'fresh_calls': 82, 'wall_s': 33.17, 'in_tokens': 135216, 'out_tokens': 10337, 'think_tokens': 0, 'mean_latency_s': 1.574}, 'pilot-lite-full.answers.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'n': 1, 'rows': 98, 'cached': 45, 'errors': 0, 'fresh_calls': 53, 'wall_s': 7.36, 'in_tokens': 93183, 'out_tokens': 7439, 'think_tokens': 0, 'mean_latency_s': 0.877}, 'pilot-lite-full.predict.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': False, 'n': 1, 'rows': 69, 'cached': 30, 'errors': 0, 'fresh_calls': 39, 'wall_s': 7.17, 'in_tokens': 53560, 'out_tokens': 1908, 'think_tokens': 0, 'mean_latency_s': 1.077}, 'pilot-lite-full.predict_noacc.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': True, 'n': 1, 'rows': 69, 'cached': 30, 'errors': 0, 'fresh_calls': 39, 'wall_s': 5.93, 'in_tokens': 48285, 'out_tokens': 1907, 'think_tokens': 0, 'mean_latency_s': 0.853}}

### PRIMARY slice=unseen_family_train_vocab view=prose

| metric | pilot-lite-full |
|---|---|
| self_V | -0.07 [-0.12, 0.00] n=69 |
| self_V[add] | -0.10 [-0.33, 0.00] n=10 |
| self_V[invariant_replace] | -0.10 [-0.17, 0.00] n=21 |
| self_V[pivotal_replace] | -0.07 [-0.20, 0.00] n=30 |
| self_V[remove] | 0.00 [0.00, 0.00] n=8 |
| self_S | 0.77 [0.68, 0.83] n=69 |
| self_S[add] | 0.90 [0.67, 1.00] n=10 |
| self_S[invariant_replace] | 0.81 [0.62, 1.00] n=21 |
| self_S[pivotal_replace] | 0.73 [0.70, 0.80] n=30 |
| self_S[remove] | 0.62 [0.50, 1.00] n=8 |
| self_S_noacc | 0.84 [0.80, 0.90] n=69 |
| self_G | 0.06 [-0.04, 0.29] n=69 |
| bank_unchanged | 0.68 [0.57, 0.86] n=69 |
| acc_maj | 0.83 [0.60, 1.00] n=30 |
| acc_maj[interaction] | 0.83 [0.60, 1.00] n=12 |
| acc_mean | 0.83 [0.60, 1.00] n=30 |
| acc_class[approve] | 0.53 [0.22, 0.78] n=59 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=20 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=61 |
| flip | 0.63 [0.50, 0.70] n=30 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=14 |
| flip[deny->approve] | 0.31 [0.00, 0.50] n=16 |
| flip_to_cd | 0.00 [0.00, 0.00] n=30 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=14 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=16 |
| cf_pair_acc | 0.47 [0.10, 0.70] n=30 |
| invariance | 0.90 [0.80, 1.00] n=30 |
| inv_pair_acc | 0.80 [0.60, 1.00] n=30 |
| expl_valid | 0.22 [0.12, 0.32] n=140 |
| expl_minimal | 0.23 [0.05, 0.40] n=120 |
| cite_distractor | 0.47 [0.41, 0.53] n=140 |
| cite_p_nec | 0.34 [0.24, 0.42] n=140 |
| cite_r_nec | 0.39 [0.17, 0.53] n=103 |
| assume_dec | 0.33 [0.10, 0.60] n=30 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| none_claim_disproved | 1.00 [1.00, 1.00] n=3 |
| none_claim_correct | 0.00 [0.00, 0.00] n=3 |
| none_claim_unresolved | 0.00 [0.00, 0.00] n=3 |
| bnd_both | 0.40 [0.00, 0.60] n=20 |
| bnd_oracle_only | 0.10 [0.00, 0.20] n=20 |
| bnd_model_only | 0.10 [0.00, 0.40] n=20 |
| bnd_neither | 0.40 [0.00, 0.80] n=20 |
| bnd_oracle_minimal | 0.40 [0.20, 0.50] n=20 |
| necessity_flip | 0.50 [0.19, 0.72] n=17 |
| fmt_err | 0.00 [0.00, 0.00] n=140 |
| len_chars | 269 [236, 314] n=140 |
| len_tok | 74 [60, 86] n=140 |

### all

| metric | pilot-lite-full |
|---|---|
| self_V | -0.07 [-0.12, 0.00] n=69 |
| self_V[add] | -0.10 [-0.33, 0.00] n=10 |
| self_V[invariant_replace] | -0.10 [-0.17, 0.00] n=21 |
| self_V[pivotal_replace] | -0.07 [-0.20, 0.00] n=30 |
| self_V[remove] | 0.00 [0.00, 0.00] n=8 |
| self_S | 0.77 [0.68, 0.83] n=69 |
| self_S[add] | 0.90 [0.67, 1.00] n=10 |
| self_S[invariant_replace] | 0.81 [0.62, 1.00] n=21 |
| self_S[pivotal_replace] | 0.73 [0.70, 0.80] n=30 |
| self_S[remove] | 0.62 [0.50, 1.00] n=8 |
| self_S_noacc | 0.84 [0.80, 0.90] n=69 |
| self_G | 0.06 [-0.04, 0.29] n=69 |
| bank_unchanged | 0.68 [0.57, 0.86] n=69 |
| acc_maj | 0.83 [0.60, 1.00] n=30 |
| acc_maj[interaction] | 0.83 [0.60, 1.00] n=12 |
| acc_mean | 0.83 [0.60, 1.00] n=30 |
| acc_class[approve] | 0.53 [0.22, 0.78] n=59 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=20 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=61 |
| flip | 0.63 [0.50, 0.70] n=30 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=14 |
| flip[deny->approve] | 0.31 [0.00, 0.50] n=16 |
| flip_to_cd | 0.00 [0.00, 0.00] n=30 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=14 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=16 |
| cf_pair_acc | 0.47 [0.10, 0.70] n=30 |
| invariance | 0.90 [0.80, 1.00] n=30 |
| inv_pair_acc | 0.80 [0.60, 1.00] n=30 |
| expl_valid | 0.22 [0.12, 0.32] n=140 |
| expl_minimal | 0.23 [0.05, 0.40] n=120 |
| cite_distractor | 0.47 [0.41, 0.53] n=140 |
| cite_p_nec | 0.34 [0.24, 0.42] n=140 |
| cite_r_nec | 0.39 [0.17, 0.53] n=103 |
| assume_dec | 0.33 [0.10, 0.60] n=30 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| none_claim_disproved | 1.00 [1.00, 1.00] n=3 |
| none_claim_correct | 0.00 [0.00, 0.00] n=3 |
| none_claim_unresolved | 0.00 [0.00, 0.00] n=3 |
| bnd_both | 0.40 [0.00, 0.60] n=20 |
| bnd_oracle_only | 0.10 [0.00, 0.20] n=20 |
| bnd_model_only | 0.10 [0.00, 0.40] n=20 |
| bnd_neither | 0.40 [0.00, 0.80] n=20 |
| bnd_oracle_minimal | 0.40 [0.20, 0.50] n=20 |
| necessity_flip | 0.50 [0.19, 0.72] n=17 |
| fmt_err | 0.00 [0.00, 0.00] n=140 |
| len_chars | 269 [236, 314] n=140 |
| len_tok | 74 [60, 86] n=140 |

### secondary: slice=unseen_family_train_vocab

| metric | pilot-lite-full |
|---|---|
| self_V | -0.07 [-0.12, 0.00] n=69 |
| self_V[add] | -0.10 [-0.33, 0.00] n=10 |
| self_V[invariant_replace] | -0.10 [-0.17, 0.00] n=21 |
| self_V[pivotal_replace] | -0.07 [-0.20, 0.00] n=30 |
| self_V[remove] | 0.00 [0.00, 0.00] n=8 |
| self_S | 0.77 [0.68, 0.83] n=69 |
| self_S[add] | 0.90 [0.67, 1.00] n=10 |
| self_S[invariant_replace] | 0.81 [0.62, 1.00] n=21 |
| self_S[pivotal_replace] | 0.73 [0.70, 0.80] n=30 |
| self_S[remove] | 0.62 [0.50, 1.00] n=8 |
| self_S_noacc | 0.84 [0.80, 0.90] n=69 |
| self_G | 0.06 [-0.04, 0.29] n=69 |
| bank_unchanged | 0.68 [0.57, 0.86] n=69 |
| acc_maj | 0.83 [0.60, 1.00] n=30 |
| acc_maj[interaction] | 0.83 [0.60, 1.00] n=12 |
| acc_mean | 0.83 [0.60, 1.00] n=30 |
| acc_class[approve] | 0.53 [0.22, 0.78] n=59 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=20 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=61 |
| flip | 0.63 [0.50, 0.70] n=30 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=14 |
| flip[deny->approve] | 0.31 [0.00, 0.50] n=16 |
| flip_to_cd | 0.00 [0.00, 0.00] n=30 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=14 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=16 |
| cf_pair_acc | 0.47 [0.10, 0.70] n=30 |
| invariance | 0.90 [0.80, 1.00] n=30 |
| inv_pair_acc | 0.80 [0.60, 1.00] n=30 |
| expl_valid | 0.22 [0.12, 0.32] n=140 |
| expl_minimal | 0.23 [0.05, 0.40] n=120 |
| cite_distractor | 0.47 [0.41, 0.53] n=140 |
| cite_p_nec | 0.34 [0.24, 0.42] n=140 |
| cite_r_nec | 0.39 [0.17, 0.53] n=103 |
| assume_dec | 0.33 [0.10, 0.60] n=30 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| none_claim_disproved | 1.00 [1.00, 1.00] n=3 |
| none_claim_correct | 0.00 [0.00, 0.00] n=3 |
| none_claim_unresolved | 0.00 [0.00, 0.00] n=3 |
| bnd_both | 0.40 [0.00, 0.60] n=20 |
| bnd_oracle_only | 0.10 [0.00, 0.20] n=20 |
| bnd_model_only | 0.10 [0.00, 0.40] n=20 |
| bnd_neither | 0.40 [0.00, 0.80] n=20 |
| bnd_oracle_minimal | 0.40 [0.20, 0.50] n=20 |
| necessity_flip | 0.50 [0.19, 0.72] n=17 |
| fmt_err | 0.00 [0.00, 0.00] n=140 |
| len_chars | 269 [236, 314] n=140 |
| len_tok | 74 [60, 86] n=140 |

### secondary: view=prose

| metric | pilot-lite-full |
|---|---|
| self_V | -0.07 [-0.12, 0.00] n=69 |
| self_V[add] | -0.10 [-0.33, 0.00] n=10 |
| self_V[invariant_replace] | -0.10 [-0.17, 0.00] n=21 |
| self_V[pivotal_replace] | -0.07 [-0.20, 0.00] n=30 |
| self_V[remove] | 0.00 [0.00, 0.00] n=8 |
| self_S | 0.77 [0.68, 0.83] n=69 |
| self_S[add] | 0.90 [0.67, 1.00] n=10 |
| self_S[invariant_replace] | 0.81 [0.62, 1.00] n=21 |
| self_S[pivotal_replace] | 0.73 [0.70, 0.80] n=30 |
| self_S[remove] | 0.62 [0.50, 1.00] n=8 |
| self_S_noacc | 0.84 [0.80, 0.90] n=69 |
| self_G | 0.06 [-0.04, 0.29] n=69 |
| bank_unchanged | 0.68 [0.57, 0.86] n=69 |
| acc_maj | 0.83 [0.60, 1.00] n=30 |
| acc_maj[interaction] | 0.83 [0.60, 1.00] n=12 |
| acc_mean | 0.83 [0.60, 1.00] n=30 |
| acc_class[approve] | 0.53 [0.22, 0.78] n=59 |
| acc_class[cannot determine] | 0.00 [0.00, 0.00] n=20 |
| acc_class[deny] | 1.00 [1.00, 1.00] n=61 |
| flip | 0.63 [0.50, 0.70] n=30 |
| flip[approve->deny] | 1.00 [1.00, 1.00] n=14 |
| flip[deny->approve] | 0.31 [0.00, 0.50] n=16 |
| flip_to_cd | 0.00 [0.00, 0.00] n=30 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=14 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=16 |
| cf_pair_acc | 0.47 [0.10, 0.70] n=30 |
| invariance | 0.90 [0.80, 1.00] n=30 |
| inv_pair_acc | 0.80 [0.60, 1.00] n=30 |
| expl_valid | 0.22 [0.12, 0.32] n=140 |
| expl_minimal | 0.23 [0.05, 0.40] n=120 |
| cite_distractor | 0.47 [0.41, 0.53] n=140 |
| cite_p_nec | 0.34 [0.24, 0.42] n=140 |
| cite_r_nec | 0.39 [0.17, 0.53] n=103 |
| assume_dec | 0.33 [0.10, 0.60] n=30 |
| assume_val | 0.80 [0.80, 0.80] n=5 |
| none_claim_disproved | 1.00 [1.00, 1.00] n=3 |
| none_claim_correct | 0.00 [0.00, 0.00] n=3 |
| none_claim_unresolved | 0.00 [0.00, 0.00] n=3 |
| bnd_both | 0.40 [0.00, 0.60] n=20 |
| bnd_oracle_only | 0.10 [0.00, 0.20] n=20 |
| bnd_model_only | 0.10 [0.00, 0.40] n=20 |
| bnd_neither | 0.40 [0.00, 0.80] n=20 |
| bnd_oracle_minimal | 0.40 [0.20, 0.50] n=20 |
| necessity_flip | 0.50 [0.19, 0.72] n=17 |
| fmt_err | 0.00 [0.00, 0.00] n=140 |
| len_chars | 269 [236, 314] n=140 |
| len_tok | 74 [60, 86] n=140 |

### descriptive splits by correctness (all)

| metric | pilot-lite-full |
|---|---|
| self_V|correct | -0.06 [-0.15, 0.00] n=51 |
| self_V|wrong | -0.11 [-0.17, 0.00] n=18 |
| self_V[add]|correct | 0.00 [0.00, 0.00] n=3 |
| self_V[add]|wrong | -0.14 [-0.33, 0.00] n=7 |
| self_V[invariant_replace]|correct | -0.06 [-0.14, 0.00] n=16 |
| self_V[invariant_replace]|wrong | -0.20 [-0.25, 0.00] n=5 |
| self_V[pivotal_replace]|correct | -0.08 [-0.22, 0.00] n=25 |
| self_V[pivotal_replace]|wrong | 0.00 [0.00, 0.00] n=5 |
| self_V[remove]|correct | 0.00 [0.00, 0.00] n=7 |
| self_V[remove]|wrong | 0.00 [0.00, 0.00] n=1 |
| self_S|correct | 0.75 [0.65, 0.82] n=51 |
| self_S|wrong | 0.83 [0.80, 1.00] n=18 |
| self_S[add]|correct | 1.00 [1.00, 1.00] n=3 |
| self_S[add]|wrong | 0.86 [0.67, 1.00] n=7 |
| self_S[invariant_replace]|correct | 0.88 [0.71, 1.00] n=16 |
| self_S[invariant_replace]|wrong | 0.60 [0.00, 0.75] n=5 |
| self_S[pivotal_replace]|correct | 0.68 [0.67, 0.70] n=25 |
| self_S[pivotal_replace]|wrong | 1.00 [1.00, 1.00] n=5 |
| self_S[remove]|correct | 0.57 [0.50, 1.00] n=7 |
| self_S[remove]|wrong | 1.00 [1.00, 1.00] n=1 |
| self_S_noacc|correct | 0.80 [0.78, 0.82] n=51 |
| self_S_noacc|wrong | 0.94 [0.80, 1.00] n=18 |
| self_G|correct | 0.02 [-0.05, 0.33] n=51 |
| self_G|wrong | 0.17 [0.00, 0.25] n=18 |
| bank_unchanged|correct | 0.65 [0.59, 0.89] n=51 |
| bank_unchanged|wrong | 0.78 [0.00, 0.83] n=18 |
| flip|correct | 0.56 [0.17, 0.70] n=25 |
| flip|wrong | 1.00 [1.00, 1.00] n=5 |
| flip[approve->deny]|correct | 1.00 [1.00, 1.00] n=9 |
| flip[approve->deny]|wrong | 1.00 [1.00, 1.00] n=5 |
| flip[deny->approve]|correct | 0.31 [0.00, 0.50] n=16 |
| flip_to_cd|correct | 0.00 [0.00, 0.00] n=25 |
| flip_to_cd|wrong | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[approve->deny]|correct | 0.00 [0.00, 0.00] n=9 |
| flip_to_cd[approve->deny]|wrong | 0.00 [0.00, 0.00] n=5 |
| flip_to_cd[deny->approve]|correct | 0.00 [0.00, 0.00] n=16 |
| cf_pair_acc|correct | 0.56 [0.17, 0.70] n=25 |
| cf_pair_acc|wrong | 0.00 [0.00, 0.00] n=5 |
| invariance|correct | 0.96 [0.89, 1.00] n=25 |
| invariance|wrong | 0.60 [0.50, 1.00] n=5 |
| inv_pair_acc|correct | 0.96 [0.89, 1.00] n=25 |
| inv_pair_acc|wrong | 0.00 [0.00, 0.00] n=5 |
| expl_valid|correct | 0.27 [0.09, 0.44] n=92 |
| expl_valid|wrong | 0.12 [0.00, 0.25] n=48 |
| expl_minimal|correct | 0.29 [0.09, 0.47] n=92 |
| expl_minimal|wrong | 0.00 [0.00, 0.00] n=28 |
| cite_distractor|correct | 0.37 [0.27, 0.41] n=92 |
| cite_distractor|wrong | 0.67 [0.50, 0.85] n=48 |
| cite_p_nec|correct | 0.43 [0.36, 0.52] n=92 |
| cite_p_nec|wrong | 0.17 [0.14, 0.31] n=48 |
| cite_r_nec|correct | 0.52 [0.30, 0.64] n=75 |
| cite_r_nec|wrong | 0.05 [0.04, 0.11] n=28 |
| assume_dec|correct | 0.40 [0.17, 0.60] n=25 |
| assume_dec|wrong | 0.00 [0.00, 0.00] n=5 |
| assume_val|correct | 0.80 [0.80, 0.80] n=5 |
| none_claim_disproved|wrong | 1.00 [1.00, 1.00] n=3 |
| none_claim_correct|wrong | 0.00 [0.00, 0.00] n=3 |
| none_claim_unresolved|wrong | 0.00 [0.00, 0.00] n=3 |
| bnd_both|correct | 0.37 [0.00, 0.56] n=19 |
| bnd_both|wrong | 1.00 [1.00, 1.00] n=1 |
| bnd_oracle_only|correct | 0.11 [0.00, 0.20] n=19 |
| bnd_oracle_only|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_model_only|correct | 0.11 [0.00, 0.40] n=19 |
| bnd_model_only|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_neither|correct | 0.42 [0.00, 0.80] n=19 |
| bnd_neither|wrong | 0.00 [0.00, 0.00] n=1 |
| bnd_oracle_minimal|correct | 0.37 [0.20, 0.44] n=19 |
| bnd_oracle_minimal|wrong | 1.00 [1.00, 1.00] n=1 |
| necessity_flip|correct | 0.61 [0.31, 0.72] n=14 |
| necessity_flip|wrong | 0.00 [0.00, 0.00] n=3 |

### coverage

| count | pilot-lite-full |
|---|---|
| api_error | 0 |
| bank_no_fresh | 0 |
| bank_unscored | 531 |
| boundary_derived_refused | 7 |
| flip_parse_fail_pairs | 0 |
| fmt_err | 0 |
| interventions_requested | 98 |
| invariance_parse_fail_pairs | 0 |
| items_in_data | 1104 |
| items_scored | 140 |
| none_claim_disproved | 3 |
| none_unsupported_assume | 1 |
| none_unsupported_support | 0 |
| outputs | 140 |
| parse_fail | 0 |
| predict_parse_fail | 0 |
| truncated | 0 |

json=runs/pilot-lite-full.eval.json
