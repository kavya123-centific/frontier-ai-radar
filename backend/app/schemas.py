"""
schemas.py
-----------------
Additions:
  - RunOut.entity_trends, RunOut.sota_watch
  - EntityTrend schema for /api/entity-trends
  - SotaEvent schema for /api/sota-watch
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class FindingOut(BaseModel):
    id:               int
    title:            str
    summary:          Optional[str]   = None
    why_matters:      Optional[str]   = None
    source_url:       Optional[str]   = None
    publisher:        Optional[str]   = None
    category:         Optional[str]   = None
    final_score:      Optional[float] = None
    impact_score:     Optional[float] = None
    novelty_score:    Optional[float] = None
    confidence_score: Optional[float] = None
    evidence:         Optional[str]   = None
    date_detected:    Optional[datetime] = None
    change_status:    Optional[str]   = "new"
    previous_hash:    Optional[str]   = None
    topic_cluster:    Optional[str]   = None
    tags:             Optional[List[str]] = []
    entities:         Optional[List[str]] = []
    run_id:           Optional[str]   = None
    created_at:       Optional[datetime] = None
    recommendation:   Optional[str]   = None
    priority:         Optional[str]   = "medium"
    impact_horizon:   Optional[str]   = "short-term"

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    run_id:               str
    status:               str
    started_at:           Optional[datetime] = None
    finished_at:          Optional[datetime] = None
    total_found:          Optional[int]   = 0
    elapsed_sec:          Optional[float] = None
    pdf_path:             Optional[str]   = None
    error_log:            Optional[str]   = None
    agent_status:         Optional[Dict]  = {}
    findings_by_category: Optional[Dict]  = {}
    entity_trends:        Optional[Dict]  = {}
    sota_watch:           Optional[List]  = []

    model_config = {"from_attributes": True}


class SourceIn(BaseModel):
    name:       str
    url:        str
    agent_type: str


class SourceOut(SourceIn):
    id:           int
    is_active:    int
    added_at:     Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_hash:    Optional[str]      = None

    model_config = {"from_attributes": True}


class ChangeDetectionOut(BaseModel):
    run_id:    str
    new:       List[FindingOut] = []
    updated:   List[FindingOut] = []
    unchanged: int = 0


class AgentMetric(BaseModel):
    name:         str
    total_found:  int
    success_runs: int
    error_runs:   int
    avg_elapsed:  float


class MetricsOut(BaseModel):
    total_runs:           int
    completed_runs:       int
    failed_runs:          int
    total_findings:       int
    avg_elapsed_sec:      float
    avg_findings_per_run: float
    findings_by_category: Dict[str, int]
    findings_by_cluster:  Dict[str, int]
    agent_metrics:        List[AgentMetric]
    change_stats:         Dict[str, int]
    top_entities:         List[Dict]
    runs_over_time:       List[Dict]


class SnapshotOut(BaseModel):
    id:           int
    url:          str
    run_id:       str
    content_hash: str
    text_excerpt: Optional[str] = None
    fetched_at:   Optional[datetime] = None
    agent_type:   Optional[str] = None

    model_config = {"from_attributes": True}


class EmailRecipientIn(BaseModel):
    email: str
    name:  Optional[str] = None
    note:  Optional[str] = None

class EmailRecipientOut(BaseModel):
    id:        int
    email:     str
    name:      Optional[str] = None
    note:      Optional[str] = None
    is_active: int
    added_at:  Optional[datetime] = None

    model_config = {"from_attributes": True}

class EmailTestIn(BaseModel):
    email: str   # Send a test email to this address