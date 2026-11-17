import time
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .config import settings, TELEMETRY
from .database import init_db, get_db, Event, Task, Vendor, Action, AuditLog
from .agents import planner_graph as pg, tools
from .rag import ingest, retriever
from .ml import predict_noshow as ml

app = FastAPI(title="OrganizerAI")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"])
@app.on_event("startup")
def _s(): init_db()

def ser(o): return {c.name: getattr(o, c.name) for c in o.__table__.columns}

@app.post("/api/events/brief")
async def brief(prompt: str = Form(...), provider: str = Form("gemini"), file: UploadFile | None = File(None), db: Session = Depends(get_db)):
    text, sources = prompt, []
    pages = []
    if file:
        data = await file.read()
        pages = ingest.pdf_pages(data) if file.filename.lower().endswith(".pdf") else [(1, ingest.image_text(data))]
        text += "\n" + "\n".join(t for _, t in pages); sources.append(file.filename)
    ex = tools.extract_entities(text); e = ex["entities"]
    ev = Event(name=f"Event in {e['city']}", city=e["city"], date=e["date"], headcount=e["headcount"], budget_inr=e["budget_inr"],
               brief=prompt, entities=e, assumptions=ex["assumptions"], provider=provider)
    db.add(ev); db.commit()
    if pages: retriever.add_chunks(ev.id, sources[0], ingest.chunk(pages))
    pg.start(ev.id, text, provider)       # runs until human_approval_gate interrupt
    return {"event_id": ev.id, "entities": e, "assumptions": ex["assumptions"], "sources": sources or ["prompt"]}

@app.get("/api/events")
def events(db: Session = Depends(get_db)): return [ser(e) for e in db.query(Event).all()]

@app.get("/api/events/{eid}")
def event(eid: int, db: Session = Depends(get_db)):
    ev = db.get(Event, eid)
    if not ev: raise HTTPException(404)
    return {**ser(ev), "tasks": [ser(t) for t in db.query(Task).filter_by(event_id=eid)],
            "vendors": [ser(v) for v in db.query(Vendor).filter_by(event_id=eid)]}

@app.get("/api/analytics/{eid}")
def analytics(eid: int, db: Session = Depends(get_db)):
    ev = db.get(Event, eid)
    return {"noshow_prob": round(ml.predict_noshow(45, 1, 10, 5, 80), 3),
            "overrun_prob": round(ml.predict_overrun(ev.budget_inr, ev.headcount, ev.entities.get("speakers", 3), .3, 40), 3)}

@app.get("/api/approvals")
def approvals(status: str = "pending", db: Session = Depends(get_db)):
    return [ser(a) for a in db.query(Action).filter_by(status=status)]

class Decision(BaseModel):
    decision: str            # approve | edit | reject
    payload: dict | None = None

@app.post("/api/approvals/{aid}/decide")
def decide(aid: int, d: Decision, db: Session = Depends(get_db)):
    a = db.get(Action, aid)
    if not a or a.status != "pending": raise HTTPException(400, "Not pending")
    a.status = {"approve": "approved", "edit": "approved", "reject": "rejected"}[d.decision]
    if d.payload: a.payload = d.payload
    db.commit()
    if db.query(Action).filter_by(event_id=a.event_id, status="pending").count() == 0:
        acts = db.query(Action).filter_by(event_id=a.event_id).all()
        dec = {str(x.id): {"decision": ("approve" if x.status == "approved" else "reject"), "payload": x.payload if x.id == aid and d.payload else None} for x in acts}
        for x in acts: x.status = "approved" if x.status == "approved" else "rejected"
        db.commit(); pg.resume(a.event_id, dec); return {"resumed": True}
    return {"resumed": False}

@app.get("/api/audit")
def audit(db: Session = Depends(get_db)): return [ser(x) for x in db.query(AuditLog).order_by(AuditLog.id.desc())]

class Q(BaseModel): event_id: int; question: str; provider: str | None = None
@app.post("/api/rag/ask")
def ask(q: Q):
    r = retriever.answer(q.event_id, q.question, q.provider)
    return r

@app.get("/api/eval/telemetry")
def telem():
    n = len(TELEMETRY) or 1
    return {"calls": len(TELEMETRY), "avg_latency_ms": round(sum(t["latency_ms"] for t in TELEMETRY) / n),
            "total_cost_inr": round(sum(t["cost_inr"] for t in TELEMETRY), 4), "recent": TELEMETRY[-20:]}

import subprocess, sys, json, os
@app.post("/api/eval/run")
def run_eval():
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "..", "eval", "benchmark.py")],
                       capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), ".."))
    try: return json.loads(p.stdout)
    except Exception: return {"error": p.stderr[-500:]}
