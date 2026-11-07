"""Run a set of cases through a model with vLLM and save every output.

Each case is a line in a JSONL file with "id" and "application". The prompt is
the template file with {application} filled in. Each run setting ("mode") is
sampled the given number of times.

Example:
  python pilots/mortgage/run_vllm_batch.py --model Qwen/Qwen3.5-9B \
      --template pilots/mortgage/prompt.txt --cases pilots/mortgage/cases.jsonl \
      --out pilots/mortgage/out/baseline.jsonl
"""
import argparse
import json
import time
from pathlib import Path

from vllm import LLM, SamplingParams

# Sampling settings follow the Qwen3.5 model card, except "nothink-greedy".
MODES = {
    "nothink-greedy": dict(thinking=False, n=1, params=dict(temperature=0.0, max_tokens=1024)),
    "nothink-sampled": dict(thinking=False, n=3, params=dict(
        temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5, max_tokens=1024)),
    "think-sampled": dict(thinking=True, n=3, params=dict(
        temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5, max_tokens=12000)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--modes", nargs="+", default=list(MODES))
    ap.add_argument("--max-model-len", type=int, default=16384)
    args = ap.parse_args()

    template = args.template.read_text()
    cases = [json.loads(l) for l in args.cases.read_text().splitlines() if l.strip()]

    engine_kwargs = dict(model=args.model, max_model_len=args.max_model_len,
                         gpu_memory_utilization=0.90, seed=0)
    try:  # skip the vision encoder when the vLLM version supports it
        llm = LLM(**engine_kwargs, language_model_only=True)
    except TypeError:
        llm = LLM(**engine_kwargs, limit_mm_per_prompt={"image": 0, "video": 0})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for mode in args.modes:
            cfg = MODES[mode]
            sp = SamplingParams(n=cfg["n"], seed=0, **cfg["params"])
            msgs = [[{"role": "user", "content": template.replace("{application}", c["application"])}]
                    for c in cases]
            t0 = time.time()
            results = llm.chat(msgs, sp, chat_template_kwargs={"enable_thinking": cfg["thinking"]})
            print(f"{mode}: {len(cases)} cases x {cfg['n']} in {time.time() - t0:.1f}s", flush=True)
            for c, m, r in zip(cases, msgs, results):
                for i, o in enumerate(r.outputs):
                    fh.write(json.dumps({
                        "model": args.model, "mode": mode, "sample": i, "id": c["id"],
                        "prompt": m[0]["content"], "output": o.text,
                        "finish_reason": o.finish_reason, "n_tokens": len(o.token_ids),
                        "expected": c.get("expected"),
                    }) + "\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
