mortgage-split-lite: decoding ['{"backend": "gemini/vertex:global", "max_tokens": 4096, "model": "gemini-3.5-flash-lite", "n": 1, "temperature": 0.0, "thinking": false, "top_k": 0, "top_p": 1.0}']; compute {'out_tokens': 81200, 'think_tokens': 0, 'call_latency_s': 679.04, 'mortgage-split-lite.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 687, 'cached': 687, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.83, 'in_tokens': 891834, 'out_tokens': 81200, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 687}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.0, 'cost_usd_fresh': 0.0, 'cost_usd_if_uncached': 0.4706}, 'mortgage-split-lite.repeat.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 687, 'cached': 687, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.81, 'in_tokens': 891834, 'out_tokens': 76811, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 687}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.0, 'cost_usd_fresh': 0.0, 'cost_usd_if_uncached': 0.4596}, 'mortgage-split-lite.predict.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 287, 'cached': 0, 'errors': 0, 'fresh_calls': 287, 'wall_s': 28.85, 'in_tokens': 298767, 'out_tokens': 7939, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 287}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.747, 'cost_usd_fresh': 0.1095, 'cost_usd_if_uncached': 0.1095}, 'mortgage-split-lite.predict_noacc.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict_noacc', 'no_account': True, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 287, 'cached': 0, 'errors': 0, 'fresh_calls': 287, 'wall_s': 27.15, 'in_tokens': 266417, 'out_tokens': 7938, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 287}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.689, 'cost_usd_fresh': 0.0998, 'cost_usd_if_uncached': 0.0998}, 'mortgage-split-lite.simulate.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 287, 'cached': 287, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.84, 'in_tokens': 176679, 'out_tokens': 7989, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 287}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.0, 'cost_usd_fresh': 0.0, 'cost_usd_if_uncached': 0.073}, 'mortgage-split-lite.simulate_noacc.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate_noacc', 'no_account': True, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 287, 'cached': 287, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.03, 'in_tokens': 152383, 'out_tokens': 8101, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 287}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.0, 'cost_usd_fresh': 0.0, 'cost_usd_if_uncached': 0.066}, 'mortgage-split-lite.simulate_shuf.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate_shuf', 'no_account': False, 'shuffle_accounts': True, 'shuf_missing': 0, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 287, 'cached': 287, 'errors': 0, 'fresh_calls': 0, 'wall_s': 1.07, 'in_tokens': 178496, 'out_tokens': 7974, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 287}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.0, 'cost_usd_fresh': 0.0, 'cost_usd_if_uncached': 0.0735}}

### PRIMARY slice=unseen_family_train_vocab view=prose

| metric | mortgage-split-lite | mortgage-split-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.05 [-0.01, 0.09] n=287 | 0.05 [-0.01, 0.09] n=287 |
| sim_delta[add] | -0.02 [-0.14, 0.09] n=43 | -0.02 [-0.14, 0.09] n=43 |
| sim_delta[changed] | 0.01 [-0.11, 0.13] n=109 | 0.01 [-0.11, 0.13] n=109 |
| sim_delta[invariant_replace] | 0.12 [0.04, 0.21] n=43 | 0.12 [0.04, 0.21] n=43 |
| sim_delta[noncrossing_replace] | 0.12 [0.00, 0.24] n=43 | 0.12 [0.00, 0.24] n=43 |
| sim_delta[pivotal_replace] | -0.02 [-0.12, 0.08] n=115 | -0.02 [-0.12, 0.08] n=115 |
| sim_delta[remove] | 0.14 [0.04, 0.26] n=43 | 0.14 [0.04, 0.26] n=43 |
| sim_delta[unchanged] | 0.07 [0.01, 0.13] n=178 | 0.07 [0.01, 0.13] n=178 |
| sim_acct | 0.64 [0.57, 0.71] n=287 | 0.64 [0.57, 0.71] n=287 |
| sim_acct[add] | 0.70 [0.57, 0.81] n=43 | 0.70 [0.57, 0.81] n=43 |
| sim_acct[invariant_replace] | 0.84 [0.71, 0.93] n=43 | 0.84 [0.71, 0.93] n=43 |
| sim_acct[noncrossing_replace] | 0.67 [0.55, 0.80] n=43 | 0.67 [0.55, 0.80] n=43 |
| sim_acct[pivotal_replace] | 0.50 [0.40, 0.60] n=115 | 0.50 [0.40, 0.60] n=115 |
| sim_acct[remove] | 0.70 [0.56, 0.83] n=43 | 0.70 [0.56, 0.83] n=43 |
| sim_shuf | 0.59 [0.53, 0.66] n=287 | 0.59 [0.53, 0.66] n=287 |
| sim_shuf[add] | 0.72 [0.57, 0.85] n=43 | 0.72 [0.57, 0.85] n=43 |
| sim_shuf[invariant_replace] | 0.72 [0.58, 0.84] n=43 | 0.72 [0.58, 0.84] n=43 |
| sim_shuf[noncrossing_replace] | 0.56 [0.40, 0.71] n=43 | 0.56 [0.40, 0.71] n=43 |
| sim_shuf[pivotal_replace] | 0.52 [0.43, 0.61] n=115 | 0.52 [0.43, 0.61] n=115 |
| sim_shuf[remove] | 0.56 [0.40, 0.72] n=43 | 0.56 [0.40, 0.72] n=43 |
| sim_gross (acct - noacc) | 0.28 [0.22, 0.34] n=287 | 0.28 [0.22, 0.34] n=287 |
| sim_gross[add] | 0.33 [0.19, 0.48] n=43 | 0.33 [0.19, 0.48] n=43 |
| sim_gross[invariant_replace] | 0.44 [0.31, 0.56] n=43 | 0.44 [0.31, 0.56] n=43 |
| sim_gross[noncrossing_replace] | 0.28 [0.12, 0.46] n=43 | 0.28 [0.12, 0.46] n=43 |
| sim_gross[pivotal_replace] | 0.26 [0.16, 0.35] n=115 | 0.26 [0.16, 0.35] n=115 |
| sim_gross[remove] | 0.12 [0.00, 0.25] n=43 | 0.12 [0.00, 0.25] n=43 |
| sim_noacc | 0.36 [0.31, 0.41] n=287 | 0.36 [0.31, 0.41] n=287 |
| sim_noacc[add] | 0.37 [0.23, 0.52] n=43 | 0.37 [0.23, 0.52] n=43 |
| sim_noacc[invariant_replace] | 0.40 [0.26, 0.51] n=43 | 0.40 [0.26, 0.51] n=43 |
| sim_noacc[noncrossing_replace] | 0.40 [0.23, 0.57] n=43 | 0.40 [0.23, 0.57] n=43 |
| sim_noacc[pivotal_replace] | 0.24 [0.16, 0.32] n=115 | 0.24 [0.16, 0.32] n=115 |
| sim_noacc[remove] | 0.58 [0.44, 0.73] n=43 | 0.58 [0.44, 0.73] n=43 |
| sim_const_unchanged (baseline: frozen decision) | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| sim_const_unchanged[add] | 0.72 [0.60, 0.83] n=43 | 0.72 [0.60, 0.83] n=43 |
| sim_const_unchanged[invariant_replace] | 0.81 [0.69, 0.91] n=43 | 0.81 [0.69, 0.91] n=43 |
| sim_const_unchanged[noncrossing_replace] | 0.74 [0.63, 0.86] n=43 | 0.74 [0.63, 0.86] n=43 |
| sim_const_unchanged[pivotal_replace] | 0.43 [0.34, 0.53] n=115 | 0.43 [0.34, 0.53] n=115 |
| sim_const_unchanged[remove] | 0.70 [0.55, 0.83] n=43 | 0.70 [0.55, 0.83] n=43 |
| sim_oracle (baseline: engine label) | 0.73 [0.68, 0.79] n=287 | 0.73 [0.68, 0.79] n=287 |
| sim_oracle[add] | 0.81 [0.69, 0.93] n=43 | 0.81 [0.69, 0.93] n=43 |
| sim_oracle[invariant_replace] | 0.81 [0.68, 0.93] n=43 | 0.81 [0.68, 0.93] n=43 |
| sim_oracle[noncrossing_replace] | 0.86 [0.76, 0.95] n=43 | 0.86 [0.76, 0.95] n=43 |
| sim_oracle[pivotal_replace] | 0.75 [0.69, 0.81] n=115 | 0.75 [0.69, 0.81] n=115 |
| sim_oracle[remove] | 0.40 [0.24, 0.56] n=43 | 0.40 [0.24, 0.56] n=43 |
| self_V (secondary) | -0.01 [-0.06, 0.03] n=287 | -0.01 [-0.06, 0.03] n=287 |
| self_V[add] | 0.02 [0.00, 0.07] n=43 | 0.02 [0.00, 0.07] n=43 |
| self_V[invariant_replace] | 0.00 [-0.10, 0.11] n=43 | 0.00 [-0.10, 0.11] n=43 |
| self_V[noncrossing_replace] | -0.12 [-0.21, -0.02] n=43 | -0.12 [-0.21, -0.02] n=43 |
| self_V[pivotal_replace] | -0.02 [-0.09, 0.05] n=115 | -0.02 [-0.09, 0.05] n=115 |
| self_V[remove] | 0.05 [-0.07, 0.17] n=43 | 0.05 [-0.07, 0.17] n=43 |
| self_S | 0.74 [0.69, 0.79] n=287 | 0.74 [0.69, 0.79] n=287 |
| self_S[add] | 0.84 [0.74, 0.93] n=43 | 0.84 [0.74, 0.93] n=43 |
| self_S[invariant_replace] | 0.86 [0.75, 0.94] n=43 | 0.86 [0.75, 0.94] n=43 |
| self_S[noncrossing_replace] | 0.67 [0.52, 0.81] n=43 | 0.67 [0.52, 0.81] n=43 |
| self_S[pivotal_replace] | 0.70 [0.61, 0.77] n=115 | 0.70 [0.61, 0.77] n=115 |
| self_S[remove] | 0.72 [0.57, 0.86] n=43 | 0.72 [0.57, 0.86] n=43 |
| self_S_noacc | 0.76 [0.70, 0.80] n=287 | 0.76 [0.70, 0.80] n=287 |
| self_S_noacc[add] | 0.81 [0.70, 0.93] n=43 | 0.81 [0.70, 0.93] n=43 |
| self_S_noacc[invariant_replace] | 0.86 [0.74, 0.96] n=43 | 0.86 [0.74, 0.96] n=43 |
| self_S_noacc[noncrossing_replace] | 0.79 [0.68, 0.89] n=43 | 0.79 [0.68, 0.89] n=43 |
| self_S_noacc[pivotal_replace] | 0.71 [0.66, 0.77] n=115 | 0.71 [0.66, 0.77] n=115 |
| self_S_noacc[remove] | 0.67 [0.54, 0.81] n=43 | 0.67 [0.54, 0.81] n=43 |
| self_G | 0.01 [-0.07, 0.08] n=287 | 0.01 [-0.07, 0.08] n=287 |
| bank_unchanged | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| acc_maj | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_maj[interaction] | 0.80 [0.64, 0.92] n=55 | 0.80 [0.64, 0.92] n=55 |
| acc_mean | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_class[approve] | 0.66 [0.57, 0.75] n=202 | 0.66 [0.57, 0.75] n=202 |
| acc_class[cannot determine] | 0.03 [0.00, 0.08] n=70 | 0.03 [0.00, 0.08] n=70 |
| acc_class[deny] | 0.93 [0.89, 0.97] n=257 | 0.93 [0.89, 0.97] n=257 |
| repeat_disagree | 0.18 [0.14, 0.22] n=529 | 0.18 [0.14, 0.22] n=529 |
| flip | 0.76 [0.68, 0.83] n=115 | 0.76 [0.68, 0.83] n=115 |
| flip~noise | 0.28 [0.19, 0.37] n=115 | 0.28 [0.19, 0.37] n=115 |
| flip[approve->deny] | 0.90 [0.80, 0.98] n=51 | 0.90 [0.80, 0.98] n=51 |
| flip[approve->deny]~noise | 0.29 [0.17, 0.43] n=51 | 0.29 [0.17, 0.43] n=51 |
| flip[deny->approve] | 0.64 [0.52, 0.77] n=64 | 0.64 [0.52, 0.77] n=64 |
| flip[deny->approve]~noise | 0.27 [0.16, 0.38] n=64 | 0.27 [0.16, 0.38] n=64 |
| flip_to_cd | 0.00 [0.00, 0.00] n=115 | 0.00 [0.00, 0.00] n=115 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=51 | 0.00 [0.00, 0.00] n=51 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=64 | 0.00 [0.00, 0.00] n=64 |
| cf_pair_acc | 0.56 [0.46, 0.65] n=115 | 0.56 [0.46, 0.65] n=115 |
| invariance | 0.84 [0.76, 0.91] n=115 | 0.84 [0.76, 0.91] n=115 |
| invariance~noise | 0.18 [0.12, 0.24] n=115 | 0.18 [0.12, 0.24] n=115 |
| inv_pair_acc | 0.74 [0.65, 0.82] n=115 | 0.74 [0.65, 0.82] n=115 |
| expl_valid | 0.24 [0.19, 0.28] n=523 | 0.24 [0.19, 0.28] n=523 |
| acct_consistent | 0.72 [0.68, 0.77] n=460 | 0.72 [0.68, 0.77] n=460 |
| expl_minimal | 0.25 [0.20, 0.30] n=453 | 0.25 [0.20, 0.30] n=453 |
| cite_distractor | 0.39 [0.35, 0.44] n=529 | 0.39 [0.35, 0.44] n=529 |
| cite_p_nec | 0.34 [0.30, 0.37] n=529 | 0.34 [0.30, 0.37] n=529 |
| cite_r_nec | 0.44 [0.38, 0.50] n=403 | 0.44 [0.38, 0.50] n=403 |
| assume_dec | 0.37 [0.30, 0.47] n=115 | 0.37 [0.30, 0.47] n=115 |
| assume_val | 0.38 [0.16, 0.62] n=16 | 0.38 [0.16, 0.62] n=16 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_neither | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_invalid | 0.28 [0.14, 0.42] n=57 | 0.28 [0.14, 0.42] n=57 |
| fmt_err | 0.00 [0.00, 0.00] n=687 | 0.00 [0.00, 0.00] n=687 |
| len_chars | 430 [399, 463] n=687 | 430 [399, 463] n=687 |
| len_tok | 118 [110, 127] n=687 | 118 [110, 127] n=687 |

