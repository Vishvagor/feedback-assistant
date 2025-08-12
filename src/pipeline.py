# src/pipeline.py
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import Counter
import pandas as pd
import re
import json
from pathlib import Path

# --- Vocabulary / filters -----------------------------------------------------

POS_WORDS = set("""
good great love helpful clear fast responsive amazing awesome excellent satisfied happy fantastic improved
""".split())

NEG_WORDS = set("""
bad confusing slow bug issue crash broken unclear difficult hate terrible poor unreliable delay lag error failed failure
""".split())

# very common tokens you don't want as "themes"
GENERIC = {"app", "feature", "issue", "ticket", "user", "users", "system", "application"}

STOPWORDS = set((
    "a an the and or but if then else for while to of in on at by is are was were be been being "
    "i me my you your we they them it this that these those from with as about into over after under "
    "s t ll ve re d m don t not no yes ok thanks thank please can could would should may might"
).split())

SYN_EQUIV = {
    # collapse obvious synonyms to a single key
    "fast": {"fast", "responsive", "snappy", "quick"},
    "crash": {"crash", "crashed", "crashing", "error", "failed", "failure"},
    "slow": {"slow", "lag", "laggy", "delay", "delayed"},
    "confusing": {"confusing", "unclear", "vague", "difficult"},
}

# --- Data classes -------------------------------------------------------------

@dataclass
class Summary:
    key_points: List[str]
    sentiments: Dict[str, int]
    actions: List[str]

# --- Tokenization / themes ----------------------------------------------------

def _syn_key(tok: str) -> str:
    for k, group in SYN_EQUIV.items():
        if tok in group:
            return k
    return tok

