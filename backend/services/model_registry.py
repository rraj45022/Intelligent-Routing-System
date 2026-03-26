from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List, Sequence

import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

from backend.core.config import settings
from backend.models.associate import Associate, AvailabilityStatus
from backend.models.ticket_history import TicketHistory
from backend.schemas.ticket import TicketCreate


@dataclass
class HistoryDocument:
    history_id: int
    source_ticket_id: int | None
    resolved_by_associate_id: int
    title: str
    description: str
    module: str
    customer_segment: str
    channel: str
    priority: str


@dataclass
class HistoryMatch:
    history_id: int
    source_ticket_id: int | None
    similarity: float
    resolved_by_associate_id: int
    title: str


@dataclass
class AssociateRoutingScore:
    associate_id: int
    final_score: float
    skill_score: float
    workload_score: float
    capacity_remaining: int


@dataclass
class SimilarityArtifacts:
    embedding_model_name: str
    history_embeddings: np.ndarray
    vector_index: NearestNeighbors
    documents: list[HistoryDocument]
    history_ids: tuple[int, ...]


def _artifact_path() -> Path:
    return Path(settings.routing_artifact_dir) / settings.routing_similarity_artifact_name


_EMBEDDING_MODEL: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer(settings.routing_embedding_model_name)
    return _EMBEDDING_MODEL


def _compose_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def _ticket_text(ticket: TicketCreate) -> str:
    return _compose_text(
        ticket.title,
        ticket.description,
        ticket.module,
        ticket.customer_segment,
        ticket.channel,
        ticket.priority.value,
    )


def _history_text_from_document(document: HistoryDocument) -> str:
    return _compose_text(
        document.title,
        document.description,
        document.module,
        document.customer_segment,
        document.channel,
        document.priority,
    )


def _history_document(history: TicketHistory) -> HistoryDocument:
    return HistoryDocument(
        history_id=history.id,
        source_ticket_id=history.source_ticket_id,
        resolved_by_associate_id=history.resolved_by_associate_id,
        title=history.title,
        description=history.description,
        module=history.module,
        customer_segment=history.customer_segment,
        channel=history.channel,
        priority=history.priority.value,
    )


def _load_artifacts(path: Path) -> SimilarityArtifacts | None:
    if not path.exists():
        return None

    payload = joblib.load(path)
    documents = [HistoryDocument(**item) for item in payload["documents"]]
    return SimilarityArtifacts(
        embedding_model_name=payload["embedding_model_name"],
        history_embeddings=np.asarray(payload["history_embeddings"]),
        vector_index=payload["vector_index"],
        documents=documents,
        history_ids=tuple(payload["history_ids"]),
    )


def train_similarity_model(
    history_rows: Sequence[TicketHistory], persist: bool = True
) -> SimilarityArtifacts | None:
    if not history_rows:
        return None

    documents = [_history_document(row) for row in history_rows]
    model = _get_embedding_model()
    history_embeddings = np.asarray(
        model.encode(
            [_history_text_from_document(doc) for doc in documents],
            batch_size=settings.routing_embedding_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    )
    vector_index = NearestNeighbors(metric="cosine")
    vector_index.fit(history_embeddings)
    artifacts = SimilarityArtifacts(
        embedding_model_name=settings.routing_embedding_model_name,
        history_embeddings=history_embeddings,
        vector_index=vector_index,
        documents=documents,
        history_ids=tuple(doc.history_id for doc in documents),
    )

    if persist:
        path = _artifact_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "embedding_model_name": artifacts.embedding_model_name,
                "history_embeddings": artifacts.history_embeddings,
                "vector_index": artifacts.vector_index,
                "documents": [asdict(doc) for doc in artifacts.documents],
                "history_ids": list(artifacts.history_ids),
            },
            path,
        )

    return artifacts


def ensure_similarity_model(history_rows: Sequence[TicketHistory]) -> SimilarityArtifacts | None:
    if not history_rows:
        return None

    path = _artifact_path()
    artifacts = _load_artifacts(path)
    current_history_ids = tuple(row.id for row in history_rows)
    if (
        artifacts is None
        or artifacts.history_ids != current_history_ids
        or artifacts.embedding_model_name != settings.routing_embedding_model_name
    ):
        return train_similarity_model(history_rows, persist=True)
    return artifacts


def _apply_similarity_boosts(ticket: TicketCreate, history: HistoryDocument, base_score: float) -> float:
    score = base_score
    if ticket.module.strip().lower() == history.module.strip().lower():
        score += 0.15
    if ticket.customer_segment.strip().lower() == history.customer_segment.strip().lower():
        score += 0.05
    if ticket.channel.strip().lower() == history.channel.strip().lower():
        score += 0.05
    if ticket.priority.value == history.priority:
        score += 0.05
    return min(score, 1.0)