### all

| metric | mortgage-split-lite | mortgage-split-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.05 [-0.01, 0.09] n=287 | 0.05 [-0.01, 0.09] n=287 |
| sim_delta[add] | -0.02 [-0.14, 0.09] n=43 | -0.02 [-0.14, 0.09] n=43 |
| sim_delta[changed] | 0.01 [-0.11, 0.13] n=109 | 0.01 [-0.11, 0.13] n=109 |
| sim_delta[invariant_replace] | 0.12 [0.04, 0.21] n=43 | 0.12 [0.04, 0.21] n=43 |
| sim_delta[noncrossing_replace] | 0.12 [0.00, 0.24] n=43 | 0.12 [0.00, 0.24] n=43 |
| sim_delta[pivotal_replace] | -0.02 [-0.12, 0.08] n=115 | -0.02 [-0.12, 0.08] n=115 |
| sim_delta[remove] | 0.14 [0.04, 0.26] n=43 | 0.14 [0.04, 0.26] n=43 |
| sim_delta[unchanged] | 0.07 [0.01, 0.13] n=178 | 0.07 [0.01, 0.13] n=178 |
| sim_acct | 0.64 [0.57, 0.71] n=287 | 0.64 [0.57, 0.71] n=287 |
| sim_acct[add] | 0.70 [0.57, 0.81] n=43 | 0.70 [0.57, 0.81] n=43 |
| sim_acct[invariant_replace] | 0.84 [0.71, 0.93] n=43 | 0.84 [0.71, 0.93] n=43 |
| sim_acct[noncrossing_replace] | 0.67 [0.55, 0.80] n=43 | 0.67 [0.55, 0.80] n=43 |
| sim_acct[pivotal_replace] | 0.50 [0.40, 0.60] n=115 | 0.50 [0.40, 0.60] n=115 |
| sim_acct[remove] | 0.70 [0.56, 0.83] n=43 | 0.70 [0.56, 0.83] n=43 |
| sim_shuf | 0.59 [0.53, 0.66] n=287 | 0.59 [0.53, 0.66] n=287 |
| sim_shuf[add] | 0.72 [0.57, 0.85] n=43 | 0.72 [0.57, 0.85] n=43 |
| sim_shuf[invariant_replace] | 0.72 [0.58, 0.84] n=43 | 0.72 [0.58, 0.84] n=43 |
| sim_shuf[noncrossing_replace] | 0.56 [0.40, 0.71] n=43 | 0.56 [0.40, 0.71] n=43 |
| sim_shuf[pivotal_replace] | 0.52 [0.43, 0.61] n=115 | 0.52 [0.43, 0.61] n=115 |
| sim_shuf[remove] | 0.56 [0.40, 0.72] n=43 | 0.56 [0.40, 0.72] n=43 |
| sim_gross (acct - noacc) | 0.28 [0.22, 0.34] n=287 | 0.28 [0.22, 0.34] n=287 |
| sim_gross[add] | 0.33 [0.19, 0.48] n=43 | 0.33 [0.19, 0.48] n=43 |
| sim_gross[invariant_replace] | 0.44 [0.31, 0.56] n=43 | 0.44 [0.31, 0.56] n=43 |
| sim_gross[noncrossing_replace] | 0.28 [0.12, 0.46] n=43 | 0.28 [0.12, 0.46] n=43 |
| sim_gross[pivotal_replace] | 0.26 [0.16, 0.35] n=115 | 0.26 [0.16, 0.35] n=115 |
| sim_gross[remove] | 0.12 [0.00, 0.25] n=43 | 0.12 [0.00, 0.25] n=43 |
| sim_noacc | 0.36 [0.31, 0.41] n=287 | 0.36 [0.31, 0.41] n=287 |
| sim_noacc[add] | 0.37 [0.23, 0.52] n=43 | 0.37 [0.23, 0.52] n=43 |
| sim_noacc[invariant_replace] | 0.40 [0.26, 0.51] n=43 | 0.40 [0.26, 0.51] n=43 |
| sim_noacc[noncrossing_replace] | 0.40 [0.23, 0.57] n=43 | 0.40 [0.23, 0.57] n=43 |
| sim_noacc[pivotal_replace] | 0.24 [0.16, 0.32] n=115 | 0.24 [0.16, 0.32] n=115 |
| sim_noacc[remove] | 0.58 [0.44, 0.73] n=43 | 0.58 [0.44, 0.73] n=43 |
| sim_const_unchanged (baseline: frozen decision) | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| sim_const_unchanged[add] | 0.72 [0.60, 0.83] n=43 | 0.72 [0.60, 0.83] n=43 |
| sim_const_unchanged[invariant_replace] | 0.81 [0.69, 0.91] n=43 | 0.81 [0.69, 0.91] n=43 |
| sim_const_unchanged[noncrossing_replace] | 0.74 [0.63, 0.86] n=43 | 0.74 [0.63, 0.86] n=43 |
| sim_const_unchanged[pivotal_replace] | 0.43 [0.34, 0.53] n=115 | 0.43 [0.34, 0.53] n=115 |
| sim_const_unchanged[remove] | 0.70 [0.55, 0.83] n=43 | 0.70 [0.55, 0.83] n=43 |
| sim_oracle (baseline: engine label) | 0.73 [0.68, 0.79] n=287 | 0.73 [0.68, 0.79] n=287 |
| sim_oracle[add] | 0.81 [0.69, 0.93] n=43 | 0.81 [0.69, 0.93] n=43 |
| sim_oracle[invariant_replace] | 0.81 [0.68, 0.93] n=43 | 0.81 [0.68, 0.93] n=43 |
| sim_oracle[noncrossing_replace] | 0.86 [0.76, 0.95] n=43 | 0.86 [0.76, 0.95] n=43 |
| sim_oracle[pivotal_replace] | 0.75 [0.69, 0.81] n=115 | 0.75 [0.69, 0.81] n=115 |
| sim_oracle[remove] | 0.40 [0.24, 0.56] n=43 | 0.40 [0.24, 0.56] n=43 |
| self_V (secondary) | -0.01 [-0.06, 0.03] n=287 | -0.01 [-0.06, 0.03] n=287 |
| self_V[add] | 0.02 [0.00, 0.07] n=43 | 0.02 [0.00, 0.07] n=43 |
| self_V[invariant_replace] | 0.00 [-0.10, 0.11] n=43 | 0.00 [-0.10, 0.11] n=43 |
| self_V[noncrossing_replace] | -0.12 [-0.21, -0.02] n=43 | -0.12 [-0.21, -0.02] n=43 |
| self_V[pivotal_replace] | -0.02 [-0.09, 0.05] n=115 | -0.02 [-0.09, 0.05] n=115 |
| self_V[remove] | 0.05 [-0.07, 0.17] n=43 | 0.05 [-0.07, 0.17] n=43 |
| self_S | 0.74 [0.69, 0.79] n=287 | 0.74 [0.69, 0.79] n=287 |
| self_S[add] | 0.84 [0.74, 0.93] n=43 | 0.84 [0.74, 0.93] n=43 |
| self_S[invariant_replace] | 0.86 [0.75, 0.94] n=43 | 0.86 [0.75, 0.94] n=43 |
| self_S[noncrossing_replace] | 0.67 [0.52, 0.81] n=43 | 0.67 [0.52, 0.81] n=43 |
| self_S[pivotal_replace] | 0.70 [0.61, 0.77] n=115 | 0.70 [0.61, 0.77] n=115 |
| self_S[remove] | 0.72 [0.57, 0.86] n=43 | 0.72 [0.57, 0.86] n=43 |
| self_S_noacc | 0.76 [0.70, 0.80] n=287 | 0.76 [0.70, 0.80] n=287 |
| self_S_noacc[add] | 0.81 [0.70, 0.93] n=43 | 0.81 [0.70, 0.93] n=43 |
| self_S_noacc[invariant_replace] | 0.86 [0.74, 0.96] n=43 | 0.86 [0.74, 0.96] n=43 |
| self_S_noacc[noncrossing_replace] | 0.79 [0.68, 0.89] n=43 | 0.79 [0.68, 0.89] n=43 |
| self_S_noacc[pivotal_replace] | 0.71 [0.66, 0.77] n=115 | 0.71 [0.66, 0.77] n=115 |
| self_S_noacc[remove] | 0.67 [0.54, 0.81] n=43 | 0.67 [0.54, 0.81] n=43 |
| self_G | 0.01 [-0.07, 0.08] n=287 | 0.01 [-0.07, 0.08] n=287 |
| bank_unchanged | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| acc_maj | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_maj[interaction] | 0.80 [0.64, 0.92] n=55 | 0.80 [0.64, 0.92] n=55 |
| acc_mean | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_class[approve] | 0.66 [0.57, 0.75] n=202 | 0.66 [0.57, 0.75] n=202 |
| acc_class[cannot determine] | 0.03 [0.00, 0.08] n=70 | 0.03 [0.00, 0.08] n=70 |
| acc_class[deny] | 0.93 [0.89, 0.97] n=257 | 0.93 [0.89, 0.97] n=257 |
| repeat_disagree | 0.18 [0.14, 0.22] n=529 | 0.18 [0.14, 0.22] n=529 |
| flip | 0.76 [0.68, 0.83] n=115 | 0.76 [0.68, 0.83] n=115 |
| flip~noise | 0.28 [0.19, 0.37] n=115 | 0.28 [0.19, 0.37] n=115 |
| flip[approve->deny] | 0.90 [0.80, 0.98] n=51 | 0.90 [0.80, 0.98] n=51 |
| flip[approve->deny]~noise | 0.29 [0.17, 0.43] n=51 | 0.29 [0.17, 0.43] n=51 |
| flip[deny->approve] | 0.64 [0.52, 0.77] n=64 | 0.64 [0.52, 0.77] n=64 |
| flip[deny->approve]~noise | 0.27 [0.16, 0.38] n=64 | 0.27 [0.16, 0.38] n=64 |
| flip_to_cd | 0.00 [0.00, 0.00] n=115 | 0.00 [0.00, 0.00] n=115 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=51 | 0.00 [0.00, 0.00] n=51 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=64 | 0.00 [0.00, 0.00] n=64 |
| cf_pair_acc | 0.56 [0.46, 0.65] n=115 | 0.56 [0.46, 0.65] n=115 |
| invariance | 0.84 [0.76, 0.91] n=115 | 0.84 [0.76, 0.91] n=115 |
| invariance~noise | 0.18 [0.12, 0.24] n=115 | 0.18 [0.12, 0.24] n=115 |
| inv_pair_acc | 0.74 [0.65, 0.82] n=115 | 0.74 [0.65, 0.82] n=115 |
| expl_valid | 0.24 [0.19, 0.28] n=523 | 0.24 [0.19, 0.28] n=523 |
| acct_consistent | 0.72 [0.68, 0.77] n=460 | 0.72 [0.68, 0.77] n=460 |
| expl_minimal | 0.25 [0.20, 0.30] n=453 | 0.25 [0.20, 0.30] n=453 |
| cite_distractor | 0.39 [0.35, 0.44] n=529 | 0.39 [0.35, 0.44] n=529 |
| cite_p_nec | 0.34 [0.30, 0.37] n=529 | 0.34 [0.30, 0.37] n=529 |
| cite_r_nec | 0.44 [0.38, 0.50] n=403 | 0.44 [0.38, 0.50] n=403 |
| assume_dec | 0.37 [0.30, 0.47] n=115 | 0.37 [0.30, 0.47] n=115 |
| assume_val | 0.38 [0.16, 0.62] n=16 | 0.38 [0.16, 0.62] n=16 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_neither | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_invalid | 0.28 [0.14, 0.42] n=57 | 0.28 [0.14, 0.42] n=57 |
| fmt_err | 0.00 [0.00, 0.00] n=687 | 0.00 [0.00, 0.00] n=687 |
| len_chars | 430 [399, 463] n=687 | 430 [399, 463] n=687 |
| len_tok | 118 [110, 127] n=687 | 118 [110, 127] n=687 |

