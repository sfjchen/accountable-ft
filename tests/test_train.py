"""
Tests the SFT export (scripts/sft_data.py) and the loss-masking Collator of train.py with the Qwen2.5-0.5B-Instruct
tokenizer (no model weights): on rows exported from data/smoke.jsonl, the decision condition masks exactly the
account tokens, the account condition masks only the prompt, and supervised token counts differ by the account
length. Skips when the tokenizer cannot be loaded (no network and no cache) or the smoke data is missing.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "data/smoke.jsonl"
sys.path.insert(0, str(ROOT))
pytestmark = pytest.mark.skipif(not SMOKE.exists(), reason="needs data/smoke.jsonl")


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    """
    Exports the smoke train split twice under the same seed, checks the files are identical, and returns the rows.
    """
    outs = [tmp_path_factory.mktemp("sft") / f"t{i}.jsonl" for i in range(2)]
    for o in outs:
        subprocess.run([sys.executable, str(ROOT / "scripts/sft_data.py"), "--data", str(SMOKE), "--split", "train",
                "--out", str(o), "--seed", "3"], check=True, capture_output=True)
    assert outs[0].read_bytes() == outs[1].read_bytes()
    return [json.loads(ln) for ln in outs[0].read_text().splitlines()]


@pytest.fixture(scope="module")
def tok():
    """
    Returns the Qwen2.5-0.5B-Instruct tokenizer, or skips with the reason it could not be loaded.
    """
    tf = pytest.importorskip("transformers")
    try:
        return tf.AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
    except OSError as e:
        pytest.skip(f"Qwen/Qwen2.5-0.5B-Instruct tokenizer not cached and not downloadable: {e}")


def test_export(rows):
    """
    Checks the export: train rows only, all 3 views, the harness prompt and target, and one account span that starts
    right after the Decision line and runs to the end of the answer.
    """
    from infer import SYSTEM, format_target
    recs = {r["id"]: r for r in map(json.loads, SMOKE.read_text().splitlines())}
    assert len(rows) == sum(r["split"] == "train" for r in recs.values())
    assert {r["id"].rsplit(":", 1)[1] for r in rows} == {"table", "prose", "prose_derive"}
    for x in rows:
        s, u, t = x["messages"]
        assert (s["role"], u["role"], t["role"], s["content"]) == ("system", "user", "assistant", SYSTEM)
        assert t["content"] == format_target(recs[x["id"]])
        (a, b), = x["mask_spans"]
        assert t["content"][:a] == f"Decision: {recs[x['id']]['gold']['decision']}\n" and b == len(t["content"])
        assert t["content"][a:].startswith("Policy support: ")


def test_collator_masks(rows, tok):
    """
    Checks on every smoke row that the decision condition masks exactly the account tokens and supervises the
    decision line, the account condition masks only the prompt, and supervised counts differ by the account length.
    """
    from train import Collator, token_stats
    ca, cd = Collator(tok, "account"), Collator(tok, "decision")
    for x in rows:
        ea, ed = ca.check(x), cd.check(x)
        assert ea["ids"] == ed["ids"]
        first = ea["sup"].index(True)
        assert all(lab == -100 for lab in ea["lab"][:first]) and [lab != -100 for lab in ea["lab"]] == ea["sup"]
        assert tok.decode(ea["ids"][:first]).endswith("<|im_start|>assistant\n")
        (na, nd), nacc = (sum(lab != -100 for lab in e["lab"]) for e in (ea, ed)), sum(ea["acct"])
        assert na - nd == nacc > 0
        assert all((lab == -100) == f for lab, f, s in zip(ed["lab"], ed["acct"], ed["sup"]) if s)
    sa, sd = token_stats(ca, rows), token_stats(cd, rows)
    assert sa["masked_frac"] == 0 and sa["truncated"] == sd["truncated"] == 0
    assert sa["supervised"] - sd["supervised"] == sd["account"] and sd["masked_frac"] == round(
            sd["account"] / sd["answer"], 6)
    print(json.dumps({"account": sa, "decision": sd}))


def test_collator_batch(rows, tok):
    """
    Checks that a padded batch keeps each row's labels and pads with -100 and attention 0.
    """
    pytest.importorskip("torch")
    from train import Collator
    col = Collator(tok, "decision")
    b, es = col(rows[:3]), [col.encode(x) for x in rows[:3]]
    for i, e in enumerate(es):
        n = len(e["ids"])
        assert b["labels"][i, :n].tolist() == e["lab"] and set(b["labels"][i, n:].tolist()) <= {-100}
        assert b["attention_mask"][i].sum().item() == n
