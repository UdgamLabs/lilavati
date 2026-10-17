# Lilavati: evaluation

Every number here was measured by Udgam Labs. Lilavati answers by writing a Python function; "code executed" means the
function is run (through `lilavati/safe_exec.py`) and its return value is compared with the reference answer.
Whole-number answers must match exactly. Decimal answers must match to the precision of the reference.

## GSM8K test (1,319 problems)

| Setting | Score |
|---|---|
| **One greedy try** | **54.7** |
| 48 tries at temperature 0.7, **checker-weighted vote** | **72.3** |
| 48 tries, the checker's single top-rated program | 66.7 |
| 48 tries, plain majority vote | 65.7 |
| 48 tries, at least one program right (an upper bound) | 89.5 |
| 16 tries, checker-weighted vote | 68.8 |
| 16 tries, the checker's single top-rated program | 65.9 |

Sampling uses plain temperature 0.7 (no top-k or top-p cut-off), as in `Lilavati.solve()`.

**Reproduce:**

```bash
pip install -e ".[eval]"
python eval/gsm8k.py                      # one greedy try per problem
python eval/gsm8k.py --tries 48           # checker-weighted vote over 48 tries (use a GPU)
```

**End-to-end check of this release.** Before publication, the released weights were scored with this repository's
`eval/gsm8k.py` on a CPU: **726 of 1,319 = 55.0%** with one greedy try (the first 300 problems: 57.7%, against 57.3% in our training-time harness). The published 54.7 comes from our training-time harness (bf16 on a GPU);
small differences come from numerical precision.

## Robustness sets (one greedy try)

| Test set | Items | Score |
|---|---|---|
| GSM-Plus testmini, the 7 answerable perturbation types | 2,100 | 39.2 |
| … of which "distraction insertion" (an irrelevant fact is added) | 300 | 20.7 |
| SVAMP (train + test) | 1,000 | 69.9 |
| ASDiv, numeric answers | 2,159 | 74.0 |
| GSM-Hard | 1,319 | 43.7 |

GSM-Plus's eighth type, "critical thinking", has no numeric answer, so it is left out. Lilavati always returns a number.

**Reproduce:** `python eval/robust.py --sets gsmplus svamp asdiv gsmhard`

## Comparison with other open models up to 150M parameters

Measured on 14 and 15 October 2026 with one harness, zero-shot and greedy. Other models answer in text, their native
format, and are scored on their boxed answer, or on the last number if there is none. The output cap differed between
models and is given in the notes (1K = 1,024, 8K = 8,192 and 16K = 16,384 new tokens).

| Model | Params | GSM8K test | Notes |
|---|---|---|---|
| **Lilavati** | 95M | **54.7** (57.3 on the first 300) | code executed |
| cagliostro-v3.5-chat | 146M | 21.3 | first 300 items; 1K-token cap |
| Falcon-H1-Tiny-R-90M | 90M | 18.7 | all items; 16K-token cap, which 53% of its answers still reached. SVAMP: 40.1 with an 8K-token cap (Lilavati 69.9) |
| MobileLLM-R1.5-140M | 140M | 6.7 | first 300 items; 99% of its answers ran past the 8K-token cap. Its developers report 8.3 |
| GPT-X3-150M | 150M | 2.3 | first 300 items; 42% of its answers reached the 1K-token cap |
| GPT-X2.5-135M | 135M | 1.7 | first 300 items; 99% of its answers reached the 1K-token cap |
| Supra2-100M-Instruct | 100M | 1.6 | all items; 2,048-token context, no answers cut off |
| JugnuLM-110M-R2plus | 110M | 1.3 | first 300 items; 90% of its answers reached the 1K-token cap |

The 2.7× in our announcement compares Lilavati with the best of these, cagliostro-v3.5-chat, on the same first 300 items:
57.3% vs 21.3%.

**Published results for models whose weights were not released:** TinyGSM (Liu et al., 2023,
[arXiv:2312.09241](https://arxiv.org/abs/2312.09241)) reports a 125M model, first pretrained on Phi-1.5 data, at 63.1%
with one try, and 68.9% when a 125M verifier picks one of 48 programs. Under that exact protocol (the checker's single top
pick), Lilavati scores 66.7%. TinyGSM's 125M model trained from random initialisation reports 53.1%.

## Contamination audit

Every document Lilavati was pretrained on was checked against each test set for shared 13-word sequences:

| Test set | Items sharing a 13-gram with the pretraining data |
|---|---|
| GSM8K test | 0 |
| GSM-Hard | 0 |
| GSM-Plus testmini | 0.8% |
| SVAMP | 2.2% |
| ASDiv | 7.1% |

Removing the overlapping items barely changes the scores. With one greedy try, the released model scores, on the items
with no overlap against the full sets: GSM-Plus 39.1 vs 39.2, SVAMP 69.6 vs 69.9 and ASDiv 75.3 vs 74.0 (the pretrained
model showed the same pattern: 37.6 vs 37.7, 68.7 vs 68.8 and 75.1 vs 73.7). So this kind of overlap does not explain
the results. A 13-gram check finds near-copies, not reworded problems. Problems added in later training were filtered
against all of these test sets for shared 8-word sequences.
