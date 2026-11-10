mortgage-lite: decoding ['{"backend": "gemini/vertex:global", "max_tokens": 4096, "model": "gemini-3.5-flash-lite", "n": 1, "temperature": 0.0, "thinking": false, "top_k": 0, "top_p": 1.0}']; compute {'out_tokens': 105986, 'think_tokens': 0, 'call_latency_s': 822.34, 'mortgage-lite.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 150, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 892, 'cached': 0, 'errors': 0, 'fresh_calls': 892, 'wall_s': 135.73, 'in_tokens': 1154772, 'out_tokens': 105986, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 892}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.922, 'cost_usd_fresh': 0.6114, 'cost_usd_if_uncached': 0.6114}, 'mortgage-lite.repeat.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'answer', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 150, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 892, 'cached': 0, 'errors': 0, 'fresh_calls': 892, 'wall_s': 888.02, 'in_tokens': 1154772, 'out_tokens': 105012, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 892}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 7.653, 'cost_usd_fresh': 0.609, 'cost_usd_if_uncached': 0.609}, 'mortgage-lite.predict.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'predict', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 2, 'cached': 0, 'errors': 0, 'fresh_calls': 2, 'wall_s': 6.04, 'in_tokens': 1995, 'out_tokens': 58, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 2}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 2.135, 'cost_usd_fresh': 0.0007, 'cost_usd_if_uncached': 0.0007}, 'mortgage-lite.simulate.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate', 'no_account': False, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 368, 'cached': 0, 'errors': 0, 'fresh_calls': 368, 'wall_s': 54.57, 'in_tokens': 228866, 'out_tokens': 10264, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 368}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.843, 'cost_usd_fresh': 0.0943, 'cost_usd_if_uncached': 0.0943}, 'mortgage-lite.simulate_noacc.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate_noacc', 'no_account': True, 'shuffle_accounts': False, 'shuf_missing': None, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 368, 'cached': 0, 'errors': 0, 'fresh_calls': 368, 'wall_s': 1974.31, 'in_tokens': 193952, 'out_tokens': 10420, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 368}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 42.872, 'cost_usd_fresh': 0.0842, 'cost_usd_if_uncached': 0.0842}, 'mortgage-lite.simulate_shuf.meta.json': {'model': 'gemini-3.5-flash-lite', 'backend': 'gemini', 'vertex': 'global', 'mode': 'simulate_shuf', 'no_account': False, 'shuffle_accounts': True, 'shuf_missing': 143, 'cases': 0, 'cache_tag': '', 'sample_seed': 0, 'n': 1, 'rows': 225, 'cached': 1, 'errors': 0, 'fresh_calls': 224, 'wall_s': 45.09, 'in_tokens': 141626, 'out_tokens': 6251, 'think_tokens': 0, 'finish': {'FinishReason.STOP': 225}, 'model_versions': ['gemini-3.5-flash-lite'], 'mean_latency_s': 0.952, 'cost_usd_fresh': 0.0579, 'cost_usd_if_uncached': 0.0581}}

### all

| metric | mortgage-lite | mortgage-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.01 [-0.06, 0.09] n=225 | 0.01 [-0.06, 0.09] n=225 |
| sim_delta[add] | 0.09 [-0.06, 0.26] n=32 | 0.09 [-0.06, 0.26] n=32 |
| sim_delta[changed] | 0.01 [-0.11, 0.15] n=79 | 0.01 [-0.11, 0.15] n=79 |
| sim_delta[invariant_replace] | 0.06 [-0.06, 0.19] n=35 | 0.06 [-0.06, 0.19] n=35 |
| sim_delta[noncrossing_replace] | 0.06 [-0.15, 0.27] n=35 | 0.06 [-0.15, 0.27] n=35 |
| sim_delta[pivotal_replace] | -0.03 [-0.16, 0.10] n=91 | -0.03 [-0.16, 0.10] n=91 |
| sim_delta[remove] | -0.03 [-0.19, 0.13] n=32 | -0.03 [-0.19, 0.13] n=32 |
| sim_delta[unchanged] | 0.01 [-0.09, 0.12] n=146 | 0.01 [-0.09, 0.12] n=146 |
| sim_acct | 0.61 [0.53, 0.69] n=225 | 0.61 [0.53, 0.69] n=225 |
| sim_acct[add] | 0.69 [0.53, 0.83] n=32 | 0.69 [0.53, 0.83] n=32 |
| sim_acct[invariant_replace] | 0.89 [0.77, 0.97] n=35 | 0.89 [0.77, 0.97] n=35 |
| sim_acct[noncrossing_replace] | 0.60 [0.44, 0.74] n=35 | 0.60 [0.44, 0.74] n=35 |
| sim_acct[pivotal_replace] | 0.52 [0.40, 0.63] n=91 | 0.52 [0.40, 0.63] n=91 |
| sim_acct[remove] | 0.53 [0.38, 0.70] n=32 | 0.53 [0.38, 0.70] n=32 |
| sim_shuf | 0.60 [0.53, 0.68] n=225 | 0.60 [0.53, 0.68] n=225 |
| sim_shuf[add] | 0.59 [0.44, 0.75] n=32 | 0.59 [0.44, 0.75] n=32 |
| sim_shuf[invariant_replace] | 0.83 [0.70, 0.94] n=35 | 0.83 [0.70, 0.94] n=35 |
| sim_shuf[noncrossing_replace] | 0.54 [0.37, 0.71] n=35 | 0.54 [0.37, 0.71] n=35 |
| sim_shuf[pivotal_replace] | 0.55 [0.43, 0.67] n=91 | 0.55 [0.43, 0.67] n=91 |
| sim_shuf[remove] | 0.56 [0.39, 0.74] n=32 | 0.56 [0.39, 0.74] n=32 |
| sim_gross (acct - noacc) | 0.28 [0.20, 0.35] n=225 | 0.28 [0.20, 0.35] n=225 |
| sim_gross[add] | 0.38 [0.24, 0.53] n=32 | 0.38 [0.24, 0.53] n=32 |
| sim_gross[invariant_replace] | 0.37 [0.21, 0.55] n=35 | 0.37 [0.21, 0.55] n=35 |
| sim_gross[noncrossing_replace] | 0.29 [0.12, 0.46] n=35 | 0.29 [0.12, 0.46] n=35 |
| sim_gross[pivotal_replace] | 0.26 [0.15, 0.39] n=91 | 0.26 [0.15, 0.39] n=91 |
| sim_gross[remove] | 0.09 [-0.09, 0.29] n=32 | 0.09 [-0.09, 0.29] n=32 |
| sim_noacc | 0.34 [0.28, 0.40] n=225 | 0.34 [0.28, 0.40] n=225 |
| sim_noacc[add] | 0.31 [0.18, 0.42] n=32 | 0.31 [0.18, 0.42] n=32 |
| sim_noacc[invariant_replace] | 0.51 [0.33, 0.70] n=35 | 0.51 [0.33, 0.70] n=35 |
| sim_noacc[noncrossing_replace] | 0.31 [0.17, 0.46] n=35 | 0.31 [0.17, 0.46] n=35 |
| sim_noacc[pivotal_replace] | 0.25 [0.17, 0.34] n=91 | 0.25 [0.17, 0.34] n=91 |
| sim_noacc[remove] | 0.44 [0.25, 0.60] n=32 | 0.44 [0.25, 0.60] n=32 |
| sim_const_unchanged (baseline: frozen decision) | 0.65 [0.59, 0.71] n=225 | 0.65 [0.59, 0.71] n=225 |
| sim_const_unchanged[add] | 0.66 [0.50, 0.80] n=32 | 0.66 [0.50, 0.80] n=32 |
| sim_const_unchanged[invariant_replace] | 0.97 [0.91, 1.00] n=35 | 0.97 [0.91, 1.00] n=35 |
| sim_const_unchanged[noncrossing_replace] | 0.77 [0.62, 0.89] n=35 | 0.77 [0.62, 0.89] n=35 |
| sim_const_unchanged[pivotal_replace] | 0.46 [0.37, 0.57] n=91 | 0.46 [0.37, 0.57] n=91 |
| sim_const_unchanged[remove] | 0.69 [0.50, 0.86] n=32 | 0.69 [0.50, 0.86] n=32 |
| sim_oracle (baseline: engine label) | 0.71 [0.65, 0.76] n=225 | 0.71 [0.65, 0.76] n=225 |
| sim_oracle[add] | 0.78 [0.61, 0.93] n=32 | 0.78 [0.61, 0.93] n=32 |
| sim_oracle[invariant_replace] | 0.89 [0.78, 0.97] n=35 | 0.89 [0.78, 0.97] n=35 |
| sim_oracle[noncrossing_replace] | 0.69 [0.52, 0.82] n=35 | 0.69 [0.52, 0.82] n=35 |
| sim_oracle[pivotal_replace] | 0.74 [0.66, 0.81] n=91 | 0.74 [0.66, 0.81] n=91 |
| sim_oracle[remove] | 0.38 [0.23, 0.53] n=32 | 0.38 [0.23, 0.53] n=32 |
| self_S | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_S[pivotal_replace] | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_G | -0.50 [-1.00, 0.00] n=2 | -0.50 [-1.00, 0.00] n=2 |
| bank_unchanged | 0.65 [0.60, 0.69] n=368 | 0.65 [0.60, 0.69] n=368 |
| acc_maj | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_maj[interaction] | 0.81 [0.71, 0.91] n=64 | 0.81 [0.71, 0.91] n=64 |
| acc_mean | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_class[approve] | 0.65 [0.56, 0.73] n=274 | 0.65 [0.56, 0.73] n=274 |
| acc_class[cannot determine] | 0.09 [0.04, 0.15] n=89 | 0.09 [0.04, 0.15] n=89 |
| acc_class[deny] | 0.93 [0.90, 0.96] n=324 | 0.93 [0.90, 0.96] n=324 |
| repeat_disagree | 0.18 [0.15, 0.21] n=687 | 0.18 [0.15, 0.21] n=687 |
| flip | 0.72 [0.65, 0.79] n=150 | 0.72 [0.65, 0.79] n=150 |
| flip~noise | 0.31 [0.24, 0.37] n=150 | 0.31 [0.24, 0.37] n=150 |
| flip[approve->deny] | 0.91 [0.84, 0.97] n=67 | 0.91 [0.84, 0.97] n=67 |
| flip[approve->deny]~noise | 0.36 [0.25, 0.47] n=67 | 0.36 [0.25, 0.47] n=67 |
| flip[deny->approve] | 0.57 [0.45, 0.67] n=83 | 0.57 [0.45, 0.67] n=83 |
| flip[deny->approve]~noise | 0.27 [0.17, 0.36] n=83 | 0.27 [0.17, 0.36] n=83 |
| flip_to_cd | 0.00 [0.00, 0.00] n=150 | 0.00 [0.00, 0.00] n=150 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=67 | 0.00 [0.00, 0.00] n=67 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=83 | 0.00 [0.00, 0.00] n=83 |
| cf_pair_acc | 0.53 [0.44, 0.63] n=150 | 0.53 [0.44, 0.63] n=150 |
| invariance | 0.87 [0.82, 0.93] n=150 | 0.87 [0.82, 0.93] n=150 |
| invariance~noise | 0.21 [0.16, 0.27] n=150 | 0.21 [0.16, 0.27] n=150 |
| inv_pair_acc | 0.77 [0.69, 0.83] n=150 | 0.77 [0.69, 0.83] n=150 |
| expl_valid | 0.24 [0.20, 0.28] n=674 | 0.24 [0.20, 0.28] n=674 |
| acct_consistent | 0.70 [0.66, 0.75] n=610 | 0.70 [0.66, 0.75] n=610 |
| expl_minimal | 0.25 [0.20, 0.30] n=578 | 0.25 [0.20, 0.30] n=578 |
| cite_distractor | 0.39 [0.35, 0.43] n=687 | 0.39 [0.35, 0.43] n=687 |
| cite_p_nec | 0.34 [0.31, 0.38] n=687 | 0.34 [0.31, 0.38] n=687 |
| cite_r_nec | 0.43 [0.38, 0.47] n=522 | 0.43 [0.38, 0.47] n=522 |
| assume_dec | 0.38 [0.30, 0.46] n=150 | 0.38 [0.30, 0.46] n=150 |
| assume_val | 0.43 [0.23, 0.65] n=21 | 0.43 [0.23, 0.65] n=21 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_neither | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_invalid | 0.33 [0.21, 0.44] n=64 | 0.33 [0.21, 0.44] n=64 |
| fmt_err | 0.00 [0.00, 0.00] n=892 | 0.00 [0.00, 0.00] n=892 |
| len_chars | 430 [403, 456] n=892 | 430 [403, 456] n=892 |
| len_tok | 119 [111, 127] n=892 | 119 [111, 127] n=892 |

