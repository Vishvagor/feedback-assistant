# app/app.py
import io, tempfile
import pandas as pd
import gradio as gr

from src.pipeline import (
    analyze_text_block,
    analyze_file_block,
    load_any,
    detect_text_columns,
)
from src.llm_mode import analyze_with_llm  # optional local LLM via Ollama

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
    return tmp.name  # return a path string

def analyze_text(text: str, mode: str):
    if not text or not text.strip():
        return "Paste feedback on the left.", None, None, None

    if mode == "LLM (local via Ollama)":
        themes, sent, acts = analyze_with_llm(text)
    else:
        themes, sent, acts = analyze_text_block(text)

    dl_path = _to_downloadable_csv(themes) if themes else None
    return themes, sent, acts, dl_path

def analyze_file(file, mode: str):
    if file is None:
        return "Upload a file (CSV/TSV/Excel/JSON).", None, None, None

    if mode == "LLM (local via Ollama)":
        # Load and concatenate detected text columns, then hand to LLM
        df = load_any(file.name)
        cols = detect_text_columns(df, max_cols=3)
        texts = []
        for c in (cols or []):
            texts.extend([str(x) for x in df[c].fillna("") if str(x).strip()])
        combined = "\n".join(texts[:5000])  # safety cut
        themes, sent, acts = analyze_with_llm(combined if combined else "(empty)")
        if themes and cols:
            themes += f"\n\n_Analyzed columns: **{', '.join(cols)}**_"
    else:
        themes, sent, acts, cols = analyze_file_block(file.name)
        if themes and cols:
            themes += f"\n\n_Analyzed columns: **{', '.join(cols)}**_"

    dl_path = _to_downloadable_csv(themes) if themes else None
    return themes, sent, acts, dl_path

with gr.Blocks(title="Feedback Assistant — offline (LLM-ready)") as demo:
    gr.Markdown(
        "# Feedback Assistant — offline (LLM-ready)\n"
        "Paste text or upload a file (CSV / TSV / Excel / JSON) → key themes, sentiment, and next actions.\n"
        "Default mode uses fast offline heuristics. Optional LLM mode runs locally via Ollama (no API keys)."
    )

    mode = gr.Dropdown(
        choices=["Offline heuristics", "LLM (local via Ollama)"],
        value="Offline heuristics",
        label="Mode",
    )

    with gr.Tab("Analyze Text"):
        inp = gr.Textbox(lines=12, label="Paste feedback (multi-line)")
        btn = gr.Button("Analyze")
        t1 = gr.Markdown(label="Key Themes")
        t2 = gr.Markdown(label="Sentiment")
        t3 = gr.Markdown(label="Suggested Actions")
        dl = gr.File(label="Download summary.csv")
        btn.click(analyze_text, [inp, mode], [t1, t2, t3, dl])

    with gr.Tab("Analyze File"):
        f = gr.File(label="Upload CSV / TSV / Excel / JSON")
        btn2 = gr.Button("Analyze")
        c1 = gr.Markdown(label="Key Themes")
        c2 = gr.Markdown(label="Sentiment")
        c3 = gr.Markdown(label="Suggested Actions")
        dl2 = gr.File(label="Download summary.csv")
        btn2.click(analyze_file, [f, mode], [c1, c2, c3, dl2])

if __name__ == "__main__":
    demo.launch()
