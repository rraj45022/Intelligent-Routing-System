"""Seed minimal associates and tickets for local testing.

Run with: ./venv/bin/python -m backend.scripts.seed_sample_data
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.core.db import AsyncSessionLocal
from backend.models.associate import Associate, AvailabilityStatus
from backend.models.ticket_history import TicketHistory
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

        existing_associates = (await session.execute(select(Associate))).scalars().all()
        existing_by_name = {associate.name: associate for associate in existing_associates}
        default_associates = [
            (
                "Alice",
                ["billing", "payments"],
                AvailabilityStatus.available,
                260,
                45,
            ),
            (
                "Bob",
                ["auth", "security"],
                AvailabilityStatus.available,
                220,
                40,
            ),
            (
                "Charlie",
                ["search", "catalog"],
                AvailabilityStatus.busy,
                210,
                35,
            ),
            (
                "Diana",
                ["shipping", "logistics"],
                AvailabilityStatus.available,
                240,
                40,
            ),
            (
                "Eve",
                ["analytics", "billing"],
                AvailabilityStatus.available,
                180,
                30,
            ),
        ]
        for name, skills, availability_status, daily_capacity, max_concurrent_tickets in default_associates:
            if name not in existing_by_name:
                session.add(
                    Associate(
                        name=name,
                        skills=skills,
                        active=True,
                        availability_status=availability_status,
                        daily_capacity=daily_capacity,
                        max_concurrent_tickets=max_concurrent_tickets,
                    )
                )

        await session.flush()

        for name, skills, availability_status, daily_capacity, max_concurrent_tickets in default_associates:
            associate = existing_by_name.get(name)
            if associate is None:
                continue
            associate.skills = skills
            associate.availability_status = availability_status
            associate.daily_capacity = daily_capacity
            associate.max_concurrent_tickets = max_concurrent_tickets

        associates = (await session.execute(select(Associate).order_by(Associate.id))).scalars().all()
        associate_by_name = {associate.name: associate for associate in associates}

        existing_ticket = await session.scalar(select(Ticket.id))
        if not existing_ticket:
            now = datetime.now(timezone.utc)
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
                    assigned_associate_id=associate_by_name["Alice"].id,
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
                    assigned_associate_id=associate_by_name["Bob"].id,
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
                    assigned_associate_id=associate_by_name["Charlie"].id,
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
                    assigned_associate_id=associate_by_name["Diana"].id,
                    resolution_hours=None,
                    reopened_flag=False,
                    escalated_flag=True,
                    csat_score=None,
                ),
            ]
            session.add_all(tickets)

        existing_history = await session.scalar(select(TicketHistory.id))
        if not existing_history:
            now = datetime.now(timezone.utc)
            history_rows = [
                TicketHistory(
                    title="Checkout payment declined for repeat cards",
                    description="Returning customers see card declines after 3DS verification during checkout.",
                    module="billing",
                    priority=PriorityEnum.High,
                    customer_segment="retail",
                    channel="web",
                    created_at=now - timedelta(days=30),
                    resolved_at=now - timedelta(days=29, hours=18),
                    resolved_by_associate_id=associate_by_name["Alice"].id,
                    resolution_hours=6.0,
                    csat_score=4.7,
                ),
                TicketHistory(
                    title="UPI payments timing out on mobile checkout",
                    description="Mobile app payment attempts hang and fail for UPI users at confirmation.",
                    module="billing",
                    priority=PriorityEnum.Critical,
                    customer_segment="retail",
                    channel="mobile",
                    created_at=now - timedelta(days=27),
                    resolved_at=now - timedelta(days=26, hours=20),
                    resolved_by_associate_id=associate_by_name["Alice"].id,
                    resolution_hours=4.0,
                    csat_score=4.8,
                ),
                TicketHistory(
                    title="Enterprise SSO login loop",
                    description="Enterprise users are redirected back to login after successful SSO callback.",
                    module="auth",
                    priority=PriorityEnum.High,
                    customer_segment="enterprise",
                    channel="web",
                    created_at=now - timedelta(days=24),
                    resolved_at=now - timedelta(days=23, hours=16),
                    resolved_by_associate_id=associate_by_name["Bob"].id,
                    resolution_hours=8.0,
                    csat_score=4.4,
                ),
                TicketHistory(
                    title="OTP delivery delayed for login",
                    description="One-time passwords arrive late, causing login failures on mobile devices.",
                    module="auth",
                    priority=PriorityEnum.Medium,
                    customer_segment="retail",
                    channel="mobile",
                    created_at=now - timedelta(days=21),
                    resolved_at=now - timedelta(days=20, hours=18),
                    resolved_by_associate_id=associate_by_name["Bob"].id,
                    resolution_hours=5.0,
                    csat_score=4.1,
                ),
                TicketHistory(
                    title="Search results missing exact product matches",
                    description="Customers searching by SKU do not see the correct products in top results.",
                    module="search",
                    priority=PriorityEnum.High,
                    customer_segment="retail",
                    channel="web",
                    created_at=now - timedelta(days=18),
                    resolved_at=now - timedelta(days=17, hours=12),
                    resolved_by_associate_id=associate_by_name["Charlie"].id,
                    resolution_hours=12.0,
                    csat_score=4.3,
                ),
                TicketHistory(
                    title="Catalog filters break relevance ranking",
                    description="Applying brand and price filters lowers search precision significantly.",
                    module="search",
                    priority=PriorityEnum.Medium,
                    customer_segment="partner",
                    channel="support",
                    created_at=now - timedelta(days=15),
                    resolved_at=now - timedelta(days=14, hours=10),
                    resolved_by_associate_id=associate_by_name["Charlie"].id,
                    resolution_hours=14.0,
                    csat_score=4.0,
                ),
                TicketHistory(
                    title="Carrier webhook delays causing shipment status lag",
                    description="Shipment tracking updates arrive several hours late from EU carriers.",
                    module="shipping",
                    priority=PriorityEnum.High,
                    customer_segment="retail",
                    channel="support",
                    created_at=now - timedelta(days=12),
                    resolved_at=now - timedelta(days=11, hours=16),
                    resolved_by_associate_id=associate_by_name["Diana"].id,
                    resolution_hours=8.5,
                    csat_score=4.6,
                ),
                TicketHistory(
                    title="Warehouse dispatch integration dropping labels",
                    description="Bulk orders are not receiving shipping labels from the dispatch integration.",
                    module="shipping",
                    priority=PriorityEnum.Critical,
                    customer_segment="enterprise",
                    channel="support",
                    created_at=now - timedelta(days=9),
                    resolved_at=now - timedelta(days=8, hours=20),
                    resolved_by_associate_id=associate_by_name["Diana"].id,
                    resolution_hours=4.5,
                    csat_score=4.5,
                ),
                TicketHistory(
                    title="Revenue dashboard mismatches billing totals",
                    description="Finance dashboard shows lower revenue than payment gateway settlement reports.",
                    module="analytics",
                    priority=PriorityEnum.High,
                    customer_segment="enterprise",
                    channel="web",
                    created_at=now - timedelta(days=7),
                    resolved_at=now - timedelta(days=6, hours=12),
                    resolved_by_associate_id=associate_by_name["Eve"].id,
                    resolution_hours=10.0,
                    csat_score=4.4,
                ),
                TicketHistory(
                    title="Billing reports missing subscription renewals",
                    description="Monthly billing reports exclude auto-renewed subscriptions for some partner accounts.",
                    module="billing",
                    priority=PriorityEnum.Medium,
                    customer_segment="partner",
                    channel="web",
                    created_at=now - timedelta(days=5),
                    resolved_at=now - timedelta(days=4, hours=8),
                    resolved_by_associate_id=associate_by_name["Eve"].id,
                    resolution_hours=16.0,
                    csat_score=4.2,
                ),
            ]
            session.add_all(history_rows)

        await session.commit()

    print("Seed completed. Default users: admin@example.com/admin123, agent@example.com/agent123.")


if __name__ == "__main__":
    asyncio.run(seed())