### secondary: slice=real_transfer

| metric | mortgage-lite | mortgage-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.01 [-0.06, 0.09] n=225 | 0.01 [-0.06, 0.09] n=225 |
| sim_delta[add] | 0.09 [-0.06, 0.26] n=32 | 0.09 [-0.06, 0.26] n=32 |
| sim_delta[changed] | 0.01 [-0.11, 0.15] n=79 | 0.01 [-0.11, 0.15] n=79 |
| sim_delta[invariant_replace] | 0.06 [-0.06, 0.19] n=35 | 0.06 [-0.06, 0.19] n=35 |
| sim_delta[noncrossing_replace] | 0.06 [-0.15, 0.27] n=35 | 0.06 [-0.15, 0.27] n=35 |
| sim_delta[pivotal_replace] | -0.03 [-0.16, 0.10] n=91 | -0.03 [-0.16, 0.10] n=91 |
| sim_delta[remove] | -0.03 [-0.19, 0.13] n=32 | -0.03 [-0.19, 0.13] n=32 |
| sim_delta[unchanged] | 0.01 [-0.09, 0.12] n=146 | 0.01 [-0.09, 0.12] n=146 |
| sim_acct | 0.61 [0.53, 0.69] n=225 | 0.61 [0.53, 0.69] n=225 |
| sim_acct[add] | 0.69 [0.53, 0.83] n=32 | 0.69 [0.53, 0.83] n=32 |
| sim_acct[invariant_replace] | 0.89 [0.77, 0.97] n=35 | 0.89 [0.77, 0.97] n=35 |
| sim_acct[noncrossing_replace] | 0.60 [0.44, 0.74] n=35 | 0.60 [0.44, 0.74] n=35 |
| sim_acct[pivotal_replace] | 0.52 [0.40, 0.63] n=91 | 0.52 [0.40, 0.63] n=91 |
| sim_acct[remove] | 0.53 [0.38, 0.70] n=32 | 0.53 [0.38, 0.70] n=32 |
| sim_shuf | 0.60 [0.53, 0.68] n=225 | 0.60 [0.53, 0.68] n=225 |
| sim_shuf[add] | 0.59 [0.44, 0.75] n=32 | 0.59 [0.44, 0.75] n=32 |
| sim_shuf[invariant_replace] | 0.83 [0.70, 0.94] n=35 | 0.83 [0.70, 0.94] n=35 |
| sim_shuf[noncrossing_replace] | 0.54 [0.37, 0.71] n=35 | 0.54 [0.37, 0.71] n=35 |
| sim_shuf[pivotal_replace] | 0.55 [0.43, 0.67] n=91 | 0.55 [0.43, 0.67] n=91 |
| sim_shuf[remove] | 0.56 [0.39, 0.74] n=32 | 0.56 [0.39, 0.74] n=32 |
| sim_gross (acct - noacc) | 0.28 [0.20, 0.35] n=225 | 0.28 [0.20, 0.35] n=225 |
| sim_gross[add] | 0.38 [0.24, 0.53] n=32 | 0.38 [0.24, 0.53] n=32 |
| sim_gross[invariant_replace] | 0.37 [0.21, 0.55] n=35 | 0.37 [0.21, 0.55] n=35 |
| sim_gross[noncrossing_replace] | 0.29 [0.12, 0.46] n=35 | 0.29 [0.12, 0.46] n=35 |
| sim_gross[pivotal_replace] | 0.26 [0.15, 0.39] n=91 | 0.26 [0.15, 0.39] n=91 |
| sim_gross[remove] | 0.09 [-0.09, 0.29] n=32 | 0.09 [-0.09, 0.29] n=32 |
| sim_noacc | 0.34 [0.28, 0.40] n=225 | 0.34 [0.28, 0.40] n=225 |
| sim_noacc[add] | 0.31 [0.18, 0.42] n=32 | 0.31 [0.18, 0.42] n=32 |
| sim_noacc[invariant_replace] | 0.51 [0.33, 0.70] n=35 | 0.51 [0.33, 0.70] n=35 |
| sim_noacc[noncrossing_replace] | 0.31 [0.17, 0.46] n=35 | 0.31 [0.17, 0.46] n=35 |
| sim_noacc[pivotal_replace] | 0.25 [0.17, 0.34] n=91 | 0.25 [0.17, 0.34] n=91 |
| sim_noacc[remove] | 0.44 [0.25, 0.60] n=32 | 0.44 [0.25, 0.60] n=32 |
| sim_const_unchanged (baseline: frozen decision) | 0.65 [0.59, 0.71] n=225 | 0.65 [0.59, 0.71] n=225 |
| sim_const_unchanged[add] | 0.66 [0.50, 0.80] n=32 | 0.66 [0.50, 0.80] n=32 |
| sim_const_unchanged[invariant_replace] | 0.97 [0.91, 1.00] n=35 | 0.97 [0.91, 1.00] n=35 |
| sim_const_unchanged[noncrossing_replace] | 0.77 [0.62, 0.89] n=35 | 0.77 [0.62, 0.89] n=35 |
| sim_const_unchanged[pivotal_replace] | 0.46 [0.37, 0.57] n=91 | 0.46 [0.37, 0.57] n=91 |
| sim_const_unchanged[remove] | 0.69 [0.50, 0.86] n=32 | 0.69 [0.50, 0.86] n=32 |
| sim_oracle (baseline: engine label) | 0.71 [0.65, 0.76] n=225 | 0.71 [0.65, 0.76] n=225 |
| sim_oracle[add] | 0.78 [0.61, 0.93] n=32 | 0.78 [0.61, 0.93] n=32 |
| sim_oracle[invariant_replace] | 0.89 [0.78, 0.97] n=35 | 0.89 [0.78, 0.97] n=35 |
| sim_oracle[noncrossing_replace] | 0.69 [0.52, 0.82] n=35 | 0.69 [0.52, 0.82] n=35 |
| sim_oracle[pivotal_replace] | 0.74 [0.66, 0.81] n=91 | 0.74 [0.66, 0.81] n=91 |
| sim_oracle[remove] | 0.38 [0.23, 0.53] n=32 | 0.38 [0.23, 0.53] n=32 |
| self_S | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_S[pivotal_replace] | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_G | -0.50 [-1.00, 0.00] n=2 | -0.50 [-1.00, 0.00] n=2 |
| bank_unchanged | 0.65 [0.60, 0.69] n=368 | 0.65 [0.60, 0.69] n=368 |
| acc_maj | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_maj[interaction] | 0.81 [0.71, 0.91] n=64 | 0.81 [0.71, 0.91] n=64 |
| acc_mean | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_class[approve] | 0.65 [0.56, 0.73] n=274 | 0.65 [0.56, 0.73] n=274 |
| acc_class[cannot determine] | 0.09 [0.04, 0.15] n=89 | 0.09 [0.04, 0.15] n=89 |
| acc_class[deny] | 0.93 [0.90, 0.96] n=324 | 0.93 [0.90, 0.96] n=324 |
| repeat_disagree | 0.18 [0.15, 0.21] n=687 | 0.18 [0.15, 0.21] n=687 |
| flip | 0.72 [0.65, 0.79] n=150 | 0.72 [0.65, 0.79] n=150 |
| flip~noise | 0.31 [0.24, 0.37] n=150 | 0.31 [0.24, 0.37] n=150 |
| flip[approve->deny] | 0.91 [0.84, 0.97] n=67 | 0.91 [0.84, 0.97] n=67 |
| flip[approve->deny]~noise | 0.36 [0.25, 0.47] n=67 | 0.36 [0.25, 0.47] n=67 |
| flip[deny->approve] | 0.57 [0.45, 0.67] n=83 | 0.57 [0.45, 0.67] n=83 |
| flip[deny->approve]~noise | 0.27 [0.17, 0.36] n=83 | 0.27 [0.17, 0.36] n=83 |
| flip_to_cd | 0.00 [0.00, 0.00] n=150 | 0.00 [0.00, 0.00] n=150 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=67 | 0.00 [0.00, 0.00] n=67 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=83 | 0.00 [0.00, 0.00] n=83 |
| cf_pair_acc | 0.53 [0.44, 0.63] n=150 | 0.53 [0.44, 0.63] n=150 |
| invariance | 0.87 [0.82, 0.93] n=150 | 0.87 [0.82, 0.93] n=150 |
| invariance~noise | 0.21 [0.16, 0.27] n=150 | 0.21 [0.16, 0.27] n=150 |
| inv_pair_acc | 0.77 [0.69, 0.83] n=150 | 0.77 [0.69, 0.83] n=150 |
| expl_valid | 0.24 [0.20, 0.28] n=674 | 0.24 [0.20, 0.28] n=674 |
| acct_consistent | 0.70 [0.66, 0.75] n=610 | 0.70 [0.66, 0.75] n=610 |
| expl_minimal | 0.25 [0.20, 0.30] n=578 | 0.25 [0.20, 0.30] n=578 |
| cite_distractor | 0.39 [0.35, 0.43] n=687 | 0.39 [0.35, 0.43] n=687 |
| cite_p_nec | 0.34 [0.31, 0.38] n=687 | 0.34 [0.31, 0.38] n=687 |
| cite_r_nec | 0.43 [0.38, 0.47] n=522 | 0.43 [0.38, 0.47] n=522 |
| assume_dec | 0.38 [0.30, 0.46] n=150 | 0.38 [0.30, 0.46] n=150 |
| assume_val | 0.43 [0.23, 0.65] n=21 | 0.43 [0.23, 0.65] n=21 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_neither | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_invalid | 0.33 [0.21, 0.44] n=64 | 0.33 [0.21, 0.44] n=64 |
| fmt_err | 0.00 [0.00, 0.00] n=892 | 0.00 [0.00, 0.00] n=892 |
| len_chars | 430 [403, 456] n=892 | 430 [403, 456] n=892 |
| len_tok | 119 [111, 127] n=892 | 119 [111, 127] n=892 |

