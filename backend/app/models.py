"""
models.py
-----------------
ADDITIONS:
  - Run.entity_trends: JSON dict of entity mention deltas vs prior run
  - Run.sota_watch: JSON list of benchmark movements
  - Run.stale_recovered: bool flag if this run auto-recovered prior stale runs
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from .database import Base


class Finding(Base):
    __tablename__ = "findings"

    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(500), nullable=False)
    summary          = Column(Text)
    why_matters      = Column(Text)
    source_url       = Column(String(1000))
    publisher        = Column(String(200))
    category         = Column(String(100))
    content_hash     = Column(String(64), unique=True, index=True)
    impact_score     = Column(Float, default=0.0)
    novelty_score    = Column(Float, default=0.0)
    final_score      = Column(Float, default=0.0)
    tags             = Column(JSON, default=list)
    entities         = Column(JSON, default=list)
    run_id           = Column(String(36), index=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    # Spec-required intelligence fields
    confidence_score = Column(Float, default=0.8)
    evidence         = Column(Text, nullable=True)
    date_detected    = Column(DateTime, default=datetime.utcnow)
    change_status    = Column(String(20), default="new")
    previous_hash    = Column(String(64), nullable=True)
    topic_cluster    = Column(String(100), nullable=True)


class Run(Base):
    __tablename__ = "runs"

    id                   = Column(Integer, primary_key=True)
    run_id               = Column(String(36), unique=True, index=True)
    status               = Column(String(50), default="running")
    started_at           = Column(DateTime, default=datetime.utcnow)
    finished_at          = Column(DateTime, nullable=True)
    pdf_path             = Column(String(500), nullable=True)
    total_found          = Column(Integer, default=0)
    elapsed_sec          = Column(Float, nullable=True)
    error_log            = Column(Text, nullable=True)
    agent_status         = Column(JSON, default=dict)
    findings_by_category = Column(JSON, default=dict)
    # v4.1 additions
    entity_trends        = Column(JSON, nullable=True)   # {entity: {current,previous,delta,trend}}
    sota_watch           = Column(JSON, nullable=True)   # [{title,source_url,delta,movement}]


class Source(Base):
    __tablename__ = "sources"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(200))
    url          = Column(String(1000), unique=True)
    agent_type   = Column(String(100))
    is_active    = Column(Integer, default=1)
    added_at     = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    last_hash    = Column(String(64), nullable=True)


class EmailRecipient(Base):
    """
    Email recipients managed via UI — Spec FR6: configurable distribution list.
    Replaces static config.yaml email_recipients list.
    """
    __tablename__ = "email_recipients"

    id        = Column(Integer, primary_key=True)
    email     = Column(String(200), unique=True, nullable=False, index=True)
    name      = Column(String(200), nullable=True)
    is_active = Column(Integer, default=1)
    added_at  = Column(DateTime, default=datetime.utcnow)
    note      = Column(String(500), nullable=True)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id           = Column(Integer, primary_key=True)
    url          = Column(String(1000), index=True)
    run_id       = Column(String(36), index=True)
    content_hash = Column(String(64), index=True)
    text_excerpt = Column(Text, nullable=True)
    fetched_at   = Column(DateTime, default=datetime.utcnow)
    agent_type   = Column(String(100), nullable=True)