def _tokenize(s: str) -> List[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [t for t in s.split() if t and t not in STOPWORDS and t not in GENERIC]
    toks = [t for t in toks if len(t) > 2 and not t.isdigit()]
    toks = [_syn_key(t) for t in toks]
    return toks

def _top_phrases(texts: List[str], top_k: int = 8) -> List[str]:
    """Prefer bigrams; fill with unigrams not already covered by chosen bigrams."""
    uni, bi = Counter(), Counter()
    for t in texts:
        toks = _tokenize(t)
        uni.update(toks)
        bi.update([" ".join(pair) for pair in zip(toks, toks[1:])])

    chosen, covered = [], set()

    # choose strongest bigrams first
    for phrase, _ in bi.most_common(top_k * 3):
        a, b = phrase.split()
        if a in GENERIC or b in GENERIC:
            continue
        if phrase not in chosen:
            chosen.append(phrase)
            covered.update([a, b])
        if len(chosen) >= top_k:
            return chosen

    # fill with unigrams not covered by bigrams
    for token, _ in uni.most_common(top_k * 3):
        if token in GENERIC or token in covered:
            continue
        chosen.append(token)
        if len(chosen) >= top_k:
            break
    return chosen

def _sentiment_counts(texts: List[str]) -> Tuple[int, int]:
    pos = neg = 0
    for t in texts:
        toks = _tokenize(t)
        pos += sum(1 for tok in toks if tok in POS_WORDS)
        neg += sum(1 for tok in toks if tok in NEG_WORDS)
    return pos, neg

def _suggest_actions(themes: List[str], pos: int, neg: int) -> List[str]:
    actions = []
    joined = " ".join(themes)
    if any(w in joined for w in ["slow", "lag", "delay"]):
        actions.append("Ship a performance fix: profile top 2 slow paths; publish before/after timings.")
    if any(w in joined for w in ["crash", "error", "failed", "failure", "bug"]):
        actions.append("Schedule a bug-bash with clear owners; status board + daily updates until resolved.")
    if any(w in joined for w in ["confusing", "unclear", "difficult"]):
        actions.append("Rewrite onboarding/UX copy; run 5-user tests; track task completion time.")
    if pos > neg:
        actions.append("Amplify the most-liked feature in onboarding and a short tutorial video.")
    if not actions:
        actions.append("Publish a weekly digest of top themes and commit one fix per sprint.")
    return actions

# --- Column detection ---------------------------------------------------------

_ID_LIKE = {"id", "uid", "guid", "ticket", "order", "case", "number"}

def _column_score(series: pd.Series) -> float:
    """Score how 'texty' a column is: higher => more likely a text column."""
    try:
        vals = series.dropna().astype(str)
    except Exception:
        return 0.0
    if vals.empty:
        return 0.0
    sample = vals.sample(min(200, len(vals)), random_state=0)
    s = " ".join(sample.tolist()).lower()

    # heuristics
    alpha_ratio = (sum(ch.isalpha() for ch in s) + 1) / (len(s) + 1)
    mean_len = sum(len(x) for x in sample) / len(sample)
    digit_ratio = (sum(ch.isdigit() for ch in s) + 1) / (len(s) + 1)
    unique_ratio = sample.nunique() / (len(sample) + 1e-9)

    score = 0.0
    score += 2.0 * alpha_ratio
    score += 0.5 * unique_ratio
    score += 0.2 * (mean_len / 30.0)  # long-ish text bumps score
    score -= 1.0 * digit_ratio        # lots of digits is suspicious

    # penalties for id-like columns
    name = series.name or ""
    if name.strip().lower() in _ID_LIKE:
        score -= 2.0
    return float(score)

def detect_text_columns(df: pd.DataFrame, max_cols: int = 3) -> List[str]:
    """Return likely text columns, sorted by score."""
    scores = []
    for col in df.columns:
        # only consider object/string columns
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            scores.append((col, _column_score(df[col])))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [c for c, s in scores[:max_cols] if s > 0.5] or ([df.columns[0]] if len(df.columns) else [])

# --- Public API ---------------------------------------------------------------

def analyze_text_block(text: str):
    if not text or not text.strip():
        return "Paste feedback on the left.", None, None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    themes = _top_phrases(lines, top_k=8)
    pos, neg = _sentiment_counts(lines)
    actions = _suggest_actions(themes, pos, neg)
    themes_md = "- " + "\n- ".join(themes)
    sent_md = f"👍 {pos}   👎 {neg}"
    acts_md = "- " + "\n- ".join(actions)
    return themes_md, sent_md, acts_md

def analyze_csv_block(
    df: pd.DataFrame,
    text_columns: Optional[List[str]] = None,
    aggregate: bool = True
):
    """
    Analyze a pandas DataFrame. If `text_columns` is None, auto-detect likely text columns.
    If `aggregate` is True, combine texts across columns; otherwise the first detected column is used.
    Returns (themes_md, sentiment_md, actions_md, used_columns)
    """
    if df is None or df.empty:
        return "Empty data.", None, None, []

    cols = text_columns or detect_text_columns(df, max_cols=3)
    if not cols:
        return "No text-like columns found.", None, None, []

    # collect texts
    texts: List[str] = []
    for c in (cols if aggregate else cols[:1]):
        texts.extend([str(x) for x in df[c].fillna("").tolist() if str(x).strip()])

    if not texts:
        return f"No text found in columns {cols}.", None, None, cols

    themes = _top_phrases(texts, top_k=8)
    pos, neg = _sentiment_counts(texts)
    actions = _suggest_actions(themes, pos, neg)
    themes_md = "- " + "\n- ".join(themes)
    sent_md = f"👍 {pos}   👎 {neg}"
    acts_md = "- " + "\n- ".join(actions)
    return themes_md, sent_md, acts_md, cols

# --- Any-file loader (CSV/TSV/JSON/Excel) ------------------------------------

def load_any(path: str) -> pd.DataFrame:
    """
    Read CSV, TSV, XLS/XLSX, or JSON into a DataFrame with best-effort defaults.
    JSON can be an array of objects or JSON Lines.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext in {".csv"}:
        return pd.read_csv(p, encoding="utf-8", on_bad_lines="skip", engine="python")
    if ext in {".tsv", ".txt"}:
        return pd.read_csv(p, sep="\t", encoding="utf-8", on_bad_lines="skip", engine="python")
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    if ext in {".json"}:
        try:
            # try records/array
            return pd.read_json(p)
        except ValueError:
            # try JSON lines
            return pd.read_json(p, lines=True)
    # fallback: try csv
    return pd.read_csv(p, encoding="utf-8", on_bad_lines="skip", engine="python")

def analyze_file_block(path: str, text_columns: Optional[List[str]] = None, aggregate: bool = True):
    """
    Convenience wrapper: load any supported file and analyze it.
    Returns (themes_md, sentiment_md, actions_md, used_columns)
    """
    df = load_any(path)
    return analyze_csv_block(df, text_columns=text_columns, aggregate=aggregate)