def find_history_matches(
    ticket: TicketCreate, history_rows: Sequence[TicketHistory], top_k: int | None = None
) -> list[HistoryMatch]:
    artifacts = ensure_similarity_model(history_rows)
    if artifacts is None:
        return []

    query_embedding = np.asarray(
        _get_embedding_model().encode(
            [_ticket_text(ticket)],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    )
    neighbor_count = min(top_k or settings.history_top_k, len(artifacts.documents))
    distances, indices = artifacts.vector_index.kneighbors(query_embedding, n_neighbors=neighbor_count)
    if indices.size == 0:
        return []
    matches: list[HistoryMatch] = []

    for raw_distance, raw_index in zip(distances[0], indices[0]):
        index = int(raw_index)
        document = artifacts.documents[index]
        similarity = max(0.0, 1.0 - float(raw_distance))
        boosted_similarity = _apply_similarity_boosts(ticket, document, similarity)
        matches.append(
            HistoryMatch(
                history_id=document.history_id,
                source_ticket_id=document.source_ticket_id,
                similarity=float(boosted_similarity),
                resolved_by_associate_id=document.resolved_by_associate_id,
                title=document.title,
            )
        )
    matches.sort(key=lambda item: item.similarity, reverse=True)
    return matches


def find_best_history_match(
    ticket: TicketCreate, history_rows: Sequence[TicketHistory]
) -> HistoryMatch | None:
    matches = find_history_matches(ticket, history_rows, top_k=1)
    return matches[0] if matches else None


def build_skill_profiles(
    history_rows: Sequence[TicketHistory], associates: Sequence[Associate]
) -> dict[int, dict[str, float]]:
    grouped: dict[tuple[int, str], list[TicketHistory]] = defaultdict(list)
    for row in history_rows:
        grouped[(row.resolved_by_associate_id, row.module.strip().lower())].append(row)

    profiles: dict[int, dict[str, float]] = {associate.id: {} for associate in associates}
    for (associate_id, module), rows in grouped.items():
        ticket_count = len(rows)
        avg_csat = sum((row.csat_score or 4.0) for row in rows) / ticket_count
        avg_resolution = sum((row.resolution_hours or 24.0) for row in rows) / ticket_count

        volume_score = min(ticket_count / 8.0, 1.0)
        quality_score = min(avg_csat / 5.0, 1.0)
        speed_score = max(0.0, 1.0 - min(avg_resolution, 48.0) / 48.0)
        profile_score = round(0.5 * volume_score + 0.3 * quality_score + 0.2 * speed_score, 4)
        profiles.setdefault(associate_id, {})[module] = profile_score

    for associate in associates:
        profile = profiles.setdefault(associate.id, {})
        for skill in associate.skills or []:
            normalized_skill = skill.strip().lower()
            profile.setdefault(normalized_skill, 0.55)
    return profiles


def _normalize_skill_score(ticket: TicketCreate, associate: Associate) -> float:
    module = ticket.module.strip().lower()
    skill_levels = {key.strip().lower(): float(value) for key, value in (associate.skill_levels or {}).items()}
    if module in skill_levels:
        return max(0.0, min(skill_levels[module], 1.0))

    skills = [skill.strip().lower() for skill in (associate.skills or [])]
    if module in skills:
        return 0.65
    return 0.1


def _workload_score(
    associate: Associate,
    open_ticket_count: int,
    daily_assigned_count: int,
) -> tuple[float, int]:
    if associate.availability_status == AvailabilityStatus.offline:
        return 0.0, 0

    max_concurrent = max(associate.max_concurrent_tickets, 1)
    daily_capacity = max(associate.daily_capacity, 1)
    concurrent_ratio = open_ticket_count / max_concurrent
    daily_ratio = daily_assigned_count / daily_capacity
    utilization = min(1.5, 0.65 * concurrent_ratio + 0.35 * daily_ratio)
    headroom = max(0.0, 1.0 - utilization)

    availability_bonus = 1.0 if associate.availability_status == AvailabilityStatus.available else 0.7
    workload_score = max(0.0, min(1.0, 0.7 * headroom + 0.3 * availability_bonus))
    capacity_remaining = min(max_concurrent - open_ticket_count, daily_capacity - daily_assigned_count)
    return workload_score, max(capacity_remaining, 0)


def score_candidates(
    ticket: TicketCreate,
    associates: Sequence[Associate],
    open_ticket_counts: dict[int, int] | None = None,
    daily_assigned_counts: dict[int, int] | None = None,
) -> List[AssociateRoutingScore]:
    if not associates:
        return []

    open_ticket_counts = open_ticket_counts or {}
    daily_assigned_counts = daily_assigned_counts or {}
    scored: list[AssociateRoutingScore] = []
    for associate in associates:
        skill_score = _normalize_skill_score(ticket, associate)
        workload_score, capacity_remaining = _workload_score(
            associate,
            open_ticket_counts.get(associate.id, 0),
            daily_assigned_counts.get(associate.id, 0),
        )
        final_score = round(0.7 * skill_score + 0.3 * workload_score, 4)
        if capacity_remaining <= 0:
            final_score *= 0.5

        scored.append(
            AssociateRoutingScore(
                associate_id=associate.id,
                final_score=final_score,
                skill_score=round(skill_score, 4),
                workload_score=round(workload_score, 4),
                capacity_remaining=capacity_remaining,
            )
        )

    scored.sort(key=lambda item: item.final_score, reverse=True)
    return scored
