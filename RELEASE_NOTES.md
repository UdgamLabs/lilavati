# Lilavati 1.0.0

First public release, October 2026. The weights are on Hugging Face ([Lilavati](https://huggingface.co/UdgamLabs/Lilavati),
[Lilavati-Checker](https://huggingface.co/UdgamLabs/Lilavati-Checker)). This repository adds the code, a local playground,
the evaluation scripts and checksums.

- **Two models, 95M parameters each:** Lilavati writes a short Python program for a maths word problem; Lilavati-Checker
  rates programs so that many tries can vote. Both were trained from scratch.
- **GSM8K test:** 54.7% with one greedy try (code executed); 72.3% with the checker-weighted vote over 48 tries.
- **Safe execution:** a structure check, a separate limited process and a timeout (`lilavati/safe_exec.py`).
- **Licence:** Apache-2.0 for code and weights.
