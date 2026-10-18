"""Lilavati playground (Gradio). Runs locally (`python app.py`, then open http://127.0.0.1:7860) and as the Hugging Face Space.
Set LILAVATI_MODEL / LILAVATI_CHECKER to local folders to use weights on disk."""
import os
import re
import time

import gradio as gr

from gradio_theme import CSS, HEAD, footer, header, theme
from lilavati import Lilavati

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # so mark.svg resolves wherever the app is launched from

lv = Lilavati(os.environ.get("LILAVATI_MODEL", "udgamlabs/Lilavati"), os.environ.get("LILAVATI_CHECKER", "udgamlabs/Lilavati-Checker"))
lv.solve("Warm up: what is 2 plus 3?", tries=2)

MAX_LEN = 700
NUMBERISH = re.compile(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|hundred|thousand|"
                       r"half|twice|double|triple|dozen|quarter)\b", re.I)
HELP = ("I'm Lilavati, a tiny 95M-parameter model that solves maths word problems by writing a small Python program and "
        "running it. Ask me a word problem with numbers, like the examples below.")
EXAMPLES = [
    "A shop sells pencils at 8 rupees each. Riya buys 6 pencils and 2 erasers at 5 rupees each. She pays with a 100 rupee note. How much change does she get?",
    "Two trains start 300 km apart and travel towards each other at 70 km/h and 80 km/h. After how many hours do they meet?",
    "A phone costs 15,000 rupees. It is 20% off, and then 5% tax is added to the sale price. What is the final price?",
    "Meera deposits 25,000 rupees at 8% simple interest per year. How much interest does she earn in 3 years?",
    "A batsman scored 45, 62, 18 and 75 runs in four matches. How many runs must he score in the fifth match to average 55 runs per match?",
    "A rectangular garden is 24 metres long and 15 metres wide. Fencing costs 120 rupees per metre. How much does it cost to fence the garden?",
]
MODES = {"Best: 8 tries + checker": 8, "Fast: 1 try": 1}


def fmt(v):
    return f"{v:,.4f}".rstrip("0").rstrip(".") if abs(v - round(v)) > 1e-9 else f"{int(round(v)):,}"


def solve(question, mode):
    q = (question or "").strip()
    if not q:
        raise gr.Error("Type a maths word problem first.")
    if len(q) > MAX_LEN:
        raise gr.Error(f"Please keep the question under {MAX_LEN} characters.")
    if not NUMBERISH.search(q):
        return HELP, "", ""
    tries, t0 = MODES.get(mode, 8), time.time()
    r = lv.solve(q, tries=tries)
    took = f"{time.time() - t0:.1f} s"
    if r["answer"] is None:
        return "Sorry, I couldn't work that one out: every program I wrote failed to run.", f"{tries} tr{'ies' if tries > 1 else 'y'} · {took}", r["program"]
    if tries == 1:
        return f"## The answer is {fmt(r['answer'])}", f"1 try · {took}", r["program"]
    agree, conf = r["agreement"], r["confidence"] or 0
    unsure = agree < 0.5 or conf < 0.5
    note = f"{tries} tries · {round(agree * tries)}/{tries} agree · checker {round(100 * conf)}% · {took}"
    return f"## The answer is {fmt(r['answer'])}" + ("\n(I'm not very sure about this one.)" if unsure else ""), note, r["program"]


EXTRA_CSS = """
#lv-answer h2 { font-family: 'Outfit', sans-serif; font-weight: 500; color: var(--ul-signal); margin: 4px 0; }
#lv-note { font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--ul-graphite); }
.ul-note { color: var(--ul-graphite); font-size: 13px; margin: 12px 0 0; }
"""

with gr.Blocks(title="Lilavati · Udgam Labs") as demo:
    gr.HTML(header("Lilavati", "Pocket Mathematician · Trained from scratch",
                   "A 95M-parameter model that solves maths word problems by writing a short Python program and running it."))
    with gr.Row(equal_height=False):
        with gr.Column(scale=5):
            question = gr.Textbox(label="Maths word problem", value=EXAMPLES[0], lines=4, max_length=MAX_LEN)
            mode = gr.Radio(list(MODES), value=list(MODES)[0], label="Mode")
            btn = gr.Button("Solve", variant="primary", size="lg")
            gr.Examples(EXAMPLES, inputs=[question], label="Try one of these")
        with gr.Column(scale=6):
            answer = gr.Markdown(elem_id="lv-answer")
            note = gr.Markdown(elem_id="lv-note")
            program = gr.Code(label="The program Lilavati wrote (it ran in a sandbox)", language="python", interactive=False)
    gr.HTML('<p class="ul-note">A small research model: it makes mistakes, so check answers that matter. It always shows the '
            'program behind the answer. Programs pass a structure check and run in a separate, limited process.</p>')
    gr.HTML(footer('Model: <a href="https://huggingface.co/udgamlabs/Lilavati">udgamlabs/Lilavati</a> + '
                   '<a href="https://huggingface.co/udgamlabs/Lilavati-Checker">Lilavati-Checker</a> (Apache-2.0) · '
                   'Code &amp; evaluation: <a href="https://github.com/udgamlabs/lilavati">GitHub</a> · '
                   '<a href="https://udgamlabs.com/models/lilavati">Try box</a>'))
    btn.click(solve, [question, mode], [answer, note, program])
    question.submit(solve, [question, mode], [answer, note, program])

if __name__ == "__main__":
    demo.queue(max_size=16, default_concurrency_limit=1).launch(theme=theme, css=CSS + EXTRA_CSS, head=HEAD, allowed_paths=["mark.svg"])