### secondary: slice=unseen_family_train_vocab

| metric | mortgage-split-lite | mortgage-split-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.05 [-0.01, 0.09] n=287 | 0.05 [-0.01, 0.09] n=287 |
| sim_delta[add] | -0.02 [-0.14, 0.09] n=43 | -0.02 [-0.14, 0.09] n=43 |
| sim_delta[changed] | 0.01 [-0.11, 0.13] n=109 | 0.01 [-0.11, 0.13] n=109 |
| sim_delta[invariant_replace] | 0.12 [0.04, 0.21] n=43 | 0.12 [0.04, 0.21] n=43 |
| sim_delta[noncrossing_replace] | 0.12 [0.00, 0.24] n=43 | 0.12 [0.00, 0.24] n=43 |
| sim_delta[pivotal_replace] | -0.02 [-0.12, 0.08] n=115 | -0.02 [-0.12, 0.08] n=115 |
| sim_delta[remove] | 0.14 [0.04, 0.26] n=43 | 0.14 [0.04, 0.26] n=43 |
| sim_delta[unchanged] | 0.07 [0.01, 0.13] n=178 | 0.07 [0.01, 0.13] n=178 |
| sim_acct | 0.64 [0.57, 0.71] n=287 | 0.64 [0.57, 0.71] n=287 |
| sim_acct[add] | 0.70 [0.57, 0.81] n=43 | 0.70 [0.57, 0.81] n=43 |
| sim_acct[invariant_replace] | 0.84 [0.71, 0.93] n=43 | 0.84 [0.71, 0.93] n=43 |
| sim_acct[noncrossing_replace] | 0.67 [0.55, 0.80] n=43 | 0.67 [0.55, 0.80] n=43 |
| sim_acct[pivotal_replace] | 0.50 [0.40, 0.60] n=115 | 0.50 [0.40, 0.60] n=115 |
| sim_acct[remove] | 0.70 [0.56, 0.83] n=43 | 0.70 [0.56, 0.83] n=43 |
| sim_shuf | 0.59 [0.53, 0.66] n=287 | 0.59 [0.53, 0.66] n=287 |
| sim_shuf[add] | 0.72 [0.57, 0.85] n=43 | 0.72 [0.57, 0.85] n=43 |
| sim_shuf[invariant_replace] | 0.72 [0.58, 0.84] n=43 | 0.72 [0.58, 0.84] n=43 |
| sim_shuf[noncrossing_replace] | 0.56 [0.40, 0.71] n=43 | 0.56 [0.40, 0.71] n=43 |
| sim_shuf[pivotal_replace] | 0.52 [0.43, 0.61] n=115 | 0.52 [0.43, 0.61] n=115 |
| sim_shuf[remove] | 0.56 [0.40, 0.72] n=43 | 0.56 [0.40, 0.72] n=43 |
| sim_gross (acct - noacc) | 0.28 [0.22, 0.34] n=287 | 0.28 [0.22, 0.34] n=287 |
| sim_gross[add] | 0.33 [0.19, 0.48] n=43 | 0.33 [0.19, 0.48] n=43 |
| sim_gross[invariant_replace] | 0.44 [0.31, 0.56] n=43 | 0.44 [0.31, 0.56] n=43 |
| sim_gross[noncrossing_replace] | 0.28 [0.12, 0.46] n=43 | 0.28 [0.12, 0.46] n=43 |
| sim_gross[pivotal_replace] | 0.26 [0.16, 0.35] n=115 | 0.26 [0.16, 0.35] n=115 |
| sim_gross[remove] | 0.12 [0.00, 0.25] n=43 | 0.12 [0.00, 0.25] n=43 |
| sim_noacc | 0.36 [0.31, 0.41] n=287 | 0.36 [0.31, 0.41] n=287 |
| sim_noacc[add] | 0.37 [0.23, 0.52] n=43 | 0.37 [0.23, 0.52] n=43 |
| sim_noacc[invariant_replace] | 0.40 [0.26, 0.51] n=43 | 0.40 [0.26, 0.51] n=43 |
| sim_noacc[noncrossing_replace] | 0.40 [0.23, 0.57] n=43 | 0.40 [0.23, 0.57] n=43 |
| sim_noacc[pivotal_replace] | 0.24 [0.16, 0.32] n=115 | 0.24 [0.16, 0.32] n=115 |
| sim_noacc[remove] | 0.58 [0.44, 0.73] n=43 | 0.58 [0.44, 0.73] n=43 |
| sim_const_unchanged (baseline: frozen decision) | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| sim_const_unchanged[add] | 0.72 [0.60, 0.83] n=43 | 0.72 [0.60, 0.83] n=43 |
| sim_const_unchanged[invariant_replace] | 0.81 [0.69, 0.91] n=43 | 0.81 [0.69, 0.91] n=43 |
| sim_const_unchanged[noncrossing_replace] | 0.74 [0.63, 0.86] n=43 | 0.74 [0.63, 0.86] n=43 |
| sim_const_unchanged[pivotal_replace] | 0.43 [0.34, 0.53] n=115 | 0.43 [0.34, 0.53] n=115 |
| sim_const_unchanged[remove] | 0.70 [0.55, 0.83] n=43 | 0.70 [0.55, 0.83] n=43 |
| sim_oracle (baseline: engine label) | 0.73 [0.68, 0.79] n=287 | 0.73 [0.68, 0.79] n=287 |
| sim_oracle[add] | 0.81 [0.69, 0.93] n=43 | 0.81 [0.69, 0.93] n=43 |
| sim_oracle[invariant_replace] | 0.81 [0.68, 0.93] n=43 | 0.81 [0.68, 0.93] n=43 |
| sim_oracle[noncrossing_replace] | 0.86 [0.76, 0.95] n=43 | 0.86 [0.76, 0.95] n=43 |
| sim_oracle[pivotal_replace] | 0.75 [0.69, 0.81] n=115 | 0.75 [0.69, 0.81] n=115 |
| sim_oracle[remove] | 0.40 [0.24, 0.56] n=43 | 0.40 [0.24, 0.56] n=43 |
| self_V (secondary) | -0.01 [-0.06, 0.03] n=287 | -0.01 [-0.06, 0.03] n=287 |
| self_V[add] | 0.02 [0.00, 0.07] n=43 | 0.02 [0.00, 0.07] n=43 |
| self_V[invariant_replace] | 0.00 [-0.10, 0.11] n=43 | 0.00 [-0.10, 0.11] n=43 |
| self_V[noncrossing_replace] | -0.12 [-0.21, -0.02] n=43 | -0.12 [-0.21, -0.02] n=43 |
| self_V[pivotal_replace] | -0.02 [-0.09, 0.05] n=115 | -0.02 [-0.09, 0.05] n=115 |
| self_V[remove] | 0.05 [-0.07, 0.17] n=43 | 0.05 [-0.07, 0.17] n=43 |
| self_S | 0.74 [0.69, 0.79] n=287 | 0.74 [0.69, 0.79] n=287 |
| self_S[add] | 0.84 [0.74, 0.93] n=43 | 0.84 [0.74, 0.93] n=43 |
| self_S[invariant_replace] | 0.86 [0.75, 0.94] n=43 | 0.86 [0.75, 0.94] n=43 |
| self_S[noncrossing_replace] | 0.67 [0.52, 0.81] n=43 | 0.67 [0.52, 0.81] n=43 |
| self_S[pivotal_replace] | 0.70 [0.61, 0.77] n=115 | 0.70 [0.61, 0.77] n=115 |
| self_S[remove] | 0.72 [0.57, 0.86] n=43 | 0.72 [0.57, 0.86] n=43 |
| self_S_noacc | 0.76 [0.70, 0.80] n=287 | 0.76 [0.70, 0.80] n=287 |
| self_S_noacc[add] | 0.81 [0.70, 0.93] n=43 | 0.81 [0.70, 0.93] n=43 |
| self_S_noacc[invariant_replace] | 0.86 [0.74, 0.96] n=43 | 0.86 [0.74, 0.96] n=43 |
| self_S_noacc[noncrossing_replace] | 0.79 [0.68, 0.89] n=43 | 0.79 [0.68, 0.89] n=43 |
| self_S_noacc[pivotal_replace] | 0.71 [0.66, 0.77] n=115 | 0.71 [0.66, 0.77] n=115 |
| self_S_noacc[remove] | 0.67 [0.54, 0.81] n=43 | 0.67 [0.54, 0.81] n=43 |
| self_G | 0.01 [-0.07, 0.08] n=287 | 0.01 [-0.07, 0.08] n=287 |
| bank_unchanged | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| acc_maj | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_maj[interaction] | 0.80 [0.64, 0.92] n=55 | 0.80 [0.64, 0.92] n=55 |
| acc_mean | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_class[approve] | 0.66 [0.57, 0.75] n=202 | 0.66 [0.57, 0.75] n=202 |
| acc_class[cannot determine] | 0.03 [0.00, 0.08] n=70 | 0.03 [0.00, 0.08] n=70 |
| acc_class[deny] | 0.93 [0.89, 0.97] n=257 | 0.93 [0.89, 0.97] n=257 |
| repeat_disagree | 0.18 [0.14, 0.22] n=529 | 0.18 [0.14, 0.22] n=529 |
| flip | 0.76 [0.68, 0.83] n=115 | 0.76 [0.68, 0.83] n=115 |
| flip~noise | 0.28 [0.19, 0.37] n=115 | 0.28 [0.19, 0.37] n=115 |
| flip[approve->deny] | 0.90 [0.80, 0.98] n=51 | 0.90 [0.80, 0.98] n=51 |
| flip[approve->deny]~noise | 0.29 [0.17, 0.43] n=51 | 0.29 [0.17, 0.43] n=51 |
| flip[deny->approve] | 0.64 [0.52, 0.77] n=64 | 0.64 [0.52, 0.77] n=64 |
| flip[deny->approve]~noise | 0.27 [0.16, 0.38] n=64 | 0.27 [0.16, 0.38] n=64 |
| flip_to_cd | 0.00 [0.00, 0.00] n=115 | 0.00 [0.00, 0.00] n=115 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=51 | 0.00 [0.00, 0.00] n=51 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=64 | 0.00 [0.00, 0.00] n=64 |
| cf_pair_acc | 0.56 [0.46, 0.65] n=115 | 0.56 [0.46, 0.65] n=115 |
| invariance | 0.84 [0.76, 0.91] n=115 | 0.84 [0.76, 0.91] n=115 |
| invariance~noise | 0.18 [0.12, 0.24] n=115 | 0.18 [0.12, 0.24] n=115 |
| inv_pair_acc | 0.74 [0.65, 0.82] n=115 | 0.74 [0.65, 0.82] n=115 |
| expl_valid | 0.24 [0.19, 0.28] n=523 | 0.24 [0.19, 0.28] n=523 |
| acct_consistent | 0.72 [0.68, 0.77] n=460 | 0.72 [0.68, 0.77] n=460 |
| expl_minimal | 0.25 [0.20, 0.30] n=453 | 0.25 [0.20, 0.30] n=453 |
| cite_distractor | 0.39 [0.35, 0.44] n=529 | 0.39 [0.35, 0.44] n=529 |
| cite_p_nec | 0.34 [0.30, 0.37] n=529 | 0.34 [0.30, 0.37] n=529 |
| cite_r_nec | 0.44 [0.38, 0.50] n=403 | 0.44 [0.38, 0.50] n=403 |
| assume_dec | 0.37 [0.30, 0.47] n=115 | 0.37 [0.30, 0.47] n=115 |
| assume_val | 0.38 [0.16, 0.62] n=16 | 0.38 [0.16, 0.62] n=16 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_neither | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_invalid | 0.28 [0.14, 0.42] n=57 | 0.28 [0.14, 0.42] n=57 |
| fmt_err | 0.00 [0.00, 0.00] n=687 | 0.00 [0.00, 0.00] n=687 |
| len_chars | 430 [399, 463] n=687 | 430 [399, 463] n=687 |
| len_tok | 118 [110, 127] n=687 | 118 [110, 127] n=687 |

