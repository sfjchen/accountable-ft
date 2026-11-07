"""LoRA SFT of Qwen3.5-9B on the SFT rows of scripts/sft_data.py, for the 2 matched conditions of PLAN.md 3.3.

Both conditions train on the same sequences (harness prompt, then the gold answer, decision first). The loss of one
example is L = mean_dec + lam * mean_acc: mean_dec is the mean token loss over the decision tokens (the Decision line
plus the end-of-turn marker after the answer), mean_acc the mean over the account lines (the row's mask_spans), and
the batch loss is the mean over examples. The Collator encodes this as per-token weights, 1 / n_dec on each decision
token and lam / n_acc on each account token, so the decision tokens carry total weight 1 per example in both
conditions however long the account is. --condition account uses lam = --acc-weight (default 1.0), --condition
decision uses lam = 0 exactly and sets the account labels to -100. The prompt is masked in both. The Collator
tokenizes the chat template with thinking off (enable_thinking False) and maps character spans to tokens by offset
mapping. Before training it checks on a sample that the training prefix equals the inference prompt with the
generation prompt, that the account tokens decode to exactly the account text, that the supervised tokens decode to
exactly the decision line plus the end-of-turn marker (lam 0) or the whole answer plus it, and that the weights sum
to 1 on the decision tokens and lam on the account tokens.

The model loads through Unsloth (FastLanguageModel, bf16, no 4-bit) and trains with a TRL SFTTrainer subclass whose
compute_loss applies the weights, saving a checkpoint each epoch, then the final adapter in <out>/adapter and the
merged 16-bit model in <out>/merged. <out>/train_meta.json records every flag, lam, the commit and dirty state, the
pinned and installed library versions, the GPU, token counts, the masked-token fraction and the realized weight
sums, then the training log. Unsloth, torch and TRL are imported inside main, so the Collator imports and runs on a
machine without CUDA. Stack (co-installs, since unsloth caps trl at 1.15 and transformers at 5.17): PINS below.

Usage:
  python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl \
          --seed 0 --out outputs/acct-s0 [--acc-weight 1.0]
"""
import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIBS = ["unsloth", "unsloth_zoo", "torch", "transformers", "trl", "peft", "vllm", "datasets", "accelerate",
        "bitsandbytes"]
PINS = {"unsloth": "2026.11.3", "trl": "1.15.0", "transformers": "5.17.0", "peft": "0.21.2", "torch": "2.14.0+cu126",
        "vllm": "0.33.0"}
PROJ = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


