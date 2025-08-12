# src/llm_mode.py
import requests, textwrap

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"  # or "llama3", etc.

def _prompt(text: str) -> str:
    return textwrap.dedent(f"""
    You are a product analyst. Given raw feedback, return:
    1) 6-8 key themes (bulleted, short phrases)
    2) a quick sentiment estimate (positive/negative counts)
    3) 3 concrete next actions

    Feedback:
    ---
    {text.strip()[:8000]}
    ---
    Return plain text with three sections: THEMES:, SENTIMENT:, ACTIONS:
    """)

def analyze_with_llm(text: str):
    # Requires Ollama running locally: https://ollama.com  -> `ollama pull mistral`
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": _prompt(text), "stream": False},
            timeout=180,
        )
        resp.raise_for_status()
        out = resp.json().get("response", "")
    except Exception as e:
        # Graceful message shown in the UI
        msg = f"LLM backend not reachable. Start Ollama and pull a model. Error: {e}"
        return f"- {msg}", "—", "—"

    parts = {"themes": "", "sentiment": "", "actions": ""}
    section = None
    for raw in out.splitlines():
        line = raw.strip()
        if line.upper().startswith("THEMES"):
            section = "themes"; continue
        if line.upper().startswith("SENTIMENT"):
            section = "sentiment"; continue
        if line.upper().startswith("ACTIONS"):
            section = "actions"; continue
        if section:
            parts[section] += raw + "\n"

    return parts["themes"].strip() or "—", parts["sentiment"].strip() or "—", parts["actions"].strip() or "—"
