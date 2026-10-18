"""Udgam Labs Gradio theme for Hugging Face Spaces (generalised from the Lilavati Space).

    from gradio_theme import theme, CSS, HEAD, header, footer
    with gr.Blocks(title="Lilavati · Udgam Labs") as demo:
        gr.HTML(header("Lilavati", "Pocket Mathematician", "A 95M-parameter model that ..."))
        ...
        gr.HTML(footer())
    demo.launch(theme=theme, css=CSS, head=HEAD, allowed_paths=["mark.svg"])

Copy logo/svg/mark/udgam-mark-text-ink.svg next to app.py as mark.svg.
"""
import gradio as gr

CSS = """
:root, .dark { --ul-ink:#1C1B18; --ul-white:#FFFFFF; --ul-band:#F7F5F0; --ul-rule:#E6E3DC; --ul-graphite:#5E5C57; --ul-signal:#B4432B; }
.gradio-container { background: var(--ul-white) !important; max-width: 1080px !important; margin: 0 auto !important; }
#ul-head { display:flex; align-items:center; gap:14px; padding: 18px 0 6px; border-bottom: 1px solid var(--ul-rule); margin-bottom: 8px; }
#ul-head img { width: 40px; height: 40px; }
#ul-head h1 { font-family: 'Outfit', sans-serif; font-weight: 500; letter-spacing: -0.02em; font-size: 34px; margin: 0; color: var(--ul-ink); }
#ul-head p { margin: 2px 0 0; color: var(--ul-graphite); font-size: 15px; }
.ul-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ul-graphite); }
#ul-foot { border-top: 1px solid var(--ul-rule); margin-top: 18px; padding-top: 12px; color: var(--ul-graphite); font-size: 13px; }
#ul-foot a, #ul-head a { color: var(--ul-ink); }
"""

theme = gr.themes.Base(
    primary_hue=gr.themes.Color(c50="#FFFFFF", c100="#F7F5F0", c200="#E6E3DC", c300="#C9C3B6", c400="#8F8A7E", c500="#3F3C36",
                                c600="#1C1B18", c700="#1C1B18", c800="#1C1B18", c900="#1C1B18", c950="#1C1B18"),
    neutral_hue="stone",
    radius_size=gr.themes.sizes.radius_none,
    font=[gr.themes.GoogleFont("Figtree"), "Helvetica Neue", "Arial", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "Menlo", "monospace"],
).set(
    body_background_fill="#FFFFFF", block_background_fill="#FFFFFF", block_border_color="#E6E3DC",
    button_primary_background_fill="#1C1B18", button_primary_background_fill_hover="#3F3C36", button_primary_text_color="#FFFFFF",
    body_background_fill_dark="#FFFFFF", block_background_fill_dark="#FFFFFF", body_text_color_dark="#1C1B18",
)

HEAD = '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500&display=swap" rel="stylesheet">'


def header(name, kind, description, mark="/gradio_api/file=mark.svg"):
    return (f'<div id="ul-head"><img src="{mark}" alt="Udgam Labs"><div>'
            f'<p class="ul-label">Udgam Labs · {kind}</p><h1>{name}</h1><p>{description}</p></div></div>')


def footer(links=""):
    return (f'<div id="ul-foot">Udgam Labs · AI research from first principles · '
            f'<a href="https://udgamlabs.com">udgamlabs.com</a>{" · " + links if links else ""}</div>')
