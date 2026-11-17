import re
from datetime import datetime

LAKH = 100000
def extract_entities(text: str) -> dict:
    t = text.replace(",", "")
    ent, assumptions = {}, []
    m = re.search(r"(?:₹|rs\.?|inr)\s*([\d.]+)\s*(lakh|lac|cr|crore)?", t, re.I)
    if m:
        v = float(m.group(1)); u = (m.group(2) or "").lower()
        ent["budget_inr"] = v * (LAKH if u in ("lakh", "lac") else 1e7 if u in ("cr", "crore") else 1)
    else:
        ent["budget_inr"] = 300000.0; assumptions.append("Budget not found; assumed ₹3,00,000")
    m = re.search(r"(\d{2,5})[- ]?(?:person|people|attendees|pax|guests)", t, re.I)
    ent["headcount"] = int(m.group(1)) if m else 100
    if not m: assumptions.append("Headcount not found; assumed 100")
    m = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*", t, re.I)
    ent["date"] = f"{m.group(1)} {m.group(2).title()}" if m else "TBD"
    if not m: assumptions.append("Date not found; marked TBD")
    cities = ["Coimbatore","Chennai","Bengaluru","Mumbai","Pune","Delhi","Hyderabad","Kochi","Nashik","Ahmedabad","Kolkata"]
    ent["city"] = next((c for c in cities if c.lower() in t.lower()), "Coimbatore")
    m = re.search(r"(\d+)\s*speakers?", t, re.I); ent["speakers"] = int(m.group(1)) if m else 3
    ent["needs"] = [k for k in ["catering", "registration", "av", "livestream", "swag"] if k in t.lower()]
    return {"entities": ent, "assumptions": assumptions}

def allocate_budget(total: float, headcount: int) -> list[dict]:
    split = {"Venue": .30, "Catering": .30, "AV & Production": .10, "Speakers & Travel": .12,
             "Marketing": .06, "Staff & Registration": .05, "Contingency": .07}
    rows = []
    for k, p in split.items():
        base = total * p; gst = .05 if k == "Catering" else .18
        rows.append({"category": k, "base_inr": round(base), "gst_rate": gst, "gst_inr": round(base * gst), "total_inr": round(base * (1 + gst))})
    return rows

def search_vendors(db_vendors: list, city: str, headcount: int, budget: float) -> list[dict]:
    out = []
    for v in db_vendors:
        if v.city.lower() != city.lower(): continue
        if v.kind == "venue" and v.capacity < headcount: continue
        score = 1.0 - min(v.cost_inr / max(budget, 1), 1) * 0.5 + (0.1 if v.av else 0) + (0.1 if v.catering else 0)
        why = f"{v.name}: in {v.city}; ₹{v.cost_inr:,.0f}" + (f", capacity {v.capacity} ≥ {headcount}" if v.kind == "venue" else "") \
              + (", AV included" if v.av else "") + (", in-house catering" if v.catering else "")
        out.append({"id": v.id, "name": v.name, "kind": v.kind, "score": round(score, 2), "why": why})
    return sorted(out, key=lambda x: -x["score"])[:6]

def detect_conflicts(sessions: list[dict], rooms: dict, expected: dict) -> list[str]:
    issues = []
    for i, a in enumerate(sessions):
        if expected.get(a["title"], 0) > rooms.get(a["room"], 1e9):
            issues.append(f"Room over capacity: '{a['title']}' in {a['room']}")
        for b in sessions[i + 1:]:
            if a["speaker"] == b["speaker"] and a["start"] < b["end"] and b["start"] < a["end"]:
                issues.append(f"Speaker conflict: {a['speaker']} in '{a['title']}' and '{b['title']}'")
    return issues

def send_email(to: str, subject: str, body: str) -> dict:   # swap for SMTP/SendGrid in prod
    return {"status": "queued", "to": to, "subject": subject, "at": datetime.utcnow().isoformat()}
