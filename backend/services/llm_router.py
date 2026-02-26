import json
import logging
from typing import Dict, Sequence

from backend.core.config import settings
from backend.models.associate import Associate
from backend.schemas.ticket import TicketCreate

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - optional dependency/runtime
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


def _build_client():
    if not settings.llm_api_key or not AsyncOpenAI:
        return None

    base_url = settings.llm_base_url
    if not base_url and settings.llm_provider.lower() == "grok":
        # xAI Grok uses OpenAI-compatible client with this base URL
        base_url = "https://api.x.ai/v1"

    return AsyncOpenAI(api_key=settings.llm_api_key, base_url=base_url) if base_url else AsyncOpenAI(api_key=settings.llm_api_key)


_client = _build_client()


async def score_with_llm(
    ticket: TicketCreate, associates: Sequence[Associate], top_k: int = 3
) -> Dict[int, float]:
    """Call LLM to score top-k associates. Returns {associate_id: score in [0,1]}.

    Falls back to empty dict if no API key/client is configured.
    """
    if not _client:
        return {}

    subset = list(associates)[: max(1, top_k)]
    candidate_text = "\n".join(
        f"- id: {a.id}, name: {a.name}, skills: {', '.join(a.skills or [])}" for a in subset
    )
    prompt = (
        "You are selecting the best associate to handle a ticket. "
        "Score each candidate between 0 and 1 (higher is better) based on skill match and general suitability. "
        "Respond with JSON object mapping associate_id to score."
    )

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Ticket: title={ticket.title}; description={ticket.description}; "
                f"module={ticket.module}; priority={ticket.priority}; "
                f"segment={ticket.customer_segment}; channel={ticket.channel}\n"
                f"Candidates:\n{candidate_text}"
            ),
        },
    ]

    try:
        resp = await _client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=200,
        )
        content = resp.choices[0].message.content if resp.choices else "{}"
        data = json.loads(content or "{}")
        scored: Dict[int, float] = {}
        for k, v in data.items():
            try:
                scored[int(k)] = float(v)
            except Exception:
                continue
        return scored
    except Exception as exc:  # pragma: no cover - runtime/IO errors
        logger.warning("LLM scoring failed; falling back to ML only: %s", exc)
        return {}
