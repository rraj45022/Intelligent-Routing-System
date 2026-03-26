from pydantic import BaseModel


class OpsMetric(BaseModel):
    label: str
    value: int | str
    detail: str | None = None


class StrategyStat(BaseModel):
    strategy: str
    count: int
    share: float


class AssociateLoadSnapshot(BaseModel):
    associate_id: int
    associate_name: str
    availability_status: str
    open_tickets: int
    daily_assigned: int
    daily_capacity: int
    max_concurrent_tickets: int
    top_skills: list[str]


class RecentBatchJob(BaseModel):
    id: int
    job_name: str
    source_name: str
    status: str
    total_tickets: int
    processed_tickets: int
    succeeded_tickets: int
    failed_tickets: int
    chunk_size: int
    requested_at: str
    completed_at: str | None = None


class RecentAuditDecision(BaseModel):
    id: int
    ticket_id: int | None
    strategy: str
    confidence: float
    chosen_associate_id: int
    chosen_associate_name: str
    llm_used: bool
    matched_history_similarity: float | None = None
    reason: str
    created_at: str


class RoutingOpsDashboard(BaseModel):
    metrics: list[OpsMetric]
    strategy_breakdown: list[StrategyStat]
    associate_load: list[AssociateLoadSnapshot]
    recent_jobs: list[RecentBatchJob]
    recent_audits: list[RecentAuditDecision]
    artifact_path: str
    embedding_model_name: str