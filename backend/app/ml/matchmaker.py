import torch, torch.nn as nn, torch.nn.functional as F
from ..rag.retriever import embed

class Ranker(nn.Module):
    """Trainable projection head over bge-small (384-d) embeddings; starts near-identity."""
    def __init__(self, d=384):
        super().__init__(); self.a = nn.Linear(d, d); self.s = nn.Linear(d, d)
        for l in (self.a, self.s): nn.init.eye_(l.weight); nn.init.zeros_(l.bias)
    def forward(self, a, s): return F.cosine_similarity(self.a(a), self.s(s), dim=-1)

_m = Ranker().eval()
def rank_sessions(interests: str, sessions: list) -> list:
    a = torch.tensor(embed([interests])); s = torch.tensor(embed([x["title"] + " " + x.get("abstract", "") for x in sessions]))
    with torch.no_grad(): score = _m(a.expand_as(s), s)
    return sorted([{**x, "relevance": round(float(sc), 3)} for x, sc in zip(sessions, score)], key=lambda x: -x["relevance"])
