import time, numpy as np, chromadb
from ..config import settings
_model = None; _client = None
def embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.embed_model)
    return _model
def col():
    global _client
    if _client is None: _client = chromadb.PersistentClient(path=settings.chroma_dir)
    return _client.get_or_create_collection("event_docs", metadata={"hnsw:space": "cosine"})
def embed(texts, query=False):
    pre = "Represent this sentence for searching relevant passages: " if query else ""
    return embedder().encode([pre + t for t in texts], normalize_embeddings=True).tolist()

def add_chunks(event_id: int, source: str, chunks: list):
    base = f"{event_id}-{source}-"
    col().upsert(ids=[f"{base}{i}" for i in range(len(chunks))], documents=[x["text"] for x in chunks],
                 embeddings=embed([x["text"] for x in chunks]),
                 metadatas=[{"event_id": event_id, "source": source, "page": x["page"], "approved": 1} for x in chunks])

WHERE = lambda eid: {"$and": [{"event_id": eid}, {"approved": 1}]}
def search(event_id: int, q: str, k: int = 4, backend: str = "chroma"):
    t0 = time.time(); qe = embed([q], query=True)
    if backend == "faiss":
        import faiss
        r = col().get(where=WHERE(event_id), include=["documents", "embeddings", "metadatas"])
        if not len(r["ids"]): return [], 0.0
        M = np.array(r["embeddings"], dtype="float32"); idx = faiss.IndexFlatIP(M.shape[1]); idx.add(M)
        D, I = idx.search(np.array(qe, dtype="float32"), min(k, len(M)))
        hits = [{"text": r["documents"][i], "source": r["metadatas"][i]["source"], "page": r["metadatas"][i]["page"], "score": float(s)} for s, i in zip(D[0], I[0])]
    else:
        r = col().query(query_embeddings=qe, n_results=k, where=WHERE(event_id), include=["documents", "metadatas", "distances"])
        hits = [{"text": d, "source": m["source"], "page": m["page"], "score": 1 - dist}
                for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])]
    return hits, (time.time() - t0) * 1000

def answer(event_id: int, q: str, provider=None):
    from ..config import llm
    hits, ms = search(event_id, q)
    conf = max((h["score"] for h in hits), default=0.0)
    if conf < 0.65:
        return {"answer": "I couldn't find this in the approved event documents.", "citations": [], "confidence": round(conf, 3), "escalate": True, "latency_ms": round(ms)}
    ctx = "\n".join(f"[{h['source']} p.{h['page']}] {h['text']}" for h in hits)
    a = llm(f"Context:\n{ctx}\n\nQuestion: {q}\nAnswer ONLY from the context in 1-3 sentences. If missing, say you don't know.", provider,
            system="You are an event FAQ assistant. Never use outside knowledge.")
    if a.startswith("[offline-stub]"): a = hits[0]["text"]
    return {"answer": a, "citations": [{"source": h["source"], "page": h["page"], "score": round(h["score"], 3)} for h in hits[:3]],
            "confidence": round(conf, 3), "escalate": False, "latency_ms": round(ms)}
