from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, event as sa_event
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    name = Column(String); city = Column(String); date = Column(String)
    headcount = Column(Integer); budget_inr = Column(Float)
    brief = Column(Text); entities = Column(JSON); assumptions = Column(JSON)
    plan = Column(JSON)          # budget lines, agenda, timeline
    provider = Column(String, default="gemini")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True); event_id = Column(Integer, ForeignKey("events.id"))
    title = Column(String); status = Column(String, default="todo")
    depends_on = Column(JSON, default=list); ai_flag = Column(String, default="")

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True); event_id = Column(Integer, ForeignKey("events.id"))
    kind = Column(String); name = Column(String); city = Column(String)
    capacity = Column(Integer, default=0); cost_inr = Column(Float); av = Column(Integer, default=0)
    catering = Column(Integer, default=0); why = Column(Text, default="")

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True); event_id = Column(Integer, ForeignKey("events.id"))
    kind = Column(String)          # send_email | publish_registration | lock_rfp
    payload = Column(JSON); confidence = Column(Float); citations = Column(JSON)
    status = Column(String, default="pending")   # pending|approved|edited|rejected|executed

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True); ts = Column(DateTime, default=datetime.utcnow)
    event_id = Column(Integer); action_id = Column(Integer); actor = Column(String)
    decision = Column(String); detail = Column(JSON)

@sa_event.listens_for(AuditLog, "before_update")
@sa_event.listens_for(AuditLog, "before_delete")
def _immutable(*a):
    raise ValueError("AuditLog is immutable")

def init_db(): Base.metadata.create_all(engine)
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
