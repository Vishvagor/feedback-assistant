# Feedback Assistant(LLM ready,offline) — Summaries, Sentiment, and Next Actions (No API Keys)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Vishvagor/llm-feedback-assistant/actions/workflows/smoke.yml/badge.svg)](../../actions/workflows/smoke.yml)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)

**What it is:** A lightweight Gradio app that turns raw feedback into **key themes**, a quick **sentiment** tally (👍/👎), and **suggested actions** — all **offline**, with **no API keys**.

**Why it matters:** This maps directly to VOC/CX/support workflows. It’s pragmatic and demo-safe (no cloud dependencies), perfect for a portfolio or a quick internal tool.

---

## Screenshot

> Replace with a real screenshot from your machine.

<img src="assets/screenshot.png" width="900" alt="App screenshot" />

---

## Quickstart

```bash
git clone https://github.com/Vishvagor/llm-feedback-assistant
cd llm-feedback-assistant

# (optional) create a virtual env
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\Activate

pip install -r requirements.txt

# run (module mode avoids import issues)
python -m app.app
