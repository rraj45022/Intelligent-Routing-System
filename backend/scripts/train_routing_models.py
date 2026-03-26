"""Train persisted routing artifacts and skill profiles.

Run with: ./venv/bin/python -m backend.scripts.train_routing_models
"""

import asyncio

from sqlalchemy import select

from backend.core.config import settings
from backend.core.db import AsyncSessionLocal
from backend.models.associate import Associate
from backend.models.ticket_history import TicketHistory
from backend.services import model_registry


async def train() -> None:
    async with AsyncSessionLocal() as session:
        history_rows = (await session.execute(select(TicketHistory).order_by(TicketHistory.id))).scalars().all()
        associates = (await session.execute(select(Associate).order_by(Associate.id))).scalars().all()

        artifacts = model_registry.train_similarity_model(history_rows, persist=True)
        skill_profiles = model_registry.build_skill_profiles(history_rows, associates)

        for associate in associates:
            associate.skill_levels = skill_profiles.get(associate.id, {})

        await session.commit()

    artifact_path = model_registry._artifact_path()
    print(
        f"Routing model training completed. history_rows={len(history_rows)} associates={len(associates)} artifact={artifact_path} model={settings.routing_embedding_model_name}"
    )


if __name__ == "__main__":
    asyncio.run(train())