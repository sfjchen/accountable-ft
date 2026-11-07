"""LoRA SFT of Qwen3.5-9B on the SFT rows of scripts/sft_data.py, for the 2 matched conditions of PLAN.md 3.3.

Both conditions train on the same sequences (harness prompt, then the gold answer, decision first). --condition
account supervises the whole answer; --condition decision sets labels to -100 on the account lines (the row's
mask_spans), so the only difference is whether the account tokens are in the loss. The prompt is masked in both, and
the end-of-turn marker after the answer is supervised in both. The Collator tokenizes the chat template with thinking
off (enable_thinking False) and maps character spans to tokens by offset mapping. Before training it checks on a
sample that the training prefix equals the inference prompt with the generation prompt, that the masked answer
tokens decode to exactly the account text, and that the supervised tokens decode to exactly the decision line plus
the end-of-turn marker (decision) or the whole answer plus it (account).

The model loads through Unsloth (FastLanguageModel, bf16, no 4-bit) and trains with TRL's SFTTrainer, saving a
checkpoint each epoch, then the final adapter in <out>/adapter and the merged 16-bit model in <out>/merged.
<out>/train_meta.json records every flag, the commit and dirty state, library versions, the GPU, token counts and
the masked-token fraction, then the training log. Unsloth, torch and TRL are imported inside main, so the Collator
imports and runs on a machine without CUDA.

Usage:
  python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl \
          --seed 0 --out outputs/acct-s0
"""
import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIBS = ["unsloth", "unsloth_zoo", "torch", "transformers", "trl", "peft", "datasets", "accelerate", "bitsandbytes"]
PROJ = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


