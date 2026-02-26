"""Seed minimal associates and tickets for local testing.

Run with: ./venv/bin/python -m backend.scripts.seed_sample_data
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from backend.core.db import AsyncSessionLocal
from backend.models.associate import Associate
from backend.models.tickets import PriorityEnum, StatusEnum, Ticket
from backend.models.user import User, UserRole
from backend.services.auth import get_password_hash


async def seed():
    async with AsyncSessionLocal() as session:
        existing_user = await session.scalar(select(User.id))
        if not existing_user:
            users = [
                User(
                    email="admin@example.com",
                    full_name="Admin",
                    hashed_password=get_password_hash("admin123"),
                    role=UserRole.admin,
                    is_active=True,
                ),
                User(
                    email="agent@example.com",
                    full_name="Agent",
                    hashed_password=get_password_hash("agent123"),
                    role=UserRole.agent,
                    is_active=True,
                ),
            ]
            session.add_all(users)

        existing_assoc = await session.scalar(select(Associate.id))
        if not existing_assoc:
            associates = [
                Associate(name="Alice", skills=["billing", "payments"], active=True),
                Associate(name="Bob", skills=["auth", "security"], active=True),
                Associate(name="Charlie", skills=["search", "catalog"], active=True),
                Associate(name="Diana", skills=["shipping", "logistics"], active=True),
            ]
            session.add_all(associates)
            await session.flush()

        existing_ticket = await session.scalar(select(Ticket.id))
        if not existing_ticket:
            now = datetime.utcnow()
            tickets = [
                Ticket(
                    title="Payment failure on checkout",
                    description="Customer cannot complete payment due to 3DS error",
                    module="billing",
                    priority=PriorityEnum.High,
                    status=StatusEnum.Resolved,
                    customer_segment="retail",
                    channel="web",
                    created_at=now - timedelta(days=5),
                    resolved_at=now - timedelta(days=4, hours=22),
                    assigned_associate_id=1,
                    resolution_hours=26,
                    reopened_flag=False,
                    escalated_flag=False,
                    csat_score=4.5,
                ),
                Ticket(
                    title="Login throttling issue",
                    description="Lockouts triggered too aggressively for legit users",
                    module="auth",
                    priority=PriorityEnum.Medium,
                    status=StatusEnum.Resolved,
                    customer_segment="enterprise",
                    channel="mobile",
                    created_at=now - timedelta(days=4),
                    resolved_at=now - timedelta(days=3, hours=12),
                    assigned_associate_id=2,
                    resolution_hours=36,
                    reopened_flag=False,
                    escalated_flag=False,
                    csat_score=4.2,
                ),
                Ticket(
                    title="Search relevance drop",
                    description="Recent deploy reduced conversion due to poor ranking",
                    module="search",
                    priority=PriorityEnum.Critical,
                    status=StatusEnum.Resolved,
                    customer_segment="retail",
                    channel="web",
                    created_at=now - timedelta(days=3),
                    resolved_at=now - timedelta(days=2, hours=20),
                    assigned_associate_id=3,
                    resolution_hours=28,
                    reopened_flag=True,
                    escalated_flag=False,
                    csat_score=3.8,
                ),
                Ticket(
                    title="Delayed shipments in EU",
                    description="Logistics partners report delays causing SLA breaches",
                    module="shipping",
                    priority=PriorityEnum.High,
                    status=StatusEnum.InProgress,
                    customer_segment="retail",
                    channel="support",
                    created_at=now - timedelta(days=1),
                    assigned_associate_id=4,
                    resolution_hours=None,
                    reopened_flag=False,
                    escalated_flag=True,
                    csat_score=None,
                ),
            ]
            session.add_all(tickets)

        await session.commit()

    print("Seed completed. Default users: admin@example.com/admin123, agent@example.com/agent123.")


if __name__ == "__main__":
    asyncio.run(seed())