### secondary: view=prose

| metric | mortgage-split-lite | mortgage-split-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.05 [-0.01, 0.09] n=287 | 0.05 [-0.01, 0.09] n=287 |
| sim_delta[add] | -0.02 [-0.14, 0.09] n=43 | -0.02 [-0.14, 0.09] n=43 |
| sim_delta[changed] | 0.01 [-0.11, 0.13] n=109 | 0.01 [-0.11, 0.13] n=109 |
| sim_delta[invariant_replace] | 0.12 [0.04, 0.21] n=43 | 0.12 [0.04, 0.21] n=43 |
| sim_delta[noncrossing_replace] | 0.12 [0.00, 0.24] n=43 | 0.12 [0.00, 0.24] n=43 |
| sim_delta[pivotal_replace] | -0.02 [-0.12, 0.08] n=115 | -0.02 [-0.12, 0.08] n=115 |
| sim_delta[remove] | 0.14 [0.04, 0.26] n=43 | 0.14 [0.04, 0.26] n=43 |
| sim_delta[unchanged] | 0.07 [0.01, 0.13] n=178 | 0.07 [0.01, 0.13] n=178 |
| sim_acct | 0.64 [0.57, 0.71] n=287 | 0.64 [0.57, 0.71] n=287 |
| sim_acct[add] | 0.70 [0.57, 0.81] n=43 | 0.70 [0.57, 0.81] n=43 |
| sim_acct[invariant_replace] | 0.84 [0.71, 0.93] n=43 | 0.84 [0.71, 0.93] n=43 |
| sim_acct[noncrossing_replace] | 0.67 [0.55, 0.80] n=43 | 0.67 [0.55, 0.80] n=43 |
| sim_acct[pivotal_replace] | 0.50 [0.40, 0.60] n=115 | 0.50 [0.40, 0.60] n=115 |
| sim_acct[remove] | 0.70 [0.56, 0.83] n=43 | 0.70 [0.56, 0.83] n=43 |
| sim_shuf | 0.59 [0.53, 0.66] n=287 | 0.59 [0.53, 0.66] n=287 |
| sim_shuf[add] | 0.72 [0.57, 0.85] n=43 | 0.72 [0.57, 0.85] n=43 |
| sim_shuf[invariant_replace] | 0.72 [0.58, 0.84] n=43 | 0.72 [0.58, 0.84] n=43 |
| sim_shuf[noncrossing_replace] | 0.56 [0.40, 0.71] n=43 | 0.56 [0.40, 0.71] n=43 |
| sim_shuf[pivotal_replace] | 0.52 [0.43, 0.61] n=115 | 0.52 [0.43, 0.61] n=115 |
| sim_shuf[remove] | 0.56 [0.40, 0.72] n=43 | 0.56 [0.40, 0.72] n=43 |
| sim_gross (acct - noacc) | 0.28 [0.22, 0.34] n=287 | 0.28 [0.22, 0.34] n=287 |
| sim_gross[add] | 0.33 [0.19, 0.48] n=43 | 0.33 [0.19, 0.48] n=43 |
| sim_gross[invariant_replace] | 0.44 [0.31, 0.56] n=43 | 0.44 [0.31, 0.56] n=43 |
| sim_gross[noncrossing_replace] | 0.28 [0.12, 0.46] n=43 | 0.28 [0.12, 0.46] n=43 |
| sim_gross[pivotal_replace] | 0.26 [0.16, 0.35] n=115 | 0.26 [0.16, 0.35] n=115 |
| sim_gross[remove] | 0.12 [0.00, 0.25] n=43 | 0.12 [0.00, 0.25] n=43 |
| sim_noacc | 0.36 [0.31, 0.41] n=287 | 0.36 [0.31, 0.41] n=287 |
| sim_noacc[add] | 0.37 [0.23, 0.52] n=43 | 0.37 [0.23, 0.52] n=43 |
| sim_noacc[invariant_replace] | 0.40 [0.26, 0.51] n=43 | 0.40 [0.26, 0.51] n=43 |
| sim_noacc[noncrossing_replace] | 0.40 [0.23, 0.57] n=43 | 0.40 [0.23, 0.57] n=43 |
| sim_noacc[pivotal_replace] | 0.24 [0.16, 0.32] n=115 | 0.24 [0.16, 0.32] n=115 |
| sim_noacc[remove] | 0.58 [0.44, 0.73] n=43 | 0.58 [0.44, 0.73] n=43 |
| sim_const_unchanged (baseline: frozen decision) | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| sim_const_unchanged[add] | 0.72 [0.60, 0.83] n=43 | 0.72 [0.60, 0.83] n=43 |
| sim_const_unchanged[invariant_replace] | 0.81 [0.69, 0.91] n=43 | 0.81 [0.69, 0.91] n=43 |
| sim_const_unchanged[noncrossing_replace] | 0.74 [0.63, 0.86] n=43 | 0.74 [0.63, 0.86] n=43 |
| sim_const_unchanged[pivotal_replace] | 0.43 [0.34, 0.53] n=115 | 0.43 [0.34, 0.53] n=115 |
| sim_const_unchanged[remove] | 0.70 [0.55, 0.83] n=43 | 0.70 [0.55, 0.83] n=43 |
| sim_oracle (baseline: engine label) | 0.73 [0.68, 0.79] n=287 | 0.73 [0.68, 0.79] n=287 |
| sim_oracle[add] | 0.81 [0.69, 0.93] n=43 | 0.81 [0.69, 0.93] n=43 |
| sim_oracle[invariant_replace] | 0.81 [0.68, 0.93] n=43 | 0.81 [0.68, 0.93] n=43 |
| sim_oracle[noncrossing_replace] | 0.86 [0.76, 0.95] n=43 | 0.86 [0.76, 0.95] n=43 |
| sim_oracle[pivotal_replace] | 0.75 [0.69, 0.81] n=115 | 0.75 [0.69, 0.81] n=115 |
| sim_oracle[remove] | 0.40 [0.24, 0.56] n=43 | 0.40 [0.24, 0.56] n=43 |
| self_V (secondary) | -0.01 [-0.06, 0.03] n=287 | -0.01 [-0.06, 0.03] n=287 |
| self_V[add] | 0.02 [0.00, 0.07] n=43 | 0.02 [0.00, 0.07] n=43 |
| self_V[invariant_replace] | 0.00 [-0.10, 0.11] n=43 | 0.00 [-0.10, 0.11] n=43 |
| self_V[noncrossing_replace] | -0.12 [-0.21, -0.02] n=43 | -0.12 [-0.21, -0.02] n=43 |
| self_V[pivotal_replace] | -0.02 [-0.09, 0.05] n=115 | -0.02 [-0.09, 0.05] n=115 |
| self_V[remove] | 0.05 [-0.07, 0.17] n=43 | 0.05 [-0.07, 0.17] n=43 |
| self_S | 0.74 [0.69, 0.79] n=287 | 0.74 [0.69, 0.79] n=287 |
| self_S[add] | 0.84 [0.74, 0.93] n=43 | 0.84 [0.74, 0.93] n=43 |
| self_S[invariant_replace] | 0.86 [0.75, 0.94] n=43 | 0.86 [0.75, 0.94] n=43 |
| self_S[noncrossing_replace] | 0.67 [0.52, 0.81] n=43 | 0.67 [0.52, 0.81] n=43 |
| self_S[pivotal_replace] | 0.70 [0.61, 0.77] n=115 | 0.70 [0.61, 0.77] n=115 |
| self_S[remove] | 0.72 [0.57, 0.86] n=43 | 0.72 [0.57, 0.86] n=43 |
| self_S_noacc | 0.76 [0.70, 0.80] n=287 | 0.76 [0.70, 0.80] n=287 |
| self_S_noacc[add] | 0.81 [0.70, 0.93] n=43 | 0.81 [0.70, 0.93] n=43 |
| self_S_noacc[invariant_replace] | 0.86 [0.74, 0.96] n=43 | 0.86 [0.74, 0.96] n=43 |
| self_S_noacc[noncrossing_replace] | 0.79 [0.68, 0.89] n=43 | 0.79 [0.68, 0.89] n=43 |
| self_S_noacc[pivotal_replace] | 0.71 [0.66, 0.77] n=115 | 0.71 [0.66, 0.77] n=115 |
| self_S_noacc[remove] | 0.67 [0.54, 0.81] n=43 | 0.67 [0.54, 0.81] n=43 |
| self_G | 0.01 [-0.07, 0.08] n=287 | 0.01 [-0.07, 0.08] n=287 |
| bank_unchanged | 0.62 [0.56, 0.68] n=287 | 0.62 [0.56, 0.68] n=287 |
| acc_maj | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_maj[interaction] | 0.80 [0.64, 0.92] n=55 | 0.80 [0.64, 0.92] n=55 |
| acc_mean | 0.80 [0.71, 0.88] n=115 | 0.80 [0.71, 0.88] n=115 |
| acc_class[approve] | 0.66 [0.57, 0.75] n=202 | 0.66 [0.57, 0.75] n=202 |
| acc_class[cannot determine] | 0.03 [0.00, 0.08] n=70 | 0.03 [0.00, 0.08] n=70 |
| acc_class[deny] | 0.93 [0.89, 0.97] n=257 | 0.93 [0.89, 0.97] n=257 |
| repeat_disagree | 0.18 [0.14, 0.22] n=529 | 0.18 [0.14, 0.22] n=529 |
| flip | 0.76 [0.68, 0.83] n=115 | 0.76 [0.68, 0.83] n=115 |
| flip~noise | 0.28 [0.19, 0.37] n=115 | 0.28 [0.19, 0.37] n=115 |
| flip[approve->deny] | 0.90 [0.80, 0.98] n=51 | 0.90 [0.80, 0.98] n=51 |
| flip[approve->deny]~noise | 0.29 [0.17, 0.43] n=51 | 0.29 [0.17, 0.43] n=51 |
| flip[deny->approve] | 0.64 [0.52, 0.77] n=64 | 0.64 [0.52, 0.77] n=64 |
| flip[deny->approve]~noise | 0.27 [0.16, 0.38] n=64 | 0.27 [0.16, 0.38] n=64 |
| flip_to_cd | 0.00 [0.00, 0.00] n=115 | 0.00 [0.00, 0.00] n=115 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=51 | 0.00 [0.00, 0.00] n=51 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=64 | 0.00 [0.00, 0.00] n=64 |
| cf_pair_acc | 0.56 [0.46, 0.65] n=115 | 0.56 [0.46, 0.65] n=115 |
| invariance | 0.84 [0.76, 0.91] n=115 | 0.84 [0.76, 0.91] n=115 |
| invariance~noise | 0.18 [0.12, 0.24] n=115 | 0.18 [0.12, 0.24] n=115 |
| inv_pair_acc | 0.74 [0.65, 0.82] n=115 | 0.74 [0.65, 0.82] n=115 |
| expl_valid | 0.24 [0.19, 0.28] n=523 | 0.24 [0.19, 0.28] n=523 |
| acct_consistent | 0.72 [0.68, 0.77] n=460 | 0.72 [0.68, 0.77] n=460 |
| expl_minimal | 0.25 [0.20, 0.30] n=453 | 0.25 [0.20, 0.30] n=453 |
| cite_distractor | 0.39 [0.35, 0.44] n=529 | 0.39 [0.35, 0.44] n=529 |
| cite_p_nec | 0.34 [0.30, 0.37] n=529 | 0.34 [0.30, 0.37] n=529 |
| cite_r_nec | 0.44 [0.38, 0.50] n=403 | 0.44 [0.38, 0.50] n=403 |
| assume_dec | 0.37 [0.30, 0.47] n=115 | 0.37 [0.30, 0.47] n=115 |
| assume_val | 0.38 [0.16, 0.62] n=16 | 0.38 [0.16, 0.62] n=16 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_neither | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=16 | 1.00 [1.00, 1.00] n=16 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| bnd_invalid | 0.28 [0.14, 0.42] n=57 | 0.28 [0.14, 0.42] n=57 |
| fmt_err | 0.00 [0.00, 0.00] n=687 | 0.00 [0.00, 0.00] n=687 |
| len_chars | 430 [399, 463] n=687 | 430 [399, 463] n=687 |
| len_tok | 118 [110, 127] n=687 | 118 [110, 127] n=687 |

