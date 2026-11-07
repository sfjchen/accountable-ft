#!/usr/bin/env bash
# farmshare/setup.sh: one-time, idempotent setup on a FarmShare login node.
# Clones or pulls the repo into scratch, builds the uv venv with the pinned stack, downloads Qwen3.5-9B, fetches
# data/v1.jsonl and data/v1.bank.jsonl (git-ignored) from DATA_SRC, exports the SFT data and runs sanity checks.
# Usage: DATA_SRC=<dir | host:dir | https://url-prefix> bash farmshare/setup.sh   (DATA_SRC only while data is absent)
set -euo pipefail
SCRATCH=${SCRATCH:-/scratch/users/$USER}
REPO=$SCRATCH/accountable-ft
mkdir -p "$SCRATCH"
if [[ -d $REPO/.git ]]; then
  git -C "$REPO" pull --ff-only
else
  git clone https://github.com/sfjchen/accountable-ft "$REPO"
fi
# shellcheck source=farmshare/env.sh
source "$REPO/farmshare/env.sh"
mkdir -p "$REPO/runs/slurm" "$REPO/outputs" "$HF_HOME" "$META_HOME"
cd "$REPO"

echo "== uv"
if ! command -v uv &>/dev/null; then
  module load uv &>/dev/null || true
fi
if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh
fi
uv --version

echo "== venv and pinned stack (train.PINS)"
[[ -x $VENV/bin/python ]] || uv venv --python 3.12 "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
CU=https://download.pytorch.org/whl/cu126
uv pip install "torch==2.14.0+cu126" --index-url "$CU"
# the constraint keeps torch on the cu126 build, the extra index gives matching torchvision and friends
echo "torch==2.14.0+cu126" > "$VENV/torch-pin.txt"
uv pip install -c "$VENV/torch-pin.txt" --extra-index-url "$CU" --index-strategy unsafe-best-match \
    unsloth==2026.11.3 trl==1.15.0 transformers==5.17.0 peft==0.21.2 vllm==0.33.0 huggingface_hub \
    -r requirements.txt

echo "== model"
python - <<'PY'
import os
import sys
from huggingface_hub import HfApi, snapshot_download
from huggingface_hub.utils import RepositoryNotFoundError

for m in ("unsloth/Qwen3.5-9B", "Qwen/Qwen3.5-9B"):
    try:
        HfApi().model_info(m)
    except RepositoryNotFoundError:
        print(f"{m}: not found")
        continue
    print(m, "->", snapshot_download(m))
    open(os.environ["MODEL_FILE"], "w").write(m + "\n")
    break
else:
    sys.exit("neither unsloth/Qwen3.5-9B nor Qwen/Qwen3.5-9B is available")
PY

echo "== data"
for f in v1.jsonl v1.bank.jsonl; do
  [[ -s data/$f ]] && continue
  [[ -n ${DATA_SRC:-} ]] || die "data/$f is git-ignored and absent. Set DATA_SRC to a directory, host:dir or" \
      "https URL prefix holding v1.jsonl and v1.bank.jsonl (see farmshare/README.md)"
  case $DATA_SRC in
    http://* | https://*) curl -fL -o "data/$f.part" "$DATA_SRC/$f" ;;
    *) rsync -a "$DATA_SRC/$f" "data/$f.part" ;;
  esac
  mv "data/$f.part" "data/$f"
done
sha256sum data/v1.jsonl data/v1.bank.jsonl data/v1.flagged.txt

echo "== SFT export"
for s in train dev; do
  python scripts/sft_data.py --split "$s" --drop-flagged data/v1.flagged.txt --out "data/v1.sft.$s.jsonl"
done

echo "== sanity"
python -c "import torch, transformers, trl, peft, vllm, openai, yaml, numpy, google.genai, infer, evaluate, engine, gen
print('imports ok, torch', torch.__version__, 'cuda', torch.version.cuda)
assert torch.version.cuda == '12.6', torch.version.cuda"
python - <<'PY'
import importlib.metadata as md
import sys
from train import PINS

got = {k: md.version(k) for k in PINS}
for k, v in PINS.items():
    print(f"{k:14} pinned {v:14} installed {got[k]:14} {'ok' if got[k] == v else 'MISMATCH'}")
sys.exit(0 if got == PINS else "installed versions differ from train.PINS")
PY
# masking and weight checks of train.Collator with the real tokenizer on 16 exported rows
python - <<'PY'
import itertools
import json
import os
from transformers import AutoTokenizer
from train import Collator

tok = AutoTokenizer.from_pretrained(open(os.environ["MODEL_FILE"]).read().strip())
with open("data/v1.sft.train.jsonl") as fh:
    rows = [json.loads(ln) for ln in itertools.islice(fh, 16)]
for c in ("account", "decision"):
    col = Collator(tok, c)
    for r in rows:
        col.check(r)
print("Collator.check ok on", len(rows), "rows, both conditions")
PY
echo "setup done: repo $REPO, model $(cat "$MODEL_FILE"), venv $VENV"
