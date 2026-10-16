"""Lilavati playground (Gradio). Runs locally (`python app.py`, then open http://127.0.0.1:7860) and as the Hugging Face Space.
Set LILAVATI_MODEL / LILAVATI_CHECKER to local folders to use weights on disk."""
import os
import re
import time

import gradio as gr

from lilavati import Lilavati

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # so mark.svg resolves wherever the app is launched from

lv = Lilavati(os.environ.get("LILAVATI_MODEL", "UdgamLabs/Lilavati"), os.environ.get("LILAVATI_CHECKER", "UdgamLabs/Lilavati-Checker"))
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


CSS = """
:root, .dark { --lv-ink:#1C1B18; --lv-ivory:#F3EFE6; --lv-paper:#FBF9F4; --lv-rule:#E3DDD0; --lv-graphite:#6B675E; --lv-signal:#B4432B; }
.gradio-container { background: var(--lv-ivory) !important; max-width: 1080px !important; margin: 0 auto !important; }
#lv-head { display:flex; align-items:center; gap:14px; padding: 18px 0 6px; border-bottom: 1px solid var(--lv-rule); margin-bottom: 8px; }
#lv-head img { width: 40px; height: 40px; }
#lv-head h1 { font-family: 'Outfit', sans-serif; font-weight: 500; letter-spacing: -0.02em; font-size: 34px; margin: 0; color: var(--lv-ink); }
#lv-head p { margin: 2px 0 0; color: var(--lv-graphite); font-size: 15px; }
.lv-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--lv-graphite); }
.lv-label b { color: var(--lv-signal); font-weight: 500; }
#lv-answer h2 { font-family: 'Outfit', sans-serif; font-weight: 500; color: var(--lv-signal); margin: 4px 0; }
#lv-note { font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--lv-graphite); }
#lv-foot { border-top: 1px solid var(--lv-rule); margin-top: 18px; padding-top: 12px; color: var(--lv-graphite); font-size: 13px; }
#lv-foot a, #lv-head a { color: var(--lv-ink); }
"""
theme = gr.themes.Base(
    primary_hue=gr.themes.Color(c50="#FBF9F4", c100="#F3EFE6", c200="#E3DDD0", c300="#C9C3B6", c400="#8F8A7E", c500="#3F3C36",
                                c600="#1C1B18", c700="#1C1B18", c800="#1C1B18", c900="#1C1B18", c950="#1C1B18"),
    neutral_hue="stone",
    radius_size=gr.themes.sizes.radius_none,
    font=[gr.themes.GoogleFont("Figtree"), "Helvetica Neue", "Arial", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "Menlo", "monospace"],
).set(
    body_background_fill="#F3EFE6", block_background_fill="#FBF9F4", block_border_color="#E3DDD0",
    button_primary_background_fill="#1C1B18", button_primary_background_fill_hover="#3F3C36", button_primary_text_color="#F3EFE6",
    body_background_fill_dark="#F3EFE6", block_background_fill_dark="#FBF9F4", body_text_color_dark="#1C1B18",
)
HEAD = '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500&display=swap" rel="stylesheet">'

with gr.Blocks(title="Lilavati · Udgam Labs") as demo:
    gr.HTML(
        '<div id="lv-head"><img src="/gradio_api/file=mark.svg" alt="Udgam Labs">'
        '<div><p class="lv-label">Udgam Labs · <b>Pocket Mathematician</b> · Trained from scratch</p>'
        '<h1>Lilavati</h1>'
        '<p>A 95M-parameter model that solves maths word problems by writing a short Python program and running it.</p></div></div>'
    )
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
    gr.HTML(
        '<div id="lv-foot">Model: <a href="https://huggingface.co/UdgamLabs/Lilavati">UdgamLabs/Lilavati</a> + '
        '<a href="https://huggingface.co/UdgamLabs/Lilavati-Checker">Lilavati-Checker</a> (Apache-2.0) · '
        'Code &amp; evaluation: <a href="https://github.com/UdgamLabs/lilavati">GitHub</a> · '
        '<a href="https://udgamlabs.com/models/lilavati">udgamlabs.com</a><br>'
        'A small research model: it makes mistakes, so check answers that matter. It always shows the program behind the '
        'answer. Programs pass a structure check and run in a separate, limited process.</div>'
    )
    btn.click(solve, [question, mode], [answer, note, program])
    question.submit(solve, [question, mode], [answer, note, program])

if __name__ == "__main__":
    demo.queue(max_size=16, default_concurrency_limit=1).launch(theme=theme, css=CSS, head=HEAD, allowed_paths=["mark.svg"])