class Collator:
    """
    Turns SFT rows into padded input_ids, attention_mask and labels for one condition (account or decision).
    """

    def __init__(self, tok, cond, max_len=4096):
        """
        Keeps the text tokenizer (the inner one when tok is a multimodal processor), the condition and the length cap.
        """
        assert cond in ("account", "decision"), cond
        self.tk, self.cond, self.max_len = getattr(tok, "tokenizer", tok), cond, max_len
        self.pad = self.tk.pad_token_id if self.tk.pad_token_id is not None else self.tk.eos_token_id

    def encode(self, ex):
        """
        Returns the token ids, labels and per-token flags of one row: sup marks the answer region (answer content
        plus the end-of-turn marker), acct the account tokens inside it, and lab the ids with -100 outside sup, and
        also on acct under the decision condition. Also returns the rendered text and the answer's char offset.
        """
        txt = self.tk.apply_chat_template(ex["messages"], tokenize=False, enable_thinking=False)
        cs = txt.rindex(ex["messages"][-1]["content"])
        se, spans = len(txt.rstrip()), [(cs + a, cs + b) for a, b in ex["mask_spans"]]
        enc = self.tk(txt, add_special_tokens=False, return_offsets_mapping=True, truncation=True,
                max_length=self.max_len)
        ids, sup, acct, lab = enc["input_ids"], [], [], []
        for i, (a, _) in zip(ids, enc["offset_mapping"]):
            sup.append(cs <= a < se)
            acct.append(any(x <= a < y for x, y in spans))
            lab.append(i if sup[-1] and not (self.cond == "decision" and acct[-1]) else -100)
        return {"ids": ids, "lab": lab, "sup": sup, "acct": acct, "txt": txt, "cs": cs,
                "trunc": len(ids) == self.max_len and se > enc["offset_mapping"][-1][1]}

    def check(self, ex):
        """
        Asserts the masking of one row: the prefix before the answer equals the inference prompt, the account tokens
        decode to exactly the mask_spans text, the supervised tokens decode to exactly the answer text left in the
        loss plus the end-of-turn marker, the decision line is supervised, and the masked answer tokens are exactly
        the account tokens under the decision condition (none under account). Returns the encoding.
        """
        e, msg = self.encode(ex), ex["messages"]
        gen = self.tk.apply_chat_template(msg[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        assert e["txt"][:e["cs"]] == gen, (ex["id"], e["txt"][:e["cs"]][-80:], gen[-80:])
        assert not e["trunc"], f"{ex['id']} is truncated at {self.max_len} tokens"
        c, dec = msg[-1]["content"], self.tk.decode
        acc = "".join(c[a:b] for a, b in ex["mask_spans"])
        keep = c[:ex["mask_spans"][0][0]] if self.cond == "decision" else c
        tail = e["txt"][e["cs"] + len(c):].rstrip()
        assert dec([i for i, f in zip(e["ids"], e["acct"]) if f]) == acc, ex["id"]
        assert dec([i for i in e["lab"] if i != -100]) == keep + tail, ex["id"]
        assert c.startswith("Decision: ") and c[:ex["mask_spans"][0][0]].count("\n") == 1, ex["id"]
        nm = sum(s and l == -100 for s, l in zip(e["sup"], e["lab"]))
        assert nm == (sum(e["acct"]) if self.cond == "decision" else 0), (ex["id"], nm, sum(e["acct"]))
        return e

    def __call__(self, exs):
        """
        Encodes and right-pads a batch, returning torch tensors for the trainer.
        """
        import torch
        es = [self.encode(x) for x in exs]
        n = max(len(e["ids"]) for e in es)
        return {"input_ids": torch.tensor([e["ids"] + [self.pad] * (n - len(e["ids"])) for e in es]),
                "attention_mask": torch.tensor([[1] * len(e["ids"]) + [0] * (n - len(e["ids"])) for e in es]),
                "labels": torch.tensor([e["lab"] + [-100] * (n - len(e["ids"])) for e in es])}


def token_stats(col, rows):
    """
    Returns token counts over rows under col's condition: all tokens, answer tokens, account tokens, supervised
    tokens, truncated rows, and the fraction of answer tokens masked out of the loss.
    """
    t = {"rows": len(rows), "tokens": 0, "answer": 0, "account": 0, "supervised": 0, "truncated": 0}
    for x in rows:
        e = col.encode(x)
        t["tokens"] += len(e["ids"])
        t["answer"] += sum(e["sup"])
        t["account"] += sum(a and s for a, s in zip(e["acct"], e["sup"]))
        t["supervised"] += sum(i != -100 for i in e["lab"])
        t["truncated"] += e["trunc"]
    t["masked_frac"] = round(1 - t["supervised"] / max(t["answer"], 1), 6)
    return t


def main():
    """
    Parses flags, loads the model through Unsloth, checks the masking, trains, saves and writes train_meta.json.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=["account", "decision"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--eval-data")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="unsloth/Qwen3.5-9B")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--warmup", type=float, default=0.03)
    ap.add_argument("--weight-decay", type=float, default=0.0)
    ap.add_argument("--scheduler", default="cosine")
    ap.add_argument("--optim", default="adamw_torch")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(ln) for ln in Path(a.data).read_text().splitlines() if ln.strip()]
    ev = [json.loads(ln) for ln in Path(a.eval_data).read_text().splitlines() if ln.strip()] if a.eval_data else []

    from unsloth import FastLanguageModel  # first, so Unsloth patches transformers and TRL before they load
    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tok = FastLanguageModel.from_pretrained(a.model, max_seq_length=a.max_len, dtype=torch.bfloat16,
            load_in_4bit=False, full_finetuning=False)
    model = FastLanguageModel.get_peft_model(model, r=a.rank, lora_alpha=a.alpha, lora_dropout=a.dropout,
            target_modules=PROJ, bias="none", use_gradient_checkpointing="unsloth", random_state=a.seed)
    col = Collator(tok, a.condition, a.max_len)
    for x in rows[:16]:
        col.check(x)
    git = lambda *c: subprocess.run(["git", "-C", str(ROOT), *c], capture_output=True, text=True).stdout.strip()
    ver = {}
    for lib in LIBS:
        try:
            ver[lib] = importlib.metadata.version(lib)
        except importlib.metadata.PackageNotFoundError:
            ver[lib] = None
    meta = {"args": vars(a), "commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")),
            "argv": sys.argv, "versions": ver, "python": sys.version.split()[0], "lora_targets": PROJ,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "bf16": True,
            "enable_thinking": False, "check_rows": min(16, len(rows)), "train_tokens": token_stats(col, rows),
            "eval_tokens": token_stats(col, ev) if ev else None,
            "trainable_params": sum(p.numel() for p in model.parameters() if p.requires_grad)}
    (out / "train_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta["train_tokens"]))
    cfg = SFTConfig(output_dir=str(out), num_train_epochs=a.epochs, learning_rate=a.lr, seed=a.seed, data_seed=a.seed,
            per_device_train_batch_size=a.batch, per_device_eval_batch_size=a.batch,
            gradient_accumulation_steps=a.grad_accum, warmup_ratio=a.warmup, weight_decay=a.weight_decay,
            lr_scheduler_type=a.scheduler, optim=a.optim, bf16=True, logging_steps=10, save_strategy="epoch",
            eval_strategy="epoch" if ev else "no", max_length=a.max_len, remove_unused_columns=False,
            dataset_kwargs={"skip_prepare_dataset": True}, report_to="none")
    tr = SFTTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(rows),
            eval_dataset=Dataset.from_list(ev) if ev else None, data_collator=col, processing_class=tok)
    res = tr.train()
    model.save_pretrained(str(out / "adapter"))
    tok.save_pretrained(str(out / "adapter"))
    model.save_pretrained_merged(str(out / "merged"), tok, save_method="merged_16bit")
    meta.update(train_metrics=res.metrics, log_history=tr.state.log_history,
            peak_mem_gb=round(torch.cuda.max_memory_allocated() / 2 ** 30, 2) if torch.cuda.is_available() else None)
    (out / "train_meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