class Collator:
    """
    Turns SFT rows into padded input_ids, attention_mask, labels and per-token loss weights for one condition
    (account or decision).
    """

    def __init__(self, tok, cond, max_len=4096, lam=1.0):
        """
        Keeps the text tokenizer (the inner one when tok is a multimodal processor), the condition, the length cap
        and the account weight lam, which is 0 under the decision condition whatever lam is passed.
        """
        assert cond in ("account", "decision"), cond
        self.tk, self.cond, self.max_len = getattr(tok, "tokenizer", tok), cond, max_len
        self.lam = float(lam) if cond == "account" else 0.0
        assert self.lam >= 0, lam
        self.pad = self.tk.pad_token_id if self.tk.pad_token_id is not None else self.tk.eos_token_id

    def encode(self, ex):
        """
        Returns the token ids, labels, weights and per-token flags of one row: sup marks the answer region (answer
        content plus the end-of-turn marker), acct the account tokens inside it, w is 1 / n_dec on the other sup
        tokens (the decision tokens), lam / n_acc on acct and 0 elsewhere, and lab the ids where w > 0, else -100.
        Also returns the rendered text and the answer's char offset.
        """
        # Qwen3.5 has thinking off by default per Unsloth's docs, the flag keeps it off if the template changes
        txt = self.tk.apply_chat_template(ex["messages"], tokenize=False, enable_thinking=False)
        cs = txt.rindex(ex["messages"][-1]["content"])
        se, spans = len(txt.rstrip()), [(cs + a, cs + b) for a, b in ex["mask_spans"]]
        enc = self.tk(txt, add_special_tokens=False, return_offsets_mapping=True, truncation=True,
                max_length=self.max_len)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        sup = [cs <= a < se for a, _ in offs]
        acct = [s and any(x <= a < y for x, y in spans) for s, (a, _) in zip(sup, offs)]
        nd, na = sum(sup) - sum(acct), sum(acct)
        w = [(self.lam / na if c else 1 / nd) if s else 0.0 for s, c in zip(sup, acct)]
        return {"ids": ids, "lab": [i if x > 0 else -100 for i, x in zip(ids, w)], "w": w, "sup": sup, "acct": acct,
                "txt": txt, "cs": cs, "trunc": len(ids) == self.max_len and se > offs[-1][1]}

    def check(self, ex):
        """
        Asserts the masking of one row: the prefix before the answer equals the inference prompt, the account tokens
        decode to exactly the mask_spans text, the supervised tokens decode to exactly the answer text left in the
        loss plus the end-of-turn marker, the decision line is supervised, the masked answer tokens are exactly the
        account tokens when lam is 0 (none otherwise), and the weights sum to 1 on the decision tokens and lam on
        the account tokens. Returns the encoding.
        """
        e, msg = self.encode(ex), ex["messages"]
        gen = self.tk.apply_chat_template(msg[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        assert e["txt"][:e["cs"]] == gen, (ex["id"], e["txt"][:e["cs"]][-80:], gen[-80:])
        assert not e["trunc"], f"{ex['id']} is truncated at {self.max_len} tokens"
        c, dec = msg[-1]["content"], self.tk.decode
        acc = "".join(c[a:b] for a, b in ex["mask_spans"])
        keep = c[:ex["mask_spans"][0][0]] if self.lam == 0 else c
        tail = e["txt"][e["cs"] + len(c):].rstrip()
        assert dec([i for i, f in zip(e["ids"], e["acct"]) if f]) == acc, ex["id"]
        assert dec([i for i in e["lab"] if i != -100]) == keep + tail, ex["id"]
        assert c.startswith("Decision: ") and c[:ex["mask_spans"][0][0]].count("\n") == 1, ex["id"]
        nm = sum(s and l == -100 for s, l in zip(e["sup"], e["lab"]))
        assert nm == (sum(e["acct"]) if self.lam == 0 else 0), (ex["id"], nm, sum(e["acct"]))
        wd = sum(x for x, s, f in zip(e["w"], e["sup"], e["acct"]) if s and not f)
        wa = sum(x for x, f in zip(e["w"], e["acct"]) if f)
        assert abs(wd - 1) < 1e-9 and abs(wa - self.lam) < 1e-9, (ex["id"], wd, wa)
        return e

    def __call__(self, exs):
        """
        Encodes and right-pads a batch, returning torch tensors for the trainer (weights 0 on padding).
        """
        import torch
        es = [self.encode(x) for x in exs]
        n = max(len(e["ids"]) for e in es)
        return {"input_ids": torch.tensor([e["ids"] + [self.pad] * (n - len(e["ids"])) for e in es]),
                "attention_mask": torch.tensor([[1] * len(e["ids"]) + [0] * (n - len(e["ids"])) for e in es]),
                "labels": torch.tensor([e["lab"] + [-100] * (n - len(e["ids"])) for e in es]),
                "weights": torch.tensor([e["w"] + [0.0] * (n - len(e["ids"])) for e in es], dtype=torch.float32)}


def weighted_loss(logits, labels, w):
    """
    Returns the batch loss: per example, the sum over tokens of weight times cross-entropy (mean_dec + lam *
    mean_acc under the Collator's weights), averaged over the examples. Position t of logits predicts token t + 1,
    and cross-entropy runs in float32 on the weighted positions only.
    """
    import torch
    import torch.nn.functional as F
    w, y = w[:, 1:].to(logits.device), labels[:, 1:].to(logits.device)
    m = w > 0
    ce = F.cross_entropy(logits[:, :-1][m].float(), y[m], reduction="none")
    per = torch.zeros(w.shape[0], device=logits.device).index_add_(0, m.nonzero()[:, 0], ce * w[m])
    return per.mean()


def token_stats(col, rows):
    """
    Returns token counts over rows under col's condition: all tokens, answer tokens, account tokens, supervised
    tokens, truncated rows, the fraction of answer tokens masked out of the loss, and the realized weight sums on
    the decision and account tokens (total and per row).
    """
    t = {"rows": len(rows), "tokens": 0, "answer": 0, "account": 0, "supervised": 0, "truncated": 0, "w_dec": 0.0,
            "w_acc": 0.0}
    for x in rows:
        e = col.encode(x)
        t["tokens"] += len(e["ids"])
        t["answer"] += sum(e["sup"])
        t["account"] += sum(e["acct"])
        t["supervised"] += sum(i != -100 for i in e["lab"])
        t["truncated"] += e["trunc"]
        t["w_dec"] += sum(w for w, s, a in zip(e["w"], e["sup"], e["acct"]) if s and not a)
        t["w_acc"] += sum(w for w, a in zip(e["w"], e["acct"]) if a)
    t["masked_frac"] = round(1 - t["supervised"] / max(t["answer"], 1), 6)
    for k in ("w_dec", "w_acc"):
        t[k] = round(t[k], 6)
        t[k + "_per_row"] = round(t[k] / max(len(rows), 1), 6)
    return t


def main():
    """
    Parses flags, loads the model through Unsloth, checks the masking and weights, trains with the weighted loss,
    saves and writes train_meta.json.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=["account", "decision"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--eval-data")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="unsloth/Qwen3.5-9B")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--acc-weight", type=float, default=1.0, help="lam on mean_acc, account condition only")
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

    os.environ.setdefault("UNSLOTH_RETURN_LOGITS", "1")  # compute_loss needs the logits, not Unsloth's fused loss
    from unsloth import FastLanguageModel  # first, so Unsloth patches transformers and TRL before they load
    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tok = FastLanguageModel.from_pretrained(a.model, max_seq_length=a.max_len, dtype=torch.bfloat16,
            load_in_4bit=False, full_finetuning=False)
    model = FastLanguageModel.get_peft_model(model, r=a.rank, lora_alpha=a.alpha, lora_dropout=a.dropout,
            target_modules=PROJ, bias="none", use_gradient_checkpointing="unsloth", random_state=a.seed)
    col = Collator(tok, a.condition, a.max_len, a.acc_weight)
    for x in rows[:16]:
        col.check(x)
    git = lambda *c: subprocess.run(["git", "-C", str(ROOT), *c], capture_output=True, text=True).stdout.strip()
    ver = {}
    for lib in LIBS:
        try:
            ver[lib] = importlib.metadata.version(lib)
        except importlib.metadata.PackageNotFoundError:
            ver[lib] = None
    meta = {"args": vars(a), "lam": col.lam, "loss": "per example mean_dec + lam * mean_acc, mean over the batch",
            "commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")), "argv": sys.argv,
            "pins": PINS, "versions": ver, "pins_match": all(ver[k] == v for k, v in PINS.items()),
            "python": sys.version.split()[0], "lora_targets": PROJ,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "bf16": True,
            "enable_thinking": False, "check_rows": min(16, len(rows)), "train_tokens": token_stats(col, rows),
            "eval_tokens": token_stats(col, ev) if ev else None,
            "trainable_params": sum(p.numel() for p in model.parameters() if p.requires_grad)}
    (out / "train_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta["train_tokens"]))

    class WeightedTrainer(SFTTrainer):
        """
        SFTTrainer whose loss is weighted_loss over the Collator's weights instead of the token-mean cross-entropy.
        """

        def __init__(self, *args, **kw):
            """
            Builds the trainer and marks the model as not taking loss kwargs, so the Trainer divides each
            micro-batch mean by the accumulation steps and the step loss is the mean over all its examples.
            """
            super().__init__(*args, **kw)
            self.model_accepts_loss_kwargs = False

        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            """
            Runs the model without labels and returns the weighted loss (and the outputs when asked).
            """
            o = model(**{k: v for k, v in inputs.items() if k not in ("labels", "weights")})
            loss = weighted_loss(o.logits, inputs["labels"], inputs["weights"])
            return (loss, o) if return_outputs else loss

    cfg = SFTConfig(output_dir=str(out), num_train_epochs=a.epochs, learning_rate=a.lr, seed=a.seed, data_seed=a.seed,
            per_device_train_batch_size=a.batch, per_device_eval_batch_size=a.batch,
            gradient_accumulation_steps=a.grad_accum, warmup_ratio=a.warmup, weight_decay=a.weight_decay,
            lr_scheduler_type=a.scheduler, optim=a.optim, bf16=True, logging_steps=10, save_strategy="epoch",
            eval_strategy="epoch" if ev else "no", max_length=a.max_len, remove_unused_columns=False,
            prediction_loss_only=True, dataset_kwargs={"skip_prepare_dataset": True}, report_to="none")
    tr = WeightedTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(rows),
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
