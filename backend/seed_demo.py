"""Run once: python seed_demo.py  -> loads a Coimbatore AI conference, vendors, and a policy PDF into RAG."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from app.database import init_db, SessionLocal, Event, Vendor, Task
from app.agents import tools
from app.rag import ingest, retriever

POLICY = [
 ["Kovai AI Summit 2026 - Attendee Policy", "Venue: Codissia Trade Fair Complex, Coimbatore. Doors open at 8:30 AM on 12 December. Sessions start at 9:30 AM.",
  "Registration: Free for students with valid ID; general tickets are Rs 1,500 including GST. Entry requires the QR code sent by email."],
 ["Refunds and Food", "Refunds are available until 7 days before the event. Lunch is vegetarian with a vegan option; Jain meals must be requested at registration.",
  "Parking: Free two-wheeler parking; four-wheeler parking costs Rs 100. Wi-Fi is provided on the SSID KovaiAI with the password on your badge."],
]
def make_pdf() -> bytes:
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4)
    for page in POLICY:
        y = 800
        for line in page:
            c.drawString(50, y, line[:95]); y -= 20
            if len(line) > 95: c.drawString(50, y, line[95:190]); y -= 20
            y -= 10
        c.showPage()
    c.save(); return buf.getvalue()

def main():
    init_db()
    with SessionLocal() as db:
        if db.query(Event).count(): print("Already seeded"); return
        brief = "Plan a 200-person AI meetup in Coimbatore on 12 December with a ₹3,00,000 budget, 3 speakers, catering, and registration"
        ex = tools.extract_entities(brief); e = ex["entities"]
        ev = Event(name="Kovai AI Summit 2026", city="Coimbatore", date="12 Dec", headcount=200, budget_inr=300000, brief=brief,
                   entities=e, assumptions=ex["assumptions"], provider="gemini",
                   plan={"budget": tools.allocate_budget(300000, 200),
                         "timeline": [{"t": "T-30d", "step": "Venue locked"}, {"t": "T-14d", "step": "Registration open"}, {"t": "T-0", "step": "Event day"}],
                         "risk_note": "Catering is the largest variable cost; confirm headcount 3 days prior.",
                         "agenda": [{"title": "Opening Keynote: Applied AI in India", "speaker": "Dr. Meera Iyer", "room": "Hall A", "start": 9.5, "end": 10.5},
                                    {"title": "Building RAG Systems", "speaker": "Arjun Nair", "room": "Hall A", "start": 10.5, "end": 11.5},
                                    {"title": "LLMs on the Edge", "speaker": "Arjun Nair", "room": "Hall B", "start": 11.0, "end": 12.0}]})
        db.add(ev); db.flush()
        for kind, name, cap, cost, av, cat in [("venue", "Codissia Trade Fair Complex", 500, 90000, 1, 1), ("venue", "PSG Tech Auditorium", 350, 60000, 1, 0),
                                                ("venue", "Hotel Residency Banquet", 220, 110000, 1, 1), ("caterer", "Annapoorna Catering", 0, 85000, 0, 1),
                                                ("av", "SoundWorks Coimbatore", 0, 30000, 1, 0)]:
            db.add(Vendor(event_id=ev.id, kind=kind, name=name, city="Coimbatore", capacity=cap, cost_inr=cost, av=av, catering=cat, why=""))
        for t, d in [("Lock venue", []), ("Confirm speakers", []), ("Finalise catering", ["Lock venue"]), ("Publish registration", ["Lock venue"])]:
            db.add(Task(event_id=ev.id, title=t, depends_on=d, ai_flag="Blocked until dependency done" if d else ""))
        db.commit(); eid = ev.id
    pdf = make_pdf(); open("sample_policy.pdf", "wb").write(pdf)
    retriever.add_chunks(eid, "attendee_policy.pdf", ingest.chunk(ingest.pdf_pages(pdf)))
    print(f"Seeded event_id={eid}")
if __name__ == "__main__": main()
