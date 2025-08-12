
from dataclasses import dataclass
import re
from collections import Counter
from typing import List, Dict, Tuple
import pandas as pd

POS_WORDS = set(("good great love helpful clear fast responsive amazing awesome excellent satisfied happy fantastic improved").split())
NEG_WORDS = set(("bad confusing slow bug issue crash broken unclear difficult hate terrible poor unreliable delay lag error").split())

STOPWORDS = set((
    "a an the and or but if then else for while to of in on at by is are was were be been being "
    "i me my you your we they them it this that these those from with as about into over after under "
    "s t ll ve re d m don t not no yes ok thanks thank please can could would should may might"
).split())

@dataclass
class Summary:
    key_points: List[str]
    sentiments: Dict[str, int]
    actions: List[str]

def _tokenize(s: str) -> List[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [t for t in s.split() if t and t not in STOPWORDS]
    return toks

def _top_phrases(texts: List[str], top_k: int = 8) -> List[str]:
    uni = Counter()
    bi = Counter()
    for t in texts:
        toks = _tokenize(t)
        uni.update(toks)
        bi.update([" ".join(pair) for pair in zip(toks, toks[1:])])
    # interleave top unigrams and bigrams for readability
    u = [w for w,_ in uni.most_common(top_k*2)]
    b = [w for w,_ in bi.most_common(top_k*2)]
    merged = []
    i=j=0
    while len(merged) < top_k and (i < len(u) or j < len(b)):
        if i < len(u):
            if u[i] not in merged:
                merged.append(u[i])
            i += 1
        if len(merged) >= top_k: break
        if j < len(b):
            if b[j] not in merged:
                merged.append(b[j])
            j += 1
    return merged

def _sentiment_counts(texts: List[str]) -> Tuple[int,int]:
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
        actions.append("Ship a performance fix: profile top 2 slow paths; publish before/after timings in release notes.")
    if any(w in joined for w in ["bug", "crash", "error", "broken"]):
        actions.append("Create a bug-bash with clear owners; add a status board and daily updates until resolved.")
    if any(w in joined for w in ["confusing", "unclear", "difficult"]):
        actions.append("Rewrite the onboarding/UX copy; run 5-user usability tests and track completion time.")
    if pos > neg:
        actions.append("Amplify the most-liked feature in onboarding and a short tutorial video.")
    if not actions:
        actions.append("Publish a weekly digest of top themes and commit one fix per sprint.")
    return actions

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

def _detect_text_column(df: pd.DataFrame) -> str:
    if "text" in df.columns:
        return "text"
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return df.columns[0]

def analyze_csv_block(df: pd.DataFrame):
    if df is None or df.empty:
        return "Empty CSV.", None, None
    col = _detect_text_column(df)
    texts = [str(x) for x in df[col].fillna("").tolist() if str(x).strip()]
    if not texts:
        return f"No text found in column '{col}'.", None, None
    themes = _top_phrases(texts, top_k=8)
    pos, neg = _sentiment_counts(texts)
    actions = _suggest_actions(themes, pos, neg)
    themes_md = "- " + "\n- ".join(themes)
    sent_md = f"👍 {pos}   👎 {neg}"
    acts_md = "- " + "\n- ".join(actions)
    return themes_md, sent_md, acts_md
