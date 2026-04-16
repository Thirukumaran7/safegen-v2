"""
SafeGen AI v2 — Database Models
SQLAlchemy models for PostgreSQL / SQLite
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id              = Column(Integer, primary_key=True, index=True)
    timestamp       = Column(DateTime, default=datetime.utcnow)
    input_text      = Column(Text, nullable=False)
    input_type      = Column(String(20), default="text")
    role            = Column(String(20), nullable=False)
    policy          = Column(String(20), nullable=False)

    # Scores
    final_score     = Column(Float)
    malware_score   = Column(Float)
    pii_score       = Column(Float)
    intent_score    = Column(Float)

    # Decision
    decision        = Column(String(20), nullable=False)
    decision_reason = Column(Text)

    # Detections
    malware_type    = Column(String(100))
    severity        = Column(String(20))
    pii_types       = Column(JSON)
    pii_count       = Column(Integer, default=0)
    intent_label    = Column(String(20))
    intent_confidence = Column(Float)
    injection_detected = Column(Boolean, default=False)

    # RAG
    rag_used        = Column(Boolean, default=False)
    rag_sources     = Column(JSON)

    # Response
    safe_response   = Column(Text)
    explanation     = Column(JSON)

    # Feedback
    feedback_agreed = Column(Boolean, nullable=True)
    feedback_comment = Column(Text, nullable=True)


class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id              = Column(Integer, primary_key=True, index=True)
    analysis_id     = Column(Integer, nullable=False)
    timestamp       = Column(DateTime, default=datetime.utcnow)
    agreed          = Column(Boolean, nullable=False)
    suggested_decision = Column(String(20), nullable=True)
    user_comment    = Column(Text, nullable=True)


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id              = Column(Integer, primary_key=True, index=True)
    title           = Column(String(200), nullable=False)
    content         = Column(Text, nullable=False)
    category        = Column(String(100))
    language        = Column(String(20), default="english")
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Database setup ────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safegen_v2.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()