### descriptive splits by correctness (all)

| metric | mortgage-split-lite | mortgage-split-lite mortgage |
|---|---|---|
| sim_delta|correct | 0.04 [-0.02, 0.11] n=203 | 0.04 [-0.02, 0.11] n=203 |
| sim_delta|wrong | 0.05 [-0.05, 0.12] n=84 | 0.05 [-0.05, 0.12] n=84 |
| sim_delta[add]|correct | 0.00 [-0.24, 0.31] n=16 | 0.00 [-0.24, 0.31] n=16 |
| sim_delta[add]|wrong | -0.04 [-0.24, 0.13] n=27 | -0.04 [-0.24, 0.13] n=27 |
| sim_delta[changed]|correct | 0.00 [-0.15, 0.15] n=78 | 0.00 [-0.15, 0.15] n=78 |
| sim_delta[changed]|wrong | 0.03 [-0.17, 0.16] n=31 | 0.03 [-0.17, 0.16] n=31 |
| sim_delta[invariant_replace]|correct | 0.13 [0.03, 0.24] n=31 | 0.13 [0.03, 0.24] n=31 |
| sim_delta[invariant_replace]|wrong | 0.08 [0.00, 0.33] n=12 | 0.08 [0.00, 0.33] n=12 |
| sim_delta[noncrossing_replace]|correct | 0.06 [-0.09, 0.21] n=32 | 0.06 [-0.09, 0.21] n=32 |
| sim_delta[noncrossing_replace]|wrong | 0.27 [0.09, 0.47] n=11 | 0.27 [0.09, 0.47] n=11 |
| sim_delta[pivotal_replace]|correct | -0.03 [-0.15, 0.09] n=92 | -0.03 [-0.15, 0.09] n=92 |
| sim_delta[pivotal_replace]|wrong | 0.04 [0.00, 0.14] n=23 | 0.04 [0.00, 0.14] n=23 |
| sim_delta[remove]|correct | 0.19 [0.06, 0.37] n=32 | 0.19 [0.06, 0.37] n=32 |
| sim_delta[remove]|wrong | 0.00 [0.00, 0.00] n=11 | 0.00 [0.00, 0.00] n=11 |
| sim_delta[unchanged]|correct | 0.07 [0.00, 0.15] n=125 | 0.07 [0.00, 0.15] n=125 |
| sim_delta[unchanged]|wrong | 0.06 [-0.03, 0.15] n=53 | 0.06 [-0.03, 0.15] n=53 |
| sim_acct|correct | 0.62 [0.55, 0.69] n=203 | 0.62 [0.55, 0.69] n=203 |
| sim_acct|wrong | 0.68 [0.57, 0.78] n=84 | 0.68 [0.57, 0.78] n=84 |
| sim_acct[add]|correct | 0.81 [0.67, 1.00] n=16 | 0.81 [0.67, 1.00] n=16 |
| sim_acct[add]|wrong | 0.63 [0.45, 0.83] n=27 | 0.63 [0.45, 0.83] n=27 |
| sim_acct[invariant_replace]|correct | 0.94 [0.85, 1.00] n=31 | 0.94 [0.85, 1.00] n=31 |
| sim_acct[invariant_replace]|wrong | 0.58 [0.27, 0.82] n=12 | 0.58 [0.27, 0.82] n=12 |
| sim_acct[noncrossing_replace]|correct | 0.72 [0.56, 0.88] n=32 | 0.72 [0.56, 0.88] n=32 |
| sim_acct[noncrossing_replace]|wrong | 0.55 [0.18, 0.85] n=11 | 0.55 [0.18, 0.85] n=11 |
| sim_acct[pivotal_replace]|correct | 0.40 [0.29, 0.52] n=92 | 0.40 [0.29, 0.52] n=92 |
| sim_acct[pivotal_replace]|wrong | 0.91 [0.81, 1.00] n=23 | 0.91 [0.81, 1.00] n=23 |
| sim_acct[remove]|correct | 0.75 [0.56, 0.89] n=32 | 0.75 [0.56, 0.89] n=32 |
| sim_acct[remove]|wrong | 0.55 [0.27, 0.80] n=11 | 0.55 [0.27, 0.80] n=11 |
| sim_shuf|correct | 0.58 [0.50, 0.65] n=203 | 0.58 [0.50, 0.65] n=203 |
| sim_shuf|wrong | 0.63 [0.54, 0.75] n=84 | 0.63 [0.54, 0.75] n=84 |
| sim_shuf[add]|correct | 0.81 [0.62, 1.00] n=16 | 0.81 [0.62, 1.00] n=16 |
| sim_shuf[add]|wrong | 0.67 [0.48, 0.85] n=27 | 0.67 [0.48, 0.85] n=27 |
| sim_shuf[invariant_replace]|correct | 0.81 [0.65, 0.94] n=31 | 0.81 [0.65, 0.94] n=31 |
| sim_shuf[invariant_replace]|wrong | 0.50 [0.11, 0.75] n=12 | 0.50 [0.11, 0.75] n=12 |
| sim_shuf[noncrossing_replace]|correct | 0.66 [0.45, 0.85] n=32 | 0.66 [0.45, 0.85] n=32 |
| sim_shuf[noncrossing_replace]|wrong | 0.27 [0.08, 0.50] n=11 | 0.27 [0.08, 0.50] n=11 |
| sim_shuf[pivotal_replace]|correct | 0.43 [0.33, 0.54] n=92 | 0.43 [0.33, 0.54] n=92 |
| sim_shuf[pivotal_replace]|wrong | 0.87 [0.75, 1.00] n=23 | 0.87 [0.75, 1.00] n=23 |
| sim_shuf[remove]|correct | 0.56 [0.37, 0.74] n=32 | 0.56 [0.37, 0.74] n=32 |
| sim_shuf[remove]|wrong | 0.55 [0.27, 0.80] n=11 | 0.55 [0.27, 0.80] n=11 |
| sim_gross|correct | 0.26 [0.18, 0.32] n=203 | 0.26 [0.18, 0.32] n=203 |
| sim_gross|wrong | 0.33 [0.24, 0.41] n=84 | 0.33 [0.24, 0.41] n=84 |
| sim_gross[add]|correct | 0.50 [0.21, 0.79] n=16 | 0.50 [0.21, 0.79] n=16 |
| sim_gross[add]|wrong | 0.22 [0.08, 0.38] n=27 | 0.22 [0.08, 0.38] n=27 |
| sim_gross[invariant_replace]|correct | 0.48 [0.32, 0.68] n=31 | 0.48 [0.32, 0.68] n=31 |
| sim_gross[invariant_replace]|wrong | 0.33 [0.10, 0.64] n=12 | 0.33 [0.10, 0.64] n=12 |
| sim_gross[noncrossing_replace]|correct | 0.19 [0.08, 0.35] n=32 | 0.19 [0.08, 0.35] n=32 |
| sim_gross[noncrossing_replace]|wrong | 0.55 [0.18, 0.85] n=11 | 0.55 [0.18, 0.85] n=11 |
| sim_gross[pivotal_replace]|correct | 0.21 [0.10, 0.31] n=92 | 0.21 [0.10, 0.31] n=92 |
| sim_gross[pivotal_replace]|wrong | 0.48 [0.32, 0.65] n=23 | 0.48 [0.32, 0.65] n=23 |
| sim_gross[remove]|correct | 0.12 [0.00, 0.28] n=32 | 0.12 [0.00, 0.28] n=32 |
| sim_gross[remove]|wrong | 0.09 [0.00, 0.30] n=11 | 0.09 [0.00, 0.30] n=11 |
| sim_noacc|correct | 0.36 [0.30, 0.43] n=203 | 0.36 [0.30, 0.43] n=203 |
| sim_noacc|wrong | 0.35 [0.27, 0.44] n=84 | 0.35 [0.27, 0.44] n=84 |
| sim_noacc[add]|correct | 0.31 [0.07, 0.58] n=16 | 0.31 [0.07, 0.58] n=16 |
| sim_noacc[add]|wrong | 0.41 [0.24, 0.61] n=27 | 0.41 [0.24, 0.61] n=27 |
| sim_noacc[invariant_replace]|correct | 0.45 [0.27, 0.62] n=31 | 0.45 [0.27, 0.62] n=31 |
| sim_noacc[invariant_replace]|wrong | 0.25 [0.00, 0.50] n=12 | 0.25 [0.00, 0.50] n=12 |
| sim_noacc[noncrossing_replace]|correct | 0.53 [0.33, 0.74] n=32 | 0.53 [0.33, 0.74] n=32 |
| sim_noacc[noncrossing_replace]|wrong | 0.00 [0.00, 0.00] n=11 | 0.00 [0.00, 0.00] n=11 |
| sim_noacc[pivotal_replace]|correct | 0.20 [0.10, 0.29] n=92 | 0.20 [0.10, 0.29] n=92 |
| sim_noacc[pivotal_replace]|wrong | 0.43 [0.30, 0.57] n=23 | 0.43 [0.30, 0.57] n=23 |
| sim_noacc[remove]|correct | 0.62 [0.44, 0.79] n=32 | 0.62 [0.44, 0.79] n=32 |
| sim_noacc[remove]|wrong | 0.45 [0.18, 0.70] n=11 | 0.45 [0.18, 0.70] n=11 |
| sim_const_unchanged|correct | 0.62 [0.56, 0.67] n=203 | 0.62 [0.56, 0.67] n=203 |
| sim_const_unchanged|wrong | 0.63 [0.53, 0.74] n=84 | 0.63 [0.53, 0.74] n=84 |
| sim_const_unchanged[add]|correct | 0.88 [0.72, 1.00] n=16 | 0.88 [0.72, 1.00] n=16 |
| sim_const_unchanged[add]|wrong | 0.63 [0.44, 0.79] n=27 | 0.63 [0.44, 0.79] n=27 |
| sim_const_unchanged[invariant_replace]|correct | 0.94 [0.85, 1.00] n=31 | 0.94 [0.85, 1.00] n=31 |
| sim_const_unchanged[invariant_replace]|wrong | 0.50 [0.11, 0.75] n=12 | 0.50 [0.11, 0.75] n=12 |
| sim_const_unchanged[noncrossing_replace]|correct | 0.91 [0.81, 1.00] n=32 | 0.91 [0.81, 1.00] n=32 |
| sim_const_unchanged[noncrossing_replace]|wrong | 0.27 [0.08, 0.50] n=11 | 0.27 [0.08, 0.50] n=11 |
| sim_const_unchanged[pivotal_replace]|correct | 0.30 [0.23, 0.38] n=92 | 0.30 [0.23, 0.38] n=92 |
| sim_const_unchanged[pivotal_replace]|wrong | 0.96 [0.86, 1.00] n=23 | 0.96 [0.86, 1.00] n=23 |
| sim_const_unchanged[remove]|correct | 0.78 [0.65, 0.90] n=32 | 0.78 [0.65, 0.90] n=32 |
| sim_const_unchanged[remove]|wrong | 0.45 [0.20, 0.73] n=11 | 0.45 [0.20, 0.73] n=11 |
| sim_oracle|correct | 0.73 [0.67, 0.80] n=203 | 0.73 [0.67, 0.80] n=203 |
| sim_oracle|wrong | 0.74 [0.66, 0.84] n=84 | 0.74 [0.66, 0.84] n=84 |
| sim_oracle[add]|correct | 0.81 [0.67, 1.00] n=16 | 0.81 [0.67, 1.00] n=16 |
| sim_oracle[add]|wrong | 0.81 [0.64, 0.96] n=27 | 0.81 [0.64, 0.96] n=27 |
| sim_oracle[invariant_replace]|correct | 0.94 [0.85, 1.00] n=31 | 0.94 [0.85, 1.00] n=31 |
| sim_oracle[invariant_replace]|wrong | 0.50 [0.25, 0.89] n=12 | 0.50 [0.25, 0.89] n=12 |
| sim_oracle[noncrossing_replace]|correct | 0.91 [0.81, 1.00] n=32 | 0.91 [0.81, 1.00] n=32 |
| sim_oracle[noncrossing_replace]|wrong | 0.73 [0.50, 0.92] n=11 | 0.73 [0.50, 0.92] n=11 |
| sim_oracle[pivotal_replace]|correct | 0.70 [0.62, 0.77] n=92 | 0.70 [0.62, 0.77] n=92 |
| sim_oracle[pivotal_replace]|wrong | 0.96 [0.86, 1.00] n=23 | 0.96 [0.86, 1.00] n=23 |
| sim_oracle[remove]|correct | 0.41 [0.24, 0.57] n=32 | 0.41 [0.24, 0.57] n=32 |
| sim_oracle[remove]|wrong | 0.36 [0.10, 0.64] n=11 | 0.36 [0.10, 0.64] n=11 |
| self_V|correct | -0.02 [-0.07, 0.02] n=203 | -0.02 [-0.07, 0.02] n=203 |
| self_V|wrong | 0.00 [-0.07, 0.07] n=84 | 0.00 [-0.07, 0.07] n=84 |
| self_V[add]|correct | 0.00 [0.00, 0.00] n=16 | 0.00 [0.00, 0.00] n=16 |
| self_V[add]|wrong | 0.04 [0.00, 0.13] n=27 | 0.04 [0.00, 0.13] n=27 |
| self_V[invariant_replace]|correct | 0.03 [-0.06, 0.15] n=31 | 0.03 [-0.06, 0.15] n=31 |
| self_V[invariant_replace]|wrong | -0.08 [-0.33, 0.21] n=12 | -0.08 [-0.33, 0.21] n=12 |
| self_V[noncrossing_replace]|correct | -0.06 [-0.18, 0.00] n=32 | -0.06 [-0.18, 0.00] n=32 |
| self_V[noncrossing_replace]|wrong | -0.27 [-0.67, -0.07] n=11 | -0.27 [-0.67, -0.07] n=11 |
| self_V[pivotal_replace]|correct | -0.03 [-0.12, 0.04] n=92 | -0.03 [-0.12, 0.04] n=92 |
| self_V[pivotal_replace]|wrong | 0.04 [0.00, 0.13] n=23 | 0.04 [0.00, 0.13] n=23 |
| self_V[remove]|correct | 0.00 [-0.15, 0.16] n=32 | 0.00 [-0.15, 0.16] n=32 |
| self_V[remove]|wrong | 0.18 [0.00, 0.45] n=11 | 0.18 [0.00, 0.45] n=11 |
| self_S|correct | 0.73 [0.67, 0.79] n=203 | 0.73 [0.67, 0.79] n=203 |
| self_S|wrong | 0.77 [0.70, 0.86] n=84 | 0.77 [0.70, 0.86] n=84 |
| self_S[add]|correct | 0.88 [0.72, 1.00] n=16 | 0.88 [0.72, 1.00] n=16 |
| self_S[add]|wrong | 0.81 [0.70, 0.93] n=27 | 0.81 [0.70, 0.93] n=27 |
| self_S[invariant_replace]|correct | 0.90 [0.81, 1.00] n=31 | 0.90 [0.81, 1.00] n=31 |
| self_S[invariant_replace]|wrong | 0.75 [0.50, 0.93] n=12 | 0.75 [0.50, 0.93] n=12 |
| self_S[noncrossing_replace]|correct | 0.75 [0.54, 0.93] n=32 | 0.75 [0.54, 0.93] n=32 |
| self_S[noncrossing_replace]|wrong | 0.45 [0.12, 0.69] n=11 | 0.45 [0.12, 0.69] n=11 |
| self_S[pivotal_replace]|correct | 0.63 [0.55, 0.71] n=92 | 0.63 [0.55, 0.71] n=92 |
| self_S[pivotal_replace]|wrong | 0.96 [0.86, 1.00] n=23 | 0.96 [0.86, 1.00] n=23 |
| self_S[remove]|correct | 0.75 [0.57, 0.90] n=32 | 0.75 [0.57, 0.90] n=32 |
| self_S[remove]|wrong | 0.64 [0.36, 0.90] n=11 | 0.64 [0.36, 0.90] n=11 |
| self_S_noacc|correct | 0.75 [0.69, 0.80] n=203 | 0.75 [0.69, 0.80] n=203 |
| self_S_noacc|wrong | 0.77 [0.70, 0.85] n=84 | 0.77 [0.70, 0.85] n=84 |
| self_S_noacc[add]|correct | 0.88 [0.72, 1.00] n=16 | 0.88 [0.72, 1.00] n=16 |
| self_S_noacc[add]|wrong | 0.78 [0.64, 0.92] n=27 | 0.78 [0.64, 0.92] n=27 |
| self_S_noacc[invariant_replace]|correct | 0.87 [0.74, 0.97] n=31 | 0.87 [0.74, 0.97] n=31 |
| self_S_noacc[invariant_replace]|wrong | 0.83 [0.56, 1.00] n=12 | 0.83 [0.56, 1.00] n=12 |
| self_S_noacc[noncrossing_replace]|correct | 0.81 [0.70, 0.93] n=32 | 0.81 [0.70, 0.93] n=32 |
| self_S_noacc[noncrossing_replace]|wrong | 0.73 [0.54, 0.92] n=11 | 0.73 [0.54, 0.92] n=11 |
| self_S_noacc[pivotal_replace]|correct | 0.66 [0.60, 0.73] n=92 | 0.66 [0.60, 0.73] n=92 |
| self_S_noacc[pivotal_replace]|wrong | 0.91 [0.81, 1.00] n=23 | 0.91 [0.81, 1.00] n=23 |
| self_S_noacc[remove]|correct | 0.75 [0.57, 0.90] n=32 | 0.75 [0.57, 0.90] n=32 |
| self_S_noacc[remove]|wrong | 0.45 [0.20, 0.73] n=11 | 0.45 [0.20, 0.73] n=11 |
| self_G|correct | 0.00 [-0.08, 0.07] n=203 | 0.00 [-0.08, 0.07] n=203 |
| self_G|wrong | 0.04 [-0.10, 0.16] n=84 | 0.04 [-0.10, 0.16] n=84 |
| bank_unchanged|correct | 0.62 [0.56, 0.67] n=203 | 0.62 [0.56, 0.67] n=203 |
| bank_unchanged|wrong | 0.63 [0.53, 0.74] n=84 | 0.63 [0.53, 0.74] n=84 |
| flip|correct | 0.70 [0.61, 0.77] n=92 | 0.70 [0.61, 0.77] n=92 |
| flip|wrong | 1.00 [1.00, 1.00] n=23 | 1.00 [1.00, 1.00] n=23 |
| flip~noise|correct | 0.29 [0.20, 0.40] n=92 | 0.29 [0.20, 0.40] n=92 |
| flip~noise|wrong | 0.22 [0.08, 0.43] n=23 | 0.22 [0.08, 0.43] n=23 |
| flip[approve->deny]|correct | 0.84 [0.68, 0.97] n=32 | 0.84 [0.68, 0.97] n=32 |
| flip[approve->deny]|wrong | 1.00 [1.00, 1.00] n=19 | 1.00 [1.00, 1.00] n=19 |
| flip[approve->deny]~noise|correct | 0.34 [0.18, 0.53] n=32 | 0.34 [0.18, 0.53] n=32 |
| flip[approve->deny]~noise|wrong | 0.21 [0.05, 0.44] n=19 | 0.21 [0.05, 0.44] n=19 |
| flip[deny->approve]|correct | 0.62 [0.49, 0.75] n=60 | 0.62 [0.49, 0.75] n=60 |
| flip[deny->approve]|wrong | 1.00 [1.00, 1.00] n=4 | 1.00 [1.00, 1.00] n=4 |
| flip[deny->approve]~noise|correct | 0.27 [0.15, 0.38] n=60 | 0.27 [0.15, 0.38] n=60 |
| flip[deny->approve]~noise|wrong | 0.25 [0.00, 0.75] n=4 | 0.25 [0.00, 0.75] n=4 |
| flip_to_cd|correct | 0.00 [0.00, 0.00] n=92 | 0.00 [0.00, 0.00] n=92 |
| flip_to_cd|wrong | 0.00 [0.00, 0.00] n=23 | 0.00 [0.00, 0.00] n=23 |
| flip_to_cd[approve->deny]|correct | 0.00 [0.00, 0.00] n=32 | 0.00 [0.00, 0.00] n=32 |
| flip_to_cd[approve->deny]|wrong | 0.00 [0.00, 0.00] n=19 | 0.00 [0.00, 0.00] n=19 |
| flip_to_cd[deny->approve]|correct | 0.00 [0.00, 0.00] n=60 | 0.00 [0.00, 0.00] n=60 |
| flip_to_cd[deny->approve]|wrong | 0.00 [0.00, 0.00] n=4 | 0.00 [0.00, 0.00] n=4 |
| cf_pair_acc|correct | 0.70 [0.61, 0.77] n=92 | 0.70 [0.61, 0.77] n=92 |
| cf_pair_acc|wrong | 0.00 [0.00, 0.00] n=23 | 0.00 [0.00, 0.00] n=23 |
| invariance|correct | 0.92 [0.87, 0.98] n=92 | 0.92 [0.87, 0.98] n=92 |
| invariance|wrong | 0.52 [0.27, 0.78] n=23 | 0.52 [0.27, 0.78] n=23 |
| invariance~noise|correct | 0.13 [0.07, 0.18] n=92 | 0.13 [0.07, 0.18] n=92 |
| invariance~noise|wrong | 0.39 [0.23, 0.58] n=23 | 0.39 [0.23, 0.58] n=23 |
| inv_pair_acc|correct | 0.92 [0.87, 0.98] n=92 | 0.92 [0.87, 0.98] n=92 |
| inv_pair_acc|wrong | 0.00 [0.00, 0.00] n=23 | 0.00 [0.00, 0.00] n=23 |
| expl_valid|correct | 0.30 [0.24, 0.35] n=369 | 0.30 [0.24, 0.35] n=369 |
| expl_valid|wrong | 0.10 [0.06, 0.15] n=154 | 0.10 [0.06, 0.15] n=154 |
| acct_consistent|correct | 0.99 [0.97, 1.00] n=335 | 0.99 [0.97, 1.00] n=335 |
| acct_consistent|wrong | 0.01 [0.00, 0.02] n=125 | 0.01 [0.00, 0.02] n=125 |
| expl_minimal|correct | 0.31 [0.25, 0.36] n=367 | 0.31 [0.25, 0.36] n=367 |
| expl_minimal|wrong | 0.00 [0.00, 0.00] n=86 | 0.00 [0.00, 0.00] n=86 |
| cite_distractor|correct | 0.32 [0.27, 0.38] n=375 | 0.32 [0.27, 0.38] n=375 |
| cite_distractor|wrong | 0.57 [0.49, 0.66] n=154 | 0.57 [0.49, 0.66] n=154 |
| cite_p_nec|correct | 0.38 [0.33, 0.43] n=375 | 0.38 [0.33, 0.43] n=375 |
| cite_p_nec|wrong | 0.23 [0.15, 0.32] n=154 | 0.23 [0.15, 0.32] n=154 |
| cite_r_nec|correct | 0.49 [0.43, 0.55] n=317 | 0.49 [0.43, 0.55] n=317 |
| cite_r_nec|wrong | 0.23 [0.17, 0.30] n=86 | 0.23 [0.17, 0.30] n=86 |
| assume_dec|correct | 0.41 [0.31, 0.52] n=92 | 0.41 [0.31, 0.52] n=92 |
| assume_dec|wrong | 0.22 [0.08, 0.39] n=23 | 0.22 [0.08, 0.39] n=23 |
| assume_val|correct | 0.46 [0.23, 0.69] n=13 | 0.46 [0.23, 0.69] n=13 |
| assume_val|wrong | 0.00 [0.00, 0.00] n=3 | 0.00 [0.00, 0.00] n=3 |
| none_claim_disproved|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved|wrong | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_both|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_both[vs_gold]|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_both[vs_gold]|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_oracle_only|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_oracle_only|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_oracle_only[vs_gold]|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_oracle_only[vs_gold]|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_model_only|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_model_only|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_model_only[vs_gold]|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_model_only[vs_gold]|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_neither|correct | 1.00 [1.00, 1.00] n=9 | 1.00 [1.00, 1.00] n=9 |
| bnd_neither|wrong | 1.00 [1.00, 1.00] n=7 | 1.00 [1.00, 1.00] n=7 |
| bnd_neither[vs_gold]|correct | 1.00 [1.00, 1.00] n=9 | 1.00 [1.00, 1.00] n=9 |
| bnd_neither[vs_gold]|wrong | 1.00 [1.00, 1.00] n=7 | 1.00 [1.00, 1.00] n=7 |
| bnd_oracle_minimal|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_oracle_minimal|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_oracle_minimal[vs_gold]|correct | 0.00 [0.00, 0.00] n=9 | 0.00 [0.00, 0.00] n=9 |
| bnd_oracle_minimal[vs_gold]|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| bnd_invalid|correct | 0.23 [0.08, 0.39] n=40 | 0.23 [0.08, 0.39] n=40 |
| bnd_invalid|wrong | 0.41 [0.19, 0.65] n=17 | 0.41 [0.19, 0.65] n=17 |

### coverage

| count | mortgage-split-lite |
|---|---|
| acct_consistent_unscored | 69 |
| api_error | 0 |
| boundary_derived_refused | 57 |
| boundary_invalid_value | 16 |
| boundary_pending | 41 |
| const_unchanged_parse_fail | 0 |
| expl_uncertified | 6 |
| flip_parse_fail_pairs | 0 |
| fmt_err | 0 |
| interventions_requested | 279 |
| invariance_parse_fail_pairs | 0 |
| items_in_data | 4044 |
| items_scored | 529 |
| necessity_pending | 238 |
| none_claim_unresolved | 1 |
| none_unsupported_assume | 9 |
| none_unsupported_support | 0 |
| oracle_parse_fail | 0 |
| outputs | 687 |
| parse_fail | 0 |
| predict_noacc_parse_fail | 0 |
| predict_parse_fail | 0 |
| sim_items_shared | 287 |
| simulate_noacc_parse_fail | 1 |
| simulate_parse_fail | 0 |
| simulate_shuf_parse_fail | 1 |
| truncated | 0 |

json=runs/mortgage-split-lite.eval.json
