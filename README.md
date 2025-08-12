# LLM Feedback Assistant — Summaries, Sentiment, and Next Actions (No API Keys)

**What it does:** Paste raw feedback **or upload a CSV** and get:
- Key themes (top phrases)
- A quick sentiment tally (👍 / 👎)
- Suggested next actions for a team

**Why it matters:** This maps directly to VOC/CX/support workflows. It’s a business-style demo that always runs (no cloud deps, no keys).

## Quickstart
```bash
pip install -r requirements.txt
python app/app.py
```
Then open the local URL (e.g., http://127.0.0.1:7860).

## Inputs
- **Text box** — paste multiple lines of feedback.
- **CSV upload** — a file with a column that contains text (auto-detected; defaults to a column named `text`).

## Outputs
- **Key Themes** — top phrases (de-duped, normalized).
- **Sentiment** — simple count (positive/negative words).
- **Suggested Actions** — concrete next steps based on dominant negatives.

## Example datasets
- `data/samples/student_feedback.csv`
- `data/samples/product_reviews.csv`
- `data/samples/support_tickets.csv`

## Roadmap (post-summit)
- Swap mock analyzer with a real small model (local or API).
- CSV column picker + export `summary.csv`.
- Theme bar chart + prompt comparison with latency/cost logging.
- Minimal FastAPI backend for `/analyze` + basic tests.

## License
MIT
