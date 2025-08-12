# app/app.py
import io
import tempfile
import pandas as pd
import gradio as gr
from src.pipeline import analyze_text_block, analyze_file_block

def _to_downloadable_csv(themes_md: str):
    """Write themes to a temp CSV and return the file path (what gr.File expects)."""
    rows = [
        t.strip().lstrip("- ").strip()
        for t in (themes_md or "").split("\n")
        if t.strip()
    ]
    df = pd.DataFrame({"themes": rows})
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    return tmp.name  # <-- return a *string path*, not a tuple/bytes

def analyze_text(text: str):
    themes, sent, acts = analyze_text_block(text)
    dl_path = _to_downloadable_csv(themes) if themes else None
    return themes, sent, acts, dl_path

def analyze_file(file):
    if file is None:
        return "Upload a file (CSV/TSV/Excel/JSON).", None, None, None
    themes, sent, acts, cols = analyze_file_block(file.name)
    if themes:
        if cols:
            themes += f"\n\n_Analyzed columns: **{', '.join(cols)}**_"
        dl_path = _to_downloadable_csv(themes)
    else:
        dl_path = None
    return themes, sent, acts, dl_path

with gr.Blocks(title="LLM Feedback Assistant") as demo:
    gr.Markdown(
        "# LLM Feedback Assistant\n"
        "Paste text or upload a file (CSV / TSV / Excel / JSON) → get key themes, sentiment, and next actions."
    )

    with gr.Tab("Analyze Text"):
        inp = gr.Textbox(lines=12, label="Paste feedback (multi-line)")
        btn = gr.Button("Analyze")
        t1 = gr.Markdown(label="Key Themes")
        t2 = gr.Markdown(label="Sentiment")
        t3 = gr.Markdown(label="Suggested Actions")
        dl = gr.File(label="Download summary.csv")
        btn.click(analyze_text, inp, [t1, t2, t3, dl])

    with gr.Tab("Analyze File"):
        f = gr.File(label="Upload CSV / TSV / Excel / JSON")
        btn2 = gr.Button("Analyze")
        c1 = gr.Markdown(label="Key Themes")
        c2 = gr.Markdown(label="Sentiment")
        c3 = gr.Markdown(label="Suggested Actions")
        dl2 = gr.File(label="Download summary.csv")
        btn2.click(analyze_file, f, [c1, c2, c3, dl2])

if __name__ == "__main__":
    demo.launch()
