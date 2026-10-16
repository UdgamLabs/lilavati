"""Lilavati: solve maths word problems by writing and running Python.

    from lilavati import Lilavati
    lv = Lilavati()                        # downloads UdgamLabs/Lilavati (+ UdgamLabs/Lilavati-Checker)
    r = lv.solve("A shop sells pens at 12 rupees each. Riya buys 7 pens and pays 100 rupees. How much change?")
    print(r["answer"], r["agreement"], r["confidence"])
    print(r["program"])                    # the program that produced the answer

How an answer is made:
  1. Lilavati (95M) writes `tries` short Python programs for the question (one greedy program if tries == 1);
  2. each program passes a structure check and runs in a limited, sandboxed process (see safe_exec.py);
  3. Lilavati-Checker (95M) rates each program; the answer with the most checker-weighted support wins.
"""
import collections, os
from concurrent.futures import ThreadPoolExecutor

from .safe_exec import run

PROMPT = "Question: {q}\nAnswer (Python):\n```python\n"


def _fmt(v):
    return f"{v:g}" if abs(v) < 1e15 else repr(v)


def _num(v):
    """Whole numbers as int (42, not 42.0); everything else unchanged."""
    return int(v) if isinstance(v, float) and v.is_integer() and abs(v) < 1e15 else v


class Lilavati:
    def __init__(self, model="UdgamLabs/Lilavati", checker="UdgamLabs/Lilavati-Checker", device=None, dtype=None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        dtype = dtype or (torch.bfloat16 if self.device == "cuda" else torch.float32)
        self.tok = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(model, dtype=dtype).to(self.device).eval()
        self.bos = self.tok.convert_tokens_to_ids("<bos>")
        self.checker = None
        # On Macs the checker runs on the CPU: its input shapes change every question, which fills Apple-GPU caches.
        self.cdev = "cpu" if self.device == "mps" else self.device
        if checker:
            self.checker = AutoModelForCausalLM.from_pretrained(checker, dtype=dtype).to(self.cdev).eval()
            self.yes, self.no = (self.tok(" yes", add_special_tokens=False)["input_ids"],
                                 self.tok(" no", add_special_tokens=False)["input_ids"])
            assert len(self.yes) == 1 and len(self.no) == 1
            self.yes, self.no = self.yes[0], self.no[0]

    def _encode(self, text):
        return [self.bos] + self.tok(text, add_special_tokens=False)["input_ids"]

    def write_programs(self, question, tries=8, temperature=0.7, max_new_tokens=320):
        torch = self.torch
        ids = torch.tensor([self._encode(PROMPT.format(q=question.strip()))], device=self.device)
        kw = (dict(do_sample=False) if tries <= 1 else   # plain temperature sampling, as in the published evaluation
              dict(do_sample=True, temperature=temperature, top_k=0, top_p=1.0, num_return_sequences=tries))
        with torch.no_grad():
            out = self.model.generate(input_ids=ids, max_new_tokens=max_new_tokens, stop_strings=["```"],
                                      tokenizer=self.tok, pad_token_id=0, **kw)
        if self.device == "mps":
            torch.mps.empty_cache()
        return [self.tok.decode(r[ids.size(1):], skip_special_tokens=True).split("```")[0].rstrip() for r in out]

    def check(self, question, programs, values):
        """P(correct) for each program, from Lilavati-Checker."""
        torch = self.torch
        texts = [f"{PROMPT.format(q=question.strip())}{p.rstrip()}\n```\nResult: {'error' if v is None else _fmt(v)}\nCorrect:"
                 for p, v in zip(programs, values)]
        enc = [self._encode(t)[-768:] for t in texts]
        L = max(map(len, enc))   # left-pad with an attention mask, and score only the last position
        ids = torch.tensor([[0] * (L - len(e)) + e for e in enc], device=self.cdev)
        mask = torch.tensor([[0] * (L - len(e)) + [1] * len(e) for e in enc], device=self.cdev)
        with torch.no_grad():
            logits = self.checker(input_ids=ids, attention_mask=mask, logits_to_keep=1).logits[:, -1]
        two = torch.stack([logits[:, self.yes], logits[:, self.no]], 1).float()
        return torch.softmax(two, 1)[:, 0].tolist()

    def solve(self, question, tries=8, temperature=0.7):
        programs = self.write_programs(question, tries, temperature)
        with ThreadPoolExecutor(min(8, len(programs))) as ex:
            values = list(ex.map(run, programs))
        if all(v is None for v in values):
            return dict(answer=None, agreement=0.0, confidence=0.0, program=programs[0], programs=programs, values=values)
        if len(programs) == 1 or self.checker is None:
            counts = collections.Counter(round(v, 6) for v in values if v is not None)
            ans, n = counts.most_common(1)[0]
            prog = next(p for p, v in zip(programs, values) if v is not None and round(v, 6) == ans)
            return dict(answer=_num(ans), agreement=n / len(programs), confidence=None, program=prog, programs=programs, values=values)
        scores = self.check(question, programs, values)
        weight = collections.defaultdict(float)
        for v, s in zip(values, scores):
            if v is not None:
                weight[round(v, 6)] += s
        ans = max(weight, key=weight.get)
        agree = sum(1 for v in values if v is not None and round(v, 6) == ans) / len(programs)
        prog = max(((p, s) for p, v, s in zip(programs, values, scores) if v is not None and round(v, 6) == ans), key=lambda x: x[1])[0]
        return dict(answer=_num(ans), agreement=agree, confidence=weight[ans] / sum(weight.values()), program=prog,
                    programs=programs, values=values, scores=scores)
