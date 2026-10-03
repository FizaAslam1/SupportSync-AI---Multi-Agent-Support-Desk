"""Tiny keyword retriever over the FAQ knowledge base (CSV). Good enough for a small KB;
swap for a vector store (Chroma/FAISS) if the KB grows."""
import re
from pathlib import Path
import pandas as pd

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.csv"
STOP = set("a an the is are was i my me to of for and or in on it do how can you your we our with this that what when why".split())


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def retrieve(query: str, category: str | None = None, k: int = 4) -> str:
    df = pd.read_csv(KB_PATH)
    q = _tokens(query)
    scored = []
    for _, r in df.iterrows():
        score = len(q & _tokens(f"{r['question']} {r['answer']}"))
        if category and r["category"] == category:
            score += 0.5
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [r for s, r in scored[:k] if s >= 1]
    if not top:
        return "NO RELEVANT KNOWLEDGE BASE ENTRIES FOUND."
    return "\n\n".join(f"[{r['category']}] Q: {r['question']}\nA: {r['answer']}" for r in top)