### secondary: slice=real_transfer view=prose

| metric | mortgage-lite | mortgage-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.01 [-0.06, 0.09] n=225 | 0.01 [-0.06, 0.09] n=225 |
| sim_delta[add] | 0.09 [-0.06, 0.26] n=32 | 0.09 [-0.06, 0.26] n=32 |
| sim_delta[changed] | 0.01 [-0.11, 0.15] n=79 | 0.01 [-0.11, 0.15] n=79 |
| sim_delta[invariant_replace] | 0.06 [-0.06, 0.19] n=35 | 0.06 [-0.06, 0.19] n=35 |
| sim_delta[noncrossing_replace] | 0.06 [-0.15, 0.27] n=35 | 0.06 [-0.15, 0.27] n=35 |
| sim_delta[pivotal_replace] | -0.03 [-0.16, 0.10] n=91 | -0.03 [-0.16, 0.10] n=91 |
| sim_delta[remove] | -0.03 [-0.19, 0.13] n=32 | -0.03 [-0.19, 0.13] n=32 |
| sim_delta[unchanged] | 0.01 [-0.09, 0.12] n=146 | 0.01 [-0.09, 0.12] n=146 |
| sim_acct | 0.61 [0.53, 0.69] n=225 | 0.61 [0.53, 0.69] n=225 |
| sim_acct[add] | 0.69 [0.53, 0.83] n=32 | 0.69 [0.53, 0.83] n=32 |
| sim_acct[invariant_replace] | 0.89 [0.77, 0.97] n=35 | 0.89 [0.77, 0.97] n=35 |
| sim_acct[noncrossing_replace] | 0.60 [0.44, 0.74] n=35 | 0.60 [0.44, 0.74] n=35 |
| sim_acct[pivotal_replace] | 0.52 [0.40, 0.63] n=91 | 0.52 [0.40, 0.63] n=91 |
| sim_acct[remove] | 0.53 [0.38, 0.70] n=32 | 0.53 [0.38, 0.70] n=32 |
| sim_shuf | 0.60 [0.53, 0.68] n=225 | 0.60 [0.53, 0.68] n=225 |
| sim_shuf[add] | 0.59 [0.44, 0.75] n=32 | 0.59 [0.44, 0.75] n=32 |
| sim_shuf[invariant_replace] | 0.83 [0.70, 0.94] n=35 | 0.83 [0.70, 0.94] n=35 |
| sim_shuf[noncrossing_replace] | 0.54 [0.37, 0.71] n=35 | 0.54 [0.37, 0.71] n=35 |
| sim_shuf[pivotal_replace] | 0.55 [0.43, 0.67] n=91 | 0.55 [0.43, 0.67] n=91 |
| sim_shuf[remove] | 0.56 [0.39, 0.74] n=32 | 0.56 [0.39, 0.74] n=32 |
| sim_gross (acct - noacc) | 0.28 [0.20, 0.35] n=225 | 0.28 [0.20, 0.35] n=225 |
| sim_gross[add] | 0.38 [0.24, 0.53] n=32 | 0.38 [0.24, 0.53] n=32 |
| sim_gross[invariant_replace] | 0.37 [0.21, 0.55] n=35 | 0.37 [0.21, 0.55] n=35 |
| sim_gross[noncrossing_replace] | 0.29 [0.12, 0.46] n=35 | 0.29 [0.12, 0.46] n=35 |
| sim_gross[pivotal_replace] | 0.26 [0.15, 0.39] n=91 | 0.26 [0.15, 0.39] n=91 |
| sim_gross[remove] | 0.09 [-0.09, 0.29] n=32 | 0.09 [-0.09, 0.29] n=32 |
| sim_noacc | 0.34 [0.28, 0.40] n=225 | 0.34 [0.28, 0.40] n=225 |
| sim_noacc[add] | 0.31 [0.18, 0.42] n=32 | 0.31 [0.18, 0.42] n=32 |
| sim_noacc[invariant_replace] | 0.51 [0.33, 0.70] n=35 | 0.51 [0.33, 0.70] n=35 |
| sim_noacc[noncrossing_replace] | 0.31 [0.17, 0.46] n=35 | 0.31 [0.17, 0.46] n=35 |
| sim_noacc[pivotal_replace] | 0.25 [0.17, 0.34] n=91 | 0.25 [0.17, 0.34] n=91 |
| sim_noacc[remove] | 0.44 [0.25, 0.60] n=32 | 0.44 [0.25, 0.60] n=32 |
| sim_const_unchanged (baseline: frozen decision) | 0.65 [0.59, 0.71] n=225 | 0.65 [0.59, 0.71] n=225 |
| sim_const_unchanged[add] | 0.66 [0.50, 0.80] n=32 | 0.66 [0.50, 0.80] n=32 |
| sim_const_unchanged[invariant_replace] | 0.97 [0.91, 1.00] n=35 | 0.97 [0.91, 1.00] n=35 |
| sim_const_unchanged[noncrossing_replace] | 0.77 [0.62, 0.89] n=35 | 0.77 [0.62, 0.89] n=35 |
| sim_const_unchanged[pivotal_replace] | 0.46 [0.37, 0.57] n=91 | 0.46 [0.37, 0.57] n=91 |
| sim_const_unchanged[remove] | 0.69 [0.50, 0.86] n=32 | 0.69 [0.50, 0.86] n=32 |
| sim_oracle (baseline: engine label) | 0.71 [0.65, 0.76] n=225 | 0.71 [0.65, 0.76] n=225 |
| sim_oracle[add] | 0.78 [0.61, 0.93] n=32 | 0.78 [0.61, 0.93] n=32 |
| sim_oracle[invariant_replace] | 0.89 [0.78, 0.97] n=35 | 0.89 [0.78, 0.97] n=35 |
| sim_oracle[noncrossing_replace] | 0.69 [0.52, 0.82] n=35 | 0.69 [0.52, 0.82] n=35 |
| sim_oracle[pivotal_replace] | 0.74 [0.66, 0.81] n=91 | 0.74 [0.66, 0.81] n=91 |
| sim_oracle[remove] | 0.38 [0.23, 0.53] n=32 | 0.38 [0.23, 0.53] n=32 |
| self_S | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_S[pivotal_replace] | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_G | -0.50 [-1.00, 0.00] n=2 | -0.50 [-1.00, 0.00] n=2 |
| bank_unchanged | 0.65 [0.60, 0.69] n=368 | 0.65 [0.60, 0.69] n=368 |
| acc_maj | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_maj[interaction] | 0.81 [0.71, 0.91] n=64 | 0.81 [0.71, 0.91] n=64 |
| acc_mean | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_class[approve] | 0.65 [0.56, 0.73] n=274 | 0.65 [0.56, 0.73] n=274 |
| acc_class[cannot determine] | 0.09 [0.04, 0.15] n=89 | 0.09 [0.04, 0.15] n=89 |
| acc_class[deny] | 0.93 [0.90, 0.96] n=324 | 0.93 [0.90, 0.96] n=324 |
| repeat_disagree | 0.18 [0.15, 0.21] n=687 | 0.18 [0.15, 0.21] n=687 |
| flip | 0.72 [0.65, 0.79] n=150 | 0.72 [0.65, 0.79] n=150 |
| flip~noise | 0.31 [0.24, 0.37] n=150 | 0.31 [0.24, 0.37] n=150 |
| flip[approve->deny] | 0.91 [0.84, 0.97] n=67 | 0.91 [0.84, 0.97] n=67 |
| flip[approve->deny]~noise | 0.36 [0.25, 0.47] n=67 | 0.36 [0.25, 0.47] n=67 |
| flip[deny->approve] | 0.57 [0.45, 0.67] n=83 | 0.57 [0.45, 0.67] n=83 |
| flip[deny->approve]~noise | 0.27 [0.17, 0.36] n=83 | 0.27 [0.17, 0.36] n=83 |
| flip_to_cd | 0.00 [0.00, 0.00] n=150 | 0.00 [0.00, 0.00] n=150 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=67 | 0.00 [0.00, 0.00] n=67 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=83 | 0.00 [0.00, 0.00] n=83 |
| cf_pair_acc | 0.53 [0.44, 0.63] n=150 | 0.53 [0.44, 0.63] n=150 |
| invariance | 0.87 [0.82, 0.93] n=150 | 0.87 [0.82, 0.93] n=150 |
| invariance~noise | 0.21 [0.16, 0.27] n=150 | 0.21 [0.16, 0.27] n=150 |
| inv_pair_acc | 0.77 [0.69, 0.83] n=150 | 0.77 [0.69, 0.83] n=150 |
| expl_valid | 0.24 [0.20, 0.28] n=674 | 0.24 [0.20, 0.28] n=674 |
| acct_consistent | 0.70 [0.66, 0.75] n=610 | 0.70 [0.66, 0.75] n=610 |
| expl_minimal | 0.25 [0.20, 0.30] n=578 | 0.25 [0.20, 0.30] n=578 |
| cite_distractor | 0.39 [0.35, 0.43] n=687 | 0.39 [0.35, 0.43] n=687 |
| cite_p_nec | 0.34 [0.31, 0.38] n=687 | 0.34 [0.31, 0.38] n=687 |
| cite_r_nec | 0.43 [0.38, 0.47] n=522 | 0.43 [0.38, 0.47] n=522 |
| assume_dec | 0.38 [0.30, 0.46] n=150 | 0.38 [0.30, 0.46] n=150 |
| assume_val | 0.43 [0.23, 0.65] n=21 | 0.43 [0.23, 0.65] n=21 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_neither | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_invalid | 0.33 [0.21, 0.44] n=64 | 0.33 [0.21, 0.44] n=64 |
| fmt_err | 0.00 [0.00, 0.00] n=892 | 0.00 [0.00, 0.00] n=892 |
| len_chars | 430 [403, 456] n=892 | 430 [403, 456] n=892 |
| len_tok | 119 [111, 127] n=892 | 119 [111, 127] n=892 |

