from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from ..config import llm
from ..database import SessionLocal, Event, Task, Vendor, Action, AuditLog
from . import tools

class S(TypedDict, total=False):
    event_id: int; brief: str; provider: str
    entities: dict; plan: dict; shortlist: list; actions: list; decisions: dict; results: list

def extract_requirements(s: S):
    return {"entities": tools.extract_entities(s["brief"])["entities"]}

def generate_plan_budget_timeline(s: S):
    e = s["entities"]
    budget = tools.allocate_budget(e["budget_inr"], e["headcount"])
    note = llm(f"In 2 sentences, summarise key risks for a {e['headcount']}-person event in {e['city']} on {e['date']}, budget INR {e['budget_inr']:.0f}.", s.get("provider"))
    tasks = [("Lock venue", []), ("Confirm speakers", []), ("Finalise catering", ["Lock venue"]),
             ("Publish registration", ["Lock venue"]), ("Send speaker invites", ["Confirm speakers"]), ("Run-of-show & AV check", ["Finalise catering"])]
    timeline = [{"t": "T-30d", "step": "Venue + vendors locked"}, {"t": "T-14d", "step": "Registration open"},
                {"t": "T-3d", "step": "Final headcount to caterer"}, {"t": "T-0", "step": "Event day"}]
    with SessionLocal() as db:
        db.query(Task).filter_by(event_id=s["event_id"]).delete()
        for t, d in tasks:
            db.add(Task(event_id=s["event_id"], title=t, depends_on=d, ai_flag="Blocked until dependency done" if d else ""))
        ev = db.get(Event, s["event_id"]); ev.plan = {"budget": budget, "timeline": timeline, "risk_note": note}; db.commit()
    return {"plan": {"budget": budget, "timeline": timeline}}

def shortlist_venues_vendors(s: S):
    e = s["entities"]
    with SessionLocal() as db:
        sl = tools.search_vendors(db.query(Vendor).all(), e["city"], e["headcount"], e["budget_inr"])
        for x in sl:
            v = db.get(Vendor, x["id"]); v.why = x["why"]
            if v.event_id is None: v.event_id = s["event_id"]
        db.commit()
    return {"shortlist": sl}

def draft_communications(s: S):
    e = s["entities"]; top = (s["shortlist"] or [{"name": "TBD", "why": "No match"}])[0]
    body = llm(f"Write a short, polite email to {top['name']} requesting a quote for {e['headcount']} guests on {e['date']} in {e['city']}.", s.get("provider"))
    acts = [
        {"kind": "send_email", "payload": {"to": "sales@vendor.example", "subject": f"Quote request – {e['date']}", "body": body}, "confidence": 0.82, "citations": [top["why"]]},
        {"kind": "publish_registration", "payload": {"title": f"Event in {e['city']}", "capacity": e["headcount"], "date": e["date"]}, "confidence": 0.74, "citations": ["Extracted from brief"]},
        {"kind": "lock_rfp", "payload": {"vendor": top["name"], "budget_cap_inr": e["budget_inr"] * 0.3}, "confidence": 0.68, "citations": [top["why"]]},
    ]
    with SessionLocal() as db:
        for a in acts:
            row = Action(event_id=s["event_id"], **a); db.add(row); db.flush(); a["id"] = row.id
        db.commit()
    return {"actions": acts}

def human_approval_gate(s: S):
    decisions = interrupt({"event_id": s["event_id"], "actions": s["actions"]})   # graph pauses here
    return {"decisions": decisions}

def execute_approved_actions(s: S):
    results = []
    with SessionLocal() as db:
        for a in s["actions"]:
            d = s["decisions"].get(str(a["id"]), {"decision": "reject"})
            row = db.get(Action, a["id"])
            if d["decision"] in ("approve", "edit"):
                payload = d.get("payload") or row.payload
                res = tools.send_email(**payload) if row.kind == "send_email" else {"status": "done", "kind": row.kind, **payload}
                row.status = "executed"; results.append(res)
                db.add(AuditLog(event_id=row.event_id, action_id=row.id, actor="organizer", decision=d["decision"], detail={"payload": payload, "result": res}))
            else:
                row.status = "rejected"
                db.add(AuditLog(event_id=row.event_id, action_id=row.id, actor="organizer", decision="reject", detail={}))
        db.commit()
    return {"results": results}

SEQ = [extract_requirements, generate_plan_budget_timeline, shortlist_venues_vendors,
       draft_communications, human_approval_gate, execute_approved_actions]
def build():
    g = StateGraph(S)
    for n in SEQ: g.add_node(n.__name__, n)
    names = [n.__name__ for n in SEQ]
    g.add_edge(START, names[0])
    for a, b in zip(names, names[1:]): g.add_edge(a, b)
    g.add_edge(names[-1], END)
    return g.compile(checkpointer=MemorySaver())

graph = build()
def cfg(eid): return {"configurable": {"thread_id": f"event-{eid}"}}
def start(eid, brief, provider): return graph.invoke({"event_id": eid, "brief": brief, "provider": provider}, cfg(eid))
def resume(eid, decisions): return graph.invoke(Command(resume=decisions), cfg(eid))
