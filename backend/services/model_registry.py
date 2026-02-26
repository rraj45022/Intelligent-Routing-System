import math
from typing import List, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression

from backend.models.associate import Associate
from backend.models.tickets import PriorityEnum
from backend.schemas.ticket import TicketCreate

# Simple in-memory model trained on synthetic data at import time.
_MODEL: LogisticRegression | None = None

PRIORITY_TO_NUM = {
    PriorityEnum.Low: 0,
    PriorityEnum.Medium: 1,
    PriorityEnum.High: 2,
    PriorityEnum.Critical: 3,
}


def _train_synthetic_model() -> LogisticRegression:
    rng = np.random.default_rng(42)
    n = 400
    skill_match = rng.integers(0, 2, size=n)
    priority = rng.integers(0, 4, size=n)
    name_signal = rng.integers(0, 5, size=n)

    # Outcome is correlated with skill_match and higher priority (more weight on skill)
    logit = 1.8 * skill_match + 0.4 * priority + 0.2 * name_signal + rng.normal(0, 0.6, size=n)
    prob = 1 / (1 + np.exp(-logit))
    y = (prob > 0.5).astype(int)

    X = np.stack([skill_match, priority, name_signal], axis=1)
    model = LogisticRegression(max_iter=200)
    model.fit(X, y)
    return model


def _ensure_model() -> LogisticRegression:
    global _MODEL
    if _MODEL is None:
        _MODEL = _train_synthetic_model()
    return _MODEL


def _priority_to_num(priority: PriorityEnum) -> int:
    return PRIORITY_TO_NUM.get(priority, 1)


def _name_signal(name: str) -> int:
    # Deterministic, lightweight proxy for "experience" without extra data.
    return (len(name) % 5)


def _featurize(ticket: TicketCreate, associate: Associate) -> list[float]:
    skills = associate.skills or []
    skill_match = 1 if ticket.module in skills else 0
    priority_num = _priority_to_num(ticket.priority)
    name_sig = _name_signal(associate.name)
    return [skill_match, priority_num, name_sig]


def score_candidates(
    ticket: TicketCreate, associates: Sequence[Associate]
) -> List[tuple[int, float]]:
    """Return (associate_id, score) pairs using the trained model."""
    model = _ensure_model()
    if not associates:
        return []

    features = np.array([_featurize(ticket, a) for a in associates])
    probs = model.predict_proba(features)[:, 1]

    scored = [(associate.id, float(score)) for associate, score in zip(associates, probs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
