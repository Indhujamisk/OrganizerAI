import os, joblib, numpy as np
from sklearn.ensemble import RandomForestClassifier
P = os.path.join(os.path.dirname(__file__), "models"); os.makedirs(P, exist_ok=True)

def _bootstrap(kind):
    rng = np.random.default_rng(42); n = 3000
    if kind == "noshow":   # lead_days, free_ticket, rsvp_gap_days, weekday, distance_km
        X = np.c_[rng.integers(1, 90, n), rng.integers(0, 2, n), rng.integers(0, 30, n), rng.integers(0, 7, n), rng.integers(0, 500, n)]
        p = .15 + .004 * X[:, 0] + .20 * X[:, 1] + .004 * X[:, 2] + .0004 * X[:, 4]
    else:                  # budget_lakh, headcount, speakers, catering_share, lead_days
        X = np.c_[rng.uniform(1, 20, n), rng.integers(30, 800, n), rng.integers(1, 12, n), rng.uniform(.1, .5, n), rng.integers(5, 120, n)]
        p = .1 + .0006 * X[:, 1] + .02 * X[:, 2] + .3 * X[:, 3] - .002 * X[:, 4] - .01 * X[:, 0]
    y = (rng.random(n) < np.clip(p, .02, .95)).astype(int)
    m = RandomForestClassifier(n_estimators=150, random_state=1).fit(X, y); joblib.dump(m, f"{P}/{kind}.joblib"); return m

def _load(kind):
    f = f"{P}/{kind}.joblib"; return joblib.load(f) if os.path.exists(f) else _bootstrap(kind)
def predict_noshow(lead_days, free_ticket, rsvp_gap_days, weekday, distance_km) -> float:
    return float(_load("noshow").predict_proba([[lead_days, free_ticket, rsvp_gap_days, weekday, distance_km]])[0][1])
def predict_overrun(budget_inr, headcount, speakers, catering_share, lead_days) -> float:
    return float(_load("overrun").predict_proba([[budget_inr / 1e5, headcount, speakers, catering_share, lead_days]])[0][1])
