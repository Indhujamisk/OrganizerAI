"""Run from backend/: python ../eval/benchmark.py  -> JSON with Chroma vs FAISS latency, hit rate, faithfulness."""
import sys, os, json, time, statistics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.rag import retriever
from app.config import llm, TELEMETRY

CASES = [("What time do doors open?", "8:30"), ("How much is a general ticket?", "1,500"), ("Are refunds available?", "7 days"),
         ("Is lunch vegetarian?", "vegetarian"), ("How much is car parking?", "100"), ("What is the Wi-Fi name?", "KovaiAI")]
OUT_OF_SCOPE = ["Who won the IPL in 2023?", "What is the CEO's phone number?"]

def run(eid=1):
    res = {}
    for b in ("chroma", "faiss"):
        lat, hits = [], 0
        for q, kw in CASES:
            h, ms = retriever.search(eid, q, backend=b); lat.append(ms)
            hits += any(kw.lower() in x["text"].lower() for x in h)
        res[b] = {"avg_latency_ms": round(statistics.mean(lat), 1), "hit_rate": round(hits / len(CASES), 2)}
    faithful = sum(any(kw.lower() in retriever.answer(eid, q)["answer"].lower() for _ in [0]) for q, kw in CASES)
    halluc = sum(not retriever.answer(eid, q)["escalate"] for q in OUT_OF_SCOPE)
    res["faithfulness"] = round(faithful / len(CASES), 2)
    res["hallucination_rate"] = round(halluc / len(OUT_OF_SCOPE), 2)   # answered when it should have escalated
    res["llm_calls"] = len(TELEMETRY); res["cost_inr"] = round(sum(t["cost_inr"] for t in TELEMETRY), 4)
    return res
if __name__ == "__main__": print(json.dumps(run(), indent=2))