### secondary: view=prose

| metric | mortgage-lite | mortgage-lite mortgage |
|---|---|---|
| sim_delta (primary: acct - shuf) | 0.01 [-0.06, 0.09] n=225 | 0.01 [-0.06, 0.09] n=225 |
| sim_delta[add] | 0.09 [-0.06, 0.26] n=32 | 0.09 [-0.06, 0.26] n=32 |
| sim_delta[changed] | 0.01 [-0.11, 0.15] n=79 | 0.01 [-0.11, 0.15] n=79 |
| sim_delta[invariant_replace] | 0.06 [-0.06, 0.19] n=35 | 0.06 [-0.06, 0.19] n=35 |
| sim_delta[noncrossing_replace] | 0.06 [-0.15, 0.27] n=35 | 0.06 [-0.15, 0.27] n=35 |
| sim_delta[pivotal_replace] | -0.03 [-0.16, 0.10] n=91 | -0.03 [-0.16, 0.10] n=91 |
| sim_delta[remove] | -0.03 [-0.19, 0.13] n=32 | -0.03 [-0.19, 0.13] n=32 |
| sim_delta[unchanged] | 0.01 [-0.09, 0.12] n=146 | 0.01 [-0.09, 0.12] n=146 |
| sim_acct | 0.61 [0.53, 0.69] n=225 | 0.61 [0.53, 0.69] n=225 |
| sim_acct[add] | 0.69 [0.53, 0.83] n=32 | 0.69 [0.53, 0.83] n=32 |
| sim_acct[invariant_replace] | 0.89 [0.77, 0.97] n=35 | 0.89 [0.77, 0.97] n=35 |
| sim_acct[noncrossing_replace] | 0.60 [0.44, 0.74] n=35 | 0.60 [0.44, 0.74] n=35 |
| sim_acct[pivotal_replace] | 0.52 [0.40, 0.63] n=91 | 0.52 [0.40, 0.63] n=91 |
| sim_acct[remove] | 0.53 [0.38, 0.70] n=32 | 0.53 [0.38, 0.70] n=32 |
| sim_shuf | 0.60 [0.53, 0.68] n=225 | 0.60 [0.53, 0.68] n=225 |
| sim_shuf[add] | 0.59 [0.44, 0.75] n=32 | 0.59 [0.44, 0.75] n=32 |
| sim_shuf[invariant_replace] | 0.83 [0.70, 0.94] n=35 | 0.83 [0.70, 0.94] n=35 |
| sim_shuf[noncrossing_replace] | 0.54 [0.37, 0.71] n=35 | 0.54 [0.37, 0.71] n=35 |
| sim_shuf[pivotal_replace] | 0.55 [0.43, 0.67] n=91 | 0.55 [0.43, 0.67] n=91 |
| sim_shuf[remove] | 0.56 [0.39, 0.74] n=32 | 0.56 [0.39, 0.74] n=32 |
| sim_gross (acct - noacc) | 0.28 [0.20, 0.35] n=225 | 0.28 [0.20, 0.35] n=225 |
| sim_gross[add] | 0.38 [0.24, 0.53] n=32 | 0.38 [0.24, 0.53] n=32 |
| sim_gross[invariant_replace] | 0.37 [0.21, 0.55] n=35 | 0.37 [0.21, 0.55] n=35 |
| sim_gross[noncrossing_replace] | 0.29 [0.12, 0.46] n=35 | 0.29 [0.12, 0.46] n=35 |
| sim_gross[pivotal_replace] | 0.26 [0.15, 0.39] n=91 | 0.26 [0.15, 0.39] n=91 |
| sim_gross[remove] | 0.09 [-0.09, 0.29] n=32 | 0.09 [-0.09, 0.29] n=32 |
| sim_noacc | 0.34 [0.28, 0.40] n=225 | 0.34 [0.28, 0.40] n=225 |
| sim_noacc[add] | 0.31 [0.18, 0.42] n=32 | 0.31 [0.18, 0.42] n=32 |
| sim_noacc[invariant_replace] | 0.51 [0.33, 0.70] n=35 | 0.51 [0.33, 0.70] n=35 |
| sim_noacc[noncrossing_replace] | 0.31 [0.17, 0.46] n=35 | 0.31 [0.17, 0.46] n=35 |
| sim_noacc[pivotal_replace] | 0.25 [0.17, 0.34] n=91 | 0.25 [0.17, 0.34] n=91 |
| sim_noacc[remove] | 0.44 [0.25, 0.60] n=32 | 0.44 [0.25, 0.60] n=32 |
| sim_const_unchanged (baseline: frozen decision) | 0.65 [0.59, 0.71] n=225 | 0.65 [0.59, 0.71] n=225 |
| sim_const_unchanged[add] | 0.66 [0.50, 0.80] n=32 | 0.66 [0.50, 0.80] n=32 |
| sim_const_unchanged[invariant_replace] | 0.97 [0.91, 1.00] n=35 | 0.97 [0.91, 1.00] n=35 |
| sim_const_unchanged[noncrossing_replace] | 0.77 [0.62, 0.89] n=35 | 0.77 [0.62, 0.89] n=35 |
| sim_const_unchanged[pivotal_replace] | 0.46 [0.37, 0.57] n=91 | 0.46 [0.37, 0.57] n=91 |
| sim_const_unchanged[remove] | 0.69 [0.50, 0.86] n=32 | 0.69 [0.50, 0.86] n=32 |
| sim_oracle (baseline: engine label) | 0.71 [0.65, 0.76] n=225 | 0.71 [0.65, 0.76] n=225 |
| sim_oracle[add] | 0.78 [0.61, 0.93] n=32 | 0.78 [0.61, 0.93] n=32 |
| sim_oracle[invariant_replace] | 0.89 [0.78, 0.97] n=35 | 0.89 [0.78, 0.97] n=35 |
| sim_oracle[noncrossing_replace] | 0.69 [0.52, 0.82] n=35 | 0.69 [0.52, 0.82] n=35 |
| sim_oracle[pivotal_replace] | 0.74 [0.66, 0.81] n=91 | 0.74 [0.66, 0.81] n=91 |
| sim_oracle[remove] | 0.38 [0.23, 0.53] n=32 | 0.38 [0.23, 0.53] n=32 |
| self_S | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_S[pivotal_replace] | 0.50 [0.00, 1.00] n=2 | 0.50 [0.00, 1.00] n=2 |
| self_G | -0.50 [-1.00, 0.00] n=2 | -0.50 [-1.00, 0.00] n=2 |
| bank_unchanged | 0.65 [0.60, 0.69] n=368 | 0.65 [0.60, 0.69] n=368 |
| acc_maj | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_maj[interaction] | 0.81 [0.71, 0.91] n=64 | 0.81 [0.71, 0.91] n=64 |
| acc_mean | 0.81 [0.73, 0.87] n=150 | 0.81 [0.73, 0.87] n=150 |
| acc_class[approve] | 0.65 [0.56, 0.73] n=274 | 0.65 [0.56, 0.73] n=274 |
| acc_class[cannot determine] | 0.09 [0.04, 0.15] n=89 | 0.09 [0.04, 0.15] n=89 |
| acc_class[deny] | 0.93 [0.90, 0.96] n=324 | 0.93 [0.90, 0.96] n=324 |
| repeat_disagree | 0.18 [0.15, 0.21] n=687 | 0.18 [0.15, 0.21] n=687 |
| flip | 0.72 [0.65, 0.79] n=150 | 0.72 [0.65, 0.79] n=150 |
| flip~noise | 0.31 [0.24, 0.37] n=150 | 0.31 [0.24, 0.37] n=150 |
| flip[approve->deny] | 0.91 [0.84, 0.97] n=67 | 0.91 [0.84, 0.97] n=67 |
| flip[approve->deny]~noise | 0.36 [0.25, 0.47] n=67 | 0.36 [0.25, 0.47] n=67 |
| flip[deny->approve] | 0.57 [0.45, 0.67] n=83 | 0.57 [0.45, 0.67] n=83 |
| flip[deny->approve]~noise | 0.27 [0.17, 0.36] n=83 | 0.27 [0.17, 0.36] n=83 |
| flip_to_cd | 0.00 [0.00, 0.00] n=150 | 0.00 [0.00, 0.00] n=150 |
| flip_to_cd[approve->deny] | 0.00 [0.00, 0.00] n=67 | 0.00 [0.00, 0.00] n=67 |
| flip_to_cd[deny->approve] | 0.00 [0.00, 0.00] n=83 | 0.00 [0.00, 0.00] n=83 |
| cf_pair_acc | 0.53 [0.44, 0.63] n=150 | 0.53 [0.44, 0.63] n=150 |
| invariance | 0.87 [0.82, 0.93] n=150 | 0.87 [0.82, 0.93] n=150 |
| invariance~noise | 0.21 [0.16, 0.27] n=150 | 0.21 [0.16, 0.27] n=150 |
| inv_pair_acc | 0.77 [0.69, 0.83] n=150 | 0.77 [0.69, 0.83] n=150 |
| expl_valid | 0.24 [0.20, 0.28] n=674 | 0.24 [0.20, 0.28] n=674 |
| acct_consistent | 0.70 [0.66, 0.75] n=610 | 0.70 [0.66, 0.75] n=610 |
| expl_minimal | 0.25 [0.20, 0.30] n=578 | 0.25 [0.20, 0.30] n=578 |
| cite_distractor | 0.39 [0.35, 0.43] n=687 | 0.39 [0.35, 0.43] n=687 |
| cite_p_nec | 0.34 [0.31, 0.38] n=687 | 0.34 [0.31, 0.38] n=687 |
| cite_r_nec | 0.43 [0.38, 0.47] n=522 | 0.43 [0.38, 0.47] n=522 |
| assume_dec | 0.38 [0.30, 0.46] n=150 | 0.38 [0.30, 0.46] n=150 |
| assume_val | 0.43 [0.23, 0.65] n=21 | 0.43 [0.23, 0.65] n=21 |
| none_claim_disproved | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_both[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_model_only[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_neither | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_neither[vs_gold] | 1.00 [1.00, 1.00] n=21 | 1.00 [1.00, 1.00] n=21 |
| bnd_oracle_minimal | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_oracle_minimal[vs_gold] | 0.00 [0.00, 0.00] n=21 | 0.00 [0.00, 0.00] n=21 |
| bnd_invalid | 0.33 [0.21, 0.44] n=64 | 0.33 [0.21, 0.44] n=64 |
| fmt_err | 0.00 [0.00, 0.00] n=892 | 0.00 [0.00, 0.00] n=892 |
| len_chars | 430 [403, 456] n=892 | 430 [403, 456] n=892 |
| len_tok | 119 [111, 127] n=892 | 119 [111, 127] n=892 |

### descriptive splits by correctness (all)

| metric | mortgage-lite | mortgage-lite mortgage |
|---|---|---|
| sim_delta|correct | 0.01 [-0.07, 0.10] n=163 | 0.01 [-0.07, 0.10] n=163 |
| sim_delta|wrong | 0.02 [-0.12, 0.17] n=62 | 0.02 [-0.12, 0.17] n=62 |
| sim_delta[add]|correct | 0.00 [-0.30, 0.30] n=10 | 0.00 [-0.30, 0.30] n=10 |
| sim_delta[add]|wrong | 0.14 [-0.05, 0.35] n=22 | 0.14 [-0.05, 0.35] n=22 |
| sim_delta[changed]|correct | 0.03 [-0.11, 0.18] n=66 | 0.03 [-0.11, 0.18] n=66 |
| sim_delta[changed]|wrong | -0.08 [-0.33, 0.17] n=13 | -0.08 [-0.33, 0.17] n=13 |
| sim_delta[invariant_replace]|correct | 0.13 [0.03, 0.27] n=30 | 0.13 [0.03, 0.27] n=30 |
| sim_delta[invariant_replace]|wrong | -0.40 [-0.80, 0.00] n=5 | -0.40 [-0.80, 0.00] n=5 |
| sim_delta[noncrossing_replace]|correct | 0.12 [-0.12, 0.33] n=26 | 0.12 [-0.12, 0.33] n=26 |
| sim_delta[noncrossing_replace]|wrong | -0.11 [-0.56, 0.33] n=9 | -0.11 [-0.56, 0.33] n=9 |
| sim_delta[pivotal_replace]|correct | -0.07 [-0.21, 0.08] n=73 | -0.07 [-0.21, 0.08] n=73 |
| sim_delta[pivotal_replace]|wrong | 0.11 [0.00, 0.29] n=18 | 0.11 [0.00, 0.29] n=18 |
| sim_delta[remove]|correct | 0.00 [-0.17, 0.21] n=24 | 0.00 [-0.17, 0.21] n=24 |
| sim_delta[remove]|wrong | -0.12 [-0.38, 0.00] n=8 | -0.12 [-0.38, 0.00] n=8 |
| sim_delta[unchanged]|correct | 0.00 [-0.11, 0.12] n=97 | 0.00 [-0.11, 0.12] n=97 |
| sim_delta[unchanged]|wrong | 0.04 [-0.10, 0.21] n=49 | 0.04 [-0.10, 0.21] n=49 |
| sim_acct|correct | 0.58 [0.50, 0.65] n=163 | 0.58 [0.50, 0.65] n=163 |
| sim_acct|wrong | 0.71 [0.59, 0.81] n=62 | 0.71 [0.59, 0.81] n=62 |
| sim_acct[add]|correct | 0.60 [0.33, 0.89] n=10 | 0.60 [0.33, 0.89] n=10 |
| sim_acct[add]|wrong | 0.73 [0.52, 0.90] n=22 | 0.73 [0.52, 0.90] n=22 |
| sim_acct[invariant_replace]|correct | 0.97 [0.89, 1.00] n=30 | 0.97 [0.89, 1.00] n=30 |
| sim_acct[invariant_replace]|wrong | 0.40 [0.00, 0.80] n=5 | 0.40 [0.00, 0.80] n=5 |
| sim_acct[noncrossing_replace]|correct | 0.69 [0.52, 0.85] n=26 | 0.69 [0.52, 0.85] n=26 |
| sim_acct[noncrossing_replace]|wrong | 0.33 [0.00, 0.67] n=9 | 0.33 [0.00, 0.67] n=9 |
| sim_acct[pivotal_replace]|correct | 0.40 [0.29, 0.51] n=73 | 0.40 [0.29, 0.51] n=73 |
| sim_acct[pivotal_replace]|wrong | 1.00 [1.00, 1.00] n=18 | 1.00 [1.00, 1.00] n=18 |
| sim_acct[remove]|correct | 0.50 [0.32, 0.67] n=24 | 0.50 [0.32, 0.67] n=24 |
| sim_acct[remove]|wrong | 0.62 [0.25, 0.88] n=8 | 0.62 [0.25, 0.88] n=8 |
| sim_shuf|correct | 0.56 [0.49, 0.65] n=163 | 0.56 [0.49, 0.65] n=163 |
| sim_shuf|wrong | 0.69 [0.58, 0.80] n=62 | 0.69 [0.58, 0.80] n=62 |
| sim_shuf[add]|correct | 0.60 [0.30, 0.89] n=10 | 0.60 [0.30, 0.89] n=10 |
| sim_shuf[add]|wrong | 0.59 [0.38, 0.78] n=22 | 0.59 [0.38, 0.78] n=22 |
| sim_shuf[invariant_replace]|correct | 0.83 [0.69, 0.96] n=30 | 0.83 [0.69, 0.96] n=30 |
| sim_shuf[invariant_replace]|wrong | 0.80 [0.40, 1.00] n=5 | 0.80 [0.40, 1.00] n=5 |
| sim_shuf[noncrossing_replace]|correct | 0.58 [0.40, 0.76] n=26 | 0.58 [0.40, 0.76] n=26 |
| sim_shuf[noncrossing_replace]|wrong | 0.44 [0.11, 0.78] n=9 | 0.44 [0.11, 0.78] n=9 |
| sim_shuf[pivotal_replace]|correct | 0.47 [0.35, 0.59] n=73 | 0.47 [0.35, 0.59] n=73 |
| sim_shuf[pivotal_replace]|wrong | 0.89 [0.71, 1.00] n=18 | 0.89 [0.71, 1.00] n=18 |
| sim_shuf[remove]|correct | 0.50 [0.30, 0.68] n=24 | 0.50 [0.30, 0.68] n=24 |
| sim_shuf[remove]|wrong | 0.75 [0.50, 1.00] n=8 | 0.75 [0.50, 1.00] n=8 |
| sim_gross|correct | 0.23 [0.14, 0.33] n=163 | 0.23 [0.14, 0.33] n=163 |
| sim_gross|wrong | 0.39 [0.25, 0.51] n=62 | 0.39 [0.25, 0.51] n=62 |
| sim_gross[add]|correct | 0.20 [0.00, 0.50] n=10 | 0.20 [0.00, 0.50] n=10 |
| sim_gross[add]|wrong | 0.45 [0.26, 0.67] n=22 | 0.45 [0.26, 0.67] n=22 |
| sim_gross[invariant_replace]|correct | 0.40 [0.21, 0.59] n=30 | 0.40 [0.21, 0.59] n=30 |
| sim_gross[invariant_replace]|wrong | 0.20 [0.00, 0.60] n=5 | 0.20 [0.00, 0.60] n=5 |
| sim_gross[noncrossing_replace]|correct | 0.31 [0.15, 0.50] n=26 | 0.31 [0.15, 0.50] n=26 |
| sim_gross[noncrossing_replace]|wrong | 0.22 [-0.22, 0.56] n=9 | 0.22 [-0.22, 0.56] n=9 |
| sim_gross[pivotal_replace]|correct | 0.19 [0.08, 0.32] n=73 | 0.19 [0.08, 0.32] n=73 |
| sim_gross[pivotal_replace]|wrong | 0.56 [0.29, 0.78] n=18 | 0.56 [0.29, 0.78] n=18 |
| sim_gross[remove]|correct | 0.08 [-0.16, 0.33] n=24 | 0.08 [-0.16, 0.33] n=24 |
| sim_gross[remove]|wrong | 0.12 [0.00, 0.38] n=8 | 0.12 [0.00, 0.38] n=8 |
| sim_noacc|correct | 0.34 [0.26, 0.42] n=163 | 0.34 [0.26, 0.42] n=163 |
| sim_noacc|wrong | 0.32 [0.23, 0.43] n=62 | 0.32 [0.23, 0.43] n=62 |
| sim_noacc[add]|correct | 0.40 [0.11, 0.67] n=10 | 0.40 [0.11, 0.67] n=10 |
| sim_noacc[add]|wrong | 0.27 [0.10, 0.44] n=22 | 0.27 [0.10, 0.44] n=22 |
| sim_noacc[invariant_replace]|correct | 0.57 [0.38, 0.75] n=30 | 0.57 [0.38, 0.75] n=30 |
| sim_noacc[invariant_replace]|wrong | 0.20 [0.00, 0.60] n=5 | 0.20 [0.00, 0.60] n=5 |
| sim_noacc[noncrossing_replace]|correct | 0.38 [0.21, 0.56] n=26 | 0.38 [0.21, 0.56] n=26 |
| sim_noacc[noncrossing_replace]|wrong | 0.11 [0.00, 0.33] n=9 | 0.11 [0.00, 0.33] n=9 |
| sim_noacc[pivotal_replace]|correct | 0.21 [0.12, 0.30] n=73 | 0.21 [0.12, 0.30] n=73 |
| sim_noacc[pivotal_replace]|wrong | 0.44 [0.22, 0.71] n=18 | 0.44 [0.22, 0.71] n=18 |
| sim_noacc[remove]|correct | 0.42 [0.21, 0.61] n=24 | 0.42 [0.21, 0.61] n=24 |
| sim_noacc[remove]|wrong | 0.50 [0.12, 0.88] n=8 | 0.50 [0.12, 0.88] n=8 |
| sim_const_unchanged|correct | 0.60 [0.53, 0.66] n=163 | 0.60 [0.53, 0.66] n=163 |
| sim_const_unchanged|wrong | 0.79 [0.69, 0.88] n=62 | 0.79 [0.69, 0.88] n=62 |
| sim_const_unchanged[add]|correct | 0.60 [0.33, 0.89] n=10 | 0.60 [0.33, 0.89] n=10 |
| sim_const_unchanged[add]|wrong | 0.68 [0.48, 0.86] n=22 | 0.68 [0.48, 0.86] n=22 |
| sim_const_unchanged[invariant_replace]|correct | 1.00 [1.00, 1.00] n=30 | 1.00 [1.00, 1.00] n=30 |
| sim_const_unchanged[invariant_replace]|wrong | 0.80 [0.40, 1.00] n=5 | 0.80 [0.40, 1.00] n=5 |
| sim_const_unchanged[noncrossing_replace]|correct | 0.81 [0.62, 0.95] n=26 | 0.81 [0.62, 0.95] n=26 |
| sim_const_unchanged[noncrossing_replace]|wrong | 0.67 [0.33, 0.89] n=9 | 0.67 [0.33, 0.89] n=9 |
| sim_const_unchanged[pivotal_replace]|correct | 0.33 [0.24, 0.43] n=73 | 0.33 [0.24, 0.43] n=73 |
| sim_const_unchanged[pivotal_replace]|wrong | 1.00 [1.00, 1.00] n=18 | 1.00 [1.00, 1.00] n=18 |
| sim_const_unchanged[remove]|correct | 0.67 [0.46, 0.86] n=24 | 0.67 [0.46, 0.86] n=24 |
| sim_const_unchanged[remove]|wrong | 0.75 [0.50, 1.00] n=8 | 0.75 [0.50, 1.00] n=8 |
| sim_oracle|correct | 0.74 [0.67, 0.79] n=163 | 0.74 [0.67, 0.79] n=163 |
| sim_oracle|wrong | 0.63 [0.54, 0.73] n=62 | 0.63 [0.54, 0.73] n=62 |
| sim_oracle[add]|correct | 0.90 [0.67, 1.00] n=10 | 0.90 [0.67, 1.00] n=10 |
| sim_oracle[add]|wrong | 0.73 [0.52, 0.91] n=22 | 0.73 [0.52, 0.91] n=22 |
| sim_oracle[invariant_replace]|correct | 1.00 [1.00, 1.00] n=30 | 1.00 [1.00, 1.00] n=30 |
| sim_oracle[invariant_replace]|wrong | 0.20 [0.00, 0.60] n=5 | 0.20 [0.00, 0.60] n=5 |
| sim_oracle[noncrossing_replace]|correct | 0.81 [0.62, 0.95] n=26 | 0.81 [0.62, 0.95] n=26 |
| sim_oracle[noncrossing_replace]|wrong | 0.33 [0.11, 0.67] n=9 | 0.33 [0.11, 0.67] n=9 |
| sim_oracle[pivotal_replace]|correct | 0.67 [0.57, 0.76] n=73 | 0.67 [0.57, 0.76] n=73 |
| sim_oracle[pivotal_replace]|wrong | 1.00 [1.00, 1.00] n=18 | 1.00 [1.00, 1.00] n=18 |
| sim_oracle[remove]|correct | 0.46 [0.30, 0.61] n=24 | 0.46 [0.30, 0.61] n=24 |
| sim_oracle[remove]|wrong | 0.12 [0.00, 0.38] n=8 | 0.12 [0.00, 0.38] n=8 |
| self_S|correct | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| self_S|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| self_S[pivotal_replace]|correct | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| self_S[pivotal_replace]|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| self_G|correct | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| self_G|wrong | -1.00 [-1.00, -1.00] n=1 | -1.00 [-1.00, -1.00] n=1 |
| bank_unchanged|correct | 0.61 [0.56, 0.67] n=264 | 0.61 [0.56, 0.67] n=264 |
| bank_unchanged|wrong | 0.73 [0.65, 0.81] n=104 | 0.73 [0.65, 0.81] n=104 |
| flip|correct | 0.66 [0.57, 0.74] n=121 | 0.66 [0.57, 0.74] n=121 |
| flip|wrong | 0.97 [0.88, 1.00] n=29 | 0.97 [0.88, 1.00] n=29 |
| flip~noise|correct | 0.31 [0.22, 0.38] n=121 | 0.31 [0.22, 0.38] n=121 |
| flip~noise|wrong | 0.31 [0.15, 0.52] n=29 | 0.31 [0.15, 0.52] n=29 |
| flip[approve->deny]|correct | 0.87 [0.76, 0.95] n=45 | 0.87 [0.76, 0.95] n=45 |
| flip[approve->deny]|wrong | 1.00 [1.00, 1.00] n=22 | 1.00 [1.00, 1.00] n=22 |
| flip[approve->deny]~noise|correct | 0.38 [0.25, 0.52] n=45 | 0.38 [0.25, 0.52] n=45 |
| flip[approve->deny]~noise|wrong | 0.32 [0.14, 0.50] n=22 | 0.32 [0.14, 0.50] n=22 |
| flip[deny->approve]|correct | 0.54 [0.42, 0.66] n=76 | 0.54 [0.42, 0.66] n=76 |
| flip[deny->approve]|wrong | 0.86 [0.50, 1.00] n=7 | 0.86 [0.50, 1.00] n=7 |
| flip[deny->approve]~noise|correct | 0.26 [0.17, 0.37] n=76 | 0.26 [0.17, 0.37] n=76 |
| flip[deny->approve]~noise|wrong | 0.29 [0.00, 0.67] n=7 | 0.29 [0.00, 0.67] n=7 |
| flip_to_cd|correct | 0.00 [0.00, 0.00] n=121 | 0.00 [0.00, 0.00] n=121 |
| flip_to_cd|wrong | 0.00 [0.00, 0.00] n=29 | 0.00 [0.00, 0.00] n=29 |
| flip_to_cd[approve->deny]|correct | 0.00 [0.00, 0.00] n=45 | 0.00 [0.00, 0.00] n=45 |
| flip_to_cd[approve->deny]|wrong | 0.00 [0.00, 0.00] n=22 | 0.00 [0.00, 0.00] n=22 |
| flip_to_cd[deny->approve]|correct | 0.00 [0.00, 0.00] n=76 | 0.00 [0.00, 0.00] n=76 |
| flip_to_cd[deny->approve]|wrong | 0.00 [0.00, 0.00] n=7 | 0.00 [0.00, 0.00] n=7 |
| cf_pair_acc|correct | 0.66 [0.57, 0.74] n=121 | 0.66 [0.57, 0.74] n=121 |
| cf_pair_acc|wrong | 0.00 [0.00, 0.00] n=29 | 0.00 [0.00, 0.00] n=29 |
| invariance|correct | 0.95 [0.91, 0.98] n=121 | 0.95 [0.91, 0.98] n=121 |
| invariance|wrong | 0.55 [0.38, 0.74] n=29 | 0.55 [0.38, 0.74] n=29 |
| invariance~noise|correct | 0.17 [0.10, 0.23] n=121 | 0.17 [0.10, 0.23] n=121 |
| invariance~noise|wrong | 0.41 [0.27, 0.60] n=29 | 0.41 [0.27, 0.60] n=29 |
| inv_pair_acc|correct | 0.95 [0.91, 0.98] n=121 | 0.95 [0.91, 0.98] n=121 |
| inv_pair_acc|wrong | 0.00 [0.00, 0.00] n=29 | 0.00 [0.00, 0.00] n=29 |
| expl_valid|correct | 0.29 [0.23, 0.34] n=476 | 0.29 [0.23, 0.34] n=476 |
| expl_valid|wrong | 0.14 [0.10, 0.18] n=198 | 0.14 [0.10, 0.18] n=198 |
| acct_consistent|correct | 0.97 [0.95, 0.99] n=438 | 0.97 [0.95, 0.99] n=438 |
| acct_consistent|wrong | 0.02 [0.00, 0.05] n=172 | 0.02 [0.00, 0.05] n=172 |
| expl_minimal|correct | 0.31 [0.25, 0.37] n=461 | 0.31 [0.25, 0.37] n=461 |
| expl_minimal|wrong | 0.00 [0.00, 0.00] n=117 | 0.00 [0.00, 0.00] n=117 |
| cite_distractor|correct | 0.34 [0.29, 0.39] n=487 | 0.34 [0.29, 0.39] n=487 |
| cite_distractor|wrong | 0.53 [0.45, 0.61] n=200 | 0.53 [0.45, 0.61] n=200 |
| cite_p_nec|correct | 0.38 [0.34, 0.43] n=487 | 0.38 [0.34, 0.43] n=487 |
| cite_p_nec|wrong | 0.25 [0.18, 0.31] n=200 | 0.25 [0.18, 0.31] n=200 |
| cite_r_nec|correct | 0.50 [0.45, 0.55] n=405 | 0.50 [0.45, 0.55] n=405 |
| cite_r_nec|wrong | 0.21 [0.16, 0.26] n=117 | 0.21 [0.16, 0.26] n=117 |
| assume_dec|correct | 0.43 [0.35, 0.51] n=121 | 0.43 [0.35, 0.51] n=121 |
| assume_dec|wrong | 0.17 [0.06, 0.31] n=29 | 0.17 [0.06, 0.31] n=29 |
| assume_val|correct | 0.41 [0.18, 0.65] n=17 | 0.41 [0.18, 0.65] n=17 |
| assume_val|wrong | 0.50 [0.00, 1.00] n=4 | 0.50 [0.00, 1.00] n=4 |
| none_claim_disproved|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_correct|wrong | 0.00 [0.00, 0.00] n=1 | 0.00 [0.00, 0.00] n=1 |
| none_claim_unresolved|wrong | 1.00 [1.00, 1.00] n=1 | 1.00 [1.00, 1.00] n=1 |
| bnd_both|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_both|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_both[vs_gold]|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_both[vs_gold]|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_oracle_only|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_oracle_only|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_oracle_only[vs_gold]|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_oracle_only[vs_gold]|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_model_only|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_model_only|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_model_only[vs_gold]|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_model_only[vs_gold]|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_neither|correct | 1.00 [1.00, 1.00] n=13 | 1.00 [1.00, 1.00] n=13 |
| bnd_neither|wrong | 1.00 [1.00, 1.00] n=8 | 1.00 [1.00, 1.00] n=8 |
| bnd_neither[vs_gold]|correct | 1.00 [1.00, 1.00] n=13 | 1.00 [1.00, 1.00] n=13 |
| bnd_neither[vs_gold]|wrong | 1.00 [1.00, 1.00] n=8 | 1.00 [1.00, 1.00] n=8 |
| bnd_oracle_minimal|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_oracle_minimal|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_oracle_minimal[vs_gold]|correct | 0.00 [0.00, 0.00] n=13 | 0.00 [0.00, 0.00] n=13 |
| bnd_oracle_minimal[vs_gold]|wrong | 0.00 [0.00, 0.00] n=8 | 0.00 [0.00, 0.00] n=8 |
| bnd_invalid|correct | 0.29 [0.17, 0.42] n=45 | 0.29 [0.17, 0.42] n=45 |
| bnd_invalid|wrong | 0.42 [0.22, 0.65] n=19 | 0.42 [0.22, 0.65] n=19 |

### coverage

| count | mortgage-lite |
|---|---|
| acct_consistent_unscored | 77 |
| api_error | 0 |
| bank_unscored | 1825 |
| boundary_derived_refused | 85 |
| boundary_invalid_value | 21 |
| boundary_pending | 43 |
| const_unchanged_parse_fail | 0 |
| expl_uncertified | 13 |
| flip_parse_fail_pairs | 0 |
| fmt_err | 0 |
| interventions_requested | 404 |
| invariance_parse_fail_pairs | 0 |
| items_in_data | 4044 |
| items_scored | 687 |
| necessity_pending | 361 |
| none_claim_unresolved | 1 |
| none_unsupported_assume | 12 |
| none_unsupported_support | 0 |
| oracle_parse_fail | 0 |
| outputs | 892 |
| parse_fail | 0 |
| predict_parse_fail | 0 |
| sim_items_shared | 225 |
| simulate_noacc_parse_fail | 2 |
| simulate_parse_fail | 0 |
| simulate_shuf_parse_fail | 0 |
| truncated | 0 |

json=runs/mortgage-lite.eval.json
