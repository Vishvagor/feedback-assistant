import gradio as gr
import pandas as pd
from src.pipeline import analyze_text_block, analyze_csv_block

def analyze_text(text: str):
    return analyze_text_block(text)

def analyze_csv(file):
    if file is None:
        return "Upload a CSV with a text column.", None, None
    df = pd.read_csv(file.name)
    return analyze_csv_block(df)

with gr.Blocks(title="LLM Feedback Assistant") as demo:
    gr.Markdown("# LLM Feedback Assistant\nPaste text or upload a CSV → get key themes, sentiment, and next actions.")

    with gr.Tab("Analyze Text"):
        text = gr.Textbox(lines=12, label="Paste feedback (multi-line)")
        btn = gr.Button("Analyze")
        out1 = gr.Markdown(label="Key Themes")
        out2 = gr.Markdown(label="Sentiment")
        out3 = gr.Markdown(label="Suggested Actions")
        btn.click(analyze_text, inputs=text, outputs=[out1, out2, out3])

    with gr.Tab("Analyze CSV"):
        csv = gr.File(label="Upload CSV (expects a 'text' column; auto-detects fallback)")
        btn2 = gr.Button("Analyze CSV")
        out1c = gr.Markdown(label="Key Themes")
        out2c = gr.Markdown(label="Sentiment")
        out3c = gr.Markdown(label="Suggested Actions")
        btn2.click(analyze_csv, inputs=csv, outputs=[out1c, out2c, out3c])

if __name__ == "__main__":
    demo.launch()